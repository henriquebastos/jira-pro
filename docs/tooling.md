# Tooling

Quick reference for tools used in this project.

| Tool    | Purpose                                            |
| ------- | -------------------------------------------------- |
| **uv** | Package management, running, building |
| **beans** | Task tracking (`beans ready`, `beans list`) |
| **pytest** | Testing with coverage |
| **ruff** | Linting (line-length=120, select E,F,I,N,UP,RUF) |
| **argparse** | CLI framework (stdlib, dynamic schema support) |
| **responses** | HTTP mocking for tests (same pattern as requests-pro) |
| **git-cliff** | Changelog generation |
| **gh** | GitHub CLI (releases, PR management) |

## Verification gate

```bash
uv run pytest
uv run ruff check src/ tests/
```

## Common commands

```bash
# Development
uv sync                          # install deps
uv run pytest                    # run tests
uv run pytest -x -q              # quick fail-fast
uv run ruff check src/ tests/    # lint
uv run ruff format src/ tests/   # format

# Task tracking
beans ready                      # see unblocked work
beans show <id>                  # read a bean
beans create "Title" --body "…"  # create a bean
beans close <id>                 # close a bean

# Release
./scripts/release.sh 0.5.0      # full release flow
```
