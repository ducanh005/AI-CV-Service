import json
import re

import httpx

from app.config import settings
from app.schemas import HRScoreCriteria


class ScoringService:
    @staticmethod
    def _extract_json_object(text: str) -> dict:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            raise ValueError("No JSON object found in model response")
        return json.loads(match.group(0))

    @staticmethod
    def _prompt(cv_text: str, job_description: str, criteria: HRScoreCriteria | None) -> str:
        criteria_text = "No explicit HR criteria provided."
        if criteria:
            criteria_text = (
                f"Required skills: {criteria.required_skills}\n"
                f"Preferred skills: {criteria.preferred_skills}\n"
                f"Education keywords: {criteria.education_keywords}\n"
                f"Minimum years experience: {criteria.min_years_experience}\n"
                f"Weights(skill/experience/education): "
                f"{criteria.skill_weight}/{criteria.experience_weight}/{criteria.education_weight}"
            )

        return (
            "You are an expert recruiter. Score how well this CV matches the job description on a scale of 0 to 100. "
            "Return only strict JSON with exactly two keys: score (number) and reasoning (string, max 220 chars).\n\n"
            f"HR_CRITERIA:\n{criteria_text}\n\n"
            f"CV:\n{cv_text}\n\n"
            f"JOB_DESCRIPTION:\n{job_description}"
        )

    def _score_with_gemini(
        self,
        cv_text: str,
        job_description: str,
        criteria: HRScoreCriteria | None,
    ) -> tuple[float, str]:
        if not settings.AISTUDIO_API_KEY:
            raise RuntimeError("AISTUDIO_API_KEY is not configured")

        prompt = self._prompt(cv_text, job_description, criteria)
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{settings.AISTUDIO_MODEL}:generateContent"
            f"?key={settings.AISTUDIO_API_KEY}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        with httpx.Client(timeout=settings.AISTUDIO_TIMEOUT_SECONDS) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        candidates = data.get("candidates") or []
        content = candidates[0].get("content", {}) if candidates else {}
        parts = content.get("parts") or []
        model_text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
        if not model_text:
            raise ValueError("Empty AI Studio response")

        parsed = self._extract_json_object(model_text)
        raw_score = float(parsed.get("score", 0))
        score = max(0.0, min(100.0, round(raw_score, 2)))
        reasoning = str(parsed.get("reasoning", "AI score generated")).strip() or "AI score generated"
        return score, reasoning[:280]

    def score(self, cv_text: str, job_description: str, criteria: HRScoreCriteria | None = None) -> tuple[float, str, str]:
        score, reasoning = self._score_with_gemini(cv_text, job_description, criteria)
        return score, reasoning, "gemini"
