# Python imports
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import threading
from urllib.parse import parse_qs, urlencode, urlparse
import webbrowser

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


SCOPES = "read:jira-work write:jira-work read:jira-user manage:jira-project offline_access"
REDIRECT_URI = "http://localhost:8888/callback"
CALLBACK_PORT = 8888


def build_authorize_url(client_id, code_challenge, redirect_uri=REDIRECT_URI, scopes=SCOPES):
    """Build the Atlassian OAuth 2.0 authorize URL."""
    params = {
        "audience": "api.atlassian.com",
        "client_id": client_id,
        "scope": scopes,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "prompt": "consent",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{JiraAuth.AUTH_URL}?{urlencode(params)}"


def wait_for_callback(port=CALLBACK_PORT):
    """Start a local HTTP server and wait for the OAuth callback. Returns the authorization code."""
    result = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = parse_qs(urlparse(self.path).query)
            if "code" in query:
                result["code"] = query["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Login successful!</h1><p>You can close this tab.</p>")
            else:
                result["error"] = query.get("error", ["unknown"])[0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Login failed</h1>")
            # Shut down server after handling
            threading.Thread(target=self.server.shutdown).start()

        def log_message(self, format, *args):
            pass  # Suppress server logs

    server = HTTPServer(("localhost", port), CallbackHandler)
    server.serve_forever()

    if "error" in result:
        raise JiraAuthError(f"OAuth callback error: {result['error']}")

    return result["code"]


def login(client_id, base_dir="~/.config/jira-cli"):
    """Run the full OAuth 2.0 login flow. Opens browser, waits for callback, saves tokens."""
    base_dir = Path(base_dir).expanduser()

    # Generate PKCE
    code_verifier, code_challenge = generate_pkce()

    # Open browser
    authorize_url = build_authorize_url(client_id, code_challenge)
    print("Opening browser for Atlassian login...")
    webbrowser.open(authorize_url)

    # Wait for callback
    print(f"Waiting for callback on {REDIRECT_URI}...")
    code = wait_for_callback()

    # Exchange code for tokens
    print("Exchanging code for tokens...")
    tokens = exchange_code(code, client_id, code_verifier, REDIRECT_URI)

    # Discover cloud resources
    print("Discovering Jira Cloud instances...")
    resources = discover_cloud_resources(tokens["access_token"])

    if not resources:
        raise JiraAuthError("No accessible Jira Cloud instances found.")

    # Use first resource (or let user choose if multiple)
    resource = resources[0]
    cloud_id = resource["id"]
    site = resource["url"].replace("https://", "")

    # Save config
    save_login_config(
        base_dir=base_dir,
        cloud_id=cloud_id,
        site=site,
        client_id=client_id,
        refresh_token=tokens["refresh_token"],
        refresh_expires_in=tokens.get("refresh_expires_in", 0),
    )

    return {"cloud_id": cloud_id, "site": site, "message": f"Logged in to {site}"}
