# Workflow — Sub-Agent Operating Script

This is the operating script for a sub-agent working on a beans epic
inside an isolated worktree. The orchestrator spawns one sub-agent per
epic and passes the epic ID.

## Input

- `EPIC_ID` — the beans epic to implement

## Step 0: Orient

1. Read the epic:

   ```bash
   beans show <EPIC_ID>
   ```

2. Understand the scope from the epic body. The body is the spec —
   it describes what needs to change, why, and what "done" looks like.

3. Check for existing leaf beans:

   ```bash
   beans list --parent <EPIC_ID>
   ```

   If leaves already exist (e.g. from a previous crashed run), assess
   their status before creating new ones.

## Step 1: Plan — break the epic into leaf beans

1. Analyze the epic scope and break it into small, independent tasks.
   Each leaf bean should map to one TDD cycle — one failing test, one
   passing implementation, one commit.

2. Create leaf beans:

   ```bash
   beans create "Short task title" --parent <EPIC_ID> --body "What to change and why. Done when: ..."
   ```

3. Add dependencies between leaves when order matters:

   ```bash
   beans dep add <blocker-id> <blocked-id>
   ```

4. Verify the plan:

   ```bash
   beans list --parent <EPIC_ID>
   beans ready --parent <EPIC_ID>
   ```

   `beans ready` should show only the unblocked starting tasks.

## Step 2: Execute — TDD loop

Repeat until no ready leaves remain:

1. **Pick** the next unblocked leaf:

   ```bash
   beans ready --parent <EPIC_ID>
   ```

2. **Claim** it:

   ```bash
   beans claim <leaf-id> --actor agent
   ```

3. **RED** — write a failing test that captures the leaf's acceptance
   criteria.

4. **GREEN** — make it pass with the simplest implementation.

5. **Verify gate:**

   ```bash
   uv run pytest
   uv run ruff check src/ tests/
   ```

6. **Review** — run `inspect-5p` on uncommitted changes.

7. **Commit:**

   ```bash
   git commit -m "feat: <description> #closes <leaf-id>"
   ```

   Use conventional commit prefixes. Include `#closes <leaf-id>` to
   link the commit to the bean.

8. **Refactor** if needed, verify green, then:

   ```bash
   git commit -m "refactor: <description>"
   ```

9. **Close** the leaf:

   ```bash
   beans close <leaf-id>
   ```

10. Check for newly unblocked leaves and continue:

    ```bash
    beans ready --parent <EPIC_ID>
    ```

## Step 3: Finalize — push and PR

1. Verify all leaves are closed:

   ```bash
   beans list --parent <EPIC_ID> --status open
   ```

   This should return nothing. If open leaves remain, go back to step 2.

2. Run the full verification gate one final time:

   ```bash
   uv run pytest
   uv run ruff check src/ tests/
   ```

3. Push the branch:

   ```bash
   git push -u origin HEAD
   ```

4. Create a PR:

   ```bash
   gh pr create --title "<epic title>" --body "<PR body>"
   ```

   The PR body should include:
   - Context: why this change (from epic body)
   - Summary: what changed (from closed leaf beans)
   - Test plan: verification commands run

5. If a GitHub Issue originated this epic, link it:

   ```bash
   gh pr edit <pr-number> --add-label "closes #<issue-number>"
   ```

6. Close the epic:

   ```bash
   beans close <EPIC_ID>
   ```

## Conventions

- **Branch naming:** `<EPIC_ID>-<friendly-slug>` (e.g. `bean-1be9a822-add-bulk-edit-command`).
  Derive the slug from the epic title: lowercase, spaces to hyphens, drop punctuation.
- **One branch per epic.** All leaf bean commits land on the same branch.
- **Conventional commits:** `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`
- **Bean references:** append `#closes <bean-id>` to the commit that completes a leaf.
- **No scope creep.** If you discover work outside the epic, create a new
  bean for it (`beans create "..." --body "..."`) — do not expand the current epic.
- **Public repo hygiene.** No company names, internal URLs, or real emails.
  Use generic examples: `acme.atlassian.net`, `alice@example.com`, `DEV-123`.

## Error handling

- **Test failure:** fix it before committing. Do not skip the verify gate.
- **inspect-5p finds issues:** fix them, re-run tests, then commit.
- **Crash/restart:** `beans ready --parent <EPIC_ID>` shows remaining work.
  Assess existing branch state and resume from where things left off.
- **Blocked by missing info:** create a comment on the GitHub Issue (if one
  exists) describing the blocker, then stop. Do not guess.

## Guards

- Never work outside the worktree directory.
- Never modify beans from other epics.
- Never push to `main` directly — always go through a PR.
- Never skip `inspect-5p` before committing.
- Never close a leaf bean without a passing verify gate.
