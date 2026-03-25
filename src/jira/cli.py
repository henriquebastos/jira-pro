# Python imports
import argparse
import json


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

    return parser.parse_args(argv)


def cli(argv=None):
    """Entry point. Parses, dispatches, handles I/O."""
    args = parse(argv)

    if args.command == "auth":
        if args.subcommand == "login":
            print(json.dumps({"message": "Login flow not yet wired"}))
        elif args.subcommand == "status":
            print(json.dumps({"status": "not logged in"}))
        elif args.subcommand == "logout":
            print(json.dumps({"message": "Logged out"}))
    elif args.command is None:
        parse(["--help"])
