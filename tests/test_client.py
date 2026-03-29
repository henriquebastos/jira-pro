# Pip imports
import pytest

# Internal imports
from jira_genie.client import (
    BoardSubClient,
    IssueSubClient,
    JiraSession,
    SearchSubClient,
    SprintSubClient,
    UserSubClient,
)

BASE_URL = "https://api.atlassian.com/ex/jira/cloud-abc/"


class TestJiraSession:
    def test_get_skips_content_type(self, responses):
        """GET without body should not set Content-Type: application/json."""
        responses.add("GET", f"{BASE_URL}test", json={"ok": True})
        session = JiraSession(base_url=BASE_URL)
        session.request("GET", "test")
        req = responses.calls[0].request
        assert "application/json" not in (req.headers.get("Content-Type") or "")

    def test_post_sets_content_type(self, responses):
        """POST with JSON body should set Content-Type."""
        responses.add("POST", f"{BASE_URL}test", json={"ok": True})
        session = JiraSession(base_url=BASE_URL)
        session.request("POST", "test", json={"key": "value"})
        req = responses.calls[0].request
        assert "application/json" in req.headers.get("Content-Type", "")


@pytest.fixture()
def issue(responses):
    from requestspro.sessions import ProSession

    session = ProSession(base_url=BASE_URL)
    return IssueSubClient(session)


@pytest.fixture()
def search(responses):
    from requestspro.sessions import ProSession

    session = ProSession(base_url=BASE_URL)
    return SearchSubClient(session)


class TestIssueSubClient:
    def test_get_calls_correct_url(self, issue, responses):
        responses.add("GET", f"{BASE_URL}rest/api/3/issue/DEV-123", json={"key": "DEV-123"})
        result = issue.get("DEV-123")
        assert result["key"] == "DEV-123"

    def test_get_passes_fields_param(self, issue, responses):
        responses.add("GET", f"{BASE_URL}rest/api/3/issue/DEV-123", json={"key": "DEV-123"})
        issue.get("DEV-123", fields=["summary", "status"])
        req = responses.calls[0].request
        assert "fields=summary%2Cstatus" in req.url

    def test_create_posts_correct_payload(self, issue, responses):
        responses.add("POST", f"{BASE_URL}rest/api/3/issue", json={"key": "DEV-999"})
        result = issue.create({"fields": {"project": {"key": "DEV"}, "summary": "New"}})
        assert result["key"] == "DEV-999"
        assert responses.calls[0].request.body

    def test_edit_puts_to_correct_url(self, issue, responses):
        responses.add("PUT", f"{BASE_URL}rest/api/3/issue/DEV-123", json={})
        issue.edit("DEV-123", {"fields": {"summary": "Updated"}})
        req = responses.calls[0].request
        assert req.method == "PUT"

    def test_edit_handles_204_no_content(self, issue, responses):
        responses.add("PUT", f"{BASE_URL}rest/api/3/issue/DEV-123", body="", status=204)
        result = issue.edit("DEV-123", {"fields": {"summary": "Updated"}})
        assert result is None

    def test_delete_sends_delete(self, issue, responses):
        responses.add("DELETE", f"{BASE_URL}rest/api/3/issue/DEV-123", body="", status=204)
        result = issue.delete("DEV-123")
        assert responses.calls[0].request.method == "DELETE"
        assert result is None  # empty body returns None


