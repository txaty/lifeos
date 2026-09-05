# Decisions

Why this system is shaped the way it is, including what was deliberately left out. Read this before
adding something back — most of the obvious additions were considered and rejected for reasons that
have not changed.

This framework was distilled from a working personal vault of ~3,800 notes. Where that vault made a
deliberate choice and recorded the reasoning, the choice is kept and credited. Where its usage data
contradicted its own structure, the structure lost.

---

## Retained

### ADR-001 — Folder and `type` agree, one to one

**Decision.** Every note type maps to exactly one folder, and the linter enforces both directions.

**Why.** It is the invariant everything else rests on. A script knows what a file is from its path
before opening it; a human knows where a note lives from what it is. The alternative — type as pure
metadata with free-form folders — means every consumer has to open and parse every file to know what
it is looking at, and it means two people can file the same thing in two places.

**Cost.** A note that is genuinely two things has to pick one. In practice this is rare and forcing
the choice is usually clarifying.

### ADR-002 — Navigation is separate from storage

**Decision.** Folders answer only "what kind of thing is this". Relationships are frontmatter links
and generated views. Nothing is ever duplicated to appear in a second place.

**Why.** Hierarchies force a single answer to "where does this belong" and are wrong the moment
something belongs in two places. Links do not have that problem. One canonical note plus many views
means there is always exactly one thing to edit.

### ADR-005 — The repository *is* the vault

**Decision.** The vault lives at the repository root, not in a `vault/` subdirectory.

**Why.** Obsidian's core Templates and Daily Notes plugins can only see files inside the vault, so
`templates/` must be in it. Agents operate from the project root, so `AGENTS.md` must be there too.
A `vault/` subdirectory would put the system files outside the thing they configure, and the write
guard, the hooks, and the Obsidian config would all have to reach across that boundary.

**Cost.** Framework updates are a `git remote add upstream` and a cherry-pick rather than a
dependency bump. The compensating design is ADR-003: your changes live in `config/` and `templates/`,
so upstream changes to `scripts/` usually merge cleanly.

**Rejected alternative.** Framework as an installable package with the vault as data. Cleaner
updates, but it splits one git history into two and puts the schema somewhere the user cannot read
while they are using it.

### ADR-006 — Tasks are inline checkboxes, never notes

**Decision.** `- [ ]` lives in the project, area, or daily note that owns it. `vault.py tasks`
collects them. There is no task type and no task database.

**Why.** A task database is a second system to maintain, and it competes with the first: you end up
with tasks that have no project and projects whose tasks live elsewhere. Inline tasks are always in
context, and the context is the part that makes a task actionable months later.

**Cost.** No due dates, priorities, or recurrence. If you need those, you need a task manager — use
one, and let this system hold the thinking rather than the scheduling.

### ADR-007 — Weekly is the only scaffolded review

**Decision.** One cadence. Monthly and quarterly reviews are deliberately not scaffolded.

**Why.** Inherited from the source vault, where it was the only ritual that survived years of use —
which is the strongest evidence available about which cadences a person will actually keep. Every
additional cadence competes with the one that works, and a review nobody runs is worse than no
review, because it makes the system look maintained when it is not.

**If you want quarterly check-ins**, add a `## Quarterly` section to `templates/weekly-review.md`
that you fill in every thirteenth week. That costs one section. A new note type costs a template, a
folder, a routing rule, a lifecycle, and a decision every time you file something.

### ADR-009 — Propose-only maintenance

**Decision.** Automated passes are additive. No bulk moves, renames, deletes, merges, or schema
migrations without an explicit request and a dry-run report.

**Why.** It bounds the blast radius of a mistaken or compromised run to "wrote a suggestion in a
file", which is what makes it safe to leave an agent running unattended. It is a security control as
much as a data-integrity one.

### ADR-010 — Untrusted content is data, and the guard is deterministic

**Decision.** Layered defence: write confinement in a PreToolUse hook, instruction files unwritable
at every depth, nonce-fenced content, and one audited egress script.

**Why.** This vault reads untrusted content with an agent that writes files — the lethal trifecta, as
normal operating mode rather than an edge case. An instruction telling a model to be careful is the
weakest available control and the one most easily argued away by the content it is reading. See
[`security.md`](security.md).

