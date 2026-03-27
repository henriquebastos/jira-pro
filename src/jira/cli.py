# Python imports
import argparse
import json
import sys

# Pip imports
import argcomplete

# Internal imports
from jira.completers import FieldSetCompleter, TemplateCompleter

# Default OAuth credentials — override with --client-id/--client-secret or env vars
DEFAULT_CLIENT_ID = "HhpJ9RgICWpmjsb7fd5oV4tulwVlKmJw"
DEFAULT_CLIENT_SECRET = "ATOA0mBJCckMTjQhYcvyiM95S2kH_M6RfZjg2H1XZPbPwMj_QYp4q45MnPCwLm-om1ln7D4BC7C9"


def parse(argv=None):
    """Pure parsing. Returns a Namespace. No I/O."""
    parser = argparse.ArgumentParser(prog="jira", description="Jira Cloud CLI")
    parser.add_argument("--instance", help="Jira instance (site name)")

    subparsers = parser.add_subparsers(dest="command")

    # auth subcommands
    auth_parser = subparsers.add_parser("auth")
    auth_parser.set_defaults(subparser=auth_parser)
    auth_sub = auth_parser.add_subparsers(dest="subcommand")
    auth_login = auth_sub.add_parser("login")
    auth_login.add_argument("--client-id", default=None, help="OAuth client ID (overrides default)")
    auth_login.add_argument("--client-secret", default=None, help="OAuth client secret (overrides default)")
    auth_sub.add_parser("status")
    auth_sub.add_parser("logout")

    # fields subcommands
    fields_parser = subparsers.add_parser("fields")
    fields_parser.set_defaults(subparser=fields_parser)
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
    issue_parser.set_defaults(subparser=issue_parser)
    issue_sub = issue_parser.add_subparsers(dest="subcommand")

    issue_get = issue_sub.add_parser("get")
    issue_get.add_argument("key", help="Issue key (e.g. DEV-123)")
    issue_get.add_argument("--fields", help="Comma-separated field list")
    issue_get.add_argument("--raw", action="store_true", help="Output raw API response")

    issue_edit = issue_sub.add_parser("edit")
    issue_edit.add_argument("key", help="Issue key")
    issue_edit.add_argument("--set", action="append", help="key=value field").completer = FieldSetCompleter()
    issue_edit.add_argument("--json", help="JSON override string")
    issue_edit.add_argument("--raw-payload", help="Raw JSON payload (bypass resolution)")

    issue_create = issue_sub.add_parser("create")
    issue_create.add_argument("--summary", help="Issue summary")
    issue_create.add_argument("--template", help="Template name").completer = TemplateCompleter()
    issue_create.add_argument("--json", help="JSON override string")
    issue_create.add_argument("--set", action="append", help="key=value field").completer = FieldSetCompleter()
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
    bulk_parser.set_defaults(subparser=bulk_parser)
    bulk_sub = bulk_parser.add_subparsers(dest="subcommand")

    bulk_edit = bulk_sub.add_parser("edit")
    bulk_edit.add_argument("keys", nargs="+", help="Issue keys")
    bulk_edit.add_argument("--set", action="append", help="key=value field").completer = FieldSetCompleter()

    # template subcommands
    template_parser = subparsers.add_parser("template")
    template_parser.set_defaults(subparser=template_parser)
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
    sprint_parser.set_defaults(subparser=sprint_parser)
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
    board_parser.set_defaults(subparser=board_parser)
    board_sub = board_parser.add_subparsers(dest="subcommand")

    board_list = board_sub.add_parser("list")
    board_list.add_argument("--project", help="Project key")

    board_backlog = board_sub.add_parser("backlog")
    board_backlog.add_argument("board_id", help="Board ID")

    # user subcommands
    user_parser = subparsers.add_parser("user")
    user_parser.set_defaults(subparser=user_parser)
    user_sub = user_parser.add_subparsers(dest="subcommand")

    user_search = user_sub.add_parser("search")
    user_search.add_argument("query", help="Search query")

    user_sub.add_parser("me")

    # completion subcommand
    completion_parser = subparsers.add_parser("completion")
    completion_parser.set_defaults(subparser=completion_parser)
    completion_sub = completion_parser.add_subparsers(dest="subcommand")
    completion_sub.add_parser("install", help="Show shell setup instructions")
    completion_sub.add_parser("bash", help="Output bash completion script")
    completion_sub.add_parser("zsh", help="Output zsh completion script")
    completion_sub.add_parser("fish", help="Output fish completion script")

    argcomplete.autocomplete(parser)
    return parser.parse_args(argv)


