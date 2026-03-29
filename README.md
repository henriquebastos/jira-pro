<p align="center">
  <img src="assets/banner.jpg" alt="jira-genie" width="100%">
</p>

# jira-genie 🧞

Your AI agent's interface to Jira Cloud. JSON in, JSON out.

Give your agents the ability to search, create, edit, and manage Jira issues
through a simple CLI. Schema-aware field resolution means agents write
`story_points` — not `customfield_10036`. Templates mean repetitive ticket
creation is a one-liner.

Works with any AI agent framework (LangChain, CrewAI, Claude Code, raw
subprocess) and as a standalone CLI for humans and scripts.

## Why

- **JSON by default** — every command outputs structured JSON that agents parse directly
- **Friendly field names** — write `story_points` instead of `customfield_10036`, resolved automatically via your instance's schema
- **Templates** — define issue defaults once, reuse across agents and workflows
- **Shell completion** — field names and enum values from your live Jira schema
- **Zero-config auth** — `jira auth login` handles OAuth, token refresh is transparent
- **Agent-ready** — designed as a tool agents call, not a TUI humans click through

## Install

```bash
# Homebrew
brew tap henriquebastos/tap
brew install jira-genie

# Or with uv
uv tool install jira-genie

# Or from source
git clone https://github.com/henriquebastos/jira-genie.git
cd jira-genie
uv tool install -e .
```

## Quick Start

```bash
# 1. Login (opens browser for Atlassian OAuth)
jira auth login

# 2. Sync your instance's field schema
jira fields sync
jira fields sync --project DEV    # sync type schemas for a specific project

# 3. Get an issue
jira issue get DEV-123
# {"key": "DEV-123", "summary": "Fix auth", "status": "To Do", "assignee": null, "priority": "P2: Medium", "type": "Task"}

# 4. Search with JQL
jira search "project = DEV AND sprint in openSprints() AND status != Done"
# [{"key": "DEV-124", "summary": "...", ...}, ...]

# 5. Create an issue
jira issue create --json '{"project": "DEV", "issuetype": "Task", "summary": "New task", "parent": "DEV-100"}'
# {"id": "12345", "key": "DEV-125", ...}
```

## Agent Integration

Every command returns JSON to stdout. Agents can call `jira` as a subprocess
and parse the output directly. Common agent workflows:

```bash
# Read an issue and decide what to do
jira issue get DEV-123

# Search for unfinished work
jira search "assignee = currentUser() AND status != Done"

# Create a task from agent analysis
jira issue create --template backend --summary "Fix race condition in payment handler"

# Update status after completing work
jira issue transition DEV-123 "Done"
jira issue comment DEV-123 "Fixed in commit abc1234"

# Bulk update parent epic
jira bulk edit DEV-1 DEV-2 DEV-3 --set parent=DEV-100
```

For raw API access (no field resolution), use `--raw` on reads and
`--raw-payload` on writes.

## Authentication

```bash
jira auth login     # opens browser, handles OAuth 2.0 (3LO) + PKCE
jira auth status    # show login state
jira auth logout    # remove stored tokens
```

Token refresh is automatic and transparent — you never deal with tokens.

### Using your own OAuth app

