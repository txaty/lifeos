# Metadata schema

<!-- GENERATED from config/lifeos.toml by `python3 scripts/vault.py docs` — edit the config, not this file -->

The contract every note in this vault keeps. `scripts/lint_frontmatter.py` enforces
it on every write (PostToolUse hook), every commit (pre-commit hook), and in CI
(`vault.py check`). Both this file and the linter are generated from — or read —
`config/lifeos.toml`, so they cannot disagree.

**To change the schema, edit `config/lifeos.toml`, then run:**

```
python3 scripts/vault.py docs && python3 scripts/vault.py check
```

## How to read this

- Enum fields hold **exactly one** value. The `a | b | c` notation lists what is
  allowed; never write the `|` into a note.
- `tags:` is a list of bare lowercase-kebab names. Never a `#` prefix.
- **Date quoting is not cosmetic.** Obsidian and YAML treat these differently:
  - `created`, `last_corroborated`, `updated` are **quoted strings**: `created: "2026-01-31"` (bookkeeping stamps)
  - `date`, `due`, `review_on` are **unquoted YAML dates**: `date: 2026-01-31` (real-world dates)
- Link fields are lists of quoted wikilinks: `- "[[Some Note]]"`. Links resolve by
  **basename**, never by path, so moving a note never breaks a link.
  Link fields: `areas`, `entity`, `people`, `projects`, `related`, `sources`, `sources_consulted`
- `aliases:` is optional on every type (Obsidian reserved).
- Fields not listed for a type are flagged as MINOR — harmless, usually a typo.

## Type registry

`type` in the frontmatter and the folder on disk must agree. That single invariant
is what lets every script know what a file is without reading it.

| `type` | Folder | Filename | Lifecycle | What it is |
|---|---|---|---|---|
| `area` | `areas/` | `Title.md` | active → dormant | A standing responsibility with no end date. Keep under ~10. |
| `daily` | `daily/` | `daily/YYYY/MM/YYYY-MM-DD.md` | — | One day of tasks, log lines, and links. A scratchpad, not a task system. |
| `inbox` | `inbox/` | `YYYY-MM-DD HHmm Title.md` | — | Unprocessed capture. Steady state: empty. |
| `log` | `logs/` | `YYYY-MM-DD-<run_type>.md` | — | One agent run. Append-only audit trail. |
| `meeting` | `meetings/` | `YYYY-MM-DD Title.md` | — | A record of one conversation. |
| `output` | `outputs/` | `YYYY-MM-DD Title.md` | — | Something you or an agent produced: an answer, a decision, a review. |
| `person` | `people/` | `Title.md` | — | Someone you actually interact with. People you only read about are wiki entities. |
| `project` | `projects/` | `Title.md` | idea → active → paused → done → archived | An outcome with a defined end state. |
| `source` | `raw/` | `YYYY-MM-DD Title.md` | — | Third-party content, captured verbatim. Append-only. |
| `wiki` | `wiki/` | `Title.md` | — | Compiled knowledge. Upserted, never duplicated, always cited. |

Files starting with `_` are registries or generated indexes and are exempt from the
frontmatter requirement.

## Controlled vocabularies

### `domain` — the one axis automation groups by

Every project, area, and wiki page picks **exactly one**. If a note spans two,
pick the primary and let `tags` carry the rest.

- `career`
- `engineering`
- `finance`
- `health`
- `learning`
- `personal`
- `projects`
- `world`

`meta` is reserved for generated index files.

### `tags` — everything else

Free-form, lowercase-kebab, no `#`. Tags are for discovery; `domain` is what
automation relies on. Suggested starting points: `mental-model`, `technique`, `strategy`, `reference`, `question`, `idea`.

### `output_type`

| Value | Folder | What it is |
|---|---|---|
| `answer` | `outputs/answers/` | A researched answer with citations. |
| `decision` | `outputs/decisions/` | A choice with options and consequences, reviewed later. |
| `review` | `outputs/reviews/` | A periodic review scaffolded from vault facts. |

### `source_type`

