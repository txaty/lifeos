# Getting started

Ten minutes from clone to your first note. You do not need to understand the architecture to start
— the system is designed so the parts you skip still work.

## Install

You need **Python 3.11+** and **Obsidian**. Nothing else — no plugins, no pip install.

```
git clone <this repo> my-vault
cd my-vault
python3 setup.py
```

Setup asks two questions, then creates the folders, installs the git hooks, seeds a small example
vault, and runs validation. You should see:

```
vault check: 0 error(s), 0 warning(s)
Vault is valid.
```

If Python is too old, setup says exactly that and what to run. On macOS the system Python is usually
3.9; `brew install python` fixes it.

### The two questions

**What is this vault called?** Cosmetic — it appears in the dashboard header.

**Which domains?** This one matters. `domain` is the single axis everything groups by: every project,
area, and knowledge page picks exactly one. Six to twelve broad areas of your life. The default set
is a reasonable start:

```
career  engineering  finance  health  learning  personal  projects  world
```

Pick categories you would use to describe how you spend your attention, not topics you find
interesting. `world` is deliberately there for the large amount of material everyone follows but
never acts on — without it, that material contaminates every other domain.

You can change domains later, but changing one means updating the notes that use it, so a few
minutes of thought here is worth it.

## Open it in Obsidian

*Open folder as vault* → choose `my-vault`. The bundled `.obsidian/` config means new notes land in
`inbox/`, daily notes use the right template and folder, and the Bases plugin is on.

Look at `Home.md` in reading view, then `bases/attention.base`. Both are showing you the example
notes that setup seeded.

## Take the tour

The examples are a small, complete, working vault. They are worth five minutes because they show the
shape better than any description:

- `projects/Run a Half Marathon.md` — an active project with a `question:`, a status, a log, and an
  embedded live view of everything attached to it.
- `areas/Fitness.md` — the standing responsibility that project sits under. Note that it has a
  *standard*, not a deadline.
- `wiki/concepts/Progressive Overload.md` — compiled knowledge, cited to a source, with a
  `## Disagreements` section where two sources conflict and neither was allowed to win.
- `outputs/decisions/2026-08-28 Train Four Days a Week Instead of Six.md` — a decision with the
  prediction written *before* the outcome. This is the format that makes hindsight honest.
- `outputs/reviews/2026-W35.md` — what a weekly review looks like when the facts come from a script.

When you have seen enough, clear them out:

```
python3 setup.py --unseed
```

That removes only the example notes you have **not** edited — anything you changed is yours now and
is kept, with a note saying so. Run `python3 setup.py --unseed --check` first if you want to see
what it would do.

## Your first day

**1. Capture something.** In Obsidian press `⌘N` and type. It lands in `inbox/`. Do not tidy it.

```
python3 scripts/vault.py new inbox "look into X"
```

**2. Make one project.** Something you are actually doing that could be finished:

```
python3 scripts/vault.py new project "Ship the thing" \
    --set domain=projects --set "question=What does it take to get this in front of users?"
```

Open it, write the `## Status` paragraph, add one task. That is a project.

**3. Make one area.** The standing responsibility that project lives under:

```
python3 scripts/vault.py new area "Side Work" --set domain=projects
```

Then link them: add `areas: ["[[Side Work]]"]` to the project's frontmatter.

**4. Check your work.**

```
python3 scripts/vault.py check
```

Green means the vault is internally consistent. Get used to running it; it takes a second and it is
the thing that keeps the system from quietly rotting.

## Your first week

- **Capture without classifying.** Resist tidying. The inbox is supposed to fill up.
- **Write a daily note** most days. Tasks, a few log lines, links to what you touched. In Obsidian
  the Daily Notes command creates it in the right place from the right template.
- **Do not create areas yet.** Wait until you notice you keep filing things into the same shape.
  Under ten areas, forever.
- **At the end of the week, run the review.** This is the one habit that makes the rest work:

  ```
  python3 scripts/vault.py status          # the facts
  python3 scripts/vault.py new review      # the scaffold
  ```

  Empty the inbox, decide something about each stale project, write three honest lines. Twenty
  minutes.

That is the whole system. Everything else — ingestion, retrieval, the agent layer — is optional
weight you can add when you feel the lack of it.

## What to read next

| You want to | Read |
|---|---|
| Use it day to day | [`daily-guide.md`](daily-guide.md) |
| Know where something goes | [`routing.md`](routing.md) — the decision tree |
| Know what a field means | [`schema.md`](schema.md) |
| Change how it works | [`customization.md`](customization.md) |
| Move existing notes in | [`migration.md`](migration.md) |
| Understand why | [`architecture.md`](architecture.md) · [`decisions.md`](decisions.md) |

## Common first-week mistakes

**Making everything a project.** Most things are tasks in a project you already have, or a line in a
daily note. If you cannot write the one-sentence `question:`, it is not a project.

**Making too many areas.** Areas are the things you are permanently responsible for. Most people have
five to eight. If you have fifteen, several are projects and several are wishes.

**Tidying at capture time.** Capture is supposed to be sloppy. The sorting happens once a week when
you can see everything at once, which is both faster and better.

**Editing generated files.** `Home.md`, `_index.md`, and `wiki/domains/*` are regenerated from your
notes. Change the notes and run `vault.py index`. `check` will tell you if you forget.

**Filing sources you will never read.** A source that never gets cited by a page is a bookmark with
extra steps. `vault.py doctor` will show you the ratio, and it is usually worse than you expect.
