# Customization

Three things are deliberately separate, and keeping them separate is what lets you change the system
without forking it:

| | What it is | How often it changes |
|---|---|---|
| **Core** | `scripts/`, `.githooks/`, `.github/` | rarely, and by pull request |
| **Configuration** | `config/lifeos.toml`, `templates/`, `bases/` | whenever your life does |
| **Your data** | every note | constantly |

**Routine customization means editing `config/lifeos.toml`.** If you find yourself editing a script
to change what the vault holds, either you have found a gap worth reporting or you are about to make
your vault hard to update.

After any config change:

```
python3 scripts/vault.py docs && python3 scripts/vault.py check
```

The first regenerates `docs/schema.md` from the config. The second tells you which existing notes no
longer fit. `scripts/lifeos_config.py` validates the config itself and refuses inconsistencies with a
specific message.

## Change the domains

`domain` is the one axis everything groups by, so this is the change with the most reach.

```toml
[vocab]
domains = ["career", "engineering", "health", "learning", "personal", "world"]
```

**Renaming a domain means updating the notes that use it.** The linter will list every one:

```
python3 scripts/vault.py check | grep "domain="
grep -rl "^domain: oldname" --include="*.md" . | xargs sed -i '' 's/^domain: oldname/domain: newname/'
python3 scripts/vault.py docs && python3 scripts/vault.py index && python3 scripts/vault.py check
```

Removing a domain also removes its generated router page; `vault.py index` cleans up on the next run.

Keep the list between six and twelve. Fewer and it stops discriminating; more and you hesitate at
filing time, which is where systems die.

## Change the review thresholds

```toml
[review]
stale_active_days = 30      # an active project untouched this long is flagged
stale_idea_days = 90        # an idea this old must be activated or deleted
decision_review_days = 14   # a decision this old with outcome: unknown is flagged
stale_wiki_days = 365       # a page uncorroborated this long shows up in `doctor`
```

If `status` is nagging you about things you are fine with, raise the number. If nothing is ever
flagged, lower it — a review that never surfaces anything is not being honest with you.

## Add a field to a note type

Say projects should record effort:

```toml
[types.project]
optional = ["kind", "areas", "due", "aliases", "people", "effort"]

[types.project.enums]
effort = ["hours", "days", "weeks", "months"]
```

Then `vault.py docs`. The linter now accepts `effort` and rejects any value outside the enum. Adding
it to `required` instead would make every existing project invalid — add to `optional` first, fill
notes in over time, and promote it later if it earns it.

## Add a source type

Ingestion is an interface. A new source type is a config block:

```toml
[types.source.variants.podcast]
folder = "raw/podcasts"
template = "source.md"
required = ["url"]
non_empty = ["url"]
url_hints = ["overcast.fm", "podcasts.apple.com"]
summary = "An episode worth keeping, captured as notes."
```

```
mkdir -p raw/podcasts && python3 scripts/vault.py docs && python3 scripts/vault.py check
```

`source_type: podcast` is now valid, the linter requires it to live in `raw/podcasts/`, and
`vault.py new podcast "Title"` works. No code changed.

A *pipeline* — something that knows how to get a transcript out of a particular platform — is a
skill, not config. Write one only when you actually have that platform.

## Add a whole note type

The same mechanism. Suppose you want a prompt library — a type this framework deliberately does not
ship ([`decisions.md`](decisions.md), ADR-008):

```toml
[paths]
content_dirs = [..., "prompts"]        # 1. agents may write here

[types.prompt]                          # 2. define the type
folder = "prompts"
filename = "title"
template = "prompt.md"
required = ["type", "title", "created", "updated", "status", "use_case", "tags"]
optional = ["domain", "aliases", "target_model"]
summary = "A prompt worth keeping and reusing."
[types.prompt.enums]
status = ["draft", "active", "deprecated"]
```

```
mkdir -p prompts
cp templates/wiki-concept.md templates/prompt.md   # 3. edit to match the frontmatter above
python3 scripts/vault.py docs && python3 scripts/vault.py check
```

Now `vault.py new prompt "Title"` works, the linter enforces the schema, the write guard permits
`prompts/`, and `docs/schema.md` documents it. **Nothing in `scripts/` was touched** — that is the
test of whether the configuration boundary is real.

Before you do this, though: read ADR-008. A type that holds twelve notes is usually a folder or a
tag pretending to be a type, and every type costs a template, a slot in the routing tree, and a
decision you make every time you file something.

## Rename a folder

```toml
[types.person]
folder = "contacts"

[paths]
content_dirs = [..., "contacts", ...]   # both places, or the config validator objects
```

```
git mv people contacts
python3 scripts/vault.py docs && python3 scripts/vault.py check
```

Links keep working: they resolve by basename, never by path. This is exactly why.

## Change templates

`templates/*.md` are yours. The only rules:

- frontmatter must satisfy the schema for that type;
- **date placeholders must match the quoting rule** — `date: {{date:YYYY-MM-DD}}` unquoted,
  `created: "{{date:YYYY-MM-DD}}"` quoted. `docs/schema.md` lists which is which, and a mismatch is
  the single most common template mistake;
- prose in `<!-- comments -->` disappears from the rendered note, which is where guidance belongs.

Test with `vault.py new <type> "Test"` and then delete the result.

## Change the views

`bases/*.base` are Obsidian Bases queries — plain YAML over your frontmatter. Edit them freely; they
read notes and write nothing.

The distinction worth preserving: **a `.base` file is a vault-wide dashboard; an embedded ` ```base `
block inside a note is a view scoped to that note** (it can use `this.file.path`, which a standalone
file cannot). That is a real difference, not duplication — keep new views on the right side of it.

## Turn things off

Not every part earns its place in every life.

| Don't want | Do this |
|---|---|
| Meetings | drop `[types.meeting]` and `meetings` from `content_dirs`; delete the folder |
| The whole knowledge layer | drop `[types.source]` and `[types.wiki]`; you now have a project system |
| The write guard | `guard_writes = false` — only if no agent ever touches this vault |
| Git hooks | `git config --unset core.hooksPath` — CI still catches it |

Removing a type you have notes for will make `check` fail loudly, which is the intended behaviour.
Move or delete the notes first.

## Optional: semantic search

BM25 works on a fresh clone with nothing installed. To add semantic matching:

```
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export LIFEOS_INDEX_DIR=~/.cache/lifeos     # keep the index out of any synced folder
```

then `dense_enabled = true` in `[retrieval]`. It is strictly additive: retrieval degrades to BM25
when the dependency is missing, so nothing you build on top of it can break by removing it.

## Staying updateable

```
git remote add upstream https://github.com/txaty/lifeos.git
git fetch upstream && git log --oneline HEAD..upstream/main -- scripts/ docs/
git cherry-pick <commit>
```

Because your changes live in `config/`, `templates/`, and your notes, upstream changes to `scripts/`
usually merge without conflict. That property is the whole reason for the split — protect it by
resisting the urge to "just tweak" a script.

If you do change one, note it in your own `docs/decisions.md` entry so future-you knows what diverged
and why.
