@conventions.md
@.beans/AGENTS.md

## Releasing

Use the release script — never release manually:

```bash
./scripts/release.sh 0.5.0
```

It runs tests, bumps the version, generates the changelog, commits, tags,
pushes, and creates the GitHub release. Requires `git-cliff` and `gh`.
