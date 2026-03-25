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
            client_secret = input("Enter your client_secret (or press Enter to skip): ").strip() or None
            from jira.auth import login
            result = login(client_id, client_secret=client_secret)
            print(json.dumps(result))
        elif args.subcommand == "status":
            try:
                from jira.config import ConfigError, discover_instance_dir
                instance_dir = discover_instance_dir(instance=getattr(args, "instance", None))
                config = json.loads((instance_dir / "config.json").read_text())
                safe = {k: v for k, v in config.items() if k != "client_secret"}
                print(json.dumps({"status": "logged in", **safe}))
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
    elif args.command == "fields":
        from jira.client import JiraClient

        if args.subcommand == "sync":
            from jira.schema import sync

            client = JiraClient.from_config(instance=args.instance)
            instance_dir = _get_instance_dir(args.instance)
            sync(client.session, instance_dir, project=getattr(args, "project", None))
            schema = json.loads((instance_dir / "schema.json").read_text())
            field_count = len(schema.get("fields", {}))
            project_count = len(schema.get("projects", {}))
            print(json.dumps({"message": f"Synced {field_count} fields, {project_count} project(s)"}))
        elif args.subcommand == "list":
            instance_dir = _get_instance_dir(args.instance)
            schema = json.loads((instance_dir / "schema.json").read_text())
            fields = schema.get("fields", {})
            filter_term = getattr(args, "filter", None)
            if filter_term:
                fields = {k: v for k, v in fields.items() if filter_term.lower() in k.lower()}
            print(json.dumps(fields, indent=2))
        elif args.subcommand == "schema":
            instance_dir = _get_instance_dir(args.instance)
            schema = json.loads((instance_dir / "schema.json").read_text())
            projects = schema.get("projects", {})
            project = projects.get(args.project, {})
            types = project.get("types", {})
            type_schema = types.get(args.type)
            if type_schema:
                print(json.dumps(type_schema, indent=2))
            else:
                available = list(types.keys())
                print(json.dumps({"error": f"Type '{args.type}' not found", "available": available}), file=sys.stderr)
                sys.exit(1)
    elif args.command == "issue":
        from jira.client import JiraClient
        from jira.formatters import format_issue

        client = JiraClient.from_config(instance=args.instance)
        if args.subcommand == "get":
            fields = args.fields.split(",") if getattr(args, "fields", None) else None
            result = client.issue.get(args.key, fields=fields)
            if getattr(args, "raw", False):
                print(json.dumps(result, indent=2))
            else:
                print(json.dumps(format_issue(result), indent=2))
        elif args.subcommand == "edit":
            if getattr(args, "raw_payload", None):
                payload = json.loads(args.raw_payload)
            else:
                fields = {}
                for s in (args.set or []):
                    k, v = s.split("=", 1)
                    fields[k] = v
                if getattr(args, "json", None):
                    fields = {**json.loads(args.json), **fields}
                from jira.schema import resolve_fields
                schema = _load_schema(args.instance)
                payload = {"fields": resolve_fields(fields, schema)}
            client.issue.edit(args.key, payload)
            print(json.dumps({"message": f"Updated {args.key}"}))
        elif args.subcommand == "create":
            if getattr(args, "raw_payload", None):
                payload = json.loads(args.raw_payload)
            else:
                from jira.templates import build_issue_fields, get_default, load_template
                schema = _load_schema(args.instance)
                template = None
                template_name = getattr(args, "template", None)
                if not template_name:
                    instance_dir = _get_instance_dir(args.instance)
                    config_file = instance_dir / "config.json"
                    template_name = get_default(config_file)
                if template_name:
                    instance_dir = _get_instance_dir(args.instance)
                    template = load_template(template_name, instance_dir / "templates")
                json_override = json.loads(args.json) if getattr(args, "json", None) else None
                cli_flags = {}
                for s in (getattr(args, "set", None) or []):
                    k, v = s.split("=", 1)
                    cli_flags[k] = v
                if getattr(args, "summary", None):
                    cli_flags["summary"] = args.summary
                resolved = build_issue_fields(template, json_override, cli_flags, schema)
                payload = {"fields": resolved}
            result = client.issue.create(payload)
            print(json.dumps(result, indent=2))
        elif args.subcommand == "transition":
            client.issue.transition(args.key, args.status)
            print(json.dumps({"message": f"Transitioned {args.key} to {args.status}"}))
        elif args.subcommand == "assign":
            client.issue.assign(args.key, args.assignee)
            print(json.dumps({"message": f"Assigned {args.key}"}))
        elif args.subcommand == "comment":
            result = client.issue.add_comment(args.key, args.body)
            print(json.dumps(result, indent=2))
        elif args.subcommand == "link":
            client.issue.link(args.inward_key, args.outward_key, args.link_type)
            print(json.dumps({"message": f"Linked {args.inward_key} → {args.outward_key}"}))
    elif args.command == "search":
        from jira.client import JiraClient
        from jira.formatters import format_issue_list

        client = JiraClient.from_config(instance=args.instance)
        fields = args.fields.split(",") if getattr(args, "fields", None) else None
        results = client.search.jql(args.jql, fields=fields)
        print(json.dumps(format_issue_list(results), indent=2))
    elif args.command == "user":
        from jira.client import JiraClient

        client = JiraClient.from_config(instance=args.instance)
        if args.subcommand == "me":
            print(json.dumps(client.user.myself(), indent=2))
        elif args.subcommand == "search":
            print(json.dumps(client.user.search(args.query), indent=2))
    elif args.command is None:
        parse(["--help"])


def _get_instance_dir(instance=None):
    from jira.config import discover_instance_dir
    return discover_instance_dir(instance=instance)


def _load_schema(instance=None):
    instance_dir = _get_instance_dir(instance)
    schema_path = instance_dir / "schema.json"
    if not schema_path.exists():
        return {}
    return json.loads(schema_path.read_text()).get("fields", {})
