# LifeOS Distillation Prompt

> Working note: the two filesystem paths this prompt originally carried have been redacted, since
> the resulting repository is public. Everything else is the prompt as written.

---

You are a senior agentic systems engineer, knowledge-systems architect, and Obsidian/LifeOS specialist.

## Objective

A friend is building his own LifeOS and wants to understand the system behind my personal second brain.

Your task is to take my existing Obsidian second-brain repository and **distill its architecture,
workflows, conventions, automation, and operating principles into a clean, reusable LifeOS framework**
that another person can safely bootstrap and adapt.

- **Source vault (read-only reference):**
  `<path to the private source vault>`
- **Target repository (where you build):**
  `<path to this repository>` — an empty git repo on `main` with no commits.

The goal is **not** to clone my vault. The goal is to extract the underlying system while removing all
personal content and installation-specific noise.

The output is intended to be published as a public repository, so treat everything you write as
world-readable.

---

## Core principle

Treat the source vault as a **reference implementation**, not as content to redistribute.

Extract:

* information architecture and the storage/navigation split
* folder layout and note-type registry
* frontmatter schema and controlled vocabularies
* naming and linking conventions
* lifecycle state machines
* templates
* the capture → route → ingest → compile → output → review loops
* project / area / decision / task management patterns
* generated views and indexes (dashboard, per-folder indexes, Bases)
* knowledge retrieval patterns
* agent operating layer and progressive disclosure
* ingestion pipelines and their dedup/registry mechanics
* the prompt-injection and egress security model
* validation scripts, hooks, and CI
* Obsidian configuration stance
* maintenance mechanisms
* design principles, invariants, and rejected alternatives

Do **not** extract my actual life data.

---

## Privacy and sanitization — hard requirement

Assume everything in the vault may contain private information. The distilled framework must contain
**zero personal data from the source vault**.

Never copy or expose: names, contacts, relationships, employers, organizations, locations, addresses,
account or financial information, health information, private projects, personal goals, daily notes,
meeting records, travel or calendar information, credentials, tokens, API keys, secrets, identifiers,
real task content, private URLs, or proprietary documents.

**Highest-risk locations — do not read for content, and never copy from:**

| Path | Why |
|---|---|
| `auth.json` | Live credentials. Gitignored in the source. Never open it. |
| `people/`, `meetings/` | Real people and conversations. |
| `daily/`, `inbox/` | Unfiltered personal life. |
| `projects/`, `projects/archive/`, `areas/` | Real project and responsibility names. |
| `outputs/`, `logs/` | Agent run records containing real project names and questions. |
| `prompts/` | Filenames embed real project names. |
| `Home.md`, `projects/_index.md`, `wiki/_index.md` | Generated indexes that concatenate real titles. |
| `wiki/`, `raw/` | Mostly public-domain knowledge, but the *selection* reveals my interests. Read for schema shape only; copy nothing. |
| `.claude/settings.local.json`, `.claude/memory/` | Machine- and person-specific state. |

The safe reading order is: `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/*.md`, `templates/*.md`,
`scripts/*.py`, `bases/*.base`, `.claude/skills/*/SKILL.md`, `.obsidian/*.json`, `.githooks/`,
`.github/`. Those files are already written as system documentation and carry almost no personal
content. Everything else should be sampled structurally (folder shapes, frontmatter keys, section
headings) rather than read.

Do not merely redact obvious names while preserving recognizable personal context. Extract the
**schema and pattern**.

For example, instead of a real project note path, derive:

```text
projects/<Project Title>.md          # a single MOC note, not a folder tree
```

Instead of copying a real daily note, write a synthetic one:

```text
## Tasks
- [ ] Draft the migration plan

## Log
- Read two papers on retrieval evaluation

## Links
- [[Example Concept Page]]
```

All examples in the distilled framework must be **synthetic and generic**. If you are uncertain
whether something is personal, exclude or generalize it.

---

## Phase 1 — Read the existing system before changing anything

**The source vault is already documented.** Do not treat this as reverse-engineering an undocumented
folder of notes. `AGENTS.md` plus six files in `docs/` are the authoritative description of the
system, and the linter mirrors `docs/schema.md` by design. Read them first; use the vault tree only to
confirm that documentation matches reality and to spot conventions the docs leave implicit.

