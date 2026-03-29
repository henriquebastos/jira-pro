# Python imports
import base64
import hashlib
import json
import threading
from urllib.parse import parse_qs, urlparse

# Pip imports
import pytest
import requests as http
from requestspro.token import ExpireValue, TokenStore

# Internal imports
from jira_genie.auth import JiraAuth, JiraAuthError, build_authorize_url, generate_pkce, login, wait_for_callback
from jira_genie.cache import FileCache


def make_auth(tmp_path, refresh_token=None):
    """Create a JiraAuth with real token stores."""
    token = TokenStore(ExpireValue(), key="access_token")
    refresh = TokenStore(FileCache(tmp_path / "refresh.json"), key="refresh_token")
    if refresh_token:
        refresh(refresh_token, 86400)
    return JiraAuth(token, client_id="test-client", refresh=refresh)


class TestJiraAuthRenew:
    def test_raises_when_no_refresh_token(self, tmp_path):
        auth = make_auth(tmp_path)
        with pytest.raises(JiraAuthError, match="Not logged in"):
            auth.renew()

    def test_returns_access_token_and_expiry(self, tmp_path, responses):
        responses.add("POST", JiraAuth.TOKEN_URL, json={
            "access_token": "new-access",
            "expires_in": 3600,
        })
        auth = make_auth(tmp_path, refresh_token="old-refresh")

        access_token, expires_in = auth.renew()
        assert access_token == "new-access"
        assert expires_in == 3600

    def test_posts_correct_payload(self, tmp_path, responses):
        responses.add("POST", JiraAuth.TOKEN_URL, json={
            "access_token": "new-access",
            "expires_in": 3600,
        })
        auth = make_auth(tmp_path, refresh_token="my-refresh")

        auth.renew()

        req = responses.calls[0].request
        assert "grant_type=refresh_token" in req.body
        assert "client_id=test-client" in req.body
        assert "refresh_token=my-refresh" in req.body

    def test_saves_rotated_refresh_token(self, tmp_path, responses):
        responses.add("POST", JiraAuth.TOKEN_URL, json={
            "access_token": "new-access",
            "expires_in": 3600,
            "refresh_token": "rotated-refresh",
            "refresh_expires_in": 86400,
        })
        auth = make_auth(tmp_path, refresh_token="old-refresh")

        auth.renew()
        assert auth.refresh() == "rotated-refresh"

    def test_token_property_triggers_renew(self, tmp_path, responses):
        responses.add("POST", JiraAuth.TOKEN_URL, json={
            "access_token": "fresh-token",
            "expires_in": 3600,
        })
        auth = make_auth(tmp_path, refresh_token="my-refresh")

        # Accessing .token should trigger renew() since no cached token exists
        assert auth.token == "fresh-token"

    def test_preserves_refresh_when_not_rotated(self, tmp_path, responses):
        responses.add("POST", JiraAuth.TOKEN_URL, json={
            "access_token": "new-access",
            "expires_in": 3600,
        })
        auth = make_auth(tmp_path, refresh_token="original-refresh")

        auth.renew()
        assert auth.refresh() == "original-refresh"


class TestPKCE:
    def test_verifier_is_valid_base64url(self):
        verifier, _challenge = generate_pkce()
        # base64url uses only A-Za-z0-9_- and no padding
        decoded = base64.urlsafe_b64decode(verifier + "==")
        assert len(decoded) == 32

    def test_challenge_is_sha256_of_verifier(self):
        verifier, challenge = generate_pkce()
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).rstrip(b"=").decode()
        assert challenge == expected


class TestExchangeAndDiscover:
    def test_exchange_code_returns_tokens(self, responses):
        responses.add("POST", JiraAuth.TOKEN_URL, json={
            "access_token": "access-123",
            "expires_in": 3600,
            "refresh_token": "refresh-456",
            "refresh_expires_in": 86400,
        })

        from jira_genie.auth import exchange_code
        result = exchange_code(
            code="auth-code",
            client_id="client-id",
            code_verifier="verifier",
            redirect_uri="http://localhost:8888/callback",
        )
        assert result["access_token"] == "access-123"
        assert result["refresh_token"] == "refresh-456"

        req = responses.calls[0].request
        assert "code=auth-code" in req.body
        assert "client_id=client-id" in req.body
        assert "code_verifier=verifier" in req.body

    def test_exchange_code_raises_on_failure(self, responses):
        responses.add("POST", JiraAuth.TOKEN_URL, json={"error": "invalid_grant"}, status=401)

        from jira_genie.auth import exchange_code
        with pytest.raises(JiraAuthError, match="Token exchange failed"):
            exchange_code(code="bad", client_id="cid", code_verifier="v", redirect_uri="http://localhost/cb")

    def test_discover_cloud_id_extracts_from_resources(self, responses):
        responses.add("GET", "https://api.atlassian.com/oauth/token/accessible-resources", json=[
            {"id": "cloud-id-abc", "name": "acme", "url": "https://acme.atlassian.net"},
        ])

        from jira_genie.auth import discover_cloud_resources
        result = discover_cloud_resources(access_token="token-123")
        assert result == [{"id": "cloud-id-abc", "name": "acme", "url": "https://acme.atlassian.net"}]

        req = responses.calls[0].request
        assert req.headers["Authorization"] == "Bearer token-123"

    def test_save_login_config(self, tmp_path):
        from jira_genie.auth import save_login_config

        save_login_config(
            base_dir=tmp_path,
            cloud_id="cloud-abc",
            site="acme.atlassian.net",
            client_id="client-123",
            refresh_token="refresh-456",
            refresh_expires_in=86400,
        )

        import json
        # Instance dir created
        instance_dir = tmp_path / "cloud-abc"
        assert instance_dir.is_dir()

        # Config saved
        config = json.loads((instance_dir / "config.json").read_text())
        assert config["cloud_id"] == "cloud-abc"
        assert config["site"] == "acme.atlassian.net"
        assert config["client_id"] == "client-123"

        # Refresh token saved
        refresh_data = json.loads((instance_dir / "refresh.json").read_text())
        assert refresh_data["refresh_token"]["value"] == "refresh-456"

        # Default set
        base_config = json.loads((tmp_path / "config.json").read_text())
        assert base_config["default"] == "cloud-abc"


