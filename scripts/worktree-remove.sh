#!/usr/bin/env bash
set -euo pipefail

# Remove a git worktree for a beans epic.
#
# Usage: ./scripts/worktree-remove.sh <epic-id> <branch-slug>
#
# Example:
#   ./scripts/worktree-remove.sh bean-1be9a822 add-bulk-edit-command

EPIC_ID="${1:?Usage: $0 <epic-id> <branch-slug>}"
SLUG="${2:?Usage: $0 <epic-id> <branch-slug>}"

BRANCH="${EPIC_ID}-${SLUG}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKTREE_ROOT="${REPO_ROOT}/../jira-genie-worktrees"
WORKTREE_PATH="${WORKTREE_ROOT}/${BRANCH}"

if [ ! -d "$WORKTREE_PATH" ]; then
  echo "Worktree not found: $WORKTREE_PATH"
  exit 0
fi

echo "==> Removing worktree: $WORKTREE_PATH"
git worktree remove "$WORKTREE_PATH" --force

# Clean up branch if it was merged
if git branch --merged main | grep -q "$BRANCH"; then
  echo "==> Deleting merged branch: $BRANCH"
  git branch -d "$BRANCH"
fi

echo "✅ Worktree removed: $WORKTREE_PATH"
