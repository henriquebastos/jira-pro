# Jira CLI Client — Plan

## Goal

Build a standalone Python CLI tool + library for Jira Cloud, following the same architecture as `an existing API client project` (requestspro client + CLI wrapper). JSON output for agent consumption, human-readable summaries when interactive.

## Repository Setup

Standalone repo at `~/projects/jira`, same structure as `beans`:

```
~/projects/jira/
├── .git/
├── .gitignore
├── .python-version            # 3.13 (match backend)
├── pyproject.toml             # uv, ruff, pytest
├── uv.lock
├── AGENTS.md                  # Agent instructions
├── PLAN.md                    # This file (moved here)
├── README.md
├── LICENSE
├── src/
│   └── jira/
│       ├── __init__.py
│       ├── auth.py            # JiraAuth (RecoverableAuth) + login flow
│       ├── cache.py           # FileCache — file-backed cache for TokenStore (→ requestspro later)
│       ├── client.py          # JiraClient (MainClient) + sub-clients
│       ├── schema.py          # Instance field discovery, sync, friendly name mapping
│       ├── templates.py       # Template loading, merging, resolution
│       ├── formatters.py      # Pure functions: API response → clean JSON
│       └── cli.py             # CLI entry point (argparse, pure I/O boundary)
└── tests/
    ├── __init__.py
    ├── test_auth.py
    ├── test_cache.py
    ├── test_client.py
    ├── test_schema.py
    ├── test_templates.py
    ├── test_formatters.py
    └── test_cli.py
```

### pyproject.toml

```toml
[project]
name = "jira-cli"
version = "0.1.0"
description = "Jira Cloud CLI + library for agents and humans"
readme = "README.md"
license = "MIT"
authors = [
    { name = "Your Name", email = "you@example.com" }
]
requires-python = ">=3.13"
dependencies = [
    "requestspro",
]

[build-system]
requires = ["uv_build>=0.10.7,<0.11.0"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = "jira"

[project.scripts]
jira = "jira.cli:cli"

[dependency-groups]
dev = [
    "pytest>=9.0.2",
    "pytest-cov>=7.0.0",
    "ruff>=0.15.6",
    "time-machine>=3.2.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=jira --cov-report=term-missing --no-header -q"

[tool.ruff]
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "RUF"]

[tool.ruff.lint.isort]
force-sort-within-sections = true
known-first-party = ["jira"]
```

### Invocation

```bash
# Via uv (development)
uv run jira issue get DEV-22173
uv run jira auth login

# Via python -m (also works)
uv run python -m jira issue get DEV-22173

# After `uv pip install -e .`
jira issue get DEV-22173
```

---

## Auth Layer (`auth.py`)

### Self-contained Atlassian OAuth 2.0 (3LO) — No acli dependency

The auth layer handles the full OAuth lifecycle using requestspro's `RecoverableAuth` + `TokenStore` interfaces, the same pattern as requestspro.

#### Token Storage

Two tokens, same `TokenStore` interface, different backends:

| Token | Lifetime | Backend | Persisted |
|-------|----------|---------|-----------|
| `access_token` | ~1 hour | `ExpireValue` (in-memory) | No |
| `refresh_token` | Weeks/months | `FileCache` (JSON file) | Yes |

```python
BASE_DIR = "~/.config/jira-cli"
# e.g. ~/.config/jira-cli/aaaaaaaa-.../
INSTANCE_DIR = discover_instance_dir(instance_name, BASE_DIR)

token   = TokenStore(ExpireValue(), offset=10)                            # access token (in-memory)
refresh = TokenStore(FileCache(f"{INSTANCE_DIR}/refresh.json"))           # refresh token (persisted)
config  = FileCache(f"{INSTANCE_DIR}/config.json")                       # client_id, cloud_id, site, default_template
```

#### Instance Resolution

```
~/.config/jira-cli/
├── config.json                                  # {"default": "aaaaaaaa-..."}
├── aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/       # mycompany
│   ├── config.json                              # {"site": "mycompany.atlassian.net", ...}
│   └── ...
└── a1b2c3d4-.../                                # second instance (if ever)
    └── ...
```

