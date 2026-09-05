#!/usr/bin/env python3
"""Validate note frontmatter against config/lifeos.toml.

This is the enforcement half of the schema. `docs/schema.md` is the documentation
half, and it is *generated from the same config*, so the two cannot drift — the
failure mode where a doc says one thing and the linter checks another is designed
out rather than policed.

The linter is generic: it knows about required fields, enums, dates, links, and
folder/type agreement, and it learns which of those apply to which note from the
config. Adding a note type is a config edit, not a code change.

Run:
  python3 scripts/lint_frontmatter.py                 # every content folder
  python3 scripts/lint_frontmatter.py <path> [...]    # specific files
  python3 scripts/lint_frontmatter.py --stdin         # paths on stdin, one per line
  python3 scripts/lint_frontmatter.py --hook          # agent hook payload (JSON) on stdin

Exit 1 when any CRITICAL or MAJOR issue is found. Stdlib only — `--hook` parses the
payload itself rather than shelling out to `jq`, so the hook has no dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import frontmatter as fmlib
from lifeos_config import VAULT, Config, ConfigError, load

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TAG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LEVELS = ("CRITICAL", "MAJOR", "MINOR")
BLOCKING = ("CRITICAL", "MAJOR")


class Issue:
    __slots__ = ("path", "line", "level", "msg")

    def __init__(self, path: str, line: int, level: str, msg: str) -> None:
        self.path, self.line, self.level, self.msg = path, line, level, msg

    def __str__(self) -> str:
        return f"{self.path}:{self.line}  {self.level}  {self.msg}"

    @property
    def blocking(self) -> bool:
        return self.level in BLOCKING


_VAULT_PREFIX = str(VAULT) + "/"


def rel(path: Path) -> str:
    """Vault-relative POSIX path. String slicing rather than Path.relative_to:
    this is called once per note per pass and pathlib's version dominated the
    profile at a few thousand notes."""
    text = str(path)
    if not text.startswith(_VAULT_PREFIX):
        resolved = str(path.resolve())
        if not resolved.startswith(_VAULT_PREFIX):
            return text
        text = resolved
    return text[len(_VAULT_PREFIX):]


# ------------------------------------------------------------------ rules

def _check_enum(cfg: Config, fm, relpath: str, field: str, allowed: list[str],
                out: list[Issue], level: str = "MAJOR") -> None:
    raw = str(fm.raw_value(field))
    ln = fm.line(field)
    if "|" in raw:
        out.append(Issue(relpath, ln, level,
                         f"{field}={raw!r} still holds the template's '|' list — pick ONE of "
                         f"{allowed}"))
        return
    value = fm.get(field)
    if value in ("", None):
        return
    if value not in allowed:
        out.append(Issue(relpath, ln, level, f"{field}={value!r} not in {allowed}"))


def _check_dates(cfg: Config, fm, relpath: str, out: list[Issue]) -> None:
    for field in cfg.dates_quoted:
        if field not in fm:
            continue
        raw = fm.raw_value(field)
        if raw and not fm.is_quoted(field):
            out.append(Issue(relpath, fm.line(field), "MAJOR",
                             f'{field}: {raw} must be a QUOTED string like "YYYY-MM-DD"'))
        elif raw and not DATE_RE.match(fmlib.unquote(raw)):
            out.append(Issue(relpath, fm.line(field), "MAJOR",
                             f"{field}={raw} is not a YYYY-MM-DD date"))
    for field in cfg.dates_unquoted:
        if field not in fm:
            continue
        raw = fm.raw_value(field)
        if raw and fm.is_quoted(field):
            out.append(Issue(relpath, fm.line(field), "MAJOR",
                             f"{field}: {raw} must be an UNQUOTED YAML date: YYYY-MM-DD"))
        elif raw and not DATE_RE.match(raw):
            out.append(Issue(relpath, fm.line(field), "MAJOR",
                             f"{field}={raw} is not a YYYY-MM-DD date"))


def _check_links(cfg: Config, fm, relpath: str, out: list[Issue]) -> None:
    for field in cfg.link_lists:
        if field not in fm:
            continue
        value = fm.get(field)
        ln = fm.line(field)
        if value in ("", None) or value == []:
            continue
        if not isinstance(value, list):
            out.append(Issue(relpath, ln, "MAJOR",
                             f'{field} must be a list of "[[wikilink]]" strings'))
            continue
        for entry in value:
            if not fmlib.is_wikilink(entry):
                out.append(Issue(relpath, ln, "MAJOR",
                                 f'{field} entry {entry!r} must be a quoted "[[wikilink]]"'))
    for field in cfg.link_scalars:
        if field in fm and fm.get(field) not in ("", None) and not fmlib.is_wikilink(fm.get(field)):
            out.append(Issue(relpath, fm.line(field), "MAJOR",
                             f'{field} must be a quoted "[[wikilink]]"'))


def _check_tags(cfg: Config, fm, relpath: str, out: list[Issue]) -> None:
    if "tags" not in fm:
        return
    tags, ln = fm.get("tags"), fm.line("tags")
    if not isinstance(tags, list):
        out.append(Issue(relpath, ln, "MAJOR", "tags must be a list, e.g. tags: [ai, strategy]"))
        return
    for tag in tags:
        t = str(tag)
        if t.startswith("#"):
            out.append(Issue(relpath, ln, "MAJOR",
                             f"tag {t!r} has a '#' prefix — tag arrays use bare names"))
        elif t and not TAG_RE.match(t):
            out.append(Issue(relpath, ln, "MINOR",
                             f"tag {t!r} is not lowercase-kebab-case"))


def _check_domain(cfg: Config, fm, relpath: str, out: list[Issue]) -> None:
    if "domain" not in fm:
        return
    allow_meta = cfg.is_generated(relpath)
    _check_enum(cfg, fm, relpath, "domain", cfg.domain_values(allow_meta), out)
    if fm.get("domain") == cfg.meta_domain and not allow_meta:
        out.append(Issue(relpath, fm.line("domain"), "MAJOR",
                         f"domain={cfg.meta_domain!r} is reserved for generated index files"))


# ------------------------------------------------------------------ file

def lint_file(path: Path, cfg: Config, text: str | None = None) -> list[Issue]:
    relpath = rel(path)
    out: list[Issue] = []

    if text is None:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            return [Issue(relpath, 1, "CRITICAL", f"unreadable: {e}")]

    fm = fmlib.parse(text)

    # A generated index lives in a content folder but is not a note of that folder's
    # type — projects/_index.md is a wiki page about projects. Trust its declared
    # type; `vault.py index` owns the file and regenerates it wholesale.
    if cfg.is_generated(relpath):
        ntype = cfg.types.get(str(fm.get("type"))) or cfg.type_for_path(relpath)
    else:
        ntype = cfg.type_for_path(relpath)
    if ntype is None:
        return []  # not a content folder — nothing to enforce

    # Registries use a leading underscore and carry no frontmatter requirement.
    is_registry = path.name.startswith("_")

    if not fm.present:
        if ntype.frontmatter_optional or is_registry:
            return []
        return [Issue(relpath, 1, "CRITICAL", "missing or malformed YAML frontmatter block")]

    for err in fm.errors:
        out.append(Issue(relpath, 1, "CRITICAL", f"frontmatter: {err}"))

    declared = fm.get("type")
    if not declared:
        out.append(Issue(relpath, 2, "CRITICAL", "missing required field: type"))
        return out

    if declared != ntype.name and not cfg.is_generated(relpath):
        out.append(Issue(relpath, fm.line("type"), "MAJOR",
                         f"type={declared!r} but folder {ntype.folder!r} expects "
                         f"type={ntype.name!r}"))

    # Required fields = the type's, plus whatever its subtype block adds.
    required = set(ntype.required)
    optional = set(ntype.optional)
    enums = dict(ntype.enums)

    non_empty = set(ntype.non_empty)
    variant = cfg.variant_for_path(relpath)
    if variant:
        required |= set(variant.required)
        optional |= set(variant.optional)
        non_empty |= set(variant.non_empty)
        enums.update(variant.enums)
    if cfg.is_generated(relpath):
        required.discard("sources")  # index pages aggregate notes, not sources

    for field in sorted(required - set(fm.data)):
        out.append(Issue(relpath, 2, "CRITICAL", f"missing required field: {field}"))
    # A required field must be *present*. An empty list still counts — a new note
    # legitimately has no links yet. Fields in `non_empty` must also have a value.
    for field in sorted(required & set(fm.data)):
        value = fm.get(field)
        empty_list = isinstance(value, list) and not value
        if value in ("", None) or (empty_list and field in non_empty):
            out.append(Issue(relpath, fm.line(field), "CRITICAL",
                             f"required field {field} is empty"))

    # When a type names a variant_field, its value and its folder must agree —
    # otherwise `source_type: paper` could sit in raw/videos/ and every view lies.
    if ntype.variant_field:
        value = fm.get(ntype.variant_field)
        if value:
            declared = ntype.variants.get(str(value))
            if declared and not relpath.startswith(declared.folder + "/"):
                out.append(Issue(relpath, fm.line(ntype.variant_field), "MAJOR",
                                 f"{ntype.variant_field}={value!r} belongs in "
                                 f"{declared.folder}/"))

    for field, allowed in enums.items():
        _check_enum(cfg, fm, relpath, field, allowed, out)

    _check_domain(cfg, fm, relpath, out)
    _check_dates(cfg, fm, relpath, out)
    _check_links(cfg, fm, relpath, out)
    _check_tags(cfg, fm, relpath, out)

    # Archive invariant: the archive status and the archive folder imply each other.
    if ntype.archive_folder:
        in_archive = relpath.startswith(ntype.archive_folder + "/")
        status = fm.get("status")
        ln = fm.line("status", 2)
        if status == ntype.archive_status and not in_archive:
            out.append(Issue(relpath, ln, "MAJOR",
                             f"status={status!r} but the file is not in {ntype.archive_folder}/"))
        if in_archive and status and status != ntype.archive_status:
            out.append(Issue(relpath, ln, "MAJOR",
                             f"file is in {ntype.archive_folder}/ but status={status!r}"))

    # Unknown fields are a MINOR: harmless in Obsidian, but usually a typo.
    known = required | optional | set(enums) | {"type", "aliases", "cssclasses"}
    if ntype.variant_field:
        known.add(ntype.variant_field)
    for field in sorted(set(fm.data) - known):
        out.append(Issue(relpath, fm.line(field), "MINOR",
                         f"unknown field {field!r} for type {ntype.name!r} "
                         f"(add it to [types.{ntype.name}].optional if intended)"))

    return out


# ------------------------------------------------------------------ driver

def iter_notes(cfg: Config, dirs=None):
    """Every content note. `dirs` scopes the walk to specific folders; root-level
    content files are only included in an unscoped walk, so a folder-scoped caller
    never picks up Home.md by surprise."""
    for d in (dirs if dirs is not None else cfg.content_dirs):
        root = VAULT / d
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.md")):
            if "/." in str(p)[len(_VAULT_PREFIX):]:
                continue   # skip dotted directories without paying for .parts
            yield p
    if dirs is None:
        for name in cfg.content_root_files:
            p = VAULT / name
            if p.is_file():
                yield p


def lint_paths(paths, cfg: Config) -> list[Issue]:
    issues: list[Issue] = []
    for p in paths:
        p = Path(p)
        if p.suffix != ".md" or not p.is_file():
            continue
        issues.extend(lint_file(p, cfg))
    return issues


def _paths_from_hook_payload(raw: str) -> list[Path]:
    """Extract the written file from an agent's PostToolUse payload.

    Parsing the JSON here rather than piping through `jq` keeps the hook a
    zero-dependency one-liner, which matters because a hook that fails to run is a
    validation layer that silently is not there.
    """
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(payload, dict):
        return []
    tool_input = payload.get("tool_input") or {}
    candidates = [tool_input.get("file_path"), tool_input.get("path"),
                  tool_input.get("notebook_path")]
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict):
            candidates.append(edit.get("file_path"))
    return [Path(c) for c in candidates if c]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="*", help="files to lint (default: all content)")
    ap.add_argument("--stdin", action="store_true", help="read paths from stdin, one per line")
    ap.add_argument("--hook", action="store_true",
                    help="read an agent hook payload (JSON) from stdin")
    ap.add_argument("--quiet", action="store_true", help="only print blocking issues")
    args = ap.parse_args(argv)

    try:
        cfg = load()
    except ConfigError as e:
        print(f"ERROR  {e}", file=sys.stderr)
        return 2

    if args.hook:
        paths = _paths_from_hook_payload(sys.stdin.read())
        if not paths:
            return 0  # not a file-writing tool call, or an unreadable payload
    elif args.stdin:
        paths = [Path(line.strip()) for line in sys.stdin if line.strip()]
    elif args.paths:
        paths = [Path(p) for p in args.paths]
    else:
        paths = list(iter_notes(cfg))

    issues = lint_paths(paths, cfg)
    blocking = [i for i in issues if i.blocking]
    shown = blocking if args.quiet else issues
    for issue in sorted(shown, key=lambda i: (i.path, i.line, LEVELS.index(i.level))):
        print(issue)

    if issues and not args.hook:
        minor = len(issues) - len(blocking)
        print(f"\n{len(blocking)} blocking, {minor} minor across {len(paths)} file(s)")
    elif blocking and args.hook:
        # Speak to the agent that just wrote the file: say what to fix, in one place.
        print(f"\nFix these before continuing. Schema: docs/schema.md", file=sys.stderr)
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
