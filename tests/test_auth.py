# Pip imports
import pytest
from requestspro.token import ExpireValue, TokenStore

# Internal imports
from jira.auth import JiraAuth, JiraAuthError
from jira.cache import FileCache


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

    def test_preserves_refresh_when_not_rotated(self, tmp_path, responses):
        responses.add("POST", JiraAuth.TOKEN_URL, json={
            "access_token": "new-access",
            "expires_in": 3600,
        })
        auth = make_auth(tmp_path, refresh_token="original-refresh")

        auth.renew()
        assert auth.refresh() == "original-refresh"
