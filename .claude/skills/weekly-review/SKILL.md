---
name: weekly-review
description: Scaffold this week's review from deterministic vault facts — inbox, stale projects, decisions due, open tasks, new knowledge — and propose status changes without applying them. Use when the user says "weekly review", "review the week", or on the weekly slot.
---

# Weekly review

The one habit that keeps everything else honest. Facts first, so the review argues with data rather
than with mood.

**Inputs:** `vault.py status --json`, `vault.py tasks`.
**Outputs:** `outputs/reviews/YYYY-Www.md`; **proposed** project status changes.
**May modify:** `outputs/reviews/`, and project frontmatter only after the user accepts a proposal.

## Step 1 — Empty the queue first

If `inbox/` is not empty, run `process-inbox` before continuing, or ask whether to skip it. Reviewing
around a full inbox reviews the wrong things.

## Step 2 — Gather facts

```
python3 scripts/vault.py status --json
python3 scripts/vault.py tasks
```

## Step 3 — Scaffold

```
python3 scripts/vault.py new review
```

Creates `outputs/reviews/YYYY-Www.md` from the template. Fill `## Facts`:

| Fact | Value |
|---|---|
| Inbox | n items (oldest d days) |
| Projects | active a · idea i · paused p · done d |
| Stale active | list |
| Old ideas | list |
| Decisions due | list |
| Open tasks | n across m notes |
| Wiki pages added | n; notable: [[…]] |

## Step 4 — Propose, do not apply

Under `## Proposed changes`, one line per project the facts argue about, **each carrying its
evidence**:

```
- [[Some Project]] active → paused (untouched 45d, no open tasks, no stated blocker)
- [[Other Project]] done → archived (run archive-project)
- [[Old Idea]] idea → activate or delete (97 days old)
- [[A Decision]] → record the outcome (decided 2026-08-28, review was due 2026-09-11)
```

**Do not touch a project file in this step.** The evidence is what lets the user disagree with you,
and a proposal without it is just an instruction.

## Step 5 — Hand over

Tell the user the review path and the proposal count. Leave `## Reflection` entirely alone — three
honest lines about the week is the part only they can write, and a model filling it in makes the
review worthless.

When they accept a proposal, apply it: edit `status`, bump `updated`, and for archives invoke
`archive-project`.

## Step 6 — Close

```
python3 scripts/vault.py index && python3 scripts/vault.py check
```

Report errors rather than suppressing them.

## Note on cadence

Monthly and quarterly reviews are deliberately not scaffolded (`docs/decisions.md`, ADR-007). If the
user wants a quarterly check-in, add a `## Quarterly` section to `templates/weekly-review.md` rather
than creating a new note type.