Resolution order (first match wins):

```
1. --instance mycompany        (CLI flag, matches site name)
2. JIRA_INSTANCE=mycompany     (env var)
3. config.json → "default"    (set automatically on first login)
4. Only one instance exists?   Use it.
5. Error: "Multiple instances found. Use --instance or set a default."
```

`auth login` sets the default automatically on first login. The `--instance` flag matches against the `site` field (e.g. `mycompany` matches `mycompany.atlassian.net`) — not the UUID.

#### FileCache (`cache.py`)

Same interface as `ExpireValue` and `django_cache` — `.get(key)` / `.set(key, value, seconds)`:

```python
class FileCache:
    """File-backed cache with expiry. Same interface as ExpireValue / django_cache.
    
    Candidate for extraction to requestspro once stable.
    """
    
    def __init__(self, path, now=utc_now):
        self.path = Path(path).expanduser()
        self._now = now

    def get(self, key, default=None):
        """Read value from file, return default if missing or expired."""
        if not self.path.exists():
            return default
        data = json.loads(self.path.read_text())
        entry = data.get(key)
        if entry is None:
            return default
        if entry.get("expires_at") and self._now() >= datetime.fromisoformat(entry["expires_at"]):
            return default
        return entry["value"]

    def set(self, key, value, seconds_to_expire):
        """Write value to file with expiry."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(self.path.read_text()) if self.path.exists() else {}
        expires_at = (self._now() + timedelta(seconds=seconds_to_expire)).isoformat() if seconds_to_expire else None
        data[key] = {"value": value, "expires_at": expires_at}
        self.path.write_text(json.dumps(data, indent=2))
```

This gives `TokenStore` a persistent backend with the exact same interface it already uses. Fully testable — inject `now` for deterministic expiry tests.

#### Auth Class

```python
class JiraAuth(RecoverableAuth):
    """Self-contained Atlassian OAuth with auto-refresh. No acli dependency."""

    AUTH_URL = "https://auth.atlassian.com/authorize"
    TOKEN_URL = "https://auth.atlassian.com/oauth/token"
    SESSION_CLASS = ProSession

    def __init__(self, token: TokenStore, client_id: str, refresh: TokenStore):
        self.client_id = client_id
        self.refresh = refresh
        super().__init__(token)

    def renew(self) -> tuple[TokenData, TokenExpiry]:
        """Refresh the access token using the stored refresh_token."""
        refresh_token = self.refresh()
        if not refresh_token:
            raise JiraAuthError("Not logged in. Run: python -m jira auth login")

        r = self.session_class().post(
            self.TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "refresh_token": refresh_token,
            },
        )
        r.raise_for_status()
        data = r.json()
        # Atlassian rotates refresh tokens — save the new one
        if data.get("refresh_token"):
            self.refresh(data["refresh_token"], data.get("refresh_expires_in", 0))
        return data["access_token"], data["expires_in"]
```

#### How it flows (same as requestspro)

```
request → RecoverableAuth.__call__(req) → self.token property
  → TokenStore(ExpireValue).__call__()
    → ExpireValue.get() → cached access_token (if still valid) ✓
    → ExpireValue.get() → None (expired)
      → self._token(*self.renew())
        → self.refresh() → FileCache.get() → refresh_token from disk
        → POST refresh_token → new access_token + rotated refresh_token
        → self.refresh(new_refresh, expiry) → FileCache.set() → saved to disk
        → return (access_token, expires_in)
      → ExpireValue.set(access_token, expires_in) → cached for next call
  → Bearer header set on request

  if 401 anyway → handle_401() → renew() + retry (RecoverableAuth built-in)
```

#### Initial Login (one-time, browser)

```bash
python -m jira auth login
```

This runs the OAuth 2.0 Authorization Code flow with PKCE:

1. Register client dynamically at Atlassian's OAuth server
2. Open browser → user authorizes → callback to localhost
3. Exchange code for access_token + refresh_token
4. Save `client_id` + `refresh_token` to `~/.config/jira-cli/tokens.json`
5. Fetch and save `cloud_id` from accessible resources

Same flow we built and proved in `atlassian-mcp-oauth.py` today.

#### CLI Auth Commands

```bash
python -m jira auth login     # Full browser OAuth flow (one-time, or when refresh_token expires)
python -m jira auth status    # Show: logged in, token valid/expired, cloud_id, user info
python -m jira auth logout    # Remove stored tokens
```

#### Token Lifecycle Summary

| Event | What happens | User action |
|-------|-------------|-------------|
| First use | No tokens exist | `python -m jira auth login` (browser) |
| access_token expired (~1h) | `renew()` uses refresh_token automatically | None — transparent |
| refresh_token rotated | `renew()` saves new refresh_token to file | None — transparent |
| refresh_token expired (rare) | `renew()` fails, CLI prints error | `python -m jira auth login` (browser) |

### Constants

```python
CLOUD_ID = "SOMEUUID"  # Also stored in tokens.json after login
BASE_URL = f"https://api.atlassian.com/ex/jira/{CLOUD_ID}"
AGILE_BASE_URL = f"https://api.atlassian.com/ex/jira/{CLOUD_ID}/rest/agile/1.0"
```

---

## Client Layer (`client.py`)

### Pattern: MainClient + Sub-clients (same as requestspro)

```python
class JiraSession(ProSession):
    RESPONSE_CLASS = JiraResponse

class JiraResponse(ProResponse):
    """Normalizes Jira API responses."""
    # Handles pagination, error extraction, etc.

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
        """Create client from stored OAuth config. No Django needed.
        
        Args:
            instance: Site name (e.g. 'mycompany'), cloud_id, or None for default.
        """
        instance_dir = discover_instance_dir(instance)
        config = FileCache(f"{instance_dir}/config.json")

        cloud_id = config.get("cloud_id")
        client_id = config.get("client_id")
        if not cloud_id or not client_id:
            raise JiraAuthError("Not logged in. Run: python -m jira auth login")

        base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}"
        token = TokenStore(ExpireValue(), offset=10)
        refresh = TokenStore(FileCache(f"{instance_dir}/refresh.json"))
        auth = JiraAuth(token, client_id, refresh)
        session = JiraSession(auth=auth, base_url=base_url)
        return cls(session)
```

### Sub-clients

#### IssueSubClient
```python
class IssueSubClient(Client):
    def get(self, issue_key, fields=None, expand=None) -> dict
    def create(self, project, issue_type, summary, **fields) -> dict
    def edit(self, issue_key, **fields) -> dict
    def delete(self, issue_key) -> None
    def transition(self, issue_key, status_name) -> dict
    def get_transitions(self, issue_key) -> list
    def assign(self, issue_key, account_id) -> None
    def add_comment(self, issue_key, body) -> dict
    def get_comments(self, issue_key) -> list
    def link(self, inward_key, outward_key, link_type) -> None
    def bulk_edit(self, issue_keys, **fields) -> list[dict]
```

#### SearchSubClient
```python
class SearchSubClient(Client):
    def jql(self, query, fields=None, max_results=50) -> list[dict]
    def jql_all(self, query, fields=None) -> list[dict]  # auto-paginate
```

#### SprintSubClient
```python
class SprintSubClient(Client):
    def get(self, sprint_id) -> dict
    def current(self, board_id) -> dict          # active sprint
    def list(self, board_id, state=None) -> list  # active, future, closed
    def issues(self, sprint_id, fields=None) -> list[dict]
```

#### BoardSubClient
```python
class BoardSubClient(Client):
    def get(self, board_id) -> dict
    def list(self, project_key=None) -> list[dict]
    def backlog(self, board_id, fields=None) -> list[dict]
```

#### UserSubClient
```python
class UserSubClient(Client):
    def search(self, query) -> list[dict]  # find by name/email
    def myself(self) -> dict
```