| Value | Folder | What it is |
|---|---|---|
| `article` | `raw/articles/` | Any public web page worth keeping. |
| `book` | `raw/books/` | Notes and excerpts from a book. |
| `note` | `raw/notes/` | Pasted text, a conversation excerpt, or your own written-up thinking. |
| `paper` | `raw/papers/` | An academic or technical paper. |
| `repo` | `raw/repos/` | A codebase worth understanding. |
| `video` | `raw/videos/` | A talk or video, captured as a transcript summary. |

## Per-type frontmatter

### `area` — `areas/`

A standing responsibility with no end date. Keep under ~10.

```yaml
type: <the type name below>
title: "..."
status: active    # one of: active | dormant
created: "YYYY-MM-DD"    # quoted
updated: "YYYY-MM-DD"    # quoted
domain: career    # exactly one of: career | engineering | finance | health | learning | personal | projects | world
tags: []    # lowercase-kebab, no '#'

# optional
# aliases: ...
# related: []    # list of "[[wikilinks]]"
```

### `daily` — `daily/`

One day of tasks, log lines, and links. A scratchpad, not a task system.

```yaml
type: <the type name below>
date: YYYY-MM-DD    # unquoted
tags: []    # lowercase-kebab, no '#'

# optional
# aliases: ...
```

### `inbox` — `inbox/`

Unprocessed capture. Steady state: empty.

Frontmatter is **optional** here: a capture from a phone is plain text and
still valid. If present, it must validate.

```yaml
type: <the type name below>

# optional
# date: YYYY-MM-DD    # unquoted
# tags: []    # lowercase-kebab, no '#'
# source_url: ...
```

### `log` — `logs/`

One agent run. Append-only audit trail.

**Immutable.** Bodies are written once and never edited afterwards.

```yaml
type: <the type name below>
date: YYYY-MM-DD    # unquoted
run_type: ingest    # one of: ingest | tidy | reflect | review | other
tags: []    # lowercase-kebab, no '#'
```

### `meeting` — `meetings/`

A record of one conversation.

```yaml
type: <the type name below>
title: "..."
date: YYYY-MM-DD    # unquoted
people: []    # list of "[[wikilinks]]"
tags: []    # lowercase-kebab, no '#'

# optional
# projects: []    # list of "[[wikilinks]]"
# areas: []    # list of "[[wikilinks]]"
# aliases: ...
```

### `output` — `outputs/`

Something you or an agent produced: an answer, a decision, a review.

```yaml
type: <the type name below>
output_type: answer    # one of: answer | decision | review
title: "..."
date: YYYY-MM-DD    # unquoted
tags: []    # lowercase-kebab, no '#'

# optional
# projects: []    # list of "[[wikilinks]]"
# areas: []    # list of "[[wikilinks]]"
# people: []    # list of "[[wikilinks]]"
# aliases: ...
```

`output_type` names the variant, and the linter checks that the
value and the folder agree. Create one with `vault.py new <variant> "Title"`:

- **`answer`** → `outputs/answers/` — A researched answer with citations. _(adds `query`, `sources_consulted`)_
- **`decision`** → `outputs/decisions/` — A choice with options and consequences, reviewed later. _(adds `status`, `outcome`; may add `stakes`, `review_on`; `status`: pending | decided | superseded; `outcome`: unknown | good | bad | mixed; `stakes`: low | medium | high)_
- **`review`** → `outputs/reviews/` — A periodic review scaffolded from vault facts. _(may add `period`; named `YYYY-Www.md`)_

### `person` — `people/`

Someone you actually interact with. People you only read about are wiki entities.

```yaml
type: <the type name below>
title: "..."
created: "YYYY-MM-DD"    # quoted
updated: "YYYY-MM-DD"    # quoted
tags: []    # lowercase-kebab, no '#'

# optional
# relation: colleague    # one of: colleague | friend | family | mentor | contact
# org: "..."
# entity: "[[Wiki Page]]"
# projects: []    # list of "[[wikilinks]]"
# areas: []    # list of "[[wikilinks]]"
# aliases: ...
```

