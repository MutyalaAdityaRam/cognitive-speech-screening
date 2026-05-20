import re

from ..config import SAFETY_NOTE
from ..report_files import enforce_report_word_limit


class SafetyAgent:
    blocked_patterns = [
        (re.compile(r"\bdefinitely\s+has dementia\b", re.I), "shows markers that may be associated with cognitive decline"),
        (re.compile(r"\bdefinitely\b", re.I), "may"),
        (re.compile(r"\bcertainly\b", re.I), "may"),
        (re.compile(r"\bdiagnosed with\b", re.I), "shows screening markers associated with"),
        (re.compile(r"\bhas dementia\b", re.I), "shows markers that may be associated with cognitive decline"),
        (re.compile(r"\bwill decline rapidly\b", re.I), "should be discussed with a healthcare professional"),
        (re.compile(r"\bprescribe\b|\bmedication\b|\btreatment plan\b", re.I), "professional consultation"),
    ]
    allowed_sections = [
        "Risk Summary",
        "Key Observations",
        "Evidence-Based Notes",
        "Recommendation",
        "Disclaimer",
    ]

    def run(self, payload: dict[str, object]) -> dict[str, object]:
        report = str(payload.get("report_text", payload.get("report", "")))
        for pattern, replacement in self.blocked_patterns:
            report = pattern.sub(replacement, report)
        report = re.sub(r"\bmay shows\b", "may show", report, flags=re.I)
        report = self._enforce_sections(report)
        report = self._compact_sections(report)
        report = enforce_report_word_limit(report, SAFETY_NOTE)
        payload["final_report"] = report
        payload["report"] = report
        payload["report_text"] = report
        return payload

    def _enforce_sections(self, report: str) -> str:
        found = {}
        current = None
        for line in report.splitlines():
            heading = self._section_heading(line)
            if heading:
                current = heading
                found.setdefault(current, [])
                continue
            if current:
                found[current].append(line)

        if not found:
            return report

        normalized = []
        for section in self.allowed_sections:
            normalized.append(section)
            body = "\n".join(found.get(section, [])).strip()
            if section == "Evidence-Based Notes" and not body:
                body = "Insufficient supporting evidence available."
            if section == "Disclaimer":
                body = SAFETY_NOTE
            normalized.append(body)
            normalized.append("")
        return "\n".join(normalized).strip()

    def _compact_sections(self, report: str) -> str:
        section_limits = {
            "Risk Summary": 65,
            "Key Observations": 75,
            "Evidence-Based Notes": 90,
            "Recommendation": 45,
            "Disclaimer": 25,
        }
        found = {}
        current = None
        for line in report.splitlines():
            heading = self._section_heading(line)
            if heading:
                current = heading
                found.setdefault(current, [])
                continue
            if current:
                found[current].append(line)

        if set(found) != set(self.allowed_sections):
            return report

        fallbacks = {
            "Risk Summary": "Screening results should be interpreted cautiously as AI-assisted cognitive speech screening information, not a diagnosis.",
            "Key Observations": "No additional observations were available beyond the submitted screening data.",
            "Evidence-Based Notes": "Insufficient supporting evidence available.",
            "Recommendation": "Professional consultation may be beneficial if there are concerns about cognition, communication, or daily functioning.",
            "Disclaimer": SAFETY_NOTE,
        }
        compacted = []
        for section in self.allowed_sections:
            compacted.append(section)
            body = "\n".join(found.get(section, [])).strip()
            if section == "Disclaimer":
                body = SAFETY_NOTE
            if section == "Recommendation":
                body = fallbacks[section]
            if not body:
                body = fallbacks[section]
            compacted.append(self._clean_body(self._limit_words(body, section_limits[section])))
            compacted.append("")
        return "\n".join(compacted).strip()

    def _limit_words(self, text: str, max_words: int) -> str:
        words = text.split()
        if len(words) <= max_words:
            return text
        sentences = re.findall(r"[^.!?]+[.!?]", text)
        kept: list[str] = []
        count = 0
        for sentence in sentences:
            sentence_words = sentence.split()
            if kept and count + len(sentence_words) > max_words:
                break
            if not kept and len(sentence_words) > max_words:
                break
            kept.append(sentence.strip())
            count += len(sentence_words)
        if kept:
            return " ".join(kept)
        return " ".join(words[:max_words]).rstrip(" ,;:") + "."

    def _clean_body(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"\bdoes not\.$", "does not establish a diagnosis.", text, flags=re.I)
        text = re.sub(r"\bdo not confirm any\.$", "do not establish a diagnosis.", text, flags=re.I)
        text = re.sub(r"\bdoes not confirm any\.$", "does not establish a diagnosis.", text, flags=re.I)
        if text and text[-1] not in ".!?":
            return f"{text}."
        return text

    def _section_heading(self, line: str) -> str | None:
        stripped = line.strip().strip("*").strip()
        stripped = re.sub(r"^#+\s*", "", stripped)
        stripped = re.sub(r"^\d+[\.)]\s*", "", stripped)
        stripped = stripped.replace("\u2011", "-").replace("\u2010", "-").replace("\u2013", "-").replace("\u2014", "-")
        stripped = stripped.strip(":").strip()
        for section in self.allowed_sections:
            if stripped.lower() == section.lower():
                return section
        return None