---

## Instance Schema Discovery (`schema.py`)

The schema layer fetches and persists the Jira instance configuration so we can:
- Map friendly names → custom field IDs (`story_points` → `customfield_10036`)
- Know which fields are required per issue type
- Know allowed values for option fields
- Power `--help`, templates, and agent schema output

### Data Sources (Jira REST API)

| Endpoint | What it gives us |
|----------|-----------------|
| `GET /rest/api/3/field` | All 1487 fields — id, name, type, custom flag |
| `GET /rest/api/3/issue/createmeta/{project}/issuetypes` | Issue types per project (Task, Epic, Bug, etc.) |
| `GET /rest/api/3/issue/createmeta/{project}/issuetypes/{typeId}` | Per-type: fields, required flag, allowed values |

### Sync Command

```bash
# Fetch and persist. Re-run anytime someone changes the Jira config.
python -m jira fields sync                     # sync all projects you have access to
python -m jira fields sync --project DEV       # sync specific project

# Also runs automatically after `auth login` (first-time setup)

# Inspect
python -m jira fields list                     # all fields, friendly names → IDs
python -m jira fields list --filter team       # search
python -m jira fields schema --project DEV --type Task   # full schema for a type
```

### Persisted Structure

All instance data lives under `~/.config/jira-cli/{cloud_id}/`:

```
~/.config/jira-cli/
└── aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/
    ├── config.json          # client_id, cloud_id, site, default_template
    ├── refresh.json         # refresh token (via FileCache/TokenStore)
    ├── schema.json          # field registry + per-project per-type schemas
    └── templates/
        ├── instant.json
        └── bug.json
```

### Schema File (`{cloud_id}/schema.json`)

One file, one read. Contains the field registry, friendly name mapping, and per-project per-type schemas:

```json
{
  "cloud_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "site": "mycompany.atlassian.net",
  "synced_at": "2026-03-24T19:00:00Z",
  "fields": {
    "summary": {"id": "summary", "type": "string", "system": true},
    "status": {"id": "status", "type": "status", "system": true},
    "parent": {"id": "parent", "type": "issuelink", "system": true},
    "labels": {"id": "labels", "type": "array", "system": true},
    "priority": {"id": "priority", "type": "priority", "system": true},
    "story_points": {"id": "customfield_10036", "type": "number", "name": "Story Points"},
    "epic_link": {"id": "customfield_10006", "type": "any", "name": "Epic Link"},
    "sprint": {"id": "customfield_10008", "type": "array", "name": "Sprint"},
    "team": {"id": "customfield_10001", "type": "option", "name": "Team"},
    "kpi": {"id": "customfield_10045", "type": "option", "name": "KPI"}
  },
  "projects": {
    "DEV": {
      "types": {
        "Task": {
          "id": "10002",
          "required": ["project", "issuetype", "summary"],
          "fields": {
            "summary": {"type": "string", "required": true},
            "parent": {"type": "issuelink", "required": false},
            "priority": {"type": "option", "required": false, "allowed": ["P0: Critical", "P1: High", "P2: Medium", "P3: Low"]},
            "story_points": {"type": "number", "required": false},
            "components": {"type": "array", "required": false, "allowed": ["API", "Web", "..."]},
            "team": {"type": "option", "required": false}
          }
        },
        "Epic": { "..." : "..." },
        "Bug": { "..." : "..." }
      }
    }
  }
}
```

Friendly name mapping is auto-generated from field names: `"Story Points"` → `story_points`, `"Epic Link"` → `epic_link`. System fields keep their native IDs: `summary`, `status`, `parent`, etc.

Agents can read this schema to know exactly what to pass without guessing. `fields sync` re-fetches and overwrites the file whenever the instance config changes.

### Field Resolution

A pure function that does two jobs: **name resolution** (friendly → field ID) and **value expansion** (flat value → nested dict based on field type from schema).