The CLI ships with a default OAuth app. To use your own, register one at
[developer.atlassian.com](https://developer.atlassian.com/console/myapps/):

1. Create an OAuth 2.0 (3LO) app
2. Callback URL: `http://localhost:8888/callback`
3. Jira API scopes: `read:jira-work`, `write:jira-work`, `read:jira-user`
4. Enable sharing under Distribution

```bash
# Via flags
jira auth login --client-id YOUR_ID --client-secret YOUR_SECRET

# Or via environment variables
export JIRA_CLIENT_ID=YOUR_ID
export JIRA_CLIENT_SECRET=YOUR_SECRET
jira auth login
```

Resolution order: flags → env vars → built-in defaults.
Credentials are saved on login and used for all subsequent token refreshes.

### Multi-Instance

```bash
jira --instance mycompany issue get DEV-123
# or
export JIRA_INSTANCE=mycompany
```

Matches against site name (`mycompany` → `mycompany.atlassian.net`).
Single instance is auto-detected.

## Commands

### Issues

```bash
jira issue get DEV-123                              # formatted JSON
jira issue get DEV-123 --fields summary,status      # specific fields
jira issue get DEV-123 --raw                        # raw API response

jira issue create --json '{"project": "DEV", "issuetype": "Task", "summary": "Title"}'
jira issue create --template my-template --summary "Title"
jira issue create --raw-payload '{"fields": {...}}'           # bypass resolution

jira issue edit DEV-123 --set priority="P1: High" --set story_points=5
jira issue edit DEV-123 --json '{"team": "Backend"}'
jira issue edit DEV-123 --raw-payload '{"fields": {...}}'     # bypass resolution

jira issue transition DEV-123 "In Progress"
jira issue assign DEV-123 alice@example.com
jira issue comment DEV-123 "Deployed to staging"
jira issue link DEV-123 DEV-456 --type blocks
```

### Search

```bash
jira search "project = DEV AND sprint in openSprints()"
jira search "parent = DEV-100" --fields summary,status,assignee
```

### Bulk

```bash
jira bulk edit DEV-1 DEV-2 DEV-3 --set parent=DEV-100
```

### Sprints and Boards

```bash
jira sprint current --board 42
jira sprint list --board 42 --state active,future
jira sprint issues 123 --fields summary,status

jira board list --project DEV
jira board backlog 42
```

### Users

```bash
jira user me
jira user search "alice"
```

## Field Resolution

The CLI maps **friendly field names** to Jira's internal field IDs using
the synced schema. You write `story_points`, the API receives `customfield_10036`.

Values are also expanded based on field type:

| You write | API receives |
|-----------|-------------|
| `"project": "DEV"` | `"project": {"key": "DEV"}` |
| `"issuetype": "Task"` | `"issuetype": {"name": "Task"}` |
| `"parent": "DEV-100"` | `"parent": {"key": "DEV-100"}` |
| `"priority": "P1: High"` | `"priority": {"name": "P1: High"}` |
| `"team": "Backend"` | `"customfield_10001": {"value": "Backend"}` |
| `"components": ["API"]` | `"components": [{"name": "API"}]` |
| `"story_points": 5` | `"customfield_10036": 5` |
| `"labels": ["urgent"]` | `"labels": ["urgent"]` |

Already-structured values (dicts) pass through without double-wrapping.
Use `--raw-payload` to bypass all resolution.

## Schema

```bash
jira fields sync                      # sync fields + discover available projects
jira fields sync --project DEV        # also sync type schemas (required fields, allowed values)
jira fields list                      # all fields
jira fields list --filter story       # search by name
jira fields schema --project DEV --type Task    # full type schema for agents
```

Run after login, and again if your Jira admin changes field configuration.
You can sync multiple projects incrementally — each `--project` adds to the
existing schema without overwriting previously synced projects.

Stored at `~/.config/jira-genie/{cloud_id}/schema.json`.

## Templates

Partial JSON with friendly field names. Define defaults for repetitive issue creation.

```bash
# Create
jira template create backend --json '{
  "project": "DEV",
  "issuetype": "Task",
  "parent": "DEV-100",
  "components": ["API"]
}'

# Use
jira issue create --template backend --summary "Fix the thing"

# Manage
jira template list
jira template show backend
jira template delete backend
jira template default backend       # set as default
jira template default               # show current default
jira template default --clear       # remove default
```

### Composition order

Fields merge in layers — later layers override earlier ones (shallow, not deep):

```
Template → --json → --set/--summary → resolve_fields() → API
```

Or bypass everything with `--raw-payload`.

## Shell Completion

```bash
jira completion install     # prints setup for your shell
```

Requires `argcomplete` on PATH: `uv tool install argcomplete`

Completes commands, template names, field names, and enum values from your
live schema:

```
jira issue create --template <TAB>         → backend, bug, ...
jira issue edit DEV-123 --set <TAB>        → story_points=, priority=, team=, ...
jira issue edit DEV-123 --set priority=<TAB>  → P0: Critical, P1: High, ...
```

## Configuration

```
~/.config/jira-genie/
├── config.json                     # default instance
└── {cloud_id}/
    ├── config.json                 # client_id, cloud_id, site
    ├── refresh.json                # OAuth refresh token
    ├── schema.json                 # field registry + type schemas
    └── templates/
        └── backend.json
```

## Development

```bash
git clone https://github.com/henriquebastos/jira-genie.git
cd jira-genie
uv sync
uv run pytest           # 148 tests
uv run ruff check src/ tests/
uv run jira --help
```

### Architecture

```
src/jira_genie/
├── adf.py          # Markdown ↔ Atlassian Document Format conversion
├── auth.py         # OAuth 2.0 (3LO) — login, token refresh, PKCE
├── cache.py        # FileCache — file-backed key-value store with expiry
├── cli.py          # argparse CLI — parse/cli split, all dispatch
├── client.py       # JiraClient + sub-clients (Issue, Search, Sprint, Board, User)
├── completers.py   # Shell completion for argcomplete
├── config.py       # Instance discovery and resolution
├── formatters.py   # Pure response transformers (raw API → clean JSON)
├── schema.py       # Field registry, type schemas, field resolution
├── skill.py        # Agent skill install/uninstall for AI coding tools
└── templates.py    # Template CRUD, merge logic, build_issue_fields
```

See [conventions.md](conventions.md) for code style and workflow guidelines.

## License

[MIT](LICENSE)
