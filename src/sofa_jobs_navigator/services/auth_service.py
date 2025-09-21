"""Google Drive authentication service."""

from __future__ import annotations

import json
from pathlib import Path
import os
from typing import Optional, Dict, Any

try:
    from google.auth.transport.requests import Request, AuthorizedSession
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
except Exception:  # pragma: no cover - optional dependency
    Request = Credentials = InstalledAppFlow = None  # type: ignore

from platformdirs import user_config_path

from ..config.flags import FlagSet, FLAGS
from ..config.reference_data import CREDENTIALS_TEMPLATE

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    # Add OpenID Connect scopes to retrieve user info (email/profile)
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
CONFIG_APP_NAME = "sofa_jobs_navigator"
TOKEN_FILE_NAME = "token.json"
CLIENT_FILE_NAME = "credentials.json"
ACCOUNT_FILE_NAME = "account.json"


class AuthService:
    """Manage OAuth credentials for Google Drive access."""

    def __init__(self, *, flags: FlagSet = FLAGS, config_dir: Optional[Path] = None) -> None:
        self._flags = flags
        self._config_dir = config_dir or user_config_path(CONFIG_APP_NAME)
        self._token_path = Path(self._config_dir) / TOKEN_FILE_NAME
        self._client_path = Path(self._config_dir) / CLIENT_FILE_NAME
        self._account_path = Path(self._config_dir) / ACCOUNT_FILE_NAME
        self._creds: Optional[Credentials] = None

    # =================== PUBLIC API ===================
    def ensure_authenticated(self) -> Credentials:
        if self._flags.offline_mode:
            raise RuntimeError("Offline mode enabled; authentication disabled")
        if Credentials is None or InstalledAppFlow is None or Request is None:
            raise RuntimeError("Google authentication libraries are not installed.")

        if not self._creds:
            self._creds = self._load_cached_credentials()

        # Ensure credentials are present, valid, and have required scopes
        missing_or_invalid = (
            (not self._creds)
            or (not self._creds.valid)
            or (hasattr(self._creds, "has_scopes") and not self._creds.has_scopes(SCOPES))
        )
        if missing_or_invalid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                self._creds.refresh(Request())
            else:
                client_file = self._ensure_client_file()
                # Validate placeholder values to avoid confusing 400 invalid_client
                try:
                    data = json.loads(client_file.read_text(encoding='utf-8'))
                    cid = (
                        data.get('installed', {}).get('client_id')
                        or data.get('web', {}).get('client_id')
                    )
                    secret = (
                        data.get('installed', {}).get('client_secret')
                        or data.get('web', {}).get('client_secret')
                    )
                    if not cid or 'YOUR_CLIENT_ID' in cid or not secret or 'YOUR_CLIENT_SECRET' in secret:
                        raise RuntimeError(
                            f"OAuth client file contains placeholder values. Replace with a real OAuth 2.0 Desktop app JSON at: {client_file}\n"
                            "See README: Enable Drive API, create OAuth client (Desktop), download JSON as credentials.json."
                        )
                except json.JSONDecodeError:
                    raise RuntimeError(f"Invalid JSON in OAuth client file: {client_file}")

                flow = InstalledAppFlow.from_client_secrets_file(str(client_file), SCOPES)
                self._creds = flow.run_local_server(port=0)
            self._save_credentials(self._creds)
            # After (re-)auth, fetch and cache userinfo for UI/telemetry
            try:
                self._maybe_fetch_and_cache_userinfo(self._creds)
            except Exception:
                pass
        return self._creds

    def clear_tokens(self) -> None:
        self._creds = None
        if self._token_path.exists():
            self._token_path.unlink()
        if self._account_path.exists():
            self._account_path.unlink()

    # Expose account info helpers
    def get_account_email(self, creds: Optional[Credentials] = None) -> Optional[str]:
        """Return cached email if available; fetch and cache if not present.

        Requires the userinfo scopes requested above. If fetching fails, returns None.
        """
        cached = self._load_cached_account()
        if cached and isinstance(cached.get("email"), str):
            return cached["email"]
        c = creds or self._creds
        if c is None:
            return None
        try:
            info = self._fetch_userinfo(c)
            email = info.get("email") if isinstance(info, dict) else None
            if email:
                self._save_account_info({"email": email})
            return email
        except Exception:
            return None

    def get_token_expiry_iso(self, creds: Optional[Credentials] = None) -> Optional[str]:
        c = creds or self._creds
        if c is None or getattr(c, "expiry", None) is None:
            return None
        try:
            return c.expiry.isoformat()
        except Exception:
            return str(c.expiry)

    # =================== HELPERS ===================
    def _ensure_client_file(self) -> Path:
        if self._client_path.exists():
            return self._client_path
        # Support env-provided credentials for seamless distribution
        # SJN_CREDENTIALS_FILE: path to a client secrets JSON
        # SJN_CREDENTIALS_JSON: inline JSON (string)
        env_file = os.environ.get('SJN_CREDENTIALS_FILE')
        env_json = os.environ.get('SJN_CREDENTIALS_JSON')
        self._config_dir.mkdir(parents=True, exist_ok=True)
        if env_file:
            src = Path(env_file)
            if src.exists():
                self._client_path.write_bytes(src.read_bytes())
                return self._client_path
        if env_json:
            try:
                data = json.loads(env_json)
                with self._client_path.open('w', encoding='utf-8') as fh:
                    json.dump(data, fh, indent=2)
                return self._client_path
            except Exception:
                pass
        with self._client_path.open('w', encoding='utf-8') as fh:
            json.dump(CREDENTIALS_TEMPLATE, fh, indent=2)
        return self._client_path

    def _load_cached_credentials(self) -> Optional[Credentials]:
        if self._token_path.exists():
            try:
                # Load cached credentials with their original scopes; do not override here.
                return Credentials.from_authorized_user_file(str(self._token_path))
            except Exception:
                return None
        return None

    def _save_credentials(self, creds: Credentials) -> None:
        if self._flags.config_dry_run:
            return
        self._config_dir.mkdir(parents=True, exist_ok=True)
        with self._token_path.open('w', encoding='utf-8') as fh:
            fh.write(creds.to_json())

    # -------- Account info caching & fetching --------
    def _load_cached_account(self) -> Optional[Dict[str, Any]]:
        if self._account_path.exists():
            try:
                return json.loads(self._account_path.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None

    def _save_account_info(self, info: Dict[str, Any]) -> None:
        if self._flags.config_dry_run:
            return
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            self._account_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _maybe_fetch_and_cache_userinfo(self, creds: Credentials) -> None:
        if self._load_cached_account():
            return
        info = self._fetch_userinfo(creds)
        if isinstance(info, dict) and info.get("email"):
            self._save_account_info({"email": info["email"], "email_verified": info.get("email_verified")})

    def _fetch_userinfo(self, creds: Credentials) -> Optional[Dict[str, Any]]:
        """Fetch userinfo via OpenID endpoint using an authorized session."""
        if AuthorizedSession is None:
            return None
        try:
            session = AuthorizedSession(creds)
            resp = session.get("https://openidconnect.googleapis.com/v1/userinfo")
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            return None
        return None


# =================== END AUTH SERVICE ===================