```python
def resolve_fields(friendly: dict, schema: dict) -> dict:
    """Translate friendly names → Jira field IDs AND expand values to API format.
    
    Name resolution:
      'story_points': ...     → 'customfield_10036': ...
      'team': ...             → 'customfield_10001': ...
      'summary': ...          → 'summary': ...  (system fields pass through)

    Value expansion (based on field type from schema):
      'summary': 'Fix bug'             → 'summary': 'Fix bug'                        (string)
      'story_points': 5                → 'customfield_10036': 5                       (number)
      'parent': 'DEV-22173'            → 'parent': {'key': 'DEV-22173'}              (issuelink)
      'priority': 'P1: High'           → 'priority': {'name': 'P1: High'}            (option by name)
      'team': 'Backend'                → 'customfield_10001': {'value': 'Backend'}   (custom option)
      'components': ['API']            → 'components': [{'name': 'API'}]             (array of named)
      'labels': ['urgent']             → 'labels': ['urgent']                         (array of strings)
    """
```

Value expansion rules are driven by the schema's field type. If a field type is unknown or the value is already a dict/list of dicts, it passes through unchanged. This means you can always provide the raw Jira format in templates or `--json` and it won't be double-wrapped.

### Commonly Used Field Sets (built-in defaults)

```python
FIELDS_SUMMARY = ["summary", "status", "assignee", "priority", "issuetype"]
FIELDS_DETAIL = FIELDS_SUMMARY + ["description", "parent", "epic_link", "sprint", "labels", "components"]
FIELDS_SPRINT_VIEW = FIELDS_SUMMARY + ["story_points", "parent"]
```

These use friendly names and get resolved to field IDs at query time.

---

## Templates

### Purpose

Partial JSON with friendly field names. Provide defaults for repetitive issue creation. Stored in `~/.config/jira-cli/templates/`.

### Example Templates

```json
// ~/.config/jira-cli/templates/instant.json
{
  "project": "DEV",
  "issuetype": "Task",
  "parent": "DEV-22173",
  "labels": ["api-v2"],
  "components": ["API"]
}
```

```json
// ~/.config/jira-cli/templates/bug.json
{
  "project": "DEV",
  "issuetype": "Bug",
  "priority": "P1: High"
}
```

### Template Management

```bash
python -m jira template list
python -m jira template show instant
python -m jira template create instant --json '{"project": "DEV", ...}'
python -m jira template edit instant           # opens $EDITOR
python -m jira template delete instant

# Default template
python -m jira template default instant        # set default
python -m jira template default                # show current
python -m jira template default --clear        # remove default
```

### Composition Order (create/edit)

Four input modes. Later layers **shallow-override** earlier ones (no deep merge — predictable, simple):

```
1. Template (base defaults)
   ↓ shallow override
2. --json (structured override, friendly names)
   ↓ shallow override
3. CLI flags --set key=value (explicit intent)
   ↓ resolve_fields()
4. Final Jira API payload
```

**Or bypass everything:**
```
--raw '{"fields": {...}}'  →  sent directly to Jira API, no resolution
```

### Examples

```bash
# Template provides: project, type, parent, labels
python -m jira issue create --template instant --summary "Fix the thing"

# Override template's parent via --json
python -m jira issue create --template instant --json '{"parent": "DEV-22000"}' --summary "Different epic"

# No template, just friendly JSON
python -m jira issue create --json '{"project": "DEV", "issuetype": "Task", "summary": "Quick fix"}'

# Uses default template (if set)
python -m jira issue create --summary "Fix the thing"

# Raw mode — bypass all resolution, send exact payload to Jira
python -m jira issue create --raw '{"fields": {"project": {"key": "DEV"}, "issuetype": {"name": "Task"}, "summary": "Fix"}}'
python -m jira issue edit DEV-22173 --raw '{"fields": {"parent": {"key": "DEV-22000"}}}'
```

### Why Shallow Override (not deep merge)

