---
name: archive-project
description: Close a project out properly — verify the outcome is written, set status archived, move it to projects/archive/, regenerate indexes, and confirm links still resolve. Use when the user says "archive project X", "close out X", or accepts an archive proposal from the weekly review.
---

# Archive a project

**Inputs:** a project title.
**Outputs:** the note under `projects/archive/` with `status: archived`; regenerated indexes.
**May modify:** that project file, and the generated indexes. Nothing else.

## Steps

1. Open `projects/<Title>.md`. If `status` is not `done`, ask whether to archive anyway. Archiving
   something still in flight is usually a decision to abandon it, and it should be made on purpose.

2. **If `## Outcome` is empty, get it filled in before anything else.** Ask for two or three
   sentences: what shipped or was learned, and what would be done differently. Write their words
   verbatim.

   **Never invent an outcome.** A project archived without one is a project you cannot learn from,
   and the outcome is the only part that compounds.

   An abandoned project still deserves one — "stopped after three weeks because the premise was
   wrong" is among the more valuable things the vault can hold.

3. If the outcome names durable knowledge, offer to compile it into `wiki/` via `ingest` (an outcome
   writeup is a legitimate `note` source). Optional; skip on "no".

4. Move it and update the status:

   ```
   git mv "projects/<Title>.md" "projects/archive/<Title>.md"
   ```

   Then set `status: archived` and bump `updated`. Attached notes keep their `projects:` links —
   links resolve by basename, so nothing else changes. The linter enforces that
   `status: archived` and the archive folder imply each other, so getting one without the other
   fails immediately.

5. ```
   python3 scripts/vault.py index && python3 scripts/vault.py check
   ```

   Both must pass.

6. Report: the new path, whether an outcome was recorded, and whether anything was promoted to the
   wiki.

## Failure

If `check` fails, fix it. If you cannot, move the file back and report — a half-archived project is
worse than an unarchived one.

**Never delete the project or its attached notes.** Archiving is not deletion; that is the whole
point of having a separate state for it.
