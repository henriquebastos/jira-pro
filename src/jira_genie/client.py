# Internal imports
from requestspro.client import Client, MainClient
from requestspro.sessions import ProSession


class JiraSession(ProSession):
    def before_prepare_body(self, request):
        """Skip JSON encoding when there's no body — CloudFront blocks GET with Content-Type: application/json."""
        if not request.data and request.json is None:
            return
        super().before_prepare_body(request)


class IssueSubClient(Client):
    def get(self, issue_key, fields=None, expand=None):
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        if expand:
            params["expand"] = expand
        return super().get(url=f"rest/api/3/issue/{issue_key}", params=params or None)

    def create(self, payload):
        return self.post(url="rest/api/3/issue", json=payload)

    def edit(self, issue_key, payload):
        response = self.session.request("PUT", f"rest/api/3/issue/{issue_key}", json=payload)
        response.raise_for_status()
        return response.json() if response.content else None

    def delete(self, issue_key):
        response = self.session.request("DELETE", f"rest/api/3/issue/{issue_key}")
        response.raise_for_status()
        return response.json() if response.content else None

    def get_transitions(self, issue_key):
        result = super().get(url=f"rest/api/3/issue/{issue_key}/transitions")
        return result.get("transitions", [])

    def transition(self, issue_key, status_name):
        transitions = self.get_transitions(issue_key)
        match = next((t for t in transitions if t["name"] == status_name), None)
        if not match:
            available = [t["name"] for t in transitions]
            raise ValueError(f"Transition '{status_name}' not found. Available: {available}")
        payload = {"transition": {"id": match["id"]}}
        response = self.session.request("POST", f"rest/api/3/issue/{issue_key}/transitions", json=payload)
        response.raise_for_status()
        return response.json() if response.content else None

    def assign(self, issue_key, account_id):
        response = self.session.request("PUT", f"rest/api/3/issue/{issue_key}/assignee", json={"accountId": account_id})
        response.raise_for_status()
        return response.json() if response.content else None

    def add_comment(self, issue_key, body):
        from jira_genie.adf import markdown_to_adf
        adf_body = markdown_to_adf(body) if isinstance(body, str) else body
        response = self.session.request("POST", f"rest/api/3/issue/{issue_key}/comment", json={"body": adf_body})
        response.raise_for_status()
        return response.json() if response.content else None

    def get_comments(self, issue_key):
        result = super().get(url=f"rest/api/3/issue/{issue_key}/comment")
        return result.get("comments", [])

    def link(self, inward_key, outward_key, link_type):
        return self.post(url="rest/api/3/issueLink", json={
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key},
        })


class SearchSubClient(Client):
    def jql(self, query, fields=None, max_results=50):
        params = {"jql": query, "maxResults": max_results}
        if fields:
            params["fields"] = ",".join(fields) if isinstance(fields, list) else fields
        result = super().get(url="rest/api/3/search/jql", params=params)
        return result.get("issues", [])

    def jql_all(self, query, fields=None):
        all_issues = []
        start_at = 0
        while True:
            params = {"jql": query, "startAt": start_at, "maxResults": 50}
            if fields:
                params["fields"] = ",".join(fields) if isinstance(fields, list) else fields
            result = super().get(url="rest/api/3/search/jql", params=params)
            issues = result.get("issues", [])
            all_issues.extend(issues)
            if start_at + len(issues) >= result.get("total", 0):
                break
            start_at += len(issues)
        return all_issues


class UserSubClient(Client):
    def myself(self):
        return super().get(url="rest/api/3/myself")

    def search(self, query):
        return super().get(url="rest/api/3/user/search", params={"query": query})


class SprintSubClient(Client):
    def get(self, sprint_id):
        return super().get(url=f"rest/agile/1.0/sprint/{sprint_id}")

    def current(self, board_id):
        result = super().get(url=f"rest/agile/1.0/board/{board_id}/sprint", params={"state": "active"})
        values = result.get("values", [])
        return values[0] if values else None

    def list(self, board_id, state=None):
        params = {}
        if state:
            params["state"] = state
        result = super().get(url=f"rest/agile/1.0/board/{board_id}/sprint", params=params or None)
        return result.get("values", [])

    def issues(self, sprint_id, fields=None):
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        result = super().get(url=f"rest/agile/1.0/sprint/{sprint_id}/issue", params=params or None)
        return result.get("issues", [])


class BoardSubClient(Client):
    def get(self, board_id):
        return super().get(url=f"rest/agile/1.0/board/{board_id}")

    def list(self, project_key=None):
        params = {}
        if project_key:
            params["projectKeyOrId"] = project_key
        result = super().get(url="rest/agile/1.0/board", params=params or None)
        return result.get("values", [])

    def backlog(self, board_id, fields=None):
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        result = super().get(url=f"rest/agile/1.0/board/{board_id}/backlog", params=params or None)
        return result.get("issues", [])


class JiraClient(MainClient):
    def __init__(self, session):
        super().__init__(session, audit=False)
        self.issue = IssueSubClient(session)
        self.search = SearchSubClient(session)
        self.sprint = SprintSubClient(session)
        self.board = BoardSubClient(session)
        self.user = UserSubClient(session)

    @classmethod
    def from_config(cls, instance=None):
        """Create client from stored OAuth config."""
        # Internal imports to avoid circular deps
        import json

        from requestspro.token import ExpireValue, TokenStore

        from jira_genie.auth import JiraAuth
        from jira_genie.cache import FileCache
        from jira_genie.config import discover_instance_dir

        instance_dir = discover_instance_dir(instance=instance)
        config = json.loads((instance_dir / "config.json").read_text())

        cloud_id = config["cloud_id"]
        client_id = config["client_id"]
        client_secret = config.get("client_secret")

        base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/"
        token = TokenStore(ExpireValue(), key="access_token", offset=10)
        refresh = TokenStore(FileCache(instance_dir / "refresh.json"), key="refresh_token")
        auth = JiraAuth(token, client_id, refresh, client_secret=client_secret)
        session = JiraSession(auth=auth, base_url=base_url)
        return cls(session)
