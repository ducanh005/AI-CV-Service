import json
import re

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import AIScore
from app.schemas.ai import HRScoreCriteria


class AICVScoringService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def heuristic_score(cv_text: str, job_description: str, criteria: HRScoreCriteria | None = None) -> tuple[float, str]:
        cv_words = {word.strip().lower() for word in cv_text.split() if word.strip()}
        jd_words = {word.strip().lower() for word in job_description.split() if word.strip()}
        if not jd_words:
            return 0.0, "No job description words provided"

        overlap = len(cv_words.intersection(jd_words))
        base_score = min(100.0, round((overlap / max(1, len(jd_words))) * 100.0, 2))

        required_bonus = 0.0
        matched_required = 0
        if criteria and criteria.required_skills:
            required_tokens = {skill.strip().lower() for skill in criteria.required_skills if skill.strip()}
            matched_required = len(required_tokens.intersection(cv_words))
            required_bonus = round((matched_required / max(1, len(required_tokens))) * 20.0, 2)

        score = min(100.0, round(base_score * 0.8 + required_bonus, 2))
        reasoning = f"Matched {overlap} JD terms and {matched_required} required skills"
        return score, reasoning

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

    async def score_with_ai(
        self,
        cv_text: str,
        job_description: str,
        criteria: HRScoreCriteria | None = None,
    ) -> tuple[float, str]:
        if not settings.AISTUDIO_API_KEY:
            return self.heuristic_score(cv_text, job_description, criteria)

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

        prompt = (
            "You are an expert recruiter. Score how well this CV matches the job description on a scale of 0 to 100. "
            "Return only strict JSON with exactly two keys: score (number) and reasoning (string, max 220 chars).\n\n"
            f"HR_CRITERIA:\n{criteria_text}\n\n"
            f"CV:\n{cv_text}\n\n"
            f"JOB_DESCRIPTION:\n{job_description}"
        )

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{settings.AISTUDIO_MODEL}:generateContent"
            f"?key={settings.AISTUDIO_API_KEY}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt,
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=settings.AISTUDIO_TIMEOUT_SECONDS) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

            candidates = data.get("candidates") or []
            content = candidates[0].get("content", {}) if candidates else {}
            parts = content.get("parts") or []
            model_text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
            if not model_text:
                raise ValueError("Empty AI response")

            parsed = self._extract_json_object(model_text)
            raw_score = float(parsed.get("score", 0))
            score = max(0.0, min(100.0, round(raw_score, 2)))
            reasoning = str(parsed.get("reasoning", "AI score generated")).strip() or "AI score generated"
            return score, reasoning[:280]
        except Exception:
            return self.heuristic_score(cv_text, job_description, criteria)

    async def upsert_application_score(self, application_id: int, score: float, reasoning: str) -> AIScore:
        from sqlalchemy import select

        existing = await self.db.scalar(select(AIScore).where(AIScore.application_id == application_id))
        if existing:
            existing.score = score
            existing.reasoning = reasoning
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        ai_score = AIScore(application_id=application_id, score=score, reasoning=reasoning)
        self.db.add(ai_score)
        await self.db.commit()
        await self.db.refresh(ai_score)
        return ai_score
