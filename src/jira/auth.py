# Python imports
import base64
import hashlib
import json
import os
from pathlib import Path

# Pip imports
import requests
from requestspro.auth import RecoverableAuth
from requestspro.sessions import ProSession
from requestspro.token import TokenStore

# Internal imports
from jira.cache import FileCache

PKCE_BYTES = 32


def generate_pkce(nbytes=PKCE_BYTES):
    """Generate PKCE code_verifier and code_challenge for OAuth 2.0."""
    verifier = base64.urlsafe_b64encode(os.urandom(nbytes)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


class JiraAuthError(Exception):
    pass


class JiraAuth(RecoverableAuth):
    """Self-contained Atlassian OAuth with auto-refresh. No acli dependency."""

    AUTH_URL = "https://auth.atlassian.com/authorize"
    TOKEN_URL = "https://auth.atlassian.com/oauth/token"
    SESSION_CLASS = ProSession

    def __init__(self, token, client_id, refresh):
        self.client_id = client_id
        self.refresh = refresh
        super().__init__(token)

    def renew(self):
        """Refresh the access token using the stored refresh_token."""
        refresh_token = self.refresh()
        if not refresh_token:
            raise JiraAuthError("Not logged in. Run: jira auth login")

        r = self.session_class().post(
            self.TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "refresh_token": refresh_token,
            },
        )
        r.raise_for_status()
        data = r.json()

        # Atlassian rotates refresh tokens — save the new one
        if data.get("refresh_token"):
            self.refresh(data["refresh_token"], data.get("refresh_expires_in", 0))

        return data["access_token"], data["expires_in"]


ACCESSIBLE_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"


def exchange_code(code, client_id, code_verifier, redirect_uri, token_url=JiraAuth.TOKEN_URL):
    """Exchange authorization code for tokens."""
    r = requests.post(
        token_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        },
    )
    r.raise_for_status()
    return r.json()


def discover_cloud_resources(access_token, url=ACCESSIBLE_RESOURCES_URL):
    """Fetch accessible Jira Cloud resources for the authenticated user."""
    r = requests.get(url, headers={"Authorization": f"Bearer {access_token}"})
    r.raise_for_status()
    return r.json()


def save_login_config(base_dir, cloud_id, site, client_id, refresh_token, refresh_expires_in):
    """Persist login config and refresh token to instance directory."""
    base = Path(base_dir)
    instance_dir = base / cloud_id
    instance_dir.mkdir(parents=True, exist_ok=True)

    # Save instance config
    config = {"cloud_id": cloud_id, "site": site, "client_id": client_id}
    (instance_dir / "config.json").write_text(json.dumps(config, indent=2))

    # Save refresh token via FileCache (same interface as TokenStore backend)
    refresh_cache = FileCache(instance_dir / "refresh.json")
    refresh_store = TokenStore(refresh_cache, key="refresh_token")
    refresh_store(refresh_token, refresh_expires_in)

    # Set as default instance
    base_config_path = base / "config.json"
    base_config = json.loads(base_config_path.read_text()) if base_config_path.exists() else {}
    base_config["default"] = cloud_id
    base_config_path.write_text(json.dumps(base_config, indent=2))