---

## Generalized

### ADR-003 — One config file, and the schema document generated from it

**Decision.** `config/lifeos.toml` is the single source of truth for folders, types, required fields,
enums, vocabularies, and thresholds. The linter reads it; `docs/schema.md` is generated from it.

**Why.** This was the single biggest problem in the source vault: its ten `domain` values, its folder
names, its tag list, and its source types were hardcoded in three places at once — the schema
document, the linter, and the scripts. Changing one meant finding the other two. That is fine for the
one person who wrote it and impossible for anyone else.

Making the schema *data* means adding a note type is a config edit — verified: the worked example in
[`customization.md`](customization.md) adds a complete type with a template and no code change at
all.

**Cost, stated plainly.** `docs/schema.md` cannot carry hand-written prose about individual fields,
because it is overwritten. Rationale lives in two places instead: comments in `config/lifeos.toml`,
next to the values they explain, and [`architecture.md`](architecture.md) for the shape. This is the
right trade — a doc that disagrees with the linter is worse than a doc with less prose in it.

**Rejected alternative.** Generate the *linter* from the config as code. Rejected: a generated linter
is harder to debug than a generic one that reads config at runtime, and there is no gain.

### ADR-004 — TOML, and Python 3.11 as the floor

**Decision.** Config is TOML, read with stdlib `tomllib`. Python 3.11+ is required.

**Why.** TOML is designed for configuration, supports comments (which carry the rationale), and has
an unambiguous parser in the standard library since 3.11. That gives zero dependencies for the whole
framework.

**Cost.** macOS system Python is 3.9, so some users need `brew install python`. Every entry point
detects this and prints exactly that instruction.

**Rejected alternative.** A hand-rolled TOML-subset fallback for 3.9/3.10. It would have removed the
bootstrap friction, but two parsers that can disagree about the same file is a genuinely nasty bug
class, and the config is the thing everything else trusts. One parser, no ambiguity.

**Rejected alternative.** YAML, to match frontmatter. Nested YAML needs either a dependency or a
hand-rolled parser — the same problem, plus YAML's own ambiguities.

### ADR-012 — Variants, instead of three special cases

**Decision.** `[types.X.variants.Y]` is one mechanism covering source types, output types, and wiki
page kinds.

**Why.** The first draft of this config had three parallel tables — `[sources.*]`, `[outputs.*]`, and
a `subfolders` list for wiki — with three code paths in the loader, the linter, and the CLI. They
were the same idea three times: *a narrower kind of note, in its own subfolder, that may add
required fields.* Collapsing them removed two code paths and made "add a source type" and "add an
output type" the same operation to learn.

A variant may or may not write its name into a frontmatter field (`variant_field`). Sources and
outputs do (`source_type`, `output_type`); wiki kinds do not, because the folder already says it and
a field that only restates the path is a field that can contradict it.

### ADR-013 — Ingestion is an interface with one reference implementation

**Decision.** Source types are config. The framework ships one generic URL/text pipeline. Platform
pipelines are skills you add when you have that platform.

**Why.** The source vault had nine source types and seven pipelines. Three types held **zero** notes;
one held 97% of everything. Shipping nine would be shipping someone else's inbox: a pipeline built
around one particular platform's quirks is not architecture, it is one person's reading habits
hardened into folders.

The generalizable part is the *interface*: dedup before fetching, gate the fetch, fence the content,
apply a quality threshold, compile with citations. That is in [`ingestion.md`](ingestion.md) and
applies to any source.

### ADR-014 — The wiki router is split by domain from day one

**Decision.** `wiki/_index.md` is a small dispatcher; `wiki/domains/<domain>.md` holds per-page hooks.

**Why.** The source vault's single flat router had grown to 212 KB — too large for an agent to read
and too central to restructure casually. It documented this as a migration to do "later". Doing it
up front costs nothing at ten pages and removes a future migration entirely. Inheriting the foresight
rather than the debt.

### ADR-015 — Retrieval is core and stdlib

**Decision.** BM25 plus one backlink hop, in the standard library. Dense embeddings optional and
strictly additive.