Start with:

* `AGENTS.md` — map, invariants, commands (tool-neutral, kept under ~150 lines)
* `CLAUDE.md` — imports `AGENTS.md`, adds Claude Code specifics (skills table, hooks, scheduling, style)
* `docs/architecture.md` — layers, navigation-vs-storage, determinism boundary, scale notes, rationale
* `docs/schema.md` — the canonical frontmatter schema and type registry
* `docs/routing.md` — the decision tree, naming, lifecycles, linking rules, agent permissions
* `docs/workflows.md` — capture, inbox processing, projects, research, weekly review, asking the vault
* `docs/ingestion.md` — shared pipeline rules: dedup, fetching, untrusted content, quality, language
* `docs/security.md` — write guard, egress gate, spotlighting, propose-only guardrail

Then determine:

1. Which parts are foundational design versus personal preference versus accumulated clutter.
2. Which documented rules the vault actually follows, and where it has drifted.
3. Which conventions are real but undocumented (infer from `templates/`, `scripts/`, and `bases/`).
4. Which parts are load-bearing for a *different* person, and which exist only because of my
   specific inputs (for example: nine ingestion source types, a Gmail newsletter heartbeat, a
   WeChat pipeline, a translation rule, a prompt library with semver refinements).
5. Which parts should not be carried into a generalized LifeOS at all.

Distinguish carefully between foundational design, useful convention, personal preference, accidental
complexity, technical debt, and obsolete structure. Do not blindly reproduce the current repository.

### Ground truth you should expect to find

Use this as a checklist against the vault, not as a substitute for reading it. If any of it is wrong,
trust the vault and say so.

**Shape.** One flat Obsidian vault that is also a git repo. Roughly 3,800 Markdown files: ~2,850
immutable source notes under `raw/`, ~840 compiled pages under `wiki/`, and a small human layer.
Top-level content folders are lowercase: `inbox/ daily/ projects/ areas/ people/ meetings/ raw/ wiki/
outputs/ prompts/ logs/ attachments/ canvas/`. System folders: `docs/ templates/ scripts/ bases/
.claude/ .githooks/ .github/ .obsidian/`. Note *titles* are Title Case; folders are not.

**It is not PARA.** It borrows PARA's projects-versus-areas distinction and deliberately rejects the
rest. There is no `Resources/` folder — `raw/` (immutable sources) plus `wiki/` (compiled knowledge)
are the resource layer. There is no top-level `Archive/` — only `projects/archive/`, and areas are
never archived, only marked dormant. There is no `Journal/` — `daily/YYYY/MM/YYYY-MM-DD.md` is a
task-and-log scratchpad. There are no goal notes and no task notes: tasks are inline `- [ ]`
checkboxes inside the owning project, area, or daily note, collected by `vault tasks`.

**Twelve note types**, each pinned to a folder by `docs/schema.md`: `inbox daily area project person
meeting source wiki output prompt log manifest`. Folder and `type` must agree.

**The routing tree** in `docs/routing.md` is applied top-down, first match wins, and it starts with
sources, not with projects:

```text
third-party content (URL, article, video, paper, repo, email, pasted text) → SOURCE → raw/ → wiki/
outcome with a defined end state                                          → PROJECT   (projects/)
standing responsibility, no end date                                      → AREA      (areas/, <~10)
a specific person you interact with                                       → PERSON    (people/)
a record of a conversation                                                → MEETING   (meetings/)
a choice with options and consequences                                    → DECISION  (outputs/decisions/)
a single action under a day of work                                       → inline `- [ ]` task
a reusable insight, model, technique, or entity summary                   → WIKI page
an answer, analysis, or review                                            → OUTPUT    (outputs/)
a prompt written or collected                                             → PROMPT    (prompts/)
a passing thought with no other home                                      → today's DAILY note
still unclear                                                             → stays in INBOX
```

**Lifecycles.** Project `idea → active → paused → done → archived`. Area `active ↔ dormant`. Decision
`pending → decided → superseded` with an `outcome` filled in at a later review. Wiki page: created by
compilation, upserted by later sources, conflicts preserved under `## Disagreements`, merged only via
a propose-only consolidation pass. Raw source: written once, never edited.

