import re

from openai import OpenAI
from ..config import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MODEL, SAFETY_NOTE
from ..rag.knowledge_base import retrieve

DOMAIN_KEYWORDS = [
    "dementia", "cognitive", "memory", "speech", "screening", "cognitive decline",
    "mfcc", "pauses", "speech rate", "lexical diversity", "report", "risk",
    "cognitive screening", "cognitive markers", "cognitive impairment", "uploaded report",
    "confidence", "observation", "transcript", "word finding", "fluency"
]

POLITE_REFUSAL_MESSAGE = (
    "I am designed specifically for dementia and cognitive speech screening support. I cannot answer unrelated questions."
)
REFUSAL_MESSAGE = POLITE_REFUSAL_MESSAGE

DIAGNOSIS_REFUSAL_MESSAGE = "I cannot diagnose medical conditions. This system provides AI-assisted cognitive screening insights only. Please consult a qualified healthcare professional."
CONCERN_RESPONSE = (
    "I understand this result may feel concerning. This screening tool is designed to identify potential "
    "speech-related cognitive indicators, but it cannot provide a medical diagnosis. A qualified healthcare "
    "professional can provide proper evaluation and guidance."
)


class ChatAgent:
    def __init__(self):
        self.client = None
        if NVIDIA_API_KEY:
            self.client = OpenAI(
                base_url=NVIDIA_BASE_URL,
                api_key=NVIDIA_API_KEY
            )

    def is_domain_question(self, question: str) -> bool:
        question_lower = question.lower()
        for keyword in DOMAIN_KEYWORDS:
            if keyword in question_lower:
                return True
        return False

    def is_diagnosis_question(self, question: str) -> bool:
        question_lower = question.lower()
        diagnosis_keywords = ["do i have dementia", "am i diagnosed with", "diagnose me", "what disease do i have", "do i have alzheimer"]
        for keyword in diagnosis_keywords:
            if keyword in question_lower:
                return True
        return False

    def is_concern_message(self, question: str) -> bool:
        question_lower = question.lower()
        concern_keywords = ["i am scared", "i'm scared", "is this serious", "should i worry", "worried", "afraid", "concerned"]
        return any(keyword in question_lower for keyword in concern_keywords)

    def _user_prefix(self, context: dict | None) -> str:
        name = str((context or {}).get("user_name") or "").strip()
        if not name:
            return ""
        first_name = name.split()[0][:40]
        return f"{first_name}, "

    def _generate_rule_based_answer(self, question: str, retrieved: list) -> str:
        answer = "Based on available screening information:\n\n"
        if retrieved:
            for item in retrieved[:3]:
                answer += f"- {item}\n"
        else:
            answer += "- I do not know. Insufficient supporting evidence available.\n"
        
        answer += f"\n{SAFETY_NOTE}"
        return answer

    def run(self, question: str, context: dict = None) -> str:
        context = context or {}
        user_prefix = self._user_prefix(context)

        if self.is_diagnosis_question(question):
            return f"{user_prefix}{DIAGNOSIS_REFUSAL_MESSAGE}"

        if self.is_concern_message(question):
            return f"{user_prefix}{CONCERN_RESPONSE}"

        uploaded_report_text = str(context.get("uploaded_report_text") or context.get("report_text") or "")

        if not self.is_domain_question(question) and not uploaded_report_text:
            return POLITE_REFUSAL_MESSAGE

        retrieved = retrieve(" ".join([question, uploaded_report_text[:1000]]))
        report_context = uploaded_report_text[:3000]
        
        try:
            if self.client:
                prompt = f"""You are a safe, dementia/cognitive speech screening chatbot. Answer only from retrieved evidence and provided report context.
You must:
1. Never diagnose medical conditions
2. Never claim certainty
3. Never prescribe medication or treatment plans
4. If evidence is unavailable, say "I do not know" and "Insufficient supporting evidence available."
5. Keep the answer short, cautious, professional, and easy to understand
6. Do not answer unrelated topics
7. Use the user's name only once if provided, and keep the tone warm, calm, and professional

User Name: {context.get("user_name") or ""}
Question: {question}
Retrieved Evidence: {retrieved}
Uploaded/Generated Report Context: {report_context}
Other Context: {context}"""
                
                response = self.client.chat.completions.create(
                    model=NVIDIA_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a safe, professional AI assistant focused on dementia and cognitive speech screening. You never make medical diagnoses, never claim certainty, and always prioritize safety. CRITICAL: All probabilities in context represent P(dementia/high-risk), where higher values indicate greater cognitive decline risk."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                answer = response.choices[0].message.content.strip()
                if not retrieved and not report_context:
                    return "I do not know. Insufficient supporting evidence available."
                answer = self._sanitize_answer(answer)
                if "qualified healthcare professional" not in answer.lower() and ("diagnos" in question.lower() or "risk" in question.lower()):
                    answer += f"\n\n{SAFETY_NOTE}"
                return answer
            else:
                return self._generate_rule_based_answer(question, retrieved)
        except Exception as e:
            print(f"Chat LLM Error: {e}")
            return self._generate_rule_based_answer(question, retrieved)

    def _sanitize_answer(self, answer: str, max_words: int = 130) -> str:
        answer = re.sub(r"【[^】]+】", "", answer)
        answer = re.sub(r"\[\d+\]", "", answer)
        answer = re.sub(r"\n{3,}", "\n\n", answer).strip()
        words = answer.split()
        if len(words) > max_words:
            answer = " ".join(words[:max_words]).rstrip(" ,;:") + "."
        unsafe_patterns = [
            (re.compile(r"\bdefinitely\b", re.I), "may"),
            (re.compile(r"\bcertainly\b", re.I), "may"),
            (re.compile(r"\bhas dementia\b", re.I), "has speech markers that may be associated with cognitive change"),
            (re.compile(r"\bdiagnosed with\b", re.I), "screened for markers associated with"),
            (re.compile(r"\bprescribe\b|\bmedication\b|\btreatment plan\b", re.I), "professional consultation"),
        ]
        for pattern, replacement in unsafe_patterns:
            answer = pattern.sub(replacement, answer)
        return answer
