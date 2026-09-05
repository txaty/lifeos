#!/usr/bin/env python3
"""PreToolUse guard: confine an agent's file writes to the vault's content folders.

This is the cheapest and most reliable layer of the security model, because it is
deterministic code rather than an instruction an agent might be talked out of. It
never reads file *content* — only the destination path — so there is nothing in it
for injected text to influence.

The threat it answers: this vault ingests untrusted third-party content with an
agent that can write files. Without confinement, text inside a fetched article
could talk that agent into rewriting its own instructions (`AGENTS.md`), its own
guard (`scripts/`), or its own permissions (`.claude/settings.json`). Blocking
those paths turns the worst case into "attacker text lands in a git-tracked note",
which a human review and `git diff` will catch.

Instruction files are blocked at EVERY depth, not just the root, because agents
load nested instruction files on demand — `inbox/AGENTS.md` would otherwise be a
direct injection path into the next session.

Wiring (see .claude/settings.json):
    PreToolUse on Write|Edit|MultiEdit|NotebookEdit -> this script, tool JSON on stdin
Block contract: exit 2 with a reason on stderr.

Deliberate human edits to system files:
    export LIFEOS_ALLOW_SYSTEM_WRITES=1
Scheduled or unattended runs must NEVER set it.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lifeos_config import VAULT, ConfigError, load

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit", "str_replace_editor"}


def vault_root() -> Path:
    """Claude Code sets CLAUDE_PROJECT_DIR; fall back to the config's own location."""
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(env).resolve() if env else VAULT


def deny(message: str) -> int:
    sys.stderr.write(message)
    return 2


def main() -> int:
    try:
        cfg = load()
    except ConfigError:
        return 0  # no config: not a LifeOS vault, nothing to guard

    if not cfg.guard_writes:
        return 0
    if cfg.env_flag("ALLOW_SYSTEM_WRITES"):
        return 0  # deliberate human-driven development session

    try:
        payload = json.load(sys.stdin)
    except Exception:
        # Fail open on an unparsable hook payload: a malformed message must never
        # brick a session. The value here is in blocking the unambiguous paths.
        return 0

    tool = payload.get("tool_name") or payload.get("tool") or ""
    if tool not in WRITE_TOOLS:
        return 0

    tool_input = payload.get("tool_input") or {}
    target = (tool_input.get("file_path") or tool_input.get("path")
              or tool_input.get("notebook_path"))
    if not target:
        return 0

    root = vault_root()
    try:
        path = Path(target)
        if not path.is_absolute():
            path = root / path
        relpath = path.resolve().relative_to(root).as_posix()
    except (ValueError, OSError):
        return deny(f"guard-writes: BLOCKED write outside the vault: {target}\n")

    parts = relpath.split("/")
    if parts[-1] in cfg.instruction_files or any(p in cfg.instruction_dirs for p in parts[:-1]):
        return deny(
            f"guard-writes: BLOCKED write to an instruction file: {relpath}\n"
            f"{', '.join(sorted(cfg.instruction_files))} and "
            f"{', '.join(sorted(cfg.instruction_dirs))}/ are protected at every depth,\n"
            "because agents load nested instruction files on demand.\n"
            f"Deliberate human change? Set {cfg.env('ALLOW_SYSTEM_WRITES')}=1 and retry.\n")

    if relpath in cfg.content_root_files:
        return 0
    if any(relpath == d or relpath.startswith(d + "/") for d in cfg.content_dirs):
        return 0

    return deny(
        f"guard-writes: BLOCKED write to a protected path: {relpath}\n"
        f"Agent writes are confined to: {' '.join(d + '/' for d in cfg.content_dirs)}"
        f"{' '.join(cfg.content_root_files)}\n"
        "Everything else (config/, docs/, scripts/, templates/, bases/, .github/) is\n"
        "system surface that a human owns.\n"
        f"Deliberate human change? Set {cfg.env('ALLOW_SYSTEM_WRITES')}=1 and retry.\n")


if __name__ == "__main__":
    sys.exit(main())
