# Workflow

How work moves through this project — from task discovery to merged commit.

## Task lifecycle

```text
beans ready          → pick a bean
beans claim <id>     → claim it
  ↓
Read bean body       → understand scope, what "done" looks like
  ↓
RED: write failing test
GREEN: make it pass  → commit: feat: …
REFACTOR: clean up   → commit: refactor: …
  ↓  (repeat until bean scope is complete)
Verify gate          → uv run pytest && uv run ruff check src/ tests/
inspect-5p           → review uncommitted changes
Commit               → #closes <bean-id> on final commit
beans close <id>     → close the bean
```

Every step below is a rule within this lifecycle.

## Bean-first rule

Every change — feature, fix, or refactor — MUST have a bean before code begins.
If you discover work mid-task, create a bean for it before starting. No exceptions,
even for "quick fixes."

## Update docs with feature changes

When a feature changes user-facing behavior (new flags, changed defaults, new commands),
update README.md in the same commit. Don't leave docs out of sync.

## Red-green-refactor TDD

1. Write a failing test (RED)
2. Make it pass minimally (GREEN)
3. Commit: `feat: <description>`
4. Refactor, verify green
5. Commit: `refactor: <description>`

## Small commits

Each commit does one thing. Use conventional commit messages:

- `feat:` — new functionality
- `fix:` — bug fix
- `refactor:` — code improvement, no behavior change
- `chore:` — tooling, config, deps
- `docs:` — documentation
- `ci:` — CI/CD changes

When a commit resolves a bean, append `#closes <bean-id>` to the commit message:

```bash
git commit -m "feat: add --body flag to create command #closes bean-69b4e720"
```

## Verify before committing

```bash
uv run pytest
uv run ruff check src/ tests/
```

## Review before committing (required)

After tests and lint pass, **always** run `inspect-5p` before committing — including
in autonomous mode:

```text
inspect-5p
```

This runs a 5-pass parallel review of uncommitted changes, covering security, correctness,
design, testing, and conventions. Fix any issues found, re-run tests, then commit.

## Public repo hygiene

This is a public repo. Before committing:

- No company names, internal URLs, or real email addresses in code, docs, or beans
- Use generic examples: `acme.atlassian.net`, `alice@example.com`, `DEV-123`
- Hardcoded API credentials are intentional (same pattern as gh CLI) — document why
- Author in pyproject.toml: `Henrique Bastos <henrique@bastos.net>`

## Releasing

Use the release script — never release manually:

```bash
./scripts/release.sh 0.5.0
```

It runs tests, bumps the version, generates the changelog, commits, tags,
pushes, and creates the GitHub release. Requires `git-cliff` and `gh`.
