---
name: capture
description: Save a thought, link, or snippet into inbox/ without classifying it. Use when the user says "capture", "note this", "save this for later", "inbox this", or pastes something with no instruction about where it goes. Do not use it for content the user explicitly asked to file somewhere.
---

# Capture

Capture is fast and dumb on purpose. Classification happens later, in `process-inbox`, when there is
context for everything at once.

**Inputs:** free text, a URL, or a pasted snippet.
**Outputs:** one file in `inbox/`.
**May modify:** `inbox/` only.

## Steps

1. **If the user already said where it goes, do not capture.** "Add a task to Project X", "note this
   about Robin" — append to that note directly (`## Tasks` or `## Notes`) and bump its `updated`.
   Capture is for uncertainty, not for everything.

2. Otherwise:

   ```
   python3 scripts/vault.py new inbox "<first line or URL>" --body "<full text>"
   ```

   The script names the file `inbox/YYYY-MM-DD HHmm <first words>.md` and adds minimal frontmatter.

3. **Add nothing of your own.** No tags, no links, no interpretation, no tidying of their wording.
   Anything you add here is something they have to check later.

4. Report the path in one line. Ask nothing.

## Failure

If the filename collides the script appends a suffix; it never overwrites. If `inbox/` is missing,
create it.