Jira fields include arrays (`labels`, `components`) and nested dicts (`parent`, `priority`). Deep merge with arrays is ambiguous — append or replace? Shallow override is predictable: if you provide a key, it fully replaces the template's value. For surgical control over nested structures, use `--raw`.

### Merge + Resolve Function (pure)

```python
def build_issue_fields(
    template: dict | None,
    json_override: dict | None,
    cli_flags: dict,
    schema: dict,
) -> dict:
    """Pure merge: template | json | flags. Then resolve friendly names + expand values."""
    base = template or {}
    merged = {**base, **(json_override or {}), **cli_flags}
    return resolve_fields(merged, schema)
```

### Input Mode Summary

| Mode | Name resolution | Value expansion | Merge behavior |
|------|----------------|-----------------|----------------|
| `--template` | ✓ | ✓ | Base layer |
| `--json '{...}'` | ✓ | ✓ | Overrides template |
| `--set key=value` | ✓ | ✓ | Overrides json + template |
| `--raw '{...}'` | ✗ | ✗ | Bypass everything, sent as-is |

---

## Formatters (`formatters.py`)

Pure functions that transform raw API responses into clean output. These are the agent-friendly JSON shapes.

```python
def format_issue(raw: dict) -> dict:
    """Raw Jira issue → clean {key, summary, status, assignee, ...}"""

def format_issue_list(raw_issues: list[dict]) -> list[dict]:
    """List of raw issues → list of clean dicts"""

def format_sprint(raw: dict) -> dict:
    """Raw sprint → {id, name, state, startDate, endDate}"""

def format_transition(raw: dict) -> dict:
    """Raw transition → {id, name, to_status}"""
```

---

## CLI Layer (`cli.py`)

### Design

Following the cli-scripts skill: `parse(argv=None)` + `cli(argv=None)` with pure functions, I/O at the boundary.

```bash
# Global flag (optional, for multi-instance setups)
python -m jira --instance mycompany <command>   # matches site name
# Also: JIRA_INSTANCE=mycompany env var
# Single instance: auto-detected, no flag needed

# Auth
python -m jira auth login                      # one-time browser OAuth flow (sets default instance)
python -m jira auth status                     # show login state, token expiry, site, cloud_id
python -m jira auth logout                     # remove stored tokens

# Schema / Fields
python -m jira fields sync                     # fetch instance config (re-runnable)
python -m jira fields sync --project DEV       # sync specific project
python -m jira fields list                     # all fields: friendly name → ID
python -m jira fields list --filter team       # search fields
python -m jira fields schema --project DEV --type Task   # full schema for agents

# Templates
python -m jira template list
python -m jira template show instant
python -m jira template create instant --json '{"project": "DEV", "issuetype": "Task", ...}'
python -m jira template edit instant           # opens $EDITOR
python -m jira template delete instant
python -m jira template default instant        # set default template
python -m jira template default                # show current default
python -m jira template default --clear        # remove default

# Issue operations
python -m jira issue get DEV-22173
python -m jira issue get DEV-22173 --fields summary,status,parent
python -m jira issue create --summary "Fix bug"                              # uses default template
python -m jira issue create --template instant --summary "Fix bug"           # explicit template
python -m jira issue create --template instant --json '{"parent": "DEV-22000"}' --summary "Override"
python -m jira issue create --json '{"project": "DEV", "issuetype": "Task", "summary": "Friendly JSON"}'
python -m jira issue create --raw '{"fields": {"project": {"key": "DEV"}, ...}}'   # bypass resolution
python -m jira issue edit DEV-22173 --set parent=DEV-22000 --set priority="P2: Medium"
python -m jira issue edit DEV-22173 --set-json '{"team": "Backend"}'
python -m jira issue edit DEV-22173 --raw '{"fields": {"parent": {"key": "DEV-22000"}}}'
python -m jira issue transition DEV-22173 "In Progress"
python -m jira issue assign DEV-22173 alice@example.com
python -m jira issue comment DEV-22173 "Deployed to staging"
python -m jira issue link DEV-22173 DEV-22174 --type blocks

# Bulk operations
python -m jira bulk edit DEV-21937 DEV-21463 DEV-22032 --set parent=DEV-22173

# Search
python -m jira search "project = DEV AND sprint in openSprints()"
python -m jira search "project = DEV AND assignee = currentUser() AND status != Done"
python -m jira search "parent = DEV-22173" --fields summary,status

# Sprint
python -m jira sprint current --board 42
python -m jira sprint list --board 42 --state active,future
python -m jira sprint issues 123 --fields summary,status,assignee

# Board
python -m jira board list --project DEV
python -m jira board backlog 42

# User
python -m jira user search "alice"
python -m jira user me
```