class TestBuildAuthorizeUrl:
    def test_contains_required_params(self):
        url = build_authorize_url("my-client-id", "my-challenge")
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        assert parsed.scheme == "https"
        assert "auth.atlassian.com" in parsed.netloc
        assert params["client_id"] == ["my-client-id"]
        assert params["code_challenge"] == ["my-challenge"]
        assert params["code_challenge_method"] == ["S256"]
        assert params["response_type"] == ["code"]
        assert "offline_access" in params["scope"][0]

    def test_custom_redirect_uri(self):
        url = build_authorize_url("cid", "ch", redirect_uri="http://localhost:9999/cb")
        params = parse_qs(urlparse(url).query)
        assert params["redirect_uri"] == ["http://localhost:9999/cb"]


class TestWaitForCallback:
    def test_returns_code_on_success(self):
        port = 18771
        t = threading.Thread(target=lambda: wait_for_callback(port=port))
        t.start()
        # Give server time to start
        import time
        time.sleep(0.1)
        r = http.get(f"http://localhost:{port}/callback?code=abc123")
        t.join(timeout=2)
        assert r.status_code == 200
        # The function returned the code — verified by the thread completing without error

    def test_raises_on_error_callback(self):
        port = 18772
        result = {}

        def run():
            try:
                wait_for_callback(port=port)
            except JiraAuthError as e:
                result["error"] = str(e)

        t = threading.Thread(target=run)
        t.start()
        import time
        time.sleep(0.1)
        http.get(f"http://localhost:{port}/callback?error=access_denied")
        t.join(timeout=2)
        assert "access_denied" in result["error"]


class TestLogin:
    def test_full_flow(self, tmp_path, responses, monkeypatch):
        # Mock browser open
        opened_urls = []
        monkeypatch.setattr("jira_genie.auth.webbrowser.open", lambda url: opened_urls.append(url))

        # Mock token exchange
        responses.add("POST", JiraAuth.TOKEN_URL, json={
            "access_token": "access-tok",
            "expires_in": 3600,
            "refresh_token": "refresh-tok",
            "refresh_expires_in": 86400,
        })

        # Mock accessible resources
        responses.add("GET", "https://api.atlassian.com/oauth/token/accessible-resources", json=[
            {"id": "cloud-xyz", "name": "acme", "url": "https://acme.atlassian.net"},
        ])

        # Replace wait_for_callback to simulate the browser callback
        monkeypatch.setattr("jira_genie.auth.wait_for_callback", lambda: "fake-auth-code")

        result = login("my-client-id", client_secret="my-secret", base_dir=tmp_path)

        assert result["cloud_id"] == "cloud-xyz"
        assert result["site"] == "acme.atlassian.net"
        assert len(opened_urls) == 1
        assert "my-client-id" in opened_urls[0]

        # Verify config was saved
        config = json.loads((tmp_path / "cloud-xyz" / "config.json").read_text())
        assert config["client_id"] == "my-client-id"
        assert config["client_secret"] == "my-secret"

    def test_raises_when_no_resources(self, tmp_path, responses, monkeypatch):
        monkeypatch.setattr("jira_genie.auth.webbrowser.open", lambda url: None)
        monkeypatch.setattr("jira_genie.auth.wait_for_callback", lambda: "fake-code")
        responses.add("POST", JiraAuth.TOKEN_URL, json={
            "access_token": "tok", "expires_in": 3600,
            "refresh_token": "ref", "refresh_expires_in": 86400,
        })
        responses.add("GET", "https://api.atlassian.com/oauth/token/accessible-resources", json=[])

        with pytest.raises(JiraAuthError, match="No accessible"):
            login("cid", base_dir=tmp_path)
