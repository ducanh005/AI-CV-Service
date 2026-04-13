import json
import re

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.models import AIScore, Application
from app.models.enums import ApplicationStatus
from app.schemas.ai import HRScoreCriteria


class AICVScoringService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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
        def _contains(text: str, token: str) -> bool:
            return token.strip().lower() in text.lower()

        def _fallback_score() -> tuple[float, str]:
            required_skills = [skill.strip() for skill in (criteria.required_skills if criteria else []) if skill.strip()]
            preferred_skills = [skill.strip() for skill in (criteria.preferred_skills if criteria else []) if skill.strip()]

            required_hits = sum(1 for skill in required_skills if _contains(cv_text, skill))
            preferred_hits = sum(1 for skill in preferred_skills if _contains(cv_text, skill))

            required_ratio = (required_hits / len(required_skills)) if required_skills else 0.5
            preferred_ratio = (preferred_hits / len(preferred_skills)) if preferred_skills else 0.5

            jd_keywords = {
                token.lower()
                for token in re.findall(r"[A-Za-z0-9+#.-]{4,}", job_description)
                if token.lower() not in {"with", "from", "that", "this", "have", "your", "candidate", "years"}
            }
            cv_text_lower = cv_text.lower()
            keyword_hits = sum(1 for kw in jd_keywords if kw in cv_text_lower)
            keyword_ratio = (keyword_hits / len(jd_keywords)) if jd_keywords else 0.5

            weighted = (required_ratio * 0.55) + (preferred_ratio * 0.2) + (keyword_ratio * 0.25)
            score = max(0.0, min(100.0, round(20 + (weighted * 80), 2)))
            reasoning = (
                f"Fallback scoring (no AISTUDIO key): required {required_hits}/{len(required_skills) or 0}, "
                f"preferred {preferred_hits}/{len(preferred_skills) or 0}, jd-keywords {keyword_hits}/{len(jd_keywords) or 0}."
            )
            return score, reasoning[:280]

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

        if not settings.AISTUDIO_API_KEY:
            return _fallback_score()

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
        except Exception as exc:
            raise AppException(f"Gemini scoring failed: {exc}", status_code=502) from exc

    async def upsert_application_score(
        self,
        application_id: int,
        score: float,
        reasoning: str,
        min_score: float | None = None,
    ) -> AIScore:
        from sqlalchemy import select

        normalized_score = max(0.0, min(100.0, round(score, 2)))
        threshold = settings.AI_DEFAULT_PASS_SCORE if min_score is None else min_score
        threshold = max(0.0, min(100.0, float(threshold)))

        application = await self.db.scalar(select(Application).where(Application.id == application_id))
        if application:
            application.status = (
                ApplicationStatus.ACCEPTED.value if normalized_score >= threshold else ApplicationStatus.REJECTED.value
            )

        existing = await self.db.scalar(select(AIScore).where(AIScore.application_id == application_id))
        if existing:
            existing.score = normalized_score
            existing.reasoning = reasoning
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        ai_score = AIScore(application_id=application_id, score=normalized_score, reasoning=reasoning)
        self.db.add(ai_score)
        await self.db.commit()
        await self.db.refresh(ai_score)
        return ai_score