### Output Format

Two modes only:

- **Default**: Clean JSON to stdout — processed by `formatters.py` (flattened, readable keys)
- **`--raw`**: Raw API response as-is (debugging, edge cases)

```bash
# Default: clean JSON (agent-friendly)
python -m jira issue get DEV-22173
# {"key": "DEV-22173", "summary": "Migrate user endpoints to v2", "status": "To Do", ...}

# Raw API response
python -m jira issue get DEV-22173 --raw
# {"expand": "...", "id": "123231", "fields": {"summary": "...", ...}}

# Humans who want tables can pipe through jq:
python -m jira search "parent = DEV-22173" | jq -r '.[] | [.key, .status, .summary] | @tsv' | column -t
```

---

## Tests (`tests/`)

### Pattern: Same as requestspro test_client.py

- **Class-based** test organization
- **Mock the session** — `make_session()` helper returns a mock `JiraSession`
- **Test sub-client methods** — verify correct URL, payload, HTTP method
- **Test formatters** — pure dict → dict, no mocks needed
- **Test CLI parse** — `parse(["issue", "get", "DEV-123"])` returns correct args
- **Test auth** — mock keychain subprocess, verify token extraction

```python
class TestIssueSubClient:
    def test_get_calls_correct_url(self):
        sub = IssueSubClient(make_session())
        with patch.object(sub, "get") as mock:
            sub.get("DEV-123")
            mock.assert_called_once_with("/rest/api/3/issue/DEV-123")
    
    def test_bulk_edit_updates_all_issues(self): ...
    def test_transition_resolves_status_name_to_id(self): ...

class TestSearchSubClient:
    def test_jql_sends_correct_query(self): ...
    def test_jql_all_paginates(self): ...

class TestFormatIssue:
    def test_extracts_key_and_summary(self): ...
    def test_handles_missing_assignee(self): ...

class TestFileCache:
    def test_get_returns_default_when_file_missing(self): ...
    def test_get_returns_default_when_key_missing(self): ...
    def test_get_returns_default_when_expired(self): ...
    def test_get_returns_value_when_valid(self): ...
    def test_get_returns_value_when_no_expiry(self): ...
    def test_set_creates_parent_dirs(self): ...
    def test_set_writes_value_and_expiry(self): ...
    def test_set_overwrites_existing_key(self): ...
    def test_set_preserves_other_keys(self): ...
    def test_injectable_now_for_deterministic_expiry(self): ...

class TestJiraAuth:
    def test_renew_posts_refresh_token_to_token_url(self): ...
    def test_renew_returns_access_token_and_expiry(self): ...
    def test_renew_saves_rotated_refresh_token(self): ...
    def test_renew_preserves_refresh_token_when_not_rotated(self): ...
    def test_renew_raises_when_no_refresh_token(self): ...
    def test_token_property_returns_cached_when_valid(self): ...
    def test_token_property_calls_renew_when_expired(self): ...

class TestCliParse:
    def test_auth_login_parses(self): ...
    def test_auth_status_parses(self): ...
    def test_issue_get_parses_key(self): ...
    def test_search_parses_jql(self): ...
    def test_bulk_edit_parses_multiple_keys(self): ...
```

---

## Implementation Order

