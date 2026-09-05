# LifeOS

[![vault check](https://github.com/txaty/lifeos/actions/workflows/vault-check.yml/badge.svg)](https://github.com/txaty/lifeos/actions/workflows/vault-check.yml)

**A second brain that an AI agent can safely operate.**

One Obsidian vault of plain Markdown that is also a git repository, with a schema strict enough that
scripts and agents can act on it, and guardrails strong enough that you can let them.

```bash
git clone https://github.com/txaty/lifeos.git my-vault
cd my-vault && python3 setup.py
```

Two questions, then you have a working vault, git hooks, a small example set, and a green check.
Nothing to install: every script is Python 3.11 standard library, and Obsidian needs no community
plugins.

---

## The problem it solves

Most note systems fail in the same two ways. They rot, because nothing checks them. And the moment
you point an AI at one, you discover it can read a malicious web page and then rewrite its own
instructions.

LifeOS answers both structurally:

**The documentation cannot lie to you.** One config file defines every note type, folder, required
field, and allowed value. The linter reads it, and `docs/schema.md` is *generated* from it. A doc
that disagrees with the enforcement is not a bug you can have here.

```toml
# config/lifeos.toml — adding a note type is a config edit, not a code change
[types.project]
folder = "projects"
required = ["type", "title", "status", "created", "updated", "domain", "question", "tags"]
[types.project.enums]
status = ["idea", "active", "paused", "done", "archived"]
```

**Agents are confined by code, not by instructions.** A pre-write hook restricts agent writes to
content folders and makes instruction files unwritable *at every depth* — because agents load nested
instruction files on demand, so `inbox/AGENTS.md` would otherwise be an injection path. All network
access goes through one audited script that refuses private, loopback, and cloud-metadata addresses
and re-validates every redirect hop.

Worst case after a successful prompt injection: attacker text sits in a git-tracked note, visible in
`git diff`. No exfiltration, no self-modification.

## The shape

```
                    inbox/      unsorted capture — steady state: empty
                    daily/      one note per day: tasks, log, links
  your life         projects/   outcomes with an end state
                    areas/      standing responsibilities, no end date
                    people/     meetings/

  what you read     raw/        sources, verbatim, append-only
  what you learned  wiki/       compiled knowledge, always cited

  what came out     outputs/    answers · decisions · reviews
                    logs/       one file per agent run, append-only
```

Ten note types, each pinned to one folder. `type` in the frontmatter and the folder on disk must
agree — that single invariant is why every script knows what a file is without opening it.

Folders answer only *what kind of thing is this*. Everything else is links and generated views: one
canonical note, many views, nothing ever duplicated to appear in a second place.

## A note is just a file

```markdown
---
type: project
title: "Run a Half Marathon"
status: active
created: "2026-07-02"
updated: "2026-09-01"
domain: health
kind: life
question: "Can I go from 5k to a half marathon in five months without getting injured?"
areas:
  - "[[Fitness]]"
due: 2026-11-15
tags: [running, habit]
---

## Status

Week 9 of 20. Longest run so far is 14 km, which is ahead of plan.

## Tasks

- [ ] Register for the November race before entries close
```

That is `examples/projects/Run a Half Marathon.md`, unedited — and it is checked by CI, so the
snippet above cannot drift from a note that actually validates.

Every project needs `question:` in one sentence. If you cannot write it, you have an idea or an
area, not a project — which is the single highest-yield rule in the whole system.

Tasks are inline checkboxes in the note that owns them, collected by `vault.py tasks`. There is no
task database, because a task database is a second system that competes with the first.

## The loop

```
capture (seconds, all week) → process (weekly) → review (20 minutes, weekly)
```

```bash
python3 scripts/vault.py status          # what needs you, from facts not vibes
python3 scripts/retrieve.py "what do I know about recovery"
python3 scripts/vault.py new decision "Drop to four training days"
python3 scripts/vault.py check           # runs on every commit and in CI
```

Retrieval is BM25 plus one hop through backlinks — so it finds the page you wanted even when that
page does not contain your words, which is most of the time.

## It holds at scale

Measured on a synthetic vault of **5,073 notes**:

| Command | Time |
|---|---|
| `vault.py index` | 0.08s |
| `vault.py status` | 0.27s |
| `retrieve.py "query"` | 0.49s |
| `vault.py check` | 1.2s |
| `vault.py doctor` | 1.2s |

At that size `Home.md` is 1.5 KB and `wiki/_index.md` is 1.0 KB.

`check` runs in the pre-commit hook, so it is kept well under the point where people reach for
`--no-verify`. The knowledge index stays small because it is a signpost, not a catalogue — the
per-domain router pages absorb the growth.

## Start here

| You are | Read |
|---|---|
| New | [`docs/getting-started.md`](docs/getting-started.md) — clone to first note, ~10 min |
| Using it daily | [`docs/daily-guide.md`](docs/daily-guide.md) |
| An AI agent | [`AGENTS.md`](AGENTS.md) — map, invariants, commands |
| Adapting it | [`docs/customization.md`](docs/customization.md) |
| Bringing notes in | [`docs/migration.md`](docs/migration.md) |
| Curious why | [`docs/architecture.md`](docs/architecture.md) · [`docs/decisions.md`](docs/decisions.md) |
| Security-minded | [`docs/security.md`](docs/security.md) |

## What it is not

Not PARA, not Zettelkasten, not a task manager, not a plugin. It takes PARA's
projects-versus-areas distinction and rejects the rest.

[`docs/decisions.md`](docs/decisions.md) records what was considered and turned down — PARA's
resources layer, Johnny.Decimal, Zettelkasten IDs, Dataview, a task database — each with its reason
and its cost. Read it before adding something back.

## Provenance

Distilled from a working personal vault of ~3,800 notes. It contains none of that vault's content:
the architecture was extracted, every example here is synthetic, and
[`docs/privacy-audit.md`](docs/privacy-audit.md) records what was taken and what was not.

The source vault's *usage data* did most of the cutting. It had a four-way `outputs/` split holding
six files, a four-way prompt library holding twelve, and three source types holding none. Counting
files is a better guide to what belongs in a framework than admiring the design.

## Contributing

Fork it and make it yours — that is the intended use. Routine changes should never require editing
`scripts/`, and there is a test asserting that a whole new note type does not.

If something does force you into the code, that is the interesting bug: please
[open an issue](https://github.com/txaty/lifeos/issues) saying what you were trying to model.
More in [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licence

[MIT](LICENSE). Take it, change it, delete half of it.
