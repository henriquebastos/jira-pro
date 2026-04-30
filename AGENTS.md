# jira-genie

Python CLI + library for Jira Cloud. JSON output for agent consumption,
human-readable when interactive.

## Orientation

- **Architecture and module map:** docs/architecture.md
- **Code conventions:** docs/conventions.md
- **Testing patterns:** docs/testing.md
- **Contributing (beans → TDD → commit):** docs/contributing.md
- **Agent workflow (sub-agent operating script):** docs/workflow.md
- **Tooling reference:** docs/tooling.md
- **Implementation design:** PLAN.md

## Verification gate

```bash
uv run pytest
uv run ruff check src/ tests/
```

## Work tracking

@docs/beans.md

## Releasing

Use the release script — never release manually:

```bash
./scripts/release.sh 0.5.0
```

Requires `git-cliff` and `gh`.
