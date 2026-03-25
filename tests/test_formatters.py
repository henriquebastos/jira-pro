# Internal imports
from jira.formatters import format_issue, format_issue_list, format_sprint, format_transition


class TestFormatIssue:
    def test_extracts_key_and_summary(self):
        raw = {
            "key": "DEV-123",
            "fields": {
                "summary": "Fix the bug",
                "status": {"name": "To Do"},
                "assignee": {"displayName": "Alice"},
                "priority": {"name": "P1: High"},
                "issuetype": {"name": "Task"},
            },
        }
        result = format_issue(raw)
        assert result["key"] == "DEV-123"
        assert result["summary"] == "Fix the bug"
        assert result["status"] == "To Do"
        assert result["assignee"] == "Alice"
        assert result["priority"] == "P1: High"
        assert result["type"] == "Task"

    def test_handles_null_assignee(self):
        raw = {
            "key": "DEV-456",
            "fields": {
                "summary": "No owner",
                "status": {"name": "Open"},
                "assignee": None,
                "priority": {"name": "P3: Low"},
                "issuetype": {"name": "Bug"},
            },
        }
        result = format_issue(raw)
        assert result["assignee"] is None

    def test_handles_missing_optional_fields(self):
        raw = {
            "key": "DEV-789",
            "fields": {
                "summary": "Minimal",
            },
        }
        result = format_issue(raw)
        assert result["key"] == "DEV-789"
        assert result["summary"] == "Minimal"
        assert result["status"] is None
        assert result["assignee"] is None


class TestFormatIssueList:
    def test_transforms_list(self):
        raw_issues = [
            {"key": "DEV-1", "fields": {"summary": "First", "status": {"name": "Done"}}},
            {"key": "DEV-2", "fields": {"summary": "Second", "status": {"name": "Open"}}},
        ]
        result = format_issue_list(raw_issues)
        assert len(result) == 2
        assert result[0]["key"] == "DEV-1"
        assert result[1]["summary"] == "Second"


class TestFormatSprint:
    def test_extracts_sprint_fields(self):
        raw = {
            "id": 42,
            "name": "Sprint 5",
            "state": "active",
            "startDate": "2026-03-01T00:00:00.000Z",
            "endDate": "2026-03-15T00:00:00.000Z",
        }
        result = format_sprint(raw)
        assert result == {
            "id": 42,
            "name": "Sprint 5",
            "state": "active",
            "startDate": "2026-03-01T00:00:00.000Z",
            "endDate": "2026-03-15T00:00:00.000Z",
        }


class TestFormatTransition:
    def test_extracts_transition_fields(self):
        raw = {
            "id": "31",
            "name": "In Progress",
            "to": {"name": "In Progress", "id": "10001"},
        }
        result = format_transition(raw)
        assert result == {"id": "31", "name": "In Progress", "to_status": "In Progress"}
