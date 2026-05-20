from openai import OpenAI
from ..config import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MODEL, SAFETY_NOTE
from ..report_files import enforce_report_word_limit, summarize_transcript


class ReportAgent:
    def __init__(self):
        self.client = None
        if NVIDIA_API_KEY:
            self.client = OpenAI(
                base_url=NVIDIA_BASE_URL,
                api_key=NVIDIA_API_KEY
            )

    def _generate_rule_based_report(self, risk_level, confidence, observations, indicators, knowledge, transcript_summary="", user_name=""):
        confidence_text = f"{confidence:.2%}" if isinstance(confidence, float) else str(confidence)
        observations = observations or []
        knowledge = knowledge or []
        transcript_summary = transcript_summary or "Transcript summary unavailable."
        greeting = self._greeting(user_name)
        evidence_notes = knowledge[:3] if knowledge else ["Insufficient supporting evidence available."]
        report = f"""Risk Summary
{greeting}Screening output suggests possible {risk_level} cognitive-speech risk with confidence of {confidence_text}. This is a screening estimate, not a diagnosis. Transcript summary: {transcript_summary}

Key Observations
"""
        if observations:
            for obs in observations[:4]:
                report += f"- {obs}\n"
        else:
            report += "- No specific speech observations were available from the submitted data.\n"

        report += """
Evidence-Based Notes
"""
        for note in evidence_notes:
            report += f"- {note}\n"

        report += """
Recommendation
Professional consultation may be beneficial if the user or caregiver has concerns about cognition, communication, or daily functioning. The screening result should be reviewed alongside clinical history and qualified assessment.

Disclaimer
"""
        report += SAFETY_NOTE
        return enforce_report_word_limit(report, SAFETY_NOTE)

    def _greeting(self, user_name: str) -> str:
        name = str(user_name or "").strip()
        if not name:
            return "Hello, your speech sample has been analyzed using our AI-assisted cognitive screening system. "
        first_name = name.split()[0][:40]
        return f"Hello {first_name}, your speech sample has been analyzed using our AI-assisted cognitive screening system. "

    def run(self, payload: dict[str, object]) -> dict[str, object]:
        risk_level = payload.get("risk_level", payload.get("prediction", "Unknown"))
        confidence = float(payload.get("confidence", payload.get("final_probability", 0.0)))
        observations = payload.get("supporting_observations", [])
        indicators = payload.get("behavioral_indicators", [])
        knowledge = payload.get("retrieved_knowledge", [])
        rationale = payload.get("rationale", "")
        transcript = payload.get("transcript", "")
        transcript_summary = str(payload.get("transcript_summary") or summarize_transcript(str(transcript)))
        user_name = str(payload.get("user_name") or payload.get("name") or "")
        
        try:
            if self.client:
                prompt = f"""Generate a concise clinician-style cognitive screening report of 250-350 words.

CRITICAL PROBABILITY SPECIFICATION:
All probabilities in context represent P(dementia/high-risk), where higher values indicate greater cognitive decline risk.
- Risk Level {risk_level} comes from: final_probability = (0.6 * prob2) + (0.4 * prob1)
- Higher probability = Higher dementia/cognitive decline risk
- Lower probability = Lower dementia/cognitive decline risk

STRICT RULES:
- Do NOT diagnose dementia or any medical condition
- Do NOT claim certainty
- Use ONLY the information provided
- If retrieved evidence is empty or insufficient, write exactly: "Insufficient supporting evidence available."
- Use cautious phrases: "may indicate", "suggests possible", "potential marker"
- NO dramatic wording, NO fake medical claims, NO hallucinations
- Do NOT add sections beyond the allowed section headings
- Append the mandatory disclaimer exactly once
- In Risk Summary, start with one brief greeting using the user's first name if provided, such as "Hello Aditya, your speech sample has been analyzed using our AI-assisted cognitive screening system."
- Do not repeat the user's name after the greeting

REQUIRED SECTIONS:
Risk Summary
Key Observations
Evidence-Based Notes
Recommendation
Disclaimer

Information to use:
User Name: {user_name}
Risk Level: {risk_level}
Confidence: {confidence:.4f}
Key Observations: {observations[:3]}
Evidence: {knowledge[:2]}
Transcript Summary: {transcript_summary}

Disclaimer: {SAFETY_NOTE}"""
                
                response = self.client.chat.completions.create(
                    model=NVIDIA_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a safe, professional AI assistant that generates concise, evidence-grounded cognitive screening reports. You never make medical diagnoses, never claim certainty, and always prioritize safety. CRITICAL: All probabilities represent P(dementia/high-risk), where higher values indicate greater cognitive decline risk."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=600,
                    temperature=0.2
                )
                report = response.choices[0].message.content.strip()
                report = enforce_report_word_limit(report, SAFETY_NOTE)
            else:
                report = self._generate_rule_based_report(risk_level, confidence, observations, indicators, knowledge, transcript_summary, user_name)
        except Exception as e:
            print(f"LLM Error: {e}")
            report = self._generate_rule_based_report(risk_level, confidence, observations, indicators, knowledge, transcript_summary, user_name)
        
        payload["transcript_summary"] = transcript_summary
        payload["report_text"] = report
        payload["report"] = report
        return payload