class TestSearchSubClient:
    def test_jql_searches(self, search, responses):
        responses.add("GET", f"{BASE_URL}rest/api/3/search/jql", json={
            "issues": [{"key": "DEV-1"}, {"key": "DEV-2"}],
            "total": 2,
        })
        result = search.jql("project = DEV")
        assert len(result) == 2
        assert result[0]["key"] == "DEV-1"

    def test_jql_with_string_fields(self, search, responses):
        responses.add("GET", f"{BASE_URL}rest/api/3/search/jql", json={
            "issues": [{"key": "DEV-1"}], "total": 1,
        })
        search.jql("project = DEV", fields="summary,status")
        req = responses.calls[0].request
        assert "fields=summary%2Cstatus" in req.url

    def test_jql_all_with_fields(self, search, responses):
        responses.add("GET", f"{BASE_URL}rest/api/3/search/jql", json={
            "issues": [{"key": "DEV-1"}], "total": 1,
        })
        search.jql_all("project = DEV", fields=["summary"])
        req = responses.calls[0].request
        assert "fields=summary" in req.url

    def test_jql_all_paginates(self, search, responses):
        responses.add("GET", f"{BASE_URL}rest/api/3/search/jql", json={
            "issues": [{"key": "DEV-1"}],
            "startAt": 0,
            "maxResults": 1,
            "total": 2,
        })
        responses.add("GET", f"{BASE_URL}rest/api/3/search/jql", json={
            "issues": [{"key": "DEV-2"}],
            "startAt": 1,
            "maxResults": 1,
            "total": 2,
        })
        result = search.jql_all("project = DEV")
        assert len(result) == 2
        assert result[0]["key"] == "DEV-1"
        assert result[1]["key"] == "DEV-2"


AGILE_URL = "https://api.atlassian.com/ex/jira/cloud-abc/"


@pytest.fixture()
def sprint(responses):
    from requestspro.sessions import ProSession

    session = ProSession(base_url=AGILE_URL)
    return SprintSubClient(session)


@pytest.fixture()
def board(responses):
    from requestspro.sessions import ProSession

    session = ProSession(base_url=AGILE_URL)
    return BoardSubClient(session)


class TestSprintSubClient:
    def test_get(self, sprint, responses):
        responses.add("GET", f"{AGILE_URL}rest/agile/1.0/sprint/42", json={"id": 42, "name": "Sprint 5"})
        result = sprint.get(42)
        assert result["id"] == 42

    def test_current(self, sprint, responses):
        responses.add("GET", f"{AGILE_URL}rest/agile/1.0/board/10/sprint", json={
            "values": [{"id": 42, "state": "active"}],
        })
        result = sprint.current(10)
        assert result["id"] == 42

    def test_list(self, sprint, responses):
        responses.add("GET", f"{AGILE_URL}rest/agile/1.0/board/10/sprint", json={
            "values": [{"id": 42}, {"id": 43}],
        })
        result = sprint.list(10, state="active,future")
        assert len(result) == 2

    def test_issues(self, sprint, responses):
        responses.add("GET", f"{AGILE_URL}rest/agile/1.0/sprint/42/issue", json={
            "issues": [{"key": "DEV-1"}, {"key": "DEV-2"}],
        })
        result = sprint.issues(42)
        assert len(result) == 2


    def test_issues_with_fields(self, sprint, responses):
        responses.add("GET", f"{AGILE_URL}rest/agile/1.0/sprint/42/issue", json={
            "issues": [{"key": "DEV-1"}],
        })
        sprint.issues(42, fields=["summary", "status"])
        req = responses.calls[0].request
        assert "fields=summary%2Cstatus" in req.url


class TestBoardSubClient:
    def test_get(self, board, responses):
        responses.add("GET", f"{AGILE_URL}rest/agile/1.0/board/10", json={"id": 10, "name": "DEV board"})
        result = board.get(10)
        assert result["id"] == 10

    def test_list(self, board, responses):
        responses.add("GET", f"{AGILE_URL}rest/agile/1.0/board", json={
            "values": [{"id": 10}],
        })
        result = board.list(project_key="DEV")
        assert len(result) == 1

    def test_backlog(self, board, responses):
        responses.add("GET", f"{AGILE_URL}rest/agile/1.0/board/10/backlog", json={
            "issues": [{"key": "DEV-99"}],
        })
        result = board.backlog(10)
        assert len(result) == 1

    def test_backlog_with_fields(self, board, responses):
        responses.add("GET", f"{AGILE_URL}rest/agile/1.0/board/10/backlog", json={
            "issues": [{"key": "DEV-99"}],
        })
        board.backlog(10, fields=["summary"])
        req = responses.calls[0].request
        assert "fields=summary" in req.url


@pytest.fixture()
def user(responses):
    from requestspro.sessions import ProSession

    session = ProSession(base_url=BASE_URL)
    return UserSubClient(session)