### `project` — `projects/`

An outcome with a defined end state.

```yaml
type: <the type name below>
title: "..."
status: idea    # one of: idea | active | paused | done | archived
created: "YYYY-MM-DD"    # quoted
updated: "YYYY-MM-DD"    # quoted
domain: career    # exactly one of: career | engineering | finance | health | learning | personal | projects | world
question: "..."
tags: []    # lowercase-kebab, no '#'

# optional
# kind: research    # one of: research | build | learning | life
# areas: []    # list of "[[wikilinks]]"
# due: YYYY-MM-DD    # unquoted
# aliases: ...
# people: []    # list of "[[wikilinks]]"
```

`status: archived` if and only if the file lives in `projects/archive/`. The linter enforces both directions.

### `source` — `raw/`

Third-party content, captured verbatim. Append-only.

**Immutable.** Bodies are written once and never edited afterwards.

```yaml
type: <the type name below>
source_type: article    # one of: article | book | note | paper | repo | video
title: "..."
author: "..."
date: YYYY-MM-DD    # unquoted
tags: []    # lowercase-kebab, no '#'

# optional
# url: "..."
# publisher: "..."
# projects: []    # list of "[[wikilinks]]"
# aliases: ...
```

`source_type` names the variant, and the linter checks that the
value and the folder agree. Create one with `vault.py new <variant> "Title"`:

- **`article`** → `raw/articles/` — Any public web page worth keeping. _(adds `url`)_
- **`book`** → `raw/books/` — Notes and excerpts from a book.
- **`note`** → `raw/notes/` — Pasted text, a conversation excerpt, or your own written-up thinking.
- **`paper`** → `raw/papers/` — An academic or technical paper. _(adds `url`, `publisher`)_
- **`repo`** → `raw/repos/` — A codebase worth understanding. _(adds `url`)_
- **`video`** → `raw/videos/` — A talk or video, captured as a transcript summary. _(adds `url`)_

### `wiki` — `wiki/`

Compiled knowledge. Upserted, never duplicated, always cited.

```yaml
type: <the type name below>
title: "..."
created: "YYYY-MM-DD"    # quoted
updated: "YYYY-MM-DD"    # quoted
sources: []    # list of "[[wikilinks]]"
domain: career    # exactly one of: career | engineering | finance | health | learning | personal | projects | world
tags: []    # lowercase-kebab, no '#'

# optional
# projects: []    # list of "[[wikilinks]]"
# aliases: ...
# last_corroborated: "YYYY-MM-DD"    # quoted
# disputed: ...
# related: []    # list of "[[wikilinks]]"
```

Variants share the schema above and differ only by folder and template.
Create one with `vault.py new <variant> "Title"`:

- **`concept`** → `wiki/concepts/` — An idea, model, or definition worth reusing.
- **`connection`** → `wiki/connections/` — A link between two domains that neither page would state alone.
- **`entity`** → `wiki/entities/` — A company, person, product, or protocol you keep encountering.
- **`technique`** → `wiki/techniques/` — Something you could actually do, with steps.

## Field semantics worth knowing

- `updated` is bumped when **content** changes. Sweeps, index regeneration, and
  link rewrites never touch it — otherwise staleness detection becomes noise.
- `sources:` on a wiki page must point at notes under `raw/`. A wiki claim without provenance does not belong.
- `projects:` on a source propagates to wiki pages compiled from it — merged,
  never overwritten.
- Tasks are inline `- [ ]` checkboxes inside the note that owns them. There is no
  task note type and no task database; `vault.py tasks` collects them.

## Thresholds

| Setting | Value | Effect |
|---|---|---|
| `stale_active_days` | 30 | an active project untouched this long is flagged |
| `stale_idea_days` | 90 | an idea this old is flagged activate-or-delete |
| `decision_review_days` | 14 | a decision this old with `outcome: unknown` is flagged |
| `stale_wiki_days` | 365 | a wiki page uncorroborated this long shows in `doctor` |
