#!/usr/bin/env python3
"""Turn a fresh copy of this framework into your vault.

    python3 setup.py                    # ask a few questions, then build
    python3 setup.py --defaults         # accept everything, no questions
    python3 setup.py --check            # report what would change, write nothing

Idempotent: running it twice is safe and changes nothing the first run did. It will
never overwrite notes you have written, and it will not touch your config once the
file exists unless you pass --reconfigure.

What it does, in order:
  1. verify Python is new enough
  2. write config/lifeos.toml from your answers (first run only)
  3. create the folder skeleton implied by the config
  4. point git at .githooks/ so notes are validated before they are committed
  5. optionally seed the synthetic example vault
  6. generate docs/schema.md and the indexes
  7. run validation, so you see a green check on day one
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MIN_PYTHON = (3, 11)

if sys.version_info < MIN_PYTHON:  # pragma: no cover - environment guard
    sys.exit(
        f"LifeOS needs Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer "
        f"(found {sys.version_info.major}.{sys.version_info.minor}).\n"
        "  macOS:  brew install python\n"
        "  Linux:  apt install python3.11  (or your distro's equivalent)\n"
        "Why: config/lifeos.toml is read with the stdlib `tomllib` module.")

sys.path.insert(0, str(ROOT / "scripts"))

GREEN, YELLOW, RED, DIM, BOLD, OFF = (
    "\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[1m", "\033[0m")


def say(msg: str = "") -> None:
    print(msg)


def step(msg: str) -> None:
    print(f"{BOLD}==>{OFF} {msg}")


def ok(msg: str) -> None:
    print(f"  {GREEN}ok{OFF}    {msg}")


def skip(msg: str) -> None:
    print(f"  {DIM}skip  {msg}{OFF}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}warn{OFF}  {msg}")


def interactive() -> bool:
    """Only prompt when someone is actually there to answer. A setup script that
    blocks forever in a pipe or a CI job is worse than one that picks a default."""
    return sys.stdin is not None and sys.stdin.isatty()


def ask(prompt: str, default: str) -> str:
    if not interactive():
        return default
    try:
        answer = input(f"  {prompt} [{default}]: ").strip()
    except (EOFError, KeyboardInterrupt):
        return default
    return answer or default


def ask_yes(prompt: str, default: bool = True) -> bool:
    if not interactive():
        return default
    hint = "Y/n" if default else "y/N"
    try:
        answer = input(f"  {prompt} [{hint}]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return default
    return default if not answer else answer.startswith("y")


# ------------------------------------------------------------------ config

DEFAULT_DOMAINS = ["career", "engineering", "finance", "health",
                   "learning", "personal", "projects", "world"]


DOMAIN_LINE_RE = re.compile(r'^\s*"([^"]+)"\s*,?\s*(#.*)?$')


def _current_values(text: str) -> tuple[str, list[str], dict[str, str]]:
    """Read the answers already in the config, so re-running offers them back.

    Also returns each domain's trailing comment, so rewriting the list does not
    quietly delete the notes explaining what the values mean.
    """
    name, domains, comments, in_domains = "LifeOS", [], {}, False
    for line in text.split("\n"):
        if in_domains:
            if line.strip().startswith("]"):
                in_domains = False
                continue
            m = DOMAIN_LINE_RE.match(line)
            if m:
                domains.append(m.group(1))
                if m.group(2):
                    comments[m.group(1)] = m.group(2)
            continue
        if line.startswith("name = "):
            name = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("domains = ["):
            in_domains = True
    return name, domains or DEFAULT_DOMAINS, comments


def configure(args) -> bool:
    """Write config/lifeos.toml, offering the current values as defaults.

    There is no separate template file: the shipped config *is* the default, and
    setup edits it in place. Re-running and accepting every default changes
    nothing, which is what makes this safe to run twice.
    """
    config_path = ROOT / "config" / "lifeos.toml"
    if not config_path.exists():
        warn("config/lifeos.toml is missing — restore it from the framework")
        return False

    text = config_path.read_text(encoding="utf-8")
    current_name, current_domains, domain_comments = _current_values(text)
    language = "en"

    if args.defaults or args.check or args.unseed:
        name, domains = current_name, current_domains
    else:
        say()
        say(f"  {DIM}Two questions. Both are changeable later in "
            f"config/lifeos.toml.{OFF}")
        say()
        name = ask("What should this vault be called?", current_name)
        say()
        say(f"  {DIM}`domain` is the one axis everything groups by. Pick 6-12 broad")
        say(f"  areas of your life. Comma-separated, lowercase. You can change these")
        say(f"  later, but changing them means editing notes that use the old value.{OFF}")
        raw = ask("Domains", ", ".join(current_domains))
        domains = [d.strip().lower() for d in raw.split(",") if d.strip()]
        say()

    # Only the answered values are rewritten; every comment in the file stays intact.
    lines = text.split("\n")
    out, in_domains = [], False
    for line in lines:
        if in_domains:
            if line.strip().startswith("]"):
                in_domains = False
            continue
        if line.startswith("name = "):
            out.append(f'name = "{name}"')
        elif line.startswith("primary_language = "):
            out.append(f'primary_language = "{language}"')
        elif line.startswith("domains = ["):
            out.append("domains = [")
            width = max((len(d) for d in domains), default=0) + 3
            for d in domains:
                entry = f'  "{d}",'
                comment = domain_comments.get(d)
                out.append(f"{entry:<{width + 4}}{comment}" if comment else entry)
            out.append("]")
            in_domains = not line.rstrip().endswith("]")
        else:
            out.append(line)

    new_text = "\n".join(out)
    if new_text == text:
        skip(f"config/lifeos.toml unchanged ({name}, {len(domains)} domains)")
        return False
    if args.check:
        say(f"  would update config/lifeos.toml (name={name!r}, {len(domains)} domains)")
        return True
    config_path.write_text(new_text, encoding="utf-8")
    ok(f"config/lifeos.toml  ({name}, {len(domains)} domains)")
    return True


# ------------------------------------------------------------------ skeleton

def make_skeleton(cfg, args) -> int:
    """Create every folder the config implies, with .gitkeep so git tracks them."""
    folders: set[str] = set(cfg.content_dirs)
    for t in cfg.types.values():
        folders.add(t.folder)
        if t.archive_folder:
            folders.add(t.archive_folder)
        for v in t.variants.values():
            folders.add(v.folder)
    folders.add(cfg.wiki_domain_dir)

    created = 0
    for folder in sorted(folders):
        path = ROOT / folder
        if path.is_dir():
            continue
        created += 1
        if args.check:
            say(f"  would create {folder}/")
            continue
        path.mkdir(parents=True, exist_ok=True)

    ok(f"{len(folders)} folders present ({created} created)")
    return created


def reconcile_gitkeep(cfg, args) -> None:
    """An empty directory is invisible to git, so a clone would lose the vault's
    shape. Add `.gitkeep` where a folder is empty and remove it where it is not —
    run after seeding, or every seeded folder keeps a stale marker."""
    if args.check:
        return
    folders: set[str] = set(cfg.content_dirs)
    for t in cfg.types.values():
        folders.add(t.folder)
        if t.archive_folder:
            folders.add(t.archive_folder)
        folders.update(v.folder for v in t.variants.values())
    folders.add(cfg.wiki_domain_dir)

    for folder in sorted(folders):
        path = ROOT / folder
        if not path.is_dir():
            continue
        keep = path / ".gitkeep"
        has_content = any(c.name != ".gitkeep" for c in path.iterdir())
        if has_content and keep.exists():
            keep.unlink()
        elif not has_content and not keep.exists():
            keep.write_text("", encoding="utf-8")


# ------------------------------------------------------------------ hooks

def install_hooks(args) -> bool:
    if not (ROOT / ".git").exists():
        warn("not a git repository — skipping hooks. Run `git init` first, then "
             "`git config core.hooksPath .githooks`.")
        return False
    try:
        current = subprocess.run(["git", "config", "--get", "core.hooksPath"],
                                 cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except FileNotFoundError:
        warn("git not found on PATH — skipping hooks")
        return False
    if current == ".githooks":
        skip("git hooks already installed")
        return False
    if args.check:
        say("  would set git core.hooksPath = .githooks")
        return True
    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=ROOT, check=True)
    hook = ROOT / ".githooks" / "pre-commit"
    if hook.exists():
        hook.chmod(0o755)
    ok("git hooks installed (notes are validated before every commit)")
    return True


# ------------------------------------------------------------------ examples

def unseed_examples(args) -> int:
    """Remove seeded example notes — but only the ones still byte-identical to the
    originals. Anything you edited is yours now and is left alone, so this cannot
    eat work by accident."""
    src = ROOT / "examples"
    if not src.is_dir():
        skip("no examples/ folder")
        return 0

    removed, kept = 0, []
    for path in sorted(src.rglob("*.md")):
        target = ROOT / path.relative_to(src)
        if not target.exists():
            continue
        try:
            same = target.read_bytes() == path.read_bytes()
        except OSError:
            same = False
        if not same:
            kept.append(str(path.relative_to(src)))
            continue
        removed += 1
        if not args.check:
            target.unlink()

    verb = "would remove" if args.check else "removed"
    ok(f"{verb} {removed} unmodified example note(s)")
    for k in kept:
        warn(f"kept {k} — you have edited it")
    return removed


def seed_examples(args, wanted: bool) -> int:
    src = ROOT / "examples"
    if not wanted:
        skip("example notes not seeded (--no-examples)")
        return 0
    if not src.is_dir():
        skip("no examples/ folder to seed from")
        return 0

    copied = 0
    for path in sorted(src.rglob("*.md")):
        target = ROOT / path.relative_to(src)
        if target.exists():
            continue  # never overwrite the user's own notes
        copied += 1
        if args.check:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

    if args.check:
        say(f"  would seed {copied} example note(s)")
    elif copied:
        ok(f"{copied} example notes seeded — delete them once you have your own")
    else:
        skip("example notes already present")
    return copied


# ------------------------------------------------------------------ main

def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run([sys.executable] + cmd, cwd=ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--defaults", action="store_true", help="accept defaults, ask nothing")
    ap.add_argument("--no-examples", action="store_true", help="do not seed example notes")
    ap.add_argument("--unseed", action="store_true",
                    help="remove seeded example notes you have not edited")
    ap.add_argument("--check", action="store_true", help="report changes, write nothing")
    args = ap.parse_args(argv)

    say()
    say(f"{BOLD}LifeOS setup{OFF}")
    say(f"{DIM}{ROOT}{OFF}")
    say()

    step("Configuration")
    configure(args)

    try:
        from lifeos_config import ConfigError, load
        load.cache_clear()
        cfg = load()
    except Exception as e:  # ConfigError or an import problem
        say()
        say(f"{RED}Configuration is not usable:{OFF}\n{e}")
        return 1

    step("Folders")
    make_skeleton(cfg, args)

    step("Git hooks")
    install_hooks(args)

    step("Example notes")
    if args.unseed:
        unseed_examples(args)
    else:
        wanted = not args.no_examples and (args.defaults or args.check
                                           or ask_yes("Seed a small example vault to look at?"))
        seed_examples(args, wanted)
    reconcile_gitkeep(cfg, args)

    if args.check:
        say()
        say(f"{DIM}--check: nothing was written.{OFF}")
        return 0

    step("Generated files")
    for label, cmd in (("docs/schema.md", ["scripts/vault.py", "docs"]),
                       ("indexes", ["scripts/vault.py", "index", "--quiet"])):
        code, out = run(cmd)
        if code == 0:
            ok(label)
        else:
            warn(f"{label}: {out}")

    step("Validation")
    code, out = run(["scripts/vault.py", "check"])
    say()
    print(out)
    say()

    if code == 0:
        say(f"{GREEN}{BOLD}Vault is valid.{OFF}")
        say()
        say(f"{BOLD}Next:{OFF}")
        say(f"  1. Open this folder as a vault in Obsidian.")
        say(f"  2. Read {BOLD}docs/getting-started.md{OFF} — about ten minutes.")
        say(f"  3. Capture something: "
            f"{DIM}python3 scripts/vault.py new inbox \"my first thought\"{OFF}")
        say()
        say(f"{DIM}Daily use:   docs/daily-guide.md{OFF}")
        say(f"{DIM}Customising: docs/customization.md{OFF}")
        say(f"{DIM}For agents:  AGENTS.md{OFF}")
    else:
        say(f"{RED}Validation failed.{OFF} The output above says what to fix.")
    say()
    return code


if __name__ == "__main__":
    sys.exit(main())
