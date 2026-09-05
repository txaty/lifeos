@AGENTS.md

## Claude Code specifics

Everything above applies. This file adds only what is specific to this tool, so the framework is
not locked to one agent product — another agent reads `AGENTS.md` and needs nothing from here.

### Skills

Invoke the skill before doing the work; each one names its inputs, outputs, and the files it may
touch.

| Task | Skill |
|---|---|
| Save a thought, link, or snippet without classifying it | `capture` |
| Route everything sitting in `inbox/` | `process-inbox` |
| Turn a URL or pasted text into a source, then a wiki page | `ingest` |
| Answer a question from what the vault already knows | `ask-vault` |
| Start a project (with a scan of what you already know) | `project-init` |
| Close a project out properly | `archive-project` |
| Scaffold the weekly review from vault facts | `weekly-review` |
| Incremental cleanup, propose-only | `vault-tidy` |

### Hooks

Both are wired in `.claude/settings.json` and run automatically:

- **PreToolUse** → `scripts/guard_writes.py` confines `Write`/`Edit` to content folders and blocks
  instruction files at every depth. If it blocks you, the answer is almost never to work around it.
  A deliberate, human-driven change to system files needs `LIFEOS_ALLOW_SYSTEM_WRITES=1` exported
  for that session — **never** in a scheduled or unattended run.
- **PostToolUse** → `scripts/lint_frontmatter.py` lints every file you write. Fix what it reports
  immediately, in the same turn, rather than at the end.

### Working style here

- Read `AGENTS.md` and stop. Open a `docs/` file when the task actually touches that concern.
- Prefer `python3 scripts/retrieve.py` over grepping, and `vault.py status --json` over reading
  many notes to work out what is going on.
- Batch questions. One `AskUserQuestion` at the end of processing beats one prompt per item.
- When a maintenance pass finds something to change, write the proposal into the run log and stop.
  Propose-only is the rule that makes unattended runs safe to leave running.

### Scheduling unattended runs

If you schedule anything (local `cron`/`launchd` running `claude -p "/ingest ..."`):

- keep the write guard active — do not export the bypass;
- gate on a deterministic trigger rather than a fixed clock where possible;
- write a `logs/YYYY-MM-DD-<run_type>.md` entry every time, including "nothing to do";
- end with `python3 scripts/vault.py check`.
