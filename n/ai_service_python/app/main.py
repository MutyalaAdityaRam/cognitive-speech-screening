from __future__ import annotations

import os
os.environ["MKL_THREADING_LAYER"] = "GNU"

import re
import shutil
import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile, mkdtemp

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .orchestrator import OrchestratorAgent
from .agents.chat_agent import ChatAgent
from .config import REPORT_DIR
from .report_files import extract_report_text, get_report_artifact, save_report_artifacts

app = FastAPI(title="Cognitive Speech Screening AI Service", version="3.0.0")


class ReportRequest(BaseModel):
    user_name: str | None = None
    name: str | None = None
    prediction: str | None = None
    confidence: float | None = None
    prob1: float | None = None
    prob2: float | None = None
    final_probability: float | None = None
    transcript: str | None = None
    supporting_observations: list[str] | None = None
    behavioral_indicators: list[str] | None = None
    retrieved_knowledge: list[str] | None = None
    rationale: str | None = None
    audio_file_path: str | None = None
    report_format: str | None = "pdf"


class ChatRequest(BaseModel):
    question: str
    context: dict | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)) -> dict[str, object]:
    """
    Predict cognitive decline risk from audio.
    
    CRITICAL: All returned probabilities (prob1, prob2, final_probability, confidence) 
    represent P(dementia/high-risk), where:
    - Higher values (closer to 1.0) = Higher dementia/cognitive decline risk
    - Lower values (closer to 0.0) = Lower dementia/cognitive decline risk
    
    Ensemble: final_probability = (0.6 * prob2) + (0.4 * prob1)
    Prediction: "High Risk" if final_probability >= 0.5, else "Low Risk"
    """
    original = Path(file.filename or "audio.wav")
    suffix = original.suffix or ".wav"
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", original.stem)[:80] or "audio"
    temp_dir = Path(mkdtemp(prefix="speech_audio_"))
    tmp_path = temp_dir / f"{safe_stem}{suffix}"
    tmp_path.write_bytes(await file.read())
    try:
        try:
            result = OrchestratorAgent().run_from_audio(tmp_path)
            # Ensure JSON response includes probability direction note
            result["_probability_note"] = "All probabilities represent P(dementia/high-risk)"
            return result
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail=f"Missing required artifact: {exc}") from exc
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/predict/audio")
async def predict_audio(file: UploadFile = File(...)) -> dict[str, object]:
    return await predict(file)


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)) -> dict[str, object]:
    original = Path(file.filename or "audio.wav")
    suffix = original.suffix or ".wav"
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", original.stem)[:80] or "audio"
    temp_dir = Path(mkdtemp(prefix="speech_audio_"))
    tmp_path = temp_dir / f"{safe_stem}{suffix}"
    tmp_path.write_bytes(await file.read())
    try:
        return OrchestratorAgent().run_transcription(tmp_path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/report")
def report(request: ReportRequest) -> dict[str, object]:
    payload = request.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(status_code=422, detail="report payload is required")
    result = OrchestratorAgent().run_report(payload)
    return {
        "report_text": result.get("report_text", result.get("final_report", "")),
        "final_report": result.get("final_report", ""),
        "transcript_summary": result.get("transcript_summary", ""),
        "supporting_observations": result.get("supporting_observations", []),
        "behavioral_indicators": result.get("behavioral_indicators", []),
        "retrieved_knowledge": result.get("retrieved_knowledge", []),
        "recommendations": result.get("recommendations", []),
    }


@app.post("/generate-report")
def generate_report(request: ReportRequest) -> dict[str, object]:
    """
    Generate a clinician-style cognitive screening report.
    
    CRITICAL: All probability values in response represent P(dementia/high-risk):
    - Higher values = Higher dementia/cognitive decline risk
    - Lower values = Lower dementia/cognitive decline risk
    """
    payload = request.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(status_code=422, detail="report payload is required")
    result = OrchestratorAgent().run_report(payload)
    artifact = save_report_artifacts(result, report_format=(request.report_format or "pdf"))
    return {
        "report_id": artifact["report_id"],
        "report_path": artifact["report_path"],
        "report_format": artifact["report_format"],
        "download_url": f"/download-report/{artifact['report_id']}?format={artifact['report_format']}",
        "report_text": result.get("report_text", ""),
        "final_report": result.get("final_report", ""),
        "transcript_summary": result.get("transcript_summary", ""),
        "prob1": result.get("prob1", 0.0),
        "prob2": result.get("prob2", 0.0),
        "final_probability": result.get("final_probability", 0.0),
        "confidence": result.get("confidence", 0.0),
        "risk_level": result.get("risk_level", ""),
        "prediction": result.get("prediction", ""),
        "_probability_note": "All probabilities represent P(dementia/high-risk)",
        "created_at": artifact["created_at"],
    }


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, object]:
    """
    Chat endpoint for dementia and cognitive screening support.
    
    CRITICAL: The chatbot uses corrected probabilities where all values represent
    P(dementia/high-risk). Higher values indicate greater cognitive decline risk.
    """
    answer = ChatAgent().run(request.question, request.context)
    return {"answer": answer}


@app.post("/upload-report")
async def upload_report(
    file: UploadFile = File(...),
    user_id: int | None = Form(default=None),
    user_name: str | None = Form(default=None),
) -> dict[str, object]:
    suffix = Path(file.filename or "report").suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(status_code=422, detail="Only PDF, DOCX, or TXT reports are supported")
    upload_dir = REPORT_DIR / "uploaded"
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(file.filename or "report").stem)[:80] or "report"
    report_id = str(uuid.uuid4())
    path = upload_dir / f"{report_id}_{safe_stem}{suffix}"
    path.write_bytes(await file.read())
    try:
        extracted_text = extract_report_text(path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Unable to extract report text: {exc}") from exc
    answer = ChatAgent().run(
        "Explain the uploaded cognitive screening report in cautious terms.",
        {"uploaded_report_text": extracted_text, "user_name": user_name or ""},
    )
    return {
        "uploaded_report_id": report_id,
        "user_id": user_id,
        "file_path": str(path),
        "extracted_text": extracted_text,
        "analysis": answer,
    }


@app.get("/download-report/{report_id}")
def download_report(report_id: str, format: str = Query(default="pdf", pattern="^(pdf|docx)$")):
    path = get_report_artifact(report_id, format)
    if path is None:
        raise HTTPException(status_code=404, detail="Report not found")
    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if format == "docx"
        else "application/pdf"
    )
    return FileResponse(path, media_type=media_type, filename=path.name)


@app.post("/predict/csv")
async def predict_csv(file: UploadFile = File(...)) -> dict[str, object]:
    suffix = Path(file.filename or "input.csv").suffix or ".csv"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    try:
        return OrchestratorAgent().run_from_csv(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)
