# Routing: where does this go?

Deterministic rules for placing information. Apply them **top-down; the first match wins.** Humans
can use the same tree without reading anything else — that is the point of putting sources first and
keeping every branch a yes/no question about the thing in front of you.

## 1. The decision tree

```
Is it third-party content — a URL, article, video, paper, repo, book, or pasted text?
  → SOURCE. Run the ingestion pipeline (docs/ingestion.md). Lands in raw/, compiles into wiki/.
    Never hand-write a raw/ file.

Is it an outcome with a defined end state — ship X, learn Y by Z, decide W?
  → PROJECT (projects/). Not started yet → status: idea.

Is it a standing responsibility with no end date — health, the house, the vault itself?
  → AREA (areas/). Areas are few (under ~10). A new one needs a reason.

Is it about a specific person you actually interact with?
  → PERSON (people/). Someone you only read about is a wiki entity instead.
    If both, the person note carries entity: "[[Their Wiki Page]]".

Is it a record of a conversation?
  → MEETING (meetings/). Link people and projects in frontmatter.

Is it a choice with options and consequences?
  → DECISION (outputs/decisions/).

Is it a single action under a day of work?
  → an inline `- [ ]` task in the project or area that owns it, or in today's daily note if it
    belongs to nothing. Tasks never get their own note.

Is it a reusable insight, model, technique, or entity summary derived from sources?
  → WIKI page. Update an existing page before creating a new one.

Is it an answer to a question, or an analysis?
  → OUTPUT (outputs/answers/). Promote the lasting parts into wiki/ afterwards.

Is it a passing thought or observation with no other home?
  → today's DAILY note, under `## Log`.

Still unclear?
  → it stays in INBOX until the weekly review. Never invent a new folder or type.
```

**Capture is not classification.** Anything caught in a hurry goes to `inbox/` untouched.
Classification happens later, in one batch. The inbox is a queue, not a home; its steady state is
empty.

### The two calls people get wrong

**Project or area?** Ask whether you could ever mark it done. "Get fit" is an area. "Run a half
marathon in November" is a project. If you cannot write the `question:` field in one sentence, it is
not a project yet.

**Wiki page or project note?** The wiki holds what is true regardless of what you are doing about
it. The project holds what you are doing. The same fact can be cited by many projects; put it in the
wiki and link it.

## 2. Naming

| Kind | Pattern | Example |
|---|---|---|
| source, meeting, decision, answer | `YYYY-MM-DD Title.md` | `2026-08-24 Running Club Intro.md` |
| weekly review | `YYYY-Www.md` | `2026-W35.md` |
| daily note | `daily/YYYY/MM/YYYY-MM-DD.md` | `daily/2026/09/2026-09-01.md` |
| capture | `YYYY-MM-DD HHmm Title.md` | `2026-09-04 0812 Zone 2 training.md` |
| project, area, person, wiki page | `Title.md`, Title Case, no date | `Progressive Overload.md` |
| agent run log | `YYYY-MM-DD-<run_type>.md` | `2026-09-01-ingest.md` |
| generated file | leading `_`, or a `<!-- GENERATED -->` marker | `_index.md`, `Home.md` |

Filenames never contain `/ \ |` — those break links, and `vault.py check` errors on them. They also
avoid `# ^ [ ] : * ? " < >`, which are legal on macOS but unreliable inside `[[links]]` or illegal
elsewhere; `check` warns and `doctor` lists them.

When a title genuinely needs one of those characters, **the filename drops it and the note declares
the pretty form in `aliases:`**, so `[[60/40 Portfolio]]` still resolves:

```
title:   "60/40 Portfolio: Issue #7"      # what you read
file:    60-40 Portfolio Issue 7.md       # what is on disk
aliases: ["60/40 Portfolio: Issue #7"]    # what makes links work
```

`vault.py new` and `vault.py rename` both do this automatically.

Two notes must never share a filename, anywhere in the vault: links resolve by basename, so
`[[Notes]]` in two folders is ambiguous and Obsidian silently picks one. `vault.py check` warns.

## 3. Lifecycles

**Project** — `idea → active → paused → done → archived`

- `idea` — captured, not started. Reviewed weekly; activate or delete within ~90 days.
- `active` — has at least one open task or a stated next step. Untouched for 30 days and
  `vault.py status` flags it.
- `paused` — deliberately on hold. Write the unblock condition under `## Status`, or it is not
  paused, it is abandoned.
- `done` — outcome delivered. Write `## Outcome` before moving on: what shipped or was learned, and
  what you would do differently.
- `archived` — moved to `projects/archive/`. Links from other notes stay; **archiving is not
  deletion**, and the `projects:` links on sources and wiki pages keep resolving.

**Area** — `active ↔ dormant`. Areas are never archived, only marked dormant. A responsibility you
have stopped meeting has not ended; it has been dropped, and the note should say so.

**Decision** — `pending → decided → superseded`. `outcome` starts `unknown` and is filled in at a
later review (default 14 days, or set `review_on:`). The prediction written at decision time is what
makes that review honest — without it, hindsight always says you were right.

**Wiki page** — created by compilation → updated in place by later sources (`updated` bumps,
`sources` grows) → optionally stamped `last_corroborated` when re-confirmed. Pages are merged only
by an explicit, proposed consolidation. Conflicting claims are preserved under `## Disagreements`.

**Source** — written once, never edited. Deleting one requires human intent.

**Inbox item** — created → routed → deleted from `inbox/`. Git history keeps it.

## 4. Linking

- Projects, areas, people, meetings, and decisions link to their neighbours through **frontmatter**
  (`projects:`, `areas:`, `people:`), which views and scripts can query — plus inline `[[wikilinks]]`
  in prose where the relationship deserves an explanation.
- Wiki pages link back to sources only through `sources:`. Wiki-to-wiki links live in the body.
- Links resolve by **basename, never by path**. `[[Progressive Overload]]`, never
  `[[wiki/concepts/Progressive Overload]]`. This is what makes moving files safe.
- A new note should pick up at least one inbound link within a week. `vault.py doctor` lists orphans.
- **Never duplicate a note to make it appear in a second context.** Link it, or add it to a view.

## 5. What agents may create without asking

Files under `raw/`, `wiki/`, `logs/`, and `outputs/` in the course of a pipeline or an answer; and
today's daily note if missing. A project, area, person, or meeting note **only** when you asked for
one or inbox processing routed an item there. Agents never invent areas or people out of source
material.

## 6. What agents never do without asking

Bulk moves, renames, or deletes. New folders, note types, or enum values — those live in
`config/lifeos.toml`, which the write guard makes unwritable, so the proposal goes in the run log
instead. Resolving a `## Disagreements` section, merging wiki pages, or editing a source body.
