# Migration

How to bring existing notes in without inheriting someone else's structure — including this one's.

## The principle

**Do not bulk-import.** A thousand notes converted by a script gives you a thousand notes that
satisfy the linter and mean nothing to you. The value of this system is in the routing decisions, and
those are the part a script cannot make.

Migrate what you are actually using. Leave the rest where it is; it is not going anywhere.

## Start empty, then pull

```
python3 setup.py --no-examples
mkdir ../old-vault-archive && cp -r <your old notes> ../old-vault-archive/
```

Keep the old vault **outside** this one, read-only. Then, for two weeks, work normally — and every
time you reach for an old note, migrate *that one*. After two weeks you will have moved the notes
you actually use, which is a much smaller number than you expect, and you will know the shape of your
own usage rather than guessing at it.

Anything you never reached for did not need migrating. That is information, not failure.

## Migrating one note

1. **Route it** with the tree in [`routing.md`](routing.md). Most old notes are one of: a project,
   a reference page (`wiki/`), or something that should have been deleted years ago.
2. **Create the target properly** — `vault.py new <type> "Title"` — so the frontmatter and path are
   right from the start.
3. **Paste the body in.** Keep your own words; do not let a model rewrite them.
4. **Add links.** One inbound link within a week, or `doctor` will list it as an orphan and it will
   deserve to be.
5. `python3 scripts/vault.py check`.

## Coming from a specific system

### Obsidian, unstructured

The most common case, and the easiest: it is already Markdown with wikilinks.

- Point `setup.py` at a **copy**, never your live vault.
- `[[Links]]` already work — this system resolves by basename, same as Obsidian's default.
- The work is adding frontmatter, and only to notes you migrate.
- If you used `#tags` as your only structure, map the five or six you actually use onto `domain` and
  leave the long tail as `tags`.

### PARA

Projects and Areas map directly. The other two need decisions:

| PARA | Here |
|---|---|
| `Projects/` | `projects/` — but require a one-sentence `question:` each. Some will turn out to be areas or tasks. |
| `Areas/` | `areas/` — keep under ten. Most PARA vaults have far too many. |
| `Resources/` | split it: things you *read* → `raw/`; things you *concluded* → `wiki/`. Most of it is neither and can go. |
| `Archive/` | finished projects → `projects/archive/`. Everything else: leave it in the old vault. |

The `Resources` split is the real work and the real payoff. It forces the question "did I learn
anything from this, or did I just save it?" — and the honest answer for most of the pile is the
second one.

### Zettelkasten

Your atomic notes are `wiki/` pages. The IDs go away; titles become the identity, and the old ID goes
in `aliases:` so existing links keep resolving:

```yaml
aliases: ["202603041432"]
```

Literature notes become `raw/` sources; permanent notes become `wiki/concepts/`. If a note is
genuinely a claim rather than a concept, title it as the claim — that convention survives intact.

### Notion, Roam, Logseq, or anything with a database

Export to Markdown first and expect to lose block references, transclusion, and inline queries.

- Database rows → notes with frontmatter, one file each.
- Database *properties* → frontmatter fields. Add them to `optional` in the config, not `required`.
- Inline queries → a `.base` view, or an embedded ` ```base ` block.
- Block references → they will break. Convert the ones you care about to note-level links; there is
  no equivalent, and this system deliberately does not have one.

Daily notes usually import cleanly into `daily/YYYY/MM/`, but only the last few months are worth
moving.

## Adopting the ideas without the structure

You do not have to take all of this. The parts are separable, roughly in order of value per unit of
effort:

1. **The weekly review with scripted facts.** Look at the numbers before forming an opinion, and
   force a decision on every stale project. Works in any system, including paper.
2. **Projects have a one-sentence `question:`.** The single highest-yield rule here. It kills about a
   third of most people's project lists on contact.
3. **Decisions get a note with the prediction written before the outcome.** Costs ten minutes,
   and it is the only way to find out whether your judgment is any good.
4. **Sources and conclusions are separate.** What you read is not what you think.
5. **Disagreements are preserved, not resolved.** When two sources you trust conflict, record both.
   Averaging them destroys the most interesting thing on the page.

Take one. If it survives three months, take another.

## Going the other way

If you leave, you take everything: Markdown files with YAML frontmatter and `[[wikilinks]]`, in a git
repository. No database, no proprietary format, no export step. `scripts/` and `config/` are the only
things specific to this framework, and deleting them leaves a perfectly ordinary Obsidian vault.

That is not a courtesy — it is the reason the format was chosen. A system you cannot leave is a
system you cannot trust with ten years of thinking.
