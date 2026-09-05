# LifeOS

A small operating system for personal knowledge and life management: one Obsidian vault of plain
Markdown that is also a git repository, designed to be run jointly by you and AI agents.

It is a **framework you bootstrap**, not an app you install. Everything is plain files: Markdown
notes, YAML frontmatter, one TOML config, and a handful of Python scripts that depend on nothing
but the standard library.

```
git clone <this repo> my-vault && cd my-vault
python3 setup.py
```

Two questions, then you get a folder skeleton, git hooks, a small example vault, and a green check
on day one. Open the folder in Obsidian and start capturing.

## What it is

- **Twelve folders, ten note types, one config file.** `config/lifeos.toml` decides what note types
  exist, what fields they require, and what values those fields may hold. The linter reads it and
  `docs/schema.md` is generated from it, so the documentation and the enforcement cannot drift.
- **Navigation is separate from storage.** Folders answer "what kind of thing is this". Everything
  else is frontmatter links and generated views. One canonical note, many views, nothing duplicated
  to make it appear in a second place.
- **A hard determinism boundary.** Judgment belongs to you and the model; everything mechanical is a
  script. Validation, naming, link integrity, and generated indexes are never a matter of opinion.
- **Security is a designed layer.** The vault reads untrusted third-party content with an agent that
  writes files, so agent writes are confined, instruction files are unwritable, and all network
  access goes through one audited script that refuses private and metadata addresses.
- **Zero plugins, zero dependencies.** Obsidian core only (including Bases). Python stdlib only.
  Optional semantic search is the single exception, and it is strictly additive.

## Start here

| You are | Read |
|---|---|
| New here | [`docs/getting-started.md`](docs/getting-started.md) — install to first note, ~10 min |
| Using it daily | [`docs/daily-guide.md`](docs/daily-guide.md) |
| An AI agent | [`AGENTS.md`](AGENTS.md) — the map, invariants, and commands |
| Adapting it | [`docs/customization.md`](docs/customization.md) |
| Migrating notes in | [`docs/migration.md`](docs/migration.md) |
| Wondering why | [`docs/architecture.md`](docs/architecture.md) · [`docs/decisions.md`](docs/decisions.md) |

## Everyday commands

```
python3 scripts/vault.py status         what needs you right now
python3 scripts/vault.py new project "Ship the thing" --set domain=projects
python3 scripts/retrieve.py "what do I know about X"
python3 scripts/vault.py check          validate everything (also runs on commit and in CI)
```

## What it is not

Not PARA, not Zettelkasten, not a task manager. It borrows PARA's projects-versus-areas distinction
and rejects the rest; tasks are inline checkboxes in the note that owns them, never their own
database. [`docs/decisions.md`](docs/decisions.md) records what was rejected and why — read it
before adding something back.

## Provenance

Distilled from a working personal vault of ~3,800 notes into a reusable framework. It contains no
content from that vault: the architecture was extracted, every example here is synthetic. See
[`docs/privacy-audit.md`](docs/privacy-audit.md).

## Licence

MIT. Take it, change it, delete half of it.
