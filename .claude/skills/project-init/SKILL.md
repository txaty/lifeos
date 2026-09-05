---
name: project-init
description: Start a project properly — a sharp question, a scan of what the vault already knows, and the relevant notes attached. Use when the user says "start a project", "new project", or when process-inbox routes an item that is an outcome with an end state.
---

# Start a project

**Inputs:** a project title, and whatever the user said about it.
**Outputs:** one project note with a real `question:`, and existing notes attached to it.
**May modify:** `projects/`, and `projects:` frontmatter on notes being attached.

## Step 1 — Is it actually a project?

A project is an outcome with a defined end state. Before creating anything, check:

- **Can it be finished?** If not, it is an area. "Get fit" is an area; "run a half marathon in
  November" is a project.
- **Can you write the `question:` in one sentence?** What it answers, or what it delivers. If not,
  it is an idea — create it with `status: idea` and let the weekly review force the issue.
- **Does an existing project already cover it?** Check `projects/_index.md`. A second project on the
  same outcome splits attention and neither gets finished.

Ask the user for the question if it is not obvious. **Do not invent one** — a fabricated `question:`
makes the field worthless for every project after it.

## Step 2 — Find what is already known

```
python3 scripts/retrieve.py "<the project's topic>" --k 15
```

This is the part that makes the skill worth invoking. Most projects start with the vault already
holding something relevant — a source read months ago, a decision made in another context, a page
compiled and forgotten. Starting from that beats starting from blank.

## Step 3 — Create it

```
python3 scripts/vault.py new project "<Title>" \
    --set domain=<one domain> --set kind=<research|build|learning|life> \
    --set "question=<one sentence>" --set "areas=<Owning Area>"
```

Fill in:

- `## Status` — where things stand and what happens next.
- `## Scope` — what is in, what is explicitly **out**, and how you will know it is done. The "out"
  list is the one that saves you later.
- `## Tasks` — one genuine first task. Not "plan the project".

## Step 4 — Attach what you found

For each relevant note from step 2, add the project to its `projects:` list (merge, never overwrite).
The embedded Base view in the project note then shows them live — no copying, no duplication.

Do not attach everything that matched. Three relevant notes beat fifteen plausible ones.

## Step 5 — Close

```
python3 scripts/vault.py index && python3 scripts/vault.py check
```

Report: the path, the question as written, and what was attached.
