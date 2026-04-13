# Architecture

Top-level map of jira-genie for navigating the codebase.

## Module Map

```text
src/jira_genie/
├── cli.py           # Entry point. parse(argv) → Namespace, cli(argv) → I/O.
│                    # All I/O lives here. Library modules are pure.
├── auth.py          # OAuth 2.0 3LO with PKCE. JiraAuth(RecoverableAuth) +
│                    # login flow + token refresh. Uses requestspro's TokenStore.
├── cache.py         # FileCache — file-backed cache with expiry. Same .get/.set
│                    # interface as ExpireValue. Backs the refresh token store.
├── config.py        # Instance discovery. Resolves --instance / env / default
│                    # to a config dir under ~/.config/jira-genie/{cloud_id}/.
├── client.py        # JiraClient(MainClient) + sub-clients:
│                    #   IssueSubClient, SearchSubClient, UserSubClient,
│                    #   SprintSubClient, BoardSubClient.
│                    # Uses requestspro's ProSession/Client pattern.
├── schema.py        # Instance field discovery. Syncs Jira field metadata,
│                    # builds friendly_name → field_id mapping, resolves
│                    # friendly dicts to Jira API payloads.
├── templates.py     # Template CRUD + build_issue_fields() merge pipeline:
│                    # template → --json → --set → resolve_fields().
├── formatters.py    # Pure functions: raw Jira API response → clean JSON.
├── adf.py           # Atlassian Document Format → Markdown conversion.
├── completers.py    # Shell completion helpers for templates and fields.
├── skill.py         # Agent skill install/uninstall (SKILL.md distribution).
└── __main__.py      # python -m jira_genie entry point.
```

## Data Flow

```text
User input (CLI)
  │
  ▼
parse(argv)              # cli.py — pure parsing, returns Namespace
  │
  ▼
build_issue_fields()     # templates.py — merge: template | json | flags
  │
  ▼
resolve_fields()         # schema.py — friendly names → field IDs + value expansion
  │
  ▼
JiraClient.issue.*()     # client.py — HTTP via requestspro
  │
  ▼
format_issue()           # formatters.py — raw API → clean JSON
  │
  ▼
stdout (JSON)            # cli.py — I/O boundary
```

## Auth Flow

```text
JiraAuth(RecoverableAuth)
  │
  ├─ access_token:  TokenStore(ExpireValue())     # in-memory, ~1h
  └─ refresh_token: TokenStore(FileCache())       # persisted, rotated by Atlassian

On request:
  token cached + valid? → use it
  token expired?        → renew() using refresh_token → POST to Atlassian
  401 anyway?           → handle_401() → renew + retry (RecoverableAuth built-in)
  refresh expired?      → error: "Run jira auth login"
```

## Config Layout

```text
~/.config/jira-genie/
├── config.json                              # {"default": "<cloud_id>"}
└── <cloud_id>/
    ├── config.json                          # client_id, cloud_id, site
    ├── refresh.json                         # refresh token (FileCache)
    ├── schema.json                          # field registry + per-project type schemas
    └── templates/
        ├── instant.json                     # user-defined templates
        └── bug.json
```

## Key Design Decisions

1. **requestspro as HTTP foundation** — ProSession, Client, MainClient, RecoverableAuth,
   TokenStore. Same patterns as other requestspro-based projects.

2. **argparse over Typer/Click** — Jira's field schema is dynamic. `--set key=value` and
   `--json '{…}'` need runtime control that decorator frameworks fight.

3. **Friendly names + resolve** — Users write `story_points`, `resolve_fields()` translates
   to `customfield_10036`. Schema is synced from the Jira instance, not hardcoded.

4. **Shallow override in templates** — template → json → flags. Each layer fully replaces
   keys from the previous. No deep merge ambiguity.

5. **Pure library, I/O at CLI boundary** — Library functions accept parameters, CLI decides
   values. No module-level config reads.

## Test Layout

```text
tests/
├── conftest.py              # shared fixtures (responses mock)
├── test_auth.py             # OAuth + token refresh
├── test_cache.py            # FileCache expiry behavior
├── test_cli.py              # parse() + cli() integration
├── test_client.py           # sub-client HTTP calls
├── test_completers.py       # shell completion
├── test_config.py           # instance discovery
├── test_formatters.py       # raw → clean JSON
├── test_schema.py           # field sync + resolve
├── test_skill.py            # skill install/uninstall
└── test_templates.py        # template CRUD + merge
```