**Naming.** Dated notes `YYYY-MM-DD Title.md`; weekly reviews `YYYY-Www.md`; daily
`daily/YYYY/MM/YYYY-MM-DD.md`; evergreen notes `Title.md`; logs `YYYY-MM-DD-<run_type>.md`; generated
files carry a leading underscore or a `<!-- GENERATED -->` marker. Characters illegal or unreliable in
wikilinks are stripped from filenames and the pretty form lives in `aliases:`.

**Metadata.** A single-value `domain` field over a closed vocabulary is the axis all automation groups
by; free-form lowercase-kebab `tags` (never with `#`) carry everything else. Link fields
(`projects: areas: people: sources: sources_consulted:`) are YAML lists of quoted wikilinks resolved
by basename, never by path. There is an explicit date-quoting rule: `date:` unquoted, `created:` and
`updated:` quoted.

**Navigation is separate from storage.** Folders answer "what kind of thing is this"; everything else
is frontmatter links and generated views. One canonical note, many views, nothing duplicated to appear
in a second place.

**Generated versus canonical** is a hard boundary. `Home.md`, `bases/*.base`, `projects/_index.md`,
`prompts/_index.md`, `wiki/domains/*`, and the retrieval index are regenerated by
`python3 scripts/vault.py index` and never hand-edited; `vault check` fails when one is stale.

