import secrets
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.core.exceptions import AppException
from app.integrations.oauth.google_oauth import (
    build_authorize_url as build_google_authorize_url,
)
from app.integrations.oauth.google_oauth import (
    exchange_code_for_token as exchange_google_code_for_token,
)
from app.integrations.oauth.google_oauth import get_profile as get_google_profile
from app.integrations.oauth.linkedin_oauth import (
    build_authorize_url as build_linkedin_authorize_url,
)
from app.integrations.oauth.linkedin_oauth import (
    exchange_code_for_token as exchange_linkedin_code_for_token,
)
from app.integrations.oauth.linkedin_oauth import get_profile as get_linkedin_profile

SUPPORTED_PROVIDERS = {"google", "linkedin"}
SUPPORTED_MODES = {"login", "register"}


class SocialOAuthService:
    def _ensure_enabled(self) -> None:
        if not settings.ENABLE_SOCIAL_AUTH:
            raise AppException("Social authentication is disabled", status_code=503)

    @staticmethod
    def normalize_provider(provider: str) -> str:
        value = (provider or "").strip().lower()
        if value not in SUPPORTED_PROVIDERS:
            raise AppException("Unsupported OAuth provider", status_code=404)
        return value

    @staticmethod
    def normalize_mode(mode: str) -> str:
        value = (mode or "login").strip().lower()
        return value if value in SUPPORTED_MODES else "login"

    def _require_provider_config(self, provider: str) -> None:
        if provider == "google":
            if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.GOOGLE_REDIRECT_URI:
                raise AppException("Google OAuth is not configured", status_code=500)
            return

        if not settings.LINKEDIN_CLIENT_ID or not settings.LINKEDIN_CLIENT_SECRET or not settings.LINKEDIN_REDIRECT_URI:
            raise AppException("LinkedIn OAuth is not configured", status_code=500)

    def build_authorize_url(self, provider: str, mode: str, state: str | None) -> dict[str, str]:
        self._ensure_enabled()

        safe_provider = self.normalize_provider(provider)
        safe_mode = self.normalize_mode(mode)
        safe_state = (state or "").strip() or f"{safe_mode}:{secrets.token_urlsafe(18)}"

        self._require_provider_config(safe_provider)

        if safe_provider == "google":
            auth_url = build_google_authorize_url(
                client_id=settings.GOOGLE_CLIENT_ID,
                redirect_uri=settings.GOOGLE_REDIRECT_URI,
                scope=settings.GOOGLE_OAUTH_SCOPE,
                state=safe_state,
            )
        else:
            auth_url = build_linkedin_authorize_url(
                client_id=settings.LINKEDIN_CLIENT_ID,
                redirect_uri=settings.LINKEDIN_REDIRECT_URI,
                scope=settings.LINKEDIN_OAUTH_SCOPE,
                state=safe_state,
            )

        return {"auth_url": auth_url, "state": safe_state, "mode": safe_mode}

    def build_callback_redirect(
        self,
        provider: str,
        *,
        code: str | None,
        state: str | None,
        error: str | None,
        error_description: str | None,
    ) -> str:
        self._ensure_enabled()

        safe_provider = self.normalize_provider(provider)
        callback_uri = (
            settings.GOOGLE_FRONTEND_CALLBACK_URI
            if safe_provider == "google"
            else settings.LINKEDIN_FRONTEND_CALLBACK_URI
        )
        if not callback_uri:
            raise AppException("Frontend callback URI is not configured", status_code=500)

        params: dict[str, str] = {}
        if code:
            params["code"] = code
        if state:
            params["state"] = state
        if error:
            params["error"] = error
        if error_description:
            params["error_description"] = error_description

        if not params:
            raise AppException("Missing callback parameters", status_code=400)

        separator = "&" if "?" in callback_uri else "?"
        return f"{callback_uri}{separator}{urlencode(params)}"

    async def exchange_code(self, provider: str, code: str) -> dict:
        self._ensure_enabled()

        safe_provider = self.normalize_provider(provider)
        self._require_provider_config(safe_provider)

        try:
            if safe_provider == "google":
                return await exchange_google_code_for_token(
                    client_id=settings.GOOGLE_CLIENT_ID,
                    client_secret=settings.GOOGLE_CLIENT_SECRET,
                    redirect_uri=settings.GOOGLE_REDIRECT_URI,
                    code=code,
                )

            return await exchange_linkedin_code_for_token(
                client_id=settings.LINKEDIN_CLIENT_ID,
                client_secret=settings.LINKEDIN_CLIENT_SECRET,
                redirect_uri=settings.LINKEDIN_REDIRECT_URI,
                code=code,
            )
        except (httpx.HTTPError, RuntimeError) as exc:
            raise AppException(f"OAuth token exchange failed: {exc}", status_code=502) from exc

    async def fetch_profile(self, provider: str, access_token: str, id_token: str | None = None) -> dict:
        self._ensure_enabled()

        safe_provider = self.normalize_provider(provider)
        try:
            if safe_provider == "google":
                return await get_google_profile(access_token)
            return await get_linkedin_profile(access_token, id_token=id_token)
        except (httpx.HTTPError, RuntimeError) as exc:
            raise AppException(f"OAuth profile fetch failed: {exc}", status_code=502) from exc
