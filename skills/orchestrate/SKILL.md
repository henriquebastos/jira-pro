---
name: orchestrate
description: >
  Poll beans for ready epics, create worktrees, and delegate to sub-agents
  that implement each epic following docs/workflow.md. Use when asked to "run
  orchestration", "process epics", or "start the agent loop".
---

# Orchestrate — Epic Dispatch Loop

Monitor beans for ready epics and delegate each to a sub-agent in an
isolated worktree.

## Prerequisites

- `gh` CLI authenticated
- `beans` CLI available
- `git` worktree support
- Scripts: `scripts/worktree-create.sh`, `scripts/worktree-remove.sh`

## Loop

### 1. Intake (optional)

Run the intake skill first if GitHub Issues should be imported:

```text
→ skills/intake/SKILL.md
```

### 2. Find ready epics

```bash
beans ready --type epic
```

This returns epics with no unresolved blockers. Skip epics that are
already claimed by another agent.

### 3. For each ready epic

#### 3a. Derive branch slug

From the epic title: lowercase, spaces to hyphens, drop punctuation,
truncate to ~50 chars.

Example: `"Add bulk edit command"` → `add-bulk-edit-command`

#### 3b. Create worktree

```bash
./scripts/worktree-create.sh <epic-id> <branch-slug>
```

This creates `../jira-genie-worktrees/<epic-id>-<slug>/` with a fresh
branch from `origin/main`, runs `uv sync`, and verifies tests pass.

#### 3c. Claim the epic

```bash
beans claim <epic-id> --actor orchestrator
```

#### 3d. Delegate to sub-agent

Spawn a sub-agent in the worktree directory with this task:

> Follow docs/workflow.md to implement epic `<epic-id>`.

The sub-agent operates autonomously inside the worktree using the
full docs/workflow.md operating script: plan → TDD loop → push → PR.

### 4. Monitor outcomes

After a sub-agent finishes:

- **Success (PR created):** the epic should be closed by the sub-agent.
  Verify with `beans show <epic-id>`.
- **Failure/crash:** check `beans ready --parent <epic-id>` for remaining
  work. The worktree and branch are preserved for retry. A new sub-agent
  can resume from the current state.
- **Blocked:** sub-agent should have stopped and reported the blocker.
  Check the GitHub Issue (if one exists) for a blocker comment.

### 5. Cleanup (after merge)

Once the PR is merged:

```bash
./scripts/worktree-remove.sh <epic-id> <branch-slug>
```

## Concurrency

- One sub-agent per epic.
- Multiple epics can run in parallel in separate worktrees.
- The orchestrator should not dispatch the same epic twice (check
  `beans show <epic-id>` — if status is `in_progress`, skip it).

## State recovery

All state lives in beans + git:

- **Which epics are in flight?** `beans list --type epic --status in_progress`
- **Which leaves remain?** `beans ready --parent <epic-id>`
- **What code exists?** `git worktree list` + branch state
- **No external DB needed.** Restart the orchestrator and it resumes
  from beans state.