**Zero community plugins.** Only Obsidian core plugins are enabled, including **Bases**, which
provides the generated table views both as `bases/*.base` files and as embedded ` ```base ` blocks
inside templates. Dataview was explicitly rejected so the vault works on mobile with no plugin
installs. `.obsidian/` config and themes are tracked; workspace files are gitignored.

**The determinism boundary is explicit.** Judgment belongs to the model; everything mechanical is a
stdlib Python script: `vault.py` (check, lint, links, index, status, tasks, doctor, new, rename),
`lint-frontmatter.py`, `guard-writes.py`, `fetch-url.py`, `dedup.py`, `build-dashboard.py`,
`split-index.py`, `reflect-due.py`, `retrieve.py`, `build-index.py`, `eval-retrieval.py`. Retrieval is
hybrid BM25 + local dense embeddings + one backlink hop, and is the only optional dependency.

**Validation already exists and is enforced three ways**: a PostToolUse hook lints every written file,
a pre-commit hook lints staged notes, and GitHub Actions runs unit tests plus `vault.py check` on
every push and PR. Your job is to generalize this, not to invent it.

**Security is a designed layer, not an afterthought.** Layer 0 scopes capabilities (a PreToolUse write
guard confines agent writes to content folders and blocks all instruction files at every depth; MCP
write tools are denied). Layer 1 spotlights untrusted bodies with a per-run nonce and fixes a trust
ordering of operator > vault > source. Layer 2 gates egress through a single fetch script that refuses
loopback, private, link-local, metadata, and CGNAT hosts. Third-party content is data, never
instructions.

**The agent layer is already three-tier progressive disclosure**: `AGENTS.md` every session → `docs/`
when the task touches that concern → `.claude/skills/*/SKILL.md` only when invoked. There are ~25
skills, ~20 templates, and 9 Base views. Do not collapse this into one large instruction file, and do
not rebuild it from scratch — port the model.

**Review cadence is weekly only.** `/weekly-review` scaffolds `outputs/reviews/YYYY-Www.md` from
`vault status` facts and proposes status changes for stale projects; the human accepts or rejects.
Monthly and quarterly reviews were deliberately **not** scaffolded, with a documented reason: if
quarterly check-ins prove wanted, they become a section in the weekly template, not a new note type.
Respect that decision unless you can argue against it explicitly.

**Rejected alternatives are documented and should stay rejected** unless you make the case: PARA's
resources layer, Johnny.Decimal numbering, Zettelkasten IDs, Dataview, and a separate task database.

---

## Phase 2 — Generalize into a reusable framework

Build a standalone framework that preserves the strongest ideas while removing personal assumptions.

Optimize for: low bootstrap friction, intuitive daily use, long-term maintainability, clear
information architecture, graceful evolution over years, minimal manual bookkeeping, discoverability,
consistent metadata, predictable behavior, low duplication, low entropy, human readability, agent
readability, automation friendliness, portability, and safe customization.

Prefer a small number of strong primitives over many special cases. In particular, decide explicitly
which of the source vault's nine ingestion source types and platform-specific pipelines belong in a
generic framework, and design ingestion as an extensible interface with one or two reference
implementations rather than porting all nine.

---

## Phase 3 — Design for three audiences

### Human-facing documentation

What the system is, why it exists, how to start, how to use it daily, how projects/areas/notes/tasks
work, how to review, how to customize, and how to avoid common failure modes.

### Agent-facing documentation

Deterministic instructions for repository navigation, note creation, metadata handling,
moving/renaming, updating generated indexes, maintaining links, respecting schemas, modifying
templates, avoiding duplication, running maintenance, and validating changes. Keep the source's
tool-neutral-plus-tool-specific split (`AGENTS.md` imported by `CLAUDE.md`) so the framework is not
locked to one agent product.

### Shared specifications

Unambiguous, ideally machine-readable specifications for directory structure, note schemas, metadata,
naming, lifecycle states, relationships, invariants, and allowed transformations. The source's
schema-doc-mirrored-by-a-linter arrangement works; consider making the schema data (YAML/JSON) with
both the doc and the linter generated from it, and state the trade-off.

---

## Phase 4 — Bootstrap experience

A new user should be able to copy the framework and start immediately:

```text
clone/copy → run setup → answer a few configuration questions → generate the vault
           → open in Obsidian → start capturing
```

Setup must at minimum install the git hooks path, create the folder skeleton, write a starter
configuration, and run validation once so the user sees a green check on day one. Provide starter
templates, synthetic example notes, an onboarding checklist, and first-day/first-week workflows.
No user should need to understand the whole architecture before using it.

All starter content must be synthetic.

---

## Phase 5 — Make customization safe

Separate three things that the source vault currently mixes:

* **Framework core** — conventions, scripts, schema, hooks. Rarely changed.
* **User configuration** — vault name, enabled modules, the `domain` vocabulary, review cadence, date
  formats, folder names, integrations. Note that the source hardcodes several of these (the ten
  `domain` values, the tag list, the folder names, the source types) in `docs/schema.md`, the linter,
  and the scripts simultaneously. This is the single biggest generalization problem in the project —
  solve it with one configuration file that the schema, linter, templates, and scripts all read.
* **User data** — the actual notes.

Aim for `core + configuration + user data`, so routine customization never means editing framework
internals.

---

## Phase 6 — Agentic architecture

The framework should work well with Claude Code and other agents. Port and improve the agent
instruction layer: root map, invariants, commands, schemas, routing rules, maintenance commands,
validation, and skills.

Agents should be able to answer: Where does this note go? New note or update an existing one? What
metadata does it need? Which generated indexes must be regenerated? Is this project active or
archived? How should it link? What may safely be renamed? What invariants must hold? What am I
forbidden to do without asking?

Keep progressive disclosure. The root instruction file stays short and points deeper only when needed.
Carry over the source's explicit "what agents may create without asking" and "what agents never do"
sections — they are the highest-value part of its agent layer.

---

## Phase 7 — Determinism and maintainability

Reduce ambiguity. Keep the routing tree's top-down, first-match-wins property. Keep the
propose-only guardrail: maintenance passes are additive and never perform bulk moves, renames,
deletes, merges, or schema migrations without an explicit request and a dry-run report.

Provide validation for invalid metadata, broken internal links, duplicate identifiers, malformed
filenames, orphan notes, stale generated indexes, invalid lifecycle states, and schema violations —
generalizing what `vault.py check`, `lint-frontmatter.py`, the hooks, and CI already do.

Favor idempotent scripts and deterministic transformations. Running a maintenance command twice must
not corrupt or duplicate state.

---

## Phase 8 — Reduce entropy

Do not preserve complexity because it exists. Look specifically for: redundant folder layers,
duplicated templates, duplicated concepts, conflicting taxonomies, unnecessary metadata, stale
indexes, obsolete automation, fragile links, conventions that require too much memory, conflicting
agent instructions, and workflows that generate maintenance burden.

Concrete candidates in the source worth interrogating: the four-way `outputs/` split, the four-way
`prompts/` split with semver refinements, the `canvas/` and `attachments/` folders, the size of
`wiki/_index.md`, the overlap between `bases/*.base` files and embedded ` ```base ` blocks, and the
overlap between `vault check`, `vault doctor`, and the tidy pass.

Simplify aggressively where it improves usability without destroying capability.

---

## Repository shape

Derive the final structure from evidence and sound design. As a starting point to evaluate, not to
copy mechanically:

```text
lifeos/
├── README.md
├── AGENTS.md                 # tool-neutral agent instructions
├── CLAUDE.md                 # imports AGENTS.md, adds Claude Code specifics
├── docs/                     # architecture, schema, routing, workflows, security, customization
├── templates/
├── scripts/
├── config/                   # the single source of user configuration
├── examples/                 # synthetic example vault
└── vault/                    # generated skeleton: inbox/ daily/ projects/ areas/ ...
```

Note that the source's own layout puts the vault at the repository root rather than under `vault/` —
the repo *is* the vault. Decide deliberately which arrangement the framework should ship, and record
the reasoning. If you keep a `system/` folder, do not name a subfolder `prompts/`; that name is taken
by the user-facing prompt library concept.

---

## Deliverables

1. Architecture overview — conceptual model, design principles, entity relationships, information lifecycle
2. Clean repository structure
3. Getting-started guide — installation, initialization, first use
4. Daily operating guide
5. Review workflow — weekly by default; justify anything beyond it
6. Templates — project, area, wiki/knowledge, daily, weekly review, person, meeting, decision, and any
   other primitive the source proves useful
7. Metadata and schema specification, with the linter mirroring it
8. Naming and linking conventions
9. Agent instructions — three-tier, tool-neutral core
10. Bootstrap/setup mechanism
11. Maintenance mechanism
12. Validation tooling — plus hooks and a CI workflow
13. Synthetic example vault
14. Customization guide
15. Migration/adoption guide — including how to adopt without inheriting my structure
16. Architecture decision record — what was retained, what was generalized, what was removed, why;
    include the source's already-recorded rejections (PARA resources, Johnny.Decimal, Zettelkasten
    IDs, Dataview, task database) and any you add
17. Security model — the untrusted-content posture, write confinement, and egress gating, generalized
18. Privacy audit — verify the output contains no source personal data

---

## Implementation rules

* **Never modify the source vault.** Treat it as read-only. It lives in iCloud Drive, so any write
  propagates to my other devices immediately. No deletes, renames, migrations, or rewrites.
* Build everything in this repository.
* Never open `auth.json`.
* The framework's own scripts should stay Python stdlib where the source does, with heavier
  dependencies (embeddings) isolated and optional.

---

## Validation

Before finishing, run an adversarial review from five perspectives:

* **New user** — can someone who has never seen my vault understand and start using this?
* **Long-term user** — does it hold up at thousands of notes and several years? The source is already
  at ~3,800 files and documents its next two scaling migrations; does the framework inherit that
  foresight?
* **Agent** — can an agent navigate and modify it predictably without rediscovering conventions?
* **Privacy reviewer** — could any output reveal or reconstruct information about me? Grep the result
  for real names, project names, employers, and domains from the source before declaring done.
* **Systems engineer** — are architecture, schemas, scripts, and workflows coherent and deterministic?

Try to break it. Look for ambiguous classifications, broken setup flows, hidden dependencies,
undocumented assumptions, privacy leakage, plugin coupling, circular workflows, maintenance traps,
non-idempotent automation, schema drift, and inconsistent agent instructions. Fix what matters.

---

## Working style

Do not start with a folder copy. Read the source's own documentation first, then verify it against the
tree, then model, then separate system from data, then propose the generalized architecture, then
implement, validate, and simplify.

Use the vault as evidence but exercise judgment. Where the existing implementation is suboptimal,
improve it rather than preserving it for fidelity. Where it made a deliberate choice and documented
the reasoning, respect the choice or argue against it explicitly — do not silently reverse it.

Do not invent features to look sophisticated. Every component must justify its maintenance cost.

The result should feel like a small, coherent operating system for personal knowledge and life
management, not a collection of Obsidian tricks.

## Definition of done

Another person can take the framework, bootstrap a fresh vault, understand the mental model, use it
immediately, maintain it over time, customize it safely, and work with AI agents effectively — without
receiving any of my personal data and without needing access to the original vault.
