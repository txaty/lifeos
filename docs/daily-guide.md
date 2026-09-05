# Daily guide

How this actually gets used, in the order you will use it.

## The loop

```
capture (seconds, all week)  →  process (once a week)  →  review (twenty minutes, once a week)
```

That is it. Everything else in this repository exists to support those three motions.

## Capture — all week, no thinking

Something occurs to you. Put it in `inbox/` and carry on.

| Where you are | What to do |
|---|---|
| Obsidian, desktop or phone | `⌘N` / the `+` button — new notes land in `inbox/` already |
| Terminal | `python3 scripts/vault.py new inbox "the thought"` |
| Reading something | clip it to `inbox/`, or paste the URL |
| Talking to an agent | "capture this" |

**Do not classify at capture time.** Deciding costs more than the thought is worth in that moment,
and doing it in a batch later is both faster and better, because you can see everything at once.

The exception: if you already know exactly where it goes — a task for a live project, a note about a
person you have a page for — just put it there. Capture is for uncertainty.

## The daily note

`daily/YYYY/MM/YYYY-MM-DD.md`. Three sections:

```markdown
## Tasks
- [ ] Things for today only

## Log
- What happened, what you noticed, what you decided

## Links
- [[Notes you touched today]]
```

**Tasks here are for today.** Anything that outlives the day belongs to its project or area — move
it, do not copy it forward, or you end up maintaining two copies of your own intentions.

**The log is the valuable part.** It is what you read when you are trying to remember when something
started going wrong. One line is enough.

You will not write one every day. That is fine; nothing depends on it.

## Working on a project

Open the project note. It has everything: status, tasks, log, and a live view of every source, page,
and decision attached to it.

- Append dated bullets under `## Log` as you go.
- Keep tasks as checkboxes under `## Tasks`.
- **Bump `updated` when the content changes** — and only then. That field is what staleness detection
  reads, so touching it during a sweep makes the review useless.
- A choice with consequences gets its own note:
  `vault.py new decision "..." --set "projects=The Project"`.

**Coming back after months:** read `## Status`, then `## Log` bottom-up, then the attached decisions.
If that is not enough to continue, the project note was not being maintained — which is itself the
useful signal.

## Filing something you read

```
python3 scripts/fetch_url.py <url> --text
```

Then write it into `raw/<type>/YYYY-MM-DD Title.md` with the original publication date, and compile
what is worth keeping into a `wiki/` page — or let the `ingest` skill do both.

**Be willing to skip.** Most of what you read is not worth a page. A source that never gets cited is
a bookmark with extra steps, and `vault.py doctor` will tell you your real ratio.

The test for a wiki page: *would I want to be reminded of this in a year, in a different context?*
If not, the source note alone is enough.

## Asking the vault

Before you search the web, ask what you already know:

```
python3 scripts/retrieve.py "how do I think about X"
python3 scripts/retrieve.py "recovery" --domain health
python3 scripts/retrieve.py "X" --type wiki
```

It searches text and then follows one hop through links, so it finds the page you wanted even when
that page does not contain your words — which is most of the time.

An answer worth keeping goes in `outputs/answers/` with its citations.

## The weekly review

The one habit that keeps everything else honest. Twenty minutes, same slot each week.

**1. Empty the inbox.** Every item goes somewhere or gets deleted. Use the tree in
[`routing.md`](routing.md); first match wins. Ambiguous items get decided in one batch at the end,
not one at a time.

**2. Look at the facts before forming an opinion.**

```
python3 scripts/vault.py status
python3 scripts/vault.py tasks
```

**3. Decide something about every flagged project.** `status` shows you what has gone stale, which
ideas have aged out, what is done but not archived, and which decisions are due for an outcome.

For each one: activate, pause *with a stated unblock condition*, archive, or delete. **"Leave it" is
not on the list.** A project you keep skipping over is either paused or dead, and saying which is the
entire value of the review.

**4. Write three lines.**

```
- Went well:
- Got in the way:
- Next week's one priority:
```

**5. Close.** `python3 scripts/vault.py index && python3 scripts/vault.py check`

## Keeping it healthy

```
python3 scripts/vault.py check        # fast; run it often, and on every commit
python3 scripts/vault.py doctor       # slower; monthly is plenty
python3 scripts/vault.py links --wanted
```

`doctor` tells you things `check` deliberately will not, because they are judgment calls: notes
nothing links to, sources no page cites, pages nothing has confirmed in a year, filenames that will
cause trouble.

`links --wanted` is the pleasant one: pages you have linked to repeatedly but never written. That
list is usually a good writing queue.

## Failure modes, and what they look like

| Symptom | What is actually happening | Fix |
|---|---|---|
| The inbox never empties | The review is not happening | Put it in the calendar. Twenty minutes. |
| Fifteen "active" projects | Nothing is being paused or killed | Force a decision on each at review |
| Notes you cannot find | Everything is being filed, nothing linked | Link from the project or area that cares |
| Two pages on one topic | Creating instead of updating | Search before you write; merge them |
| Sources pile up, nothing compiled | Collecting has become the hobby | `doctor`; skip more, keep less |
| `check` has been red for weeks | The safety net has been switched off | Fix it now; it only gets worse |

The general pattern: this system fails by *accumulating*, not by breaking. The weekly review is the
only thing standing between you and a very tidy pile of things you meant to read.
