from __future__ import annotations

import json
import re
import textwrap
import uuid
import zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from .config import REPORT_DIR


REPORT_INDEX = REPORT_DIR / "reports_index.json"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def summarize_transcript(transcript: str, max_words: int = 45) -> str:
    words = re.sub(r"\s+", " ", transcript or "").strip().split()
    if not words:
        return "Transcript summary unavailable."
    summary = " ".join(words[:max_words])
    return f"{summary}..." if len(words) > max_words else summary


def normalize_disclaimer_once(text: str, disclaimer: str) -> str:
    text = (text or "").strip()
    text = text.replace(disclaimer, "").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if re.search(r"(?im)^Disclaimer\s*$", text):
        text = re.sub(r"(?im)(^Disclaimer\s*$).*", rf"\1\n{disclaimer}", text, count=1, flags=re.S)
        return text.strip()
    return f"{text}\n\nDisclaimer\n{disclaimer}".strip()


def enforce_word_limit(text: str, min_words: int = 250, max_words: int = 350) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(" ,;:") + "."


def enforce_report_word_limit(text: str, disclaimer: str, max_words: int = 350) -> str:
    normalized = normalize_disclaimer_once(text, disclaimer)
    if len(normalized.split()) <= max_words:
        return normalized
    content = normalized.replace(disclaimer, "").strip()
    content = re.sub(r"(?im)^Disclaimer\s*$", "", content).strip()
    reserved = len(("Disclaimer " + disclaimer).split())
    content_limit = max(1, max_words - reserved)
    trimmed = enforce_word_limit(content, max_words=content_limit)
    return normalize_disclaimer_once(trimmed, disclaimer)


def save_report_artifacts(payload: dict[str, object], session_id: int | None = None, report_format: str = "pdf") -> dict[str, object]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_id = str(uuid.uuid4())
    generated_at = utc_timestamp()
    base = REPORT_DIR / report_id
    report_text = str(payload.get("final_report") or payload.get("report_text") or "")
    transcript = str(payload.get("transcript") or "")
    summary = summarize_transcript(transcript)
    metadata = {
        "report_id": report_id,
        "session_id": session_id,
        "risk_level": payload.get("risk_level") or payload.get("prediction") or "Unknown",
        "confidence": payload.get("confidence") or payload.get("final_probability") or 0,
        "transcript_summary": summary,
        "report_text": report_text,
        "created_at": generated_at,
    }
    report_format = report_format.lower()
    if report_format not in {"pdf", "docx"}:
        report_format = "pdf"
    report_path = base.with_suffix(f".{report_format}")
    txt_path = base.with_suffix(".txt")
    body = _artifact_body(metadata)
    txt_path.write_text(body, encoding="utf-8")
    if report_format == "docx":
        write_simple_docx(report_path, body)
    else:
        write_simple_pdf(report_path, body)

    record = {
        **metadata,
        "report_path": str(report_path),
        "report_format": report_format,
        "report_txt_path": str(txt_path),
    }
    index = _read_index()
    index[report_id] = record
    REPORT_INDEX.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return record


def get_report_artifact(report_id: str, fmt: str) -> Path | None:
    record = _read_index().get(report_id)
    if not record:
        return None
    fmt = fmt.lower()
    if fmt not in {"pdf", "docx"}:
        fmt = "pdf"
    path = Path(str(record.get("report_path", "")))
    if not path.exists() or path.suffix.lower() != f".{fmt}":
        path = REPORT_DIR / f"{report_id}.{fmt}"
        body = _artifact_body(record)
        if fmt == "docx":
            write_simple_docx(path, body)
        else:
            write_simple_pdf(path, body)
        record["report_path"] = str(path)
        record["report_format"] = fmt
        index = _read_index()
        index[report_id] = record
        REPORT_INDEX.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return path if path.exists() else None


def extract_report_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return _extract_docx(path)
    if suffix == ".pdf":
        return _extract_pdf_fallback(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def write_simple_docx(path: Path, text: str) -> None:
    paragraphs = "".join(
        f"<w:p><w:r><w:t>{escape(line)}</w:t></w:r></w:p>"
        for line in text.splitlines()
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{paragraphs}</w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", _content_types_xml())
        docx.writestr("_rels/.rels", _rels_xml())
        docx.writestr("word/document.xml", document)


def write_simple_pdf(path: Path, text: str) -> None:
    lines = []
    for raw in text.splitlines():
        wrapped = textwrap.wrap(raw, width=88) or [""]
        lines.extend(wrapped)
    pages = [lines[i : i + 45] for i in range(0, len(lines), 45)] or [[]]
    objects = ["<< /Type /Catalog /Pages 2 0 R >>"]
    kids = []
    for page_no, page_lines in enumerate(pages):
        page_obj = 3 + page_no * 2
        content_obj = page_obj + 1
        kids.append(f"{page_obj} 0 R")
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {content_obj} 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>")
        stream = _pdf_text_stream(page_lines)
        objects.append(f"<< /Length {len(stream.encode('latin-1', errors='replace'))} >>\nstream\n{stream}\nendstream")
    objects.insert(1, f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>")
    _write_pdf_objects(path, objects)


def _artifact_body(metadata: dict[str, object]) -> str:
    return (
        f"Generated: {metadata['created_at']}\n"
        f"Risk Level: {metadata['risk_level']}\n"
        f"Confidence: {metadata['confidence']}\n\n"
        f"Transcript Summary\n{metadata['transcript_summary']}\n\n"
        f"{metadata['report_text']}"
    )


def _read_index() -> dict[str, dict[str, object]]:
    if not REPORT_INDEX.exists():
        return {}
    try:
        return json.loads(REPORT_INDEX.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_text_stream(lines: list[str]) -> str:
    commands = ["BT", "/F1 10 Tf", "50 750 Td", "14 TL"]
    for line in lines:
        commands.append(f"({_pdf_escape(line)}) Tj")
        commands.append("T*")
    commands.append("ET")
    return "\n".join(commands)


def _write_pdf_objects(path: Path, objects: list[str]) -> None:
    chunks = ["%PDF-1.4\n"]
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(sum(len(chunk.encode("latin-1", errors="replace")) for chunk in chunks))
        chunks.append(f"{idx} 0 obj\n{obj}\nendobj\n")
    xref = sum(len(chunk.encode("latin-1", errors="replace")) for chunk in chunks)
    chunks.append(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n")
    for offset in offsets[1:]:
        chunks.append(f"{offset:010d} 00000 n \n")
    chunks.append(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF")
    path.write_bytes("".join(chunks).encode("latin-1", errors="replace"))


def _extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as docx:
        xml = docx.read("word/document.xml").decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", " ", xml)
    return re.sub(r"\s+", " ", text).strip()


def _extract_pdf_fallback(path: Path) -> str:
    raw = path.read_bytes().decode("latin-1", errors="ignore")
    matches = re.findall(r"\((.*?)\)\s*Tj", raw)
    if matches:
        return re.sub(r"\s+", " ", " ".join(matches)).strip()
    return re.sub(r"\s+", " ", raw).strip()[:5000]


def _content_types_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )


def _rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
