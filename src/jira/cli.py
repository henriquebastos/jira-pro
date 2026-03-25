# Python imports
import argparse
import json
import sys


def parse(argv=None):
    """Pure parsing. Returns a Namespace. No I/O."""
    parser = argparse.ArgumentParser(prog="jira", description="Jira Cloud CLI")
    parser.add_argument("--instance", help="Jira instance (site name)")

    subparsers = parser.add_subparsers(dest="command")

    # auth subcommands
    auth_parser = subparsers.add_parser("auth")
    auth_sub = auth_parser.add_subparsers(dest="subcommand")
    auth_sub.add_parser("login")
    auth_sub.add_parser("status")
    auth_sub.add_parser("logout")

    # fields subcommands
    fields_parser = subparsers.add_parser("fields")
    fields_sub = fields_parser.add_subparsers(dest="subcommand")

    fields_sync = fields_sub.add_parser("sync")
    fields_sync.add_argument("--project", help="Sync specific project")

    fields_list = fields_sub.add_parser("list")
    fields_list.add_argument("--filter", help="Filter fields by name")

    fields_schema = fields_sub.add_parser("schema")
    fields_schema.add_argument("--project", required=True, help="Project key")
    fields_schema.add_argument("--type", required=True, help="Issue type name")

    # issue subcommands
    issue_parser = subparsers.add_parser("issue")
    issue_sub = issue_parser.add_subparsers(dest="subcommand")

    issue_get = issue_sub.add_parser("get")
    issue_get.add_argument("key", help="Issue key (e.g. DEV-123)")
    issue_get.add_argument("--fields", help="Comma-separated field list")
    issue_get.add_argument("--raw", action="store_true", help="Output raw API response")

    issue_edit = issue_sub.add_parser("edit")
    issue_edit.add_argument("key", help="Issue key")
    issue_edit.add_argument("--set", action="append", help="key=value field")
    issue_edit.add_argument("--json", help="JSON override string")
    issue_edit.add_argument("--raw-payload", help="Raw JSON payload (bypass resolution)")

    issue_create = issue_sub.add_parser("create")
    issue_create.add_argument("--summary", help="Issue summary")
    issue_create.add_argument("--template", help="Template name")
    issue_create.add_argument("--json", help="JSON override string")
    issue_create.add_argument("--set", action="append", help="key=value field")
    issue_create.add_argument("--raw-payload", help="Raw JSON payload (bypass resolution)")

    issue_transition = issue_sub.add_parser("transition")
    issue_transition.add_argument("key", help="Issue key")
    issue_transition.add_argument("status", help="Target status name")

    issue_assign = issue_sub.add_parser("assign")
    issue_assign.add_argument("key", help="Issue key")
    issue_assign.add_argument("assignee", help="Email or account ID")

    issue_comment = issue_sub.add_parser("comment")
    issue_comment.add_argument("key", help="Issue key")
    issue_comment.add_argument("body", help="Comment text")

    issue_link = issue_sub.add_parser("link")
    issue_link.add_argument("inward_key", help="Inward issue key")
    issue_link.add_argument("outward_key", help="Outward issue key")
    issue_link.add_argument("--type", dest="link_type", default="blocks", help="Link type")

    # search command
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("jql", help="JQL query string")
    search_parser.add_argument("--fields", help="Comma-separated field list")

    # bulk subcommands
    bulk_parser = subparsers.add_parser("bulk")
    bulk_sub = bulk_parser.add_subparsers(dest="subcommand")

    bulk_edit = bulk_sub.add_parser("edit")
    bulk_edit.add_argument("keys", nargs="+", help="Issue keys")
    bulk_edit.add_argument("--set", action="append", help="key=value field")

    # template subcommands
    template_parser = subparsers.add_parser("template")
    template_sub = template_parser.add_subparsers(dest="subcommand")

    template_sub.add_parser("list")

    template_show = template_sub.add_parser("show")
    template_show.add_argument("name", help="Template name")

    template_create = template_sub.add_parser("create")
    template_create.add_argument("name", help="Template name")
    template_create.add_argument("--json", required=True, help="Template JSON")

    template_edit = template_sub.add_parser("edit")
    template_edit.add_argument("name", help="Template name")

    template_delete = template_sub.add_parser("delete")
    template_delete.add_argument("name", help="Template name")

    template_default = template_sub.add_parser("default")
    template_default.add_argument("name", nargs="?", default=None, help="Template name to set as default")
    template_default.add_argument("--clear", action="store_true", help="Clear default template")

    # sprint subcommands
    sprint_parser = subparsers.add_parser("sprint")
    sprint_sub = sprint_parser.add_subparsers(dest="subcommand")

    sprint_current = sprint_sub.add_parser("current")
    sprint_current.add_argument("--board", required=True, help="Board ID")

    sprint_list = sprint_sub.add_parser("list")
    sprint_list.add_argument("--board", required=True, help="Board ID")
    sprint_list.add_argument("--state", help="Sprint states (e.g. active,future)")

    sprint_issues = sprint_sub.add_parser("issues")
    sprint_issues.add_argument("sprint_id", help="Sprint ID")
    sprint_issues.add_argument("--fields", help="Comma-separated field list")

    # board subcommands
    board_parser = subparsers.add_parser("board")
    board_sub = board_parser.add_subparsers(dest="subcommand")

    board_list = board_sub.add_parser("list")
    board_list.add_argument("--project", help="Project key")

    board_backlog = board_sub.add_parser("backlog")
    board_backlog.add_argument("board_id", help="Board ID")

    # user subcommands
    user_parser = subparsers.add_parser("user")
    user_sub = user_parser.add_subparsers(dest="subcommand")

    user_search = user_sub.add_parser("search")
    user_search.add_argument("query", help="Search query")

    user_sub.add_parser("me")

    return parser.parse_args(argv)


def cli(argv=None):
    """Entry point. Parses, dispatches, handles I/O."""
    args = parse(argv)

    if args.command == "auth":
        if args.subcommand == "login":
            client_id = input("Enter your Atlassian OAuth client_id: ").strip()
            if not client_id:
                print(json.dumps({"error": "client_id is required"}), file=sys.stderr)
                sys.exit(1)
            from jira.auth import login
            result = login(client_id)
            print(json.dumps(result))
        elif args.subcommand == "status":
            try:
                from jira.config import ConfigError, discover_instance_dir
                instance_dir = discover_instance_dir(instance=getattr(args, "instance", None))
                config = json.loads((instance_dir / "config.json").read_text())
                print(json.dumps({"status": "logged in", **config}))
            except (ConfigError, FileNotFoundError):
                print(json.dumps({"status": "not logged in"}))
        elif args.subcommand == "logout":
            try:
                import shutil

                from jira.config import ConfigError, discover_instance_dir
                instance_dir = discover_instance_dir(instance=getattr(args, "instance", None))
                shutil.rmtree(instance_dir)
                print(json.dumps({"message": "Logged out"}))
            except (ConfigError, FileNotFoundError):
                print(json.dumps({"message": "Not logged in"}))
    elif args.command is None:
        parse(["--help"])