**Why.** "What do I already know about X" is the question a second brain exists to answer; if that
needs an install step, it does not get asked on day one. The backlink hop is what a graph gives you
over a search box: the note you want often does not contain your words, but its neighbour does.

---

## Removed

### ADR-008 — No prompt library type

**Removed.** The source had a `prompt` type with four subfolders, semantic versioning, and a
refinement-log mechanism with `parent:` links. It held **twelve notes**, two subfolders were empty,
and one note type existed to version another.

**Why.** Twelve notes across four folders with semver is a system built for a scale that never
arrived. A prompt worth keeping is a wiki technique page; a prompt under active development is a
project. Removing it also frees the name `prompts/`.

**If you want it back**, [`customization.md`](customization.md) shows exactly how, in config alone.
That is the test of whether this was the right kind of removal.

### ADR-016 — Outputs collapsed from four folders to three

**Removed.** `outputs/analyses/` merged into `outputs/answers/`.

**Why.** The source split outputs four ways to hold **six files**, two of the folders empty. An
"analysis" is an answer with more work in it; the distinction cost a folder, a template, and a
routing decision, and bought nothing. `decisions/` and `reviews/` stay because they have genuinely
different lifecycles — a decision has a pending→decided→superseded arc and a scheduled outcome
review; a review is named by ISO week.

### ADR-017 — No `canvas/`, and `attachments/` stays but is not a concept

**Removed.** The `canvas/` folder (one file in the source) is gone; the Canvas core plugin is off.
`attachments/` remains because Obsidian needs somewhere to put pasted images, but it is not a note
type and nothing indexes it.

**Why.** A folder holding one file is not a structure, and a JSON canvas format is a dependency on a
feature that may not survive. Turn Canvas on if you want it; nothing here depends on it either way.

### ADR-018 — No platform-specific rules in the core

**Removed.** Platform-specific ingestion pipelines, a scheduled mail-ingest job, a bot-wall
fallback chain, a transparent-proxy auto-detector, and a hardcoded single-language assumption.

**Why.** Each was a correct solution to a specific person's specific circumstances. The *general*
versions were kept: language is `primary_language` in config with a documented
original-plus-translation rule; the proxy exception is an explicit opt-in with a hint printed at the
moment it is needed, rather than a heuristic that decides for you when to relax a security control.

---

## Rejected, and staying rejected

These were considered and turned down. The reasons are here so the question does not have to be
re-litigated every year.

### PARA's "resources"

**Rejected.** `raw/` (what you read, immutable, cited) plus `wiki/` (what you concluded, compiled,
upserted) is a more useful split than one undifferentiated Resources pile. The distinction between
*source* and *synthesis* is the one that matters, and PARA does not make it.

Projects-versus-areas is kept, and is the only part of PARA that earns its place: a thing that can be
finished behaves differently from a thing that cannot.

### Johnny.Decimal numbering

**Rejected.** Reserved numeric blocks assume growth is evenly distributed across categories. Real
vaults grow overwhelmingly in one or two places — in the source vault, 97% of sources were one type.
Numbers also force you to know the taxonomy before you have the notes, and they make every link
unreadable.

### Zettelkasten IDs

**Rejected.** `202608241432` filenames are stable and unambiguous, which is the entire argument for
them. But they make every link unreadable to a human, and titles have proven stable enough in
practice. Where a title genuinely must change, `vault.py rename` rewrites the links and keeps the old
name as an alias, which solves the actual problem IDs were solving.

### Dataview

**Rejected.** It is more powerful than Bases. It is also a community plugin, which means the vault
stops working on a device where it is not installed, and it puts a query language between you and
your notes. Bases is core, works on mobile with no install, and is enough. Zero community plugins is
a property worth defending: every plugin is a bet that something else will still exist in five years.

### A separate task database

**Rejected.** See ADR-006.

### Monthly and quarterly review notes

**Rejected.** See ADR-007.

---

## How to add to this file

If you change something structural, add an entry. Say what you decided, why, and what it costs —
the cost is the part future-you will want, because it is what tells you whether the trade still
holds. A decision with no stated cost is usually a decision that was not actually made.
