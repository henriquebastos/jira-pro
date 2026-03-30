#!/usr/bin/env bash
set -euo pipefail

VERSION=${1:?Usage: ./scripts/release.sh <version>}

echo "==> Verifying..."
uv run pytest -x -q
uv run ruff check src/ tests/

echo "==> Bumping to $VERSION..."
sed -i '' "s/^version = .*/version = \"$VERSION\"/" pyproject.toml

echo "==> Generating changelog..."
git-cliff --tag "v$VERSION" -o CHANGELOG.md

echo "==> Committing and tagging..."
git add -A
git commit -m "chore(release): prepare for v$VERSION"
git tag "v$VERSION"

echo "==> Pushing..."
git push && git push --tags

echo "==> Creating GitHub release..."
git-cliff --tag "v$VERSION" --unreleased | gh release create "v$VERSION" --title "v$VERSION" --notes-file -

echo "✅ v$VERSION released"
