from urllib.parse import urlencode

from app.core.config import settings


LINKEDIN_AUTH_BASE_URL = "https://www.linkedin.com/oauth/v2/authorization"


def get_linkedin_oauth_url(state: str, scopes: list[str] | None = None) -> str:
    scopes = scopes or ["openid", "profile", "email"]
    params = {
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "state": state,
        "scope": " ".join(scopes),
    }
    return f"{LINKEDIN_AUTH_BASE_URL}?{urlencode(params)}"


def exchange_code_for_profile(code: str) -> dict[str, str]:
    # Mock profile payload for now.
    return {
        "provider": "linkedin",
        "code": code,
        "full_name": "LinkedIn Candidate",
        "email": "linkedin.candidate@example.com",
        "headline": "Software Engineer",
    }
