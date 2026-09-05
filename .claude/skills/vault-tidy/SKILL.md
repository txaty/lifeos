---
name: vault-tidy
description: Find and report what has drifted — orphans, uncited sources, stale pages, broken links, unsafe filenames — and fix only the unambiguous mechanical errors. Propose everything else. Use when the user says "tidy the vault", "clean up", or "run maintenance".
---

# Tidy

**Additive and propose-only.** This is the rule that makes it safe to run unattended: a tidy pass may
fix an unambiguous mechanical error; everything else is a proposal in the run log.

**Inputs:** the whole vault, read-only to begin with.
**Outputs:** `logs/YYYY-MM-DD-tidy.md`; a small number of mechanical fixes.
**May modify:** `logs/`, plus the specific fixes listed below.
**Never:** bulk moves, renames, deletes, merges, frontmatter migrations, or resolving a
`## Disagreements` section — none of it, not even when it looks obvious.

## Step 1 — Look

```
python3 scripts/vault.py doctor
python3 scripts/vault.py links --wanted
```

`doctor` reports what `check` deliberately will not, because these are judgment calls: orphans,
uncited sources, stale pages, dangling citations, link-unsafe filenames, pages with no domain.

## Step 2 — Fix only what has one right answer

You may fix, without asking:

- a generated file that is stale → `python3 scripts/vault.py index`
- a lint error with exactly one possible correction (an unquoted `created:`, a `#` on a tag, a
  template's `a | b | c` left unsubstituted where the intended value is unambiguous from context)
- a broken link whose target was renamed and now has the old name in `aliases:` — the link already
  resolves; nothing to do but confirm it

That is the whole list. If a fix requires knowing what the user meant, it is a proposal.

## Step 3 — Propose everything else

Write these into the run log, with evidence, and stop:

- **Orphans** — "these N pages have no inbound links; here are the three most likely places to link
  each from"
- **Near-duplicate pages** — "[[A]] and [[B]] appear to cover the same concept" — **propose, never
  merge.** Merging destroys the version the user would have kept.
- **Uncited sources** — the coverage figure and the oldest offenders. This trend matters more than
  the number.
- **Stale pages** — untouched beyond `stale_wiki_days`; suggest re-confirming or retiring.
- **Unsafe filenames** — with the exact `vault.py rename` command for each, not run.
- **Missing `domain`** — with a suggestion each, applied only on request.
- **Structural observations** — an area with no projects for months, a project with no tasks and no
  log entries. Say what you see; the decision is theirs.

## Step 4 — Log

Write `logs/YYYY-MM-DD-tidy.md` with `## What ran`, `## Files written`, `## Skipped`, and
`## Proposals`. Include the proposals even when there are many — a proposal that is not written down
did not happen.

Then `python3 scripts/vault.py check`.

## Step 5 — Report

```
Fixed: n mechanical issues (listed).
Proposed: m changes for review — see logs/YYYY-MM-DD-tidy.md.
Health: orphans o · source coverage c% · stale pages s · broken links b.
```

Lead with the proposals count, not the fixes. What you *did not* do is the more important half.
