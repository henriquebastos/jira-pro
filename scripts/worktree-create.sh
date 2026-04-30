#!/usr/bin/env bash
set -euo pipefail

# Create an isolated git worktree for a beans epic.
#
# Usage: ./scripts/worktree-create.sh <epic-id> <branch-slug>
#
# Example:
#   ./scripts/worktree-create.sh bean-1be9a822 add-bulk-edit-command
#   → creates worktree at ../jira-genie-worktrees/bean-1be9a822-add-bulk-edit-command

EPIC_ID="${1:?Usage: $0 <epic-id> <branch-slug>}"
SLUG="${2:?Usage: $0 <epic-id> <branch-slug>}"

BRANCH="${EPIC_ID}-${SLUG}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKTREE_ROOT="${REPO_ROOT}/../jira-genie-worktrees"
WORKTREE_PATH="${WORKTREE_ROOT}/${BRANCH}"

if [ -d "$WORKTREE_PATH" ]; then
  echo "Worktree already exists: $WORKTREE_PATH"
  exit 0
fi

echo "==> Creating worktree: $WORKTREE_PATH (branch: $BRANCH)"
mkdir -p "$WORKTREE_ROOT"

# Fetch latest main before branching
git fetch origin main

# Create worktree with new branch from origin/main
git worktree add -b "$BRANCH" "$WORKTREE_PATH" origin/main

# Bootstrap the worktree
cd "$WORKTREE_PATH"
uv sync

# Quick sanity check
uv run pytest -x -q

echo "✅ Worktree ready: $WORKTREE_PATH"
echo "   Branch: $BRANCH"
echo "   Epic: $EPIC_ID"
