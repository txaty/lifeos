# Workflows

The recurring loops. Each names its inputs, its outputs, the files it may touch, and how it fails.
Mechanics live in `scripts/vault.py`; judgment lives in the skills under `.claude/skills/`.

## Daily

### Capture — any time, any device

Capture is fast and dumb by design. Classification happens later, in one batch, when you have
context for all of it at once.

- **In Obsidian:** `⌘N` (or the mobile `+`) lands in `inbox/` — that is what `newFileLocation` is
  set to. Type and move on. No frontmatter needed.
- **Terminal:** `python3 scripts/vault.py new inbox "the thing"`
- **Agent:** `capture` skill.
- **Web clipper:** point it at `inbox/`; the URL gets routed to a pipeline at processing time.

The one rule: if you already know where it belongs, don't capture — put it there. Capture is for
when deciding would cost more than the thought is worth right now.

### Daily note

`daily/YYYY/MM/YYYY-MM-DD.md`, from `templates/daily.md`. Three sections: `## Tasks`, `## Log`,
`## Links`.

It is a scratchpad and a journal, not a task system. A task that outlives the day belongs to its
project or area — move it there rather than copying it forward, or you will maintain two copies of
your own intentions.

## Weekly

### Process the inbox

For each file, oldest first:

1. **Classify** with the tree in `docs/routing.md`. First match wins.
2. **Act** — create or append the target note. Use `vault.py new` so paths and frontmatter are right.
3. **Delete the inbox file**, but only after the destination write succeeds and lints. Git keeps it.
4. **Batch the ambiguous ones.** One question at the end covering everything unclear, never one
   prompt per item. Anything still unresolved stays in `inbox/` and gets named in the summary.

*May modify:* `inbox/ daily/ projects/ areas/ people/ meetings/ outputs/` and whatever an invoked
pipeline owns. *Never* writes `wiki/` directly — that is compilation's job.

### Weekly review

The only scaffolded cadence, and deliberately so (`docs/decisions.md`, ADR-011). Purpose: keep
projects honest, empty the queue, notice what the vault learned.

1. **Empty the inbox first.** Reviewing around a full inbox reviews the wrong things.
2. **Gather facts before opinions:** `python3 scripts/vault.py status` and `vault.py tasks`. Facts
   first is the whole trick — it makes the review argue with data rather than with mood.
3. **Scaffold** `outputs/reviews/YYYY-Www.md` from the template, with those facts filled in.
4. **Propose, do not apply.** One line per project the facts argue about, each carrying its evidence:

   ```
   - [[Some Project]] active → paused (untouched 45d, no open tasks, no stated blocker)
   - [[Other Project]] done → archived (run archive-project)
   - [[Old Idea]] idea → activate or delete (97 days old)
   ```

   Accept or strike each line. Nothing is applied until you do.
5. **Write three lines** yourself: what went well, what got in the way, next week's one priority.
   The scaffold cannot do this part and should not try.
6. **Close:** `vault.py index && vault.py check`.

## Projects

**Start.** `vault.py new project "Title"` — or the `project-init` skill, which additionally searches
what you already know and attaches it, so you start from your own prior work rather than from blank.

Every project needs `question:` — the one sentence it answers or the outcome it delivers. If you
cannot write it, you have an idea or an area, not a project.

**Work.** Append dated bullets under `## Log`. Keep tasks as checkboxes under `## Tasks`. Bump
`updated` when content changes — and *only* then, because that field is what staleness detection
reads. Decisions made along the way get their own note in `outputs/decisions/`, linked with
`projects:`.

**Resume after months.** Read in this order: `## Status`, then `## Log`, then the attached decisions,
then the linked notes in the embedded Base view. That is enough to continue without re-deriving
anything — which is the actual test of whether the project note was maintained.

**Finish.** Set `status: done`, write `## Outcome` (what shipped or was learned; what you would do
differently). Promote durable knowledge into `wiki/`. Then `archive-project` moves the file to
`projects/archive/`, sets `status: archived`, and regenerates the indexes. Attached notes keep their
links.

An abandoned project still deserves an outcome. "Stopped after three weeks because the premise was
wrong" is one of the more valuable things the vault can hold.

## Knowledge

```
source → extracted insight → synthesis → decision, action, or reusable knowledge
```

1. Sources are ingested into `raw/` and compiled into `wiki/` (`docs/ingestion.md`).
2. A project collects the relevant notes through `projects:` links and records synthesis under
   `## Findings`.
3. Questions get answered into `outputs/answers/`; the lasting parts become wiki pages.

**Avoid the graveyard.** A source that never reaches a wiki page or a project is a digest, not
knowledge. `vault.py doctor` reports what share of your sources are cited by at least one page, so
the trend stays visible rather than becoming a vague feeling that you save too much.

## Asking the vault

- **"What do I already know about X?"** — `python3 scripts/retrieve.py "X"`, read the top results,
  answer with citations. File a lasting answer in `outputs/answers/`. Do this *before* searching the
  web; the point of the system is that it sometimes already knows.
- **"What needs my attention?"** — `vault.py status`, or `bases/attention.base` in Obsidian. Both
  read the same frontmatter, so they cannot disagree.
- **"Everything about this person"** — open `people/<Name>.md`; the backlinks pane and the embedded
  view list every meeting, project, and decision that mentions them.
- **"Why did I decide that?"** — `outputs/decisions/`. `## Context` and `## Options` are the record,
  and `## Expected outcome` is what makes the later review honest.

## Maintenance

| Loop | When | What it writes |
|---|---|---|
| Ingest | when you have something to file | `raw/`, `wiki/`, `logs/` |
| Weekly review | weekly | `outputs/reviews/`, accepted status changes |
| Tidy | occasionally | fixes since the last run, `logs/*-tidy.md` — **propose-only** |
| Check | every commit, and in CI | nothing; an exit code |
| Index | after any structural change | `Home.md`, `projects/_index.md`, `wiki/` routers |

Maintenance is additive and propose-only. A tidy pass may fix an unambiguous mechanical error; it
may never perform bulk moves, renames, deletes, merges, or schema migrations without an explicit
request and a dry-run report. This is the rule that makes it safe to leave an agent running
unattended.

## When things fail

- A skill that hits a linter error fixes it before reporting. If it cannot, it says so and leaves the
  file for review rather than deleting it.
- Scripts never partially rewrite a file: they write to a temp path and rename, so a crash leaves the
  previous version intact.
- If `vault.py check` fails in CI, the fix is a commit, not a config change.
- If the write guard blocks you, that is the system working. Ask, don't route around it.
