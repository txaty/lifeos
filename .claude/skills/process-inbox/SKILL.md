---
name: process-inbox
description: Route every item in inbox/ to its proper home using the decision tree in docs/routing.md, then delete the inbox file. Use when the user says "process my inbox", "clear the inbox", "triage captures", or at the start of a weekly review.
---

# Process inbox

**Inputs:** every file in `inbox/`.
**Outputs:** items routed; inbox empty except what genuinely could not be decided; a summary.
**May modify:** `inbox/ daily/ projects/ areas/ people/ meetings/ outputs/`, plus whatever an invoked
ingestion run owns.
**Never:** writes `wiki/` directly, creates a folder or note type, or invents a person or an area.

## Step 1 — Load context once

```
python3 scripts/vault.py status --json
ls areas/ people/ projects/
```

Knowing what already exists is what stops you creating `people/Robin.md` when `people/Robin Hale.md`
is right there. Keep `docs/routing.md` §1 open; apply it top-down, first match wins.

## Step 2 — Classify, oldest first

Read the whole item before deciding.

| It looks like | Do |
|---|---|
| a URL | run `ingest` on it; attach it to a project if the capture names one |
| an outcome with an end state | `vault.py new project "<Title>" --set status=idea`; paste their text under `## Status` |
| a task for something that exists | append `- [ ]` under that note's `## Tasks`; bump `updated` |
| a note about a known person | append a dated bullet under their `## Notes`; bump `updated` |
| a note about an unknown person | **ask** (batched, step 4) before creating a person note |
| a record of a conversation | `vault.py new meeting "<Title>" --date YYYY-MM-DD`; fill `people:` |
| a choice with options | `vault.py new decision "<Title>"`; fill `## Context` and `## Options` |
| their own thinking, worth keeping | `ingest` as a `note` source, then compile |
| a passing thought | append to today's daily note under `## Log` |
| genuinely unclear | leave it; list it under "Unresolved" |

**Preserve their wording.** Paste what they wrote; add nothing they did not write. Keep the original
capture date as the bullet date, not today's.

## Step 3 — Delete the inbox file

Only after the destination write has succeeded **and** `python3 scripts/lint_frontmatter.py <target>`
passes. Never delete before the target exists. Git history keeps it either way.

## Step 4 — Ask once, at the end

Collect everything ambiguous and ask **one** batched question covering all of it. One prompt per item
turns a five-minute triage into an interrogation. Apply the answers, then repeat step 3 for those.
Anything still unresolved stays in `inbox/`.

## Step 5 — Report

```
Processed N items: a → projects, b → people, c → meetings, d → daily, e → ingested, f → decisions.
Unresolved: g (listed).
Created: <paths>.  Appended: <paths>.
```

Then `python3 scripts/vault.py check` and fix anything it reports.
