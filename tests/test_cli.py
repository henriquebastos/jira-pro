# Internal imports
from jira.cli import parse


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
