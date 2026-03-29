# Internal imports
from jira_genie.cli import parse


class TestParseAuth:
    def test_auth_login(self):
        args = parse(["auth", "login"])
        assert args.command == "auth"
        assert args.subcommand == "login"

    def test_auth_status(self):
        args = parse(["auth", "status"])
        assert args.command == "auth"
        assert args.subcommand == "status"

    def test_auth_logout(self):
        args = parse(["auth", "logout"])
        assert args.command == "auth"
        assert args.subcommand == "logout"

    def test_instance_flag(self):
        args = parse(["--instance", "acme", "auth", "login"])
        assert args.instance == "acme"
        assert args.command == "auth"

    def test_auth_login_with_custom_credentials(self):
        args = parse(["auth", "login", "--client-id", "my-id", "--client-secret", "my-secret"])
        assert args.client_id == "my-id"
        assert args.client_secret == "my-secret"

    def test_auth_login_defaults_to_none(self):
        args = parse(["auth", "login"])
        assert args.client_id is None
        assert args.client_secret is None


class TestParseFields:
    def test_fields_sync(self):
        args = parse(["fields", "sync"])
        assert args.command == "fields"
        assert args.subcommand == "sync"

    def test_fields_sync_with_project(self):
        args = parse(["fields", "sync", "--project", "DEV"])
        assert args.project == "DEV"

    def test_fields_list(self):
        args = parse(["fields", "list"])
        assert args.command == "fields"
        assert args.subcommand == "list"

    def test_fields_list_with_filter(self):
        args = parse(["fields", "list", "--filter", "team"])
        assert args.filter == "team"

    def test_fields_schema(self):
        args = parse(["fields", "schema", "--project", "DEV", "--type", "Task"])
        assert args.project == "DEV"
        assert args.type == "Task"


class TestParseIssue:
    def test_issue_get(self):
        args = parse(["issue", "get", "DEV-123"])
        assert args.command == "issue"
        assert args.subcommand == "get"
        assert args.key == "DEV-123"

    def test_issue_get_with_fields(self):
        args = parse(["issue", "get", "DEV-123", "--fields", "summary,status"])
        assert args.fields == "summary,status"

    def test_issue_get_raw(self):
        args = parse(["issue", "get", "DEV-123", "--raw"])
        assert args.raw is True

    def test_issue_edit_with_set(self):
        args = parse(["issue", "edit", "DEV-123", "--set", "parent=DEV-100", "--set", "priority=P1"])
        assert args.set == ["parent=DEV-100", "priority=P1"]

    def test_issue_edit_with_json(self):
        args = parse(["issue", "edit", "DEV-123", "--json", '{"team": "Backend"}'])
        assert args.json == '{"team": "Backend"}'

    def test_issue_edit_body_file(self):
        args = parse(["issue", "edit", "DEV-123", "--body-file", "/tmp/desc.md"])
        assert args.body_file == "/tmp/desc.md"

    def test_issue_edit_description(self):
        args = parse(["issue", "edit", "DEV-123", "--description", "New desc"])
        assert args.description == "New desc"

    def test_issue_edit_raw(self):
        args = parse(["issue", "edit", "DEV-123", "--raw-payload", '{"fields": {}}'])
        assert args.raw_payload == '{"fields": {}}'

    def test_search(self):
        args = parse(["search", "project = DEV AND status != Done"])
        assert args.command == "search"
        assert args.jql == "project = DEV AND status != Done"

    def test_search_with_fields(self):
        args = parse(["search", "project = DEV", "--fields", "summary,status"])
        assert args.fields == "summary,status"

    def test_bulk_edit(self):
        args = parse(["bulk", "edit", "DEV-1", "DEV-2", "--set", "parent=DEV-100"])
        assert args.command == "bulk"
        assert args.keys == ["DEV-1", "DEV-2"]
        assert args.set == ["parent=DEV-100"]

    def test_bulk_edit_with_json(self):
        args = parse(["bulk", "edit", "DEV-1", "DEV-2", "--json", '{"team": "Backend"}'])
        assert args.json == '{"team": "Backend"}'


class TestParseTemplate:
    def test_template_list(self):
        args = parse(["template", "list"])
        assert args.command == "template"
        assert args.subcommand == "list"

    def test_template_show(self):
        args = parse(["template", "show", "instant"])
        assert args.name == "instant"

    def test_template_create(self):
        args = parse(["template", "create", "instant", "--json", '{"project": "DEV"}'])
        assert args.name == "instant"
        assert args.json == '{"project": "DEV"}'

    def test_template_delete(self):
        args = parse(["template", "delete", "instant"])
        assert args.name == "instant"

    def test_template_default_set(self):
        args = parse(["template", "default", "instant"])
        assert args.name == "instant"

    def test_template_default_show(self):
        args = parse(["template", "default"])
        assert args.name is None

    def test_template_default_clear(self):
        args = parse(["template", "default", "--clear"])
        assert args.clear is True

    def test_issue_create(self):
        args = parse(["issue", "create", "--summary", "Fix bug"])
        assert args.subcommand == "create"
        assert args.summary == "Fix bug"

    def test_issue_create_with_template(self):
        args = parse(["issue", "create", "--template", "instant", "--summary", "Fix"])
        assert args.template == "instant"

    def test_issue_create_raw(self):
        args = parse(["issue", "create", "--raw-payload", '{"fields": {}}'])
        assert args.raw_payload == '{"fields": {}}'

    def test_issue_create_body_file(self):
        args = parse(["issue", "create", "--body-file", "/tmp/desc.md", "--summary", "Title"])
        assert args.body_file == "/tmp/desc.md"


class TestParseSprint:
    def test_sprint_current(self):
        args = parse(["sprint", "current", "--board", "42"])
        assert args.command == "sprint"
        assert args.subcommand == "current"
        assert args.board == "42"

    def test_sprint_list(self):
        args = parse(["sprint", "list", "--board", "42", "--state", "active,future"])
        assert args.state == "active,future"

    def test_sprint_issues(self):
        args = parse(["sprint", "issues", "123", "--fields", "summary,status"])
        assert args.sprint_id == "123"
        assert args.fields == "summary,status"


class TestParseBoard:
    def test_board_list(self):
        args = parse(["board", "list", "--project", "DEV"])
        assert args.project == "DEV"

    def test_board_backlog(self):
        args = parse(["board", "backlog", "42"])
        assert args.board_id == "42"


class TestParseUser:
    def test_user_search(self):
        args = parse(["user", "search", "alice"])
        assert args.query == "alice"

    def test_user_me(self):
        args = parse(["user", "me"])
        assert args.subcommand == "me"


class TestParseIssueOps:
    def test_issue_transition(self):
        args = parse(["issue", "transition", "DEV-123", "In Progress"])
        assert args.key == "DEV-123"
        assert args.status == "In Progress"

    def test_issue_assign(self):
        args = parse(["issue", "assign", "DEV-123", "alice@example.com"])
        assert args.assignee == "alice@example.com"

    def test_issue_comment(self):
        args = parse(["issue", "comment", "DEV-123", "Deployed"])
        assert args.body == "Deployed"

    def test_issue_comment_body_file(self):
        args = parse(["issue", "comment", "DEV-123", "--body-file", "/tmp/comment.md"])
        assert args.body_file == "/tmp/comment.md"

    def test_issue_link(self):
        args = parse(["issue", "link", "DEV-1", "DEV-2", "--type", "blocks"])
        assert args.inward_key == "DEV-1"
        assert args.outward_key == "DEV-2"
        assert args.link_type == "blocks"