### Phase 1: Foundation
1. `cache.py` — FileCache (get/set with expiry, same interface as ExpireValue)
2. `auth.py` — JiraAuth(RecoverableAuth) + two TokenStores + OAuth login flow
3. `cli.py` — `auth login`, `auth status`, `auth logout`
4. Tests for cache + auth

### Phase 2: Schema + Core
5. `schema.py` — field sync, friendly name mapping, field resolution, per-type schema
6. `cli.py` — `fields sync`, `fields list`, `fields schema`
7. `client.py` — JiraClient + IssueSubClient + SearchSubClient
8. `formatters.py` — format_issue, format_issue_list
9. `cli.py` — `issue get`, `issue edit`, `search`, `bulk edit`
10. Tests for schema + client + formatters

### Phase 3: Templates + Create
11. `templates.py` — template CRUD, default template, merge logic
12. `cli.py` — `template` commands + `issue create` with template/json/flags composition
13. Tests for templates

### Phase 4: Sprint & Board
14. SprintSubClient — current, list, issues
15. BoardSubClient — list, backlog
16. CLI commands for sprint/board
17. Tests

### Phase 5: Polish
18. UserSubClient — search, me
19. `issue transition`, `issue comment`, `issue link`, `issue assign`
20. CLAUDE.md documentation

---

## Key Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Token source | Self-contained OAuth 2.0 (3LO) | No acli dependency, auto-refresh via refresh_token, one-time browser login |
| Access token cache | `TokenStore(ExpireValue())` | Same interface as requestspro's `TokenStore(django_cache)`, but in-memory, no Django |
| Refresh token storage | `TokenStore(FileCache())` | Same `TokenStore` interface, file-backed. Atlassian rotates refresh tokens. |
| Config storage | `FileCache("~/.config/jira-cli/config.json")` | client_id, cloud_id — persistent, no expiry |
| Auth class | `JiraAuth(RecoverableAuth)` | Same pattern as `ExistingAuth` — `renew()` + 401 auto-recovery |
| HTTP library | requestspro | Same as requestspro — ProSession, ProResponse, Client, MainClient |
| No Django dependency | Yes | CLI must work standalone (like existing CLI) |
| JSON output default | Yes | Agents parse JSON; humans can use `--format table` |
| Package location | `~/projects/jira` (standalone repo) | Own repo like `beans`, not tied to backend |
| REST API, not MCP | Yes | Full API coverage, no Cloudflare, no token expiry hassle |
| Jira Cloud only | Yes | Targets Jira Cloud instances only |

---

## Future Extraction to requestspro

Track improvements built here that should move to requestspro when stable:

| Component | Current location | Notes |
|-----------|-----------------|-------|
| `FileCache` | `jira/cache.py` | General-purpose file-backed cache with expiry. Same `.get()`/`.set()` interface as `ExpireValue` and `django_cache`. Any `TokenStore` can use it. |

---

## Jira API Endpoints Reference

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Get issue | GET | `/rest/api/3/issue/{key}` |
| Create issue | POST | `/rest/api/3/issue` |
| Edit issue | PUT | `/rest/api/3/issue/{key}` |
| Delete issue | DELETE | `/rest/api/3/issue/{key}` |
| Get transitions | GET | `/rest/api/3/issue/{key}/transitions` |
| Transition issue | POST | `/rest/api/3/issue/{key}/transitions` |
| Assign issue | PUT | `/rest/api/3/issue/{key}/assignee` |
| Add comment | POST | `/rest/api/3/issue/{key}/comment` |
| Search (JQL) | POST | `/rest/api/3/search` |
| Link issues | POST | `/rest/api/3/issueLink` |
| Get boards | GET | `/rest/agile/1.0/board` |
| Get sprints | GET | `/rest/agile/1.0/board/{boardId}/sprint` |
| Get sprint issues | GET | `/rest/agile/1.0/sprint/{sprintId}/issue` |
| Get backlog | GET | `/rest/agile/1.0/board/{boardId}/backlog` |
| Search users | GET | `/rest/api/3/user/search` |
| Get myself | GET | `/rest/api/3/myself` |
