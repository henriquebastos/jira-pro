# Internal imports
from requestspro.auth import RecoverableAuth
from requestspro.sessions import ProSession


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
