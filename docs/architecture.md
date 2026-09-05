# Architecture

## One sentence

A vault of plain Markdown where a human captures and decides, agents ingest and compile, and a
handful of stdlib Python scripts hold the invariants so neither party has to remember them.

## The shape

```
 capture ──► inbox/ ──► (route) ──► daily/ · projects/ · areas/ · people/ · meetings/ · outputs/
                                              │
 sources ──► raw/ ──► compile ──────► wiki/ ◄─┘   (linked by projects:, outputs filed back)
                                        │
 generated views: Home.md · projects/_index.md · wiki/_index.md · wiki/domains/* · bases/*.base
 audit trail:     logs/ · git history
```

| Layer | Folders | Who writes | Mutability |
|---|---|---|---|
| Capture | `inbox/` | human, any device | transient; emptied by processing |
| Life and work | `daily/ areas/ projects/ people/ meetings/` | human; agents on request | edited in place |
| Sources | `raw/` | ingestion only | append-only |
| Knowledge | `wiki/` | agents | upserted; conflicts preserved |
| Outputs | `outputs/` | agents + human | filed back into `wiki/` when durable |
| Audit | `logs/` | agents | append-only, one file per run |
| Generated | `Home.md`, `*/_index.md`, `wiki/domains/` | scripts | regenerated, never hand-edited |
| System | `config/ docs/ scripts/ templates/ bases/` | human only | protected by the write guard |

## Five ideas hold it together

### 1. Folder and `type` agree, always

`config/lifeos.toml` maps each note type to exactly one folder, and the linter enforces both
directions. That one invariant is why nothing else has to guess: a script knows what a file is from
its path, before opening it, and a human knows where a note lives from what it is.

### 2. Navigation is separate from storage

Folders answer only "what kind of thing is this". Everything else is links and frontmatter:

- **`domain`** — one controlled value per note. This is the axis every script and view groups by.
  Exactly one, because a filing axis that permits two values is not an axis.
- **`projects:` / `areas:` / `people:`** — YAML lists of wikilinks. A project note and a person page
  are thin views over these links, not containers.
- **Bases** (`bases/*.base`) — live tables over that frontmatter, for humans.
- **Retrieval** (`scripts/retrieve.py`) — BM25 plus one backlink hop, for "what do I know about X".

One canonical note, many views. Nothing is ever copied so it can appear in a second place. If you
want a note to show up somewhere else, link it or add it to a view.

### 3. There is a hard determinism boundary

Judgment belongs to the human and the model. Everything mechanical is a script, and no script ever
interprets note content as an instruction.

| Concern | Script |
|---|---|
| The vault's shape | `config/lifeos.toml` → `lifeos_config.py` |
| Frontmatter validation | `lint_frontmatter.py` |
| Structure, links, indexes, status, creation, renaming | `vault.py` |
| Write confinement | `guard_writes.py` (PreToolUse hook) |
| Network access | `fetch_url.py` |
| Search | `retrieve.py` |
| The schema document | `gen_schema_doc.py` |

The line falls where reversibility does. "Is this a project or an area?" is a judgment call a human
should make once. "Is this filename legal, does this link resolve, is this index stale?" has one
right answer, so a script owns it and nobody has to hold it in their head.

### 4. Generated and canonical never mix

Generated files carry a `<!-- GENERATED -->` marker, or a leading `_`, or both. Editing one by hand
is always wrong; the fix is to change the input and re-run `vault.py index`. `vault.py check` fails
when a generated file is stale, so the two cannot silently diverge.

The one sanctioned exception is explicitly delimited: text between `<!-- PROSE:START -->` and
`<!-- PROSE:END -->` in a generated domain page survives regeneration. Anything that needs a human
voice gets a marked slot rather than an informal convention nobody remembers.

### 5. The agent layer is progressive disclosure

Three tiers, loaded only as needed:

1. **`AGENTS.md`** (~120 lines) — map, invariants, commands. Read every session. `CLAUDE.md` imports
   it and adds tool-specific detail, so the framework is not tied to one agent product.
2. **`docs/`** — read the one file the task touches.
3. **`.claude/skills/*/SKILL.md`** — read only when invoked.

The budget matters: an agent answering a question should read `AGENTS.md`, run retrieval, and open
three notes. It should never need the whole vault, and the structure is arranged so it never has to.

## Scale, and what breaks first

Measured on a synthetic vault of **5,073 notes** (3,000 sources, 1,800 knowledge pages, 200
projects) — larger than the vault this framework was distilled from:

| Command | Time |
|---|---|
| `vault.py index` | 0.08s |
| `vault.py status` | 0.27s |
| `vault.py links` | 0.45s |
| `retrieve.py "<query>"` | 0.49s |
| `vault.py check` | 1.2s |
| `vault.py doctor` | 1.2s |

`check` runs on every commit, so it is kept comfortably under the threshold where people start
reaching for `--no-verify`. Retrieval builds its index on demand rather than maintaining a cache,
so there is nothing to invalidate and nothing to rebuild after an edit.

At the same size, `Home.md` is 1.5 KB and `wiki/_index.md` is 1.0 KB, because both are signposts
rather than catalogues. The per-domain router pages absorb the growth instead.

Two things are designed for the size they will become rather than the size they start at:

- **The wiki router is already split per domain.** `wiki/_index.md` is a dispatcher listing domains
  and recent pages; `wiki/domains/<domain>.md` holds the per-page hooks. A single flat router becomes
  unreadable somewhere around two thousand pages, and by then it is load-bearing and awkward to
  change. Splitting up front costs nothing at ten pages.
- **`raw/` is sharded by source type from the start**, and a busy type can be sharded again by year
  without breaking anything: links resolve by basename, never by path, so moving a file is safe.

What genuinely does not scale, and is meant not to: `areas/` (keep under ten — more and none get
attention) and the number of note types. Both are bounded by human attention, not by tooling.

## AI-written content

- `raw/` bodies are verbatim source material. Nothing edits them after ingestion.
- `wiki/` is model synthesis, always with `sources:`. A claim with no provenance does not belong.
  Conflicts stay explicit under `## Disagreements` rather than being averaged away.
- `outputs/` are answers and analyses, with `sources_consulted:`.
- Human-authored notes are edited by agents only on request, and agents append rather than rewrite.
- Nothing fabricates citations, people, dates, or history. A missing fact is written down as missing.

## Why this and not something else

- **Projects versus areas** is borrowed from PARA and is the one distinction that earns its keep:
  a thing that can be finished behaves differently from a thing that cannot. PARA's "resources" is
  replaced by `raw/` (what you read) plus `wiki/` (what you concluded), which is a more useful split
  than one undifferentiated pile.
- **Evergreen notes** for `wiki/`: titled as claims or concepts, updated in place, densely linked.
- **Tasks stay inline** in the note that owns them, collected by `vault.py tasks`. A task database is
  a second system to maintain, and it competes with the first one.
- **Plain files, no plugins.** The vault has to work on a phone, in a text editor, and in ten years.
  Every dependency is a bet that something else will still exist.

`docs/decisions.md` records what was considered and rejected, with reasons. Read it before adding
something back.
