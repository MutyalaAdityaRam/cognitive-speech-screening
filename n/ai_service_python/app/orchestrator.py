from __future__ import annotations

from pathlib import Path

from .agents.data_agent import DataAgent
from .agents.explanation_agent import ExplanationAgent
from .agents.prediction_agent import PredictionAgent
from .agents.report_agent import ReportAgent
from .agents.retrieval_agent import RetrievalAgent
from .agents.safety_agent import SafetyAgent


class OrchestratorAgent:
    def __init__(self) -> None:
        self.data_agent = DataAgent()
        self.prediction_agent = PredictionAgent()
        self.explanation_agent = ExplanationAgent()
        self.retrieval_agent = RetrievalAgent()
        self.report_agent = ReportAgent()
        self.safety_agent = SafetyAgent()

    def _validate_probability_direction(self, payload: dict[str, object]) -> dict[str, object]:
        """
        CRITICAL VALIDATION: Ensure all probabilities represent dementia/high-risk (Class 0).
        
        Class 0 = dementia / high-risk
        Class 1 = non_dementia / low-risk
        
        All probabilities (prob1, prob2, final_probability, confidence) must represent
        the probability of dementia/high-risk.
        """
        prob1 = float(payload.get("prob1", 0.0))
        prob2 = float(payload.get("prob2", 0.0))
        final_prob = float(payload.get("final_probability", 0.0))
        
        # Validate that probabilities are in valid range [0, 1]
        if not (0.0 <= prob1 <= 1.0):
            raise ValueError(f"Invalid prob1: {prob1}. Must be in [0, 1].")
        if not (0.0 <= prob2 <= 1.0):
            raise ValueError(f"Invalid prob2: {prob2}. Must be in [0, 1].")
        if not (0.0 <= final_prob <= 1.0):
            raise ValueError(f"Invalid final_probability: {final_prob}. Must be in [0, 1].")
        
        # Verify prediction aligns with probability
        prediction = str(payload.get("prediction", "")).lower()
        risk_level = str(payload.get("risk_level", "")).lower()
        
        is_high_risk = final_prob >= 0.5
        expected_prediction = "high risk" if is_high_risk else "low risk"
        
        if prediction != expected_prediction and prediction:
            raise ValueError(f"Prediction mismatch: {prediction} vs expected {expected_prediction}")
        if risk_level != expected_prediction and risk_level:
            raise ValueError(f"Risk level mismatch: {risk_level} vs expected {expected_prediction}")
        
        return payload

    def run_from_csv(self, csv_path: str | Path) -> dict[str, object]:
        data = self.data_agent.run_from_csv(csv_path)
        if not data.get("valid"):
            return {"status": "needs_restart", "message": data.get("message", "No voice detected. Please restart reading.")}
        return self._run(data)

    def run_from_audio(self, audio_path: str | Path) -> dict[str, object]:
        data = self.data_agent.run_from_audio(audio_path)
        if not data.get("valid"):
            return {"status": "needs_restart", "message": data.get("message", "No voice detected. Please restart reading.")}
        return self._run(data)

    def run_transcription(self, audio_path: str | Path) -> dict[str, object]:
        data = self.data_agent.transcribe_from_audio(audio_path)
        if not data.get("valid"):
            return {"status": "needs_restart", "message": data.get("message", "No voice detected. Please restart reading.")}
        return {
            "transcript": data.get("transcript", ""),
            "transcript_clean": data.get("transcript_clean", ""),
            "audio_file_path": data.get("audio_file_path", ""),
        }

    def run_report(self, payload: dict[str, object]) -> dict[str, object]:
        payload = self.explanation_agent.run(payload)
        payload = self.retrieval_agent.run(payload)
        payload = self.report_agent.run(payload)
        payload = self.safety_agent.run(payload)
        return payload

    def _run(self, data: dict[str, object]) -> dict[str, object]:
        payload = {**data, **self.prediction_agent.run(data)}
        # CRITICAL: Validate probability direction before proceeding
        payload = self._validate_probability_direction(payload)
        payload = self.explanation_agent.run(payload)
        payload = self.retrieval_agent.run(payload)
        payload = self.report_agent.run(payload)
        payload = self.safety_agent.run(payload)
        return {
            "prediction": payload["prediction"],
            "risk_level": payload["risk_level"],
            "prob1": payload["prob1"],
            "prob2": payload["prob2"],
            "final_probability": payload["final_probability"],
            "confidence": payload["confidence"],
            "model_outputs": payload["model_outputs"],
            "supporting_observations": payload["supporting_observations"],
            "behavioral_indicators": payload.get("behavioral_indicators", []),
            "retrieved_knowledge": payload["retrieved_knowledge"],
            "recommendations": payload.get("recommendations", []),
            "final_report": payload["final_report"],
            "report_text": payload["report_text"],
            "transcript": payload.get("transcript", ""),
            "audio_file_path": payload.get("audio_file_path", ""),
        }
