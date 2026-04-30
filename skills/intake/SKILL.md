---
name: intake
description: >
  Sync GitHub Issues into beans epics. Run periodically or on demand to import
  new issues as beans epics for the orchestrator to pick up.
---

# Intake — GitHub Issues → Beans Epics

Import open GitHub Issues as beans epics so the orchestrator has a single
work queue.

## Prerequisites

- `gh` CLI authenticated (`gh auth status`)
- `beans` CLI available

## How it works

1. Fetch open GitHub Issues that haven't been imported yet.
2. For each issue, create a beans epic with the issue body as the spec.
3. Tag the epic with a `ref_id` so we can detect duplicates on re-runs.

## Steps

### 1. Fetch open issues

```bash
gh issue list --state open --json number,title,body,labels --limit 100
```

### 2. Check for already-imported issues

For each issue, check if a bean with a matching `ref_id` already exists.
The `ref_id` convention is `gh-<number>` (e.g. `gh-42`).

```bash
beans list --json | jq '.[] | select(.ref_id == "gh-42")'
```

If a bean already exists for this issue, skip it.

### 3. Create beans epic

For each new issue:

```bash
beans create "<issue title>" \
  --type epic \
  --body "<issue body>" \
  --ref-id "gh-<number>"
```

### 4. Report

List what was imported:

```bash
echo "Imported: #<number> → <bean-id>"
```

## Mapping

| GitHub Issue field | Beans epic field |
| ------------------ | ---------------- |
| `number`           | `ref_id` as `gh-<number>` |
| `title`            | `title` |
| `body`             | `body` |
| `labels`           | not mapped (could be priority later) |

## Notes

- This is a one-way sync: GH Issues → beans. Beans don't write back to GH Issues.
- PR linking happens at finalize time (docs/workflow.md step 3), not during intake.
- Re-running intake is safe — duplicates are skipped via `ref_id`.
- Closed GH Issues are not imported. If an issue is closed after import,
  the orchestrator handles it by checking bean status, not GH state.