class TestUserSubClient:
    def test_myself(self, user, responses):
        responses.add("GET", f"{BASE_URL}rest/api/3/myself", json={"displayName": "Alice"})
        result = user.myself()
        assert result["displayName"] == "Alice"

    def test_search(self, user, responses):
        responses.add("GET", f"{BASE_URL}rest/api/3/user/search", json=[{"displayName": "Alice"}])
        result = user.search("alice")
        assert len(result) == 1


    def test_get_passes_expand_param(self, issue, responses):
        responses.add("GET", f"{BASE_URL}rest/api/3/issue/DEV-123", json={"key": "DEV-123"})
        issue.get("DEV-123", expand=["changelog"])
        req = responses.calls[0].request
        assert "expand=changelog" in req.url


class TestIssueSubClientExtended:
    def test_get_transitions(self, issue, responses):
        responses.add("GET", f"{BASE_URL}rest/api/3/issue/DEV-123/transitions", json={
            "transitions": [{"id": "31", "name": "In Progress"}],
        })
        result = issue.get_transitions("DEV-123")
        assert len(result) == 1
        assert result[0]["name"] == "In Progress"

    def test_transition_raises_on_invalid_status(self, issue, responses):
        responses.add("GET", f"{BASE_URL}rest/api/3/issue/DEV-123/transitions", json={
            "transitions": [{"id": "31", "name": "In Progress"}],
        })
        import pytest
        with pytest.raises(ValueError, match="Transition 'Done' not found"):
            issue.transition("DEV-123", "Done")

    def test_transition(self, issue, responses):
        responses.add("GET", f"{BASE_URL}rest/api/3/issue/DEV-123/transitions", json={
            "transitions": [{"id": "31", "name": "In Progress"}, {"id": "41", "name": "Done"}],
        })
        responses.add("POST", f"{BASE_URL}rest/api/3/issue/DEV-123/transitions", json={})
        issue.transition("DEV-123", "Done")
        req = responses.calls[1].request
        import json
        body = json.loads(req.body)
        assert body["transition"]["id"] == "41"

    def test_assign(self, issue, responses):
        responses.add("PUT", f"{BASE_URL}rest/api/3/issue/DEV-123/assignee", json={})
        issue.assign("DEV-123", "account-id-123")
        import json
        body = json.loads(responses.calls[0].request.body)
        assert body["accountId"] == "account-id-123"

    def test_add_comment(self, issue, responses):
        responses.add("POST", f"{BASE_URL}rest/api/3/issue/DEV-123/comment", json={"id": "1"})
        result = issue.add_comment("DEV-123", "Hello")
        assert result["id"] == "1"

    def test_add_comment_converts_markdown_to_adf(self, issue, responses):
        responses.add("POST", f"{BASE_URL}rest/api/3/issue/DEV-123/comment", json={"id": "2"})
        issue.add_comment("DEV-123", "**bold** text")
        import json
        body = json.loads(responses.calls[0].request.body)
        # Should be ADF, not plain string
        assert body["body"]["type"] == "doc"
        assert body["body"]["version"] == 1

    def test_add_comment_handles_204_no_content(self, issue, responses):
        responses.add("POST", f"{BASE_URL}rest/api/3/issue/DEV-123/comment", body="", status=204)
        result = issue.add_comment("DEV-123", "Hello")
        assert result is None

    def test_get_comments(self, issue, responses):
        responses.add("GET", f"{BASE_URL}rest/api/3/issue/DEV-123/comment", json={
            "comments": [{"id": "1", "body": "Hello"}],
        })
        result = issue.get_comments("DEV-123")
        assert len(result) == 1

    def test_link(self, issue, responses):
        responses.add("POST", f"{BASE_URL}rest/api/3/issueLink", json={})
        issue.link("DEV-1", "DEV-2", "blocks")
        import json
        body = json.loads(responses.calls[0].request.body)
        assert body["type"]["name"] == "blocks"
        assert body["inwardIssue"]["key"] == "DEV-1"
        assert body["outwardIssue"]["key"] == "DEV-2"