def cli(argv=None):
    """Entry point. Parses, dispatches, handles I/O."""
    args = parse(argv)

    # Show help when subcommand is missing
    if args.command and not getattr(args, "subcommand", None) and args.command != "search":
        args.subparser.print_help()
        return

    handlers = {
        "auth": _handle_auth,
        "fields": _handle_fields,
        "issue": _handle_issue,
        "search": _handle_search,
        "user": _handle_user,
        "completion": _handle_completion,
    }
    handler = handlers.get(args.command)
    if handler:
        handler(args)
    elif args.command is None:
        parse(["--help"])


def _handle_auth(args, client_id=DEFAULT_CLIENT_ID, client_secret=DEFAULT_CLIENT_SECRET):
    if args.subcommand == "login":
        import os

        from jira.auth import login
        cid = args.client_id or os.environ.get("JIRA_CLIENT_ID") or client_id
        csecret = args.client_secret or os.environ.get("JIRA_CLIENT_SECRET") or client_secret
        result = login(cid, client_secret=csecret)
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


def _handle_fields(args):
    from jira.client import JiraClient

    if args.subcommand == "sync":
        from jira.schema import sync
        client = JiraClient.from_config(instance=args.instance)
        instance_dir = _get_instance_dir(args.instance)
        project = getattr(args, "project", None)
        sync(client.session, instance_dir, project=project)
        schema = json.loads((instance_dir / "schema.json").read_text())
        field_count = len(schema.get("fields", {}))
        available = schema.get("available_projects", [])
        synced = list(schema.get("projects", {}).keys())
        result = {"fields": field_count, "available_projects": available, "synced_projects": synced}
        if not project and not synced:
            result["hint"] = "Run `jira fields sync --project KEY` to sync type schemas for a project"
        print(json.dumps(result))
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


def _handle_issue(args):
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
            fields = _parse_set_flags(args.set)
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
            cli_flags = _parse_set_flags(getattr(args, "set", None))
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


def _handle_search(args):
    from jira.client import JiraClient
    from jira.formatters import format_issue_list

    client = JiraClient.from_config(instance=args.instance)
    fields = args.fields.split(",") if getattr(args, "fields", None) else None
    results = client.search.jql(args.jql, fields=fields)
    print(json.dumps(format_issue_list(results), indent=2))


def _handle_user(args):
    from jira.client import JiraClient

    client = JiraClient.from_config(instance=args.instance)
    if args.subcommand == "me":
        print(json.dumps(client.user.myself(), indent=2))
    elif args.subcommand == "search":
        print(json.dumps(client.user.search(args.query), indent=2))


def _handle_completion(args):
    if args.subcommand == "install":
        import os
        shell = os.path.basename(os.environ.get("SHELL", ""))
        if shell == "zsh":
            print("# Add to ~/.zshrc:\n")
            print("autoload -U bashcompinit")
            print("bashcompinit")
            print('eval "$(register-python-argcomplete jira)"')
        elif shell == "fish":
            print("# Add to ~/.config/fish/config.fish:\n")
            print("register-python-argcomplete --shell fish jira | source")
        else:
            print(f"# Add to ~/.{shell}rc:\n")
            print('eval "$(register-python-argcomplete jira)"')
    elif args.subcommand in ("bash", "zsh"):
        import subprocess
        subprocess.run(["register-python-argcomplete", "jira"])
    elif args.subcommand == "fish":
        import subprocess
        subprocess.run(["register-python-argcomplete", "--shell", "fish", "jira"])


def _parse_set_flags(set_args):
    """Parse --set key=value flags into a dict. Raises SystemExit on invalid format."""
    fields = {}
    for s in (set_args or []):
        if "=" not in s:
            print(json.dumps({"error": f"Invalid --set format: '{s}'. Expected key=value"}), file=sys.stderr)
            sys.exit(1)
        k, v = s.split("=", 1)
        fields[k] = v
    return fields


def _get_instance_dir(instance=None):
    from jira.config import discover_instance_dir
    return discover_instance_dir(instance=instance)


def _load_schema(instance=None):
    instance_dir = _get_instance_dir(instance)
    schema_path = instance_dir / "schema.json"
    if not schema_path.exists():
        return {}
    return json.loads(schema_path.read_text()).get("fields", {})
