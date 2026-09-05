#!/usr/bin/env python3
"""Load and validate config/lifeos.toml.

Every other script reads the vault's shape through this module, so there is exactly
one place where "what note types exist" is decided. Nothing here imports anything
outside the standard library.

Python 3.11+ is required for `tomllib`. That is a deliberate trade-off: one TOML
parser, no hand-rolled fallback that could disagree with it. See docs/decisions.md
(ADR-004).
"""
from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

if sys.version_info < (3, 11):  # pragma: no cover - environment guard
    sys.exit(
        "LifeOS needs Python 3.11 or newer (found "
        f"{sys.version_info.major}.{sys.version_info.minor}).\n"
        "  macOS:  brew install python\n"
        "  Linux:  apt install python3.11  (or your distro's equivalent)\n"
        "Why: config/lifeos.toml is read with the stdlib `tomllib` module."
    )

import tomllib

VAULT = Path(__file__).resolve().parent.parent
CONFIG_PATH = VAULT / "config" / "lifeos.toml"

# Filename patterns a type may declare. Regexes live in vault.py; this is the vocabulary.
FILENAME_PATTERNS = {"title", "dated", "daily", "week", "log", "capture", "free"}


class ConfigError(Exception):
    """config/lifeos.toml is missing, unparsable, or internally inconsistent."""


class Variant:
    """One [types.X.variants.Y] block.

    A variant is a narrower kind of note that lives in its own subfolder and may add
    required fields or enums. Sources, outputs, and wiki page kinds are all the same
    mechanism — one primitive instead of three special cases.
    """

    __slots__ = ("name", "parent", "folder", "filename", "template", "required",
                 "optional", "enums", "summary", "url_hints", "non_empty")

    def __init__(self, name: str, parent: str, block: dict) -> None:
        self.name = name
        self.parent = parent
        self.folder = block.get("folder", "")
        self.filename = block.get("filename")
        self.template = block.get("template")
        self.required = list(block.get("required", []))
        self.optional = list(block.get("optional", []))
        self.non_empty = list(block.get("non_empty", []))
        self.enums = {k: list(v) for k, v in (block.get("enums") or {}).items()}
        self.summary = block.get("summary", "")
        self.url_hints = list(block.get("url_hints", []))

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Variant {self.parent}.{self.name} -> {self.folder}/>"


class NoteType:
    """One [types.X] block, resolved into the questions callers actually ask."""

    __slots__ = ("name", "folder", "filename", "template", "required", "optional",
                 "enums", "summary", "immutable", "frontmatter_optional",
                 "variants", "variant_field", "archive_folder", "archive_status",
                 "non_empty")

    def __init__(self, name: str, block: dict) -> None:
        self.name = name
        self.folder = block.get("folder", name)
        self.filename = block.get("filename", "title")
        self.template = block.get("template")
        self.required = list(block.get("required", []))
        self.optional = list(block.get("optional", []))
        self.non_empty = list(block.get("non_empty", []))
        self.enums = {k: list(v) for k, v in (block.get("enums") or {}).items()}
        self.summary = block.get("summary", "")
        self.immutable = bool(block.get("immutable", False))
        self.frontmatter_optional = bool(block.get("frontmatter_optional", False))
        self.variant_field = block.get("variant_field")
        self.archive_folder = block.get("archive_folder")
        self.archive_status = block.get("archive_status")
        self.variants = {n: Variant(n, name, b)
                         for n, b in (block.get("variants") or {}).items()}
        # A variant_field is an enum over the variant names, by construction.
        if self.variant_field and self.variant_field not in self.enums:
            self.enums[self.variant_field] = sorted(self.variants)

    @property
    def known_fields(self) -> set[str]:
        fields = set(self.required) | set(self.optional) | {"aliases"}
        for v in self.variants.values():
            fields |= set(v.required) | set(v.optional) | set(v.enums)
        if self.variant_field:
            fields.add(self.variant_field)
        return fields

    @property
    def subfolders(self) -> list[str]:
        return sorted(v.folder.split("/", 1)[1] for v in self.variants.values()
                      if "/" in v.folder)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<NoteType {self.name} -> {self.folder}/>"


class Config:
    """The vault's shape, read once and shared."""

    def __init__(self, data: dict, path: Path) -> None:
        self.path = path
        self.raw = data

        vault = data.get("vault", {})
        self.name = vault.get("name", "LifeOS")
        self.primary_language = vault.get("primary_language", "en")
        self.env_prefix = vault.get("env_prefix", "LIFEOS")

        vocab = data.get("vocab", {})
        self.domains = list(vocab.get("domains", []))
        self.meta_domain = vocab.get("meta_domain", "meta")
        self.suggested_tags = list(vocab.get("suggested_tags", []))

        review = data.get("review", {})
        self.cadence = review.get("cadence", "weekly")
        self.stale_active_days = int(review.get("stale_active_days", 30))
        self.stale_idea_days = int(review.get("stale_idea_days", 90))
        self.decision_review_days = int(review.get("decision_review_days", 14))
        self.stale_wiki_days = int(review.get("stale_wiki_days", 365))

        paths = data.get("paths", {})
        self.content_dirs = list(paths.get("content_dirs", []))
        self.content_root_files = list(paths.get("content_root_files", []))
        self.system_dirs = list(paths.get("system_dirs", []))
        self.generated_files = list(paths.get("generated_files", []))
        self.wiki_domain_dir = paths.get("wiki_domain_dir", "wiki/domains")

        fields = data.get("fields", {})
        self.dates_quoted = set(fields.get("dates_quoted", []))
        self.dates_unquoted = set(fields.get("dates_unquoted", []))
        self.link_lists = set(fields.get("link_lists", []))
        self.link_scalars = set(fields.get("link_scalars", []))

        self.types = {n: NoteType(n, b) for n, b in (data.get("types") or {}).items()}

        sec = data.get("security", {})
        self.guard_writes = bool(sec.get("guard_writes", True))
        self.instruction_files = set(sec.get("instruction_files", []))
        self.instruction_dirs = set(sec.get("instruction_dirs", []))
        self.allowlist_only = bool(sec.get("allowlist_only", False))
        self.publisher_allowlist = list(sec.get("publisher_allowlist", []))
        self.allow_benchmark_range = bool(sec.get("allow_benchmark_range", False))

        ret = data.get("retrieval", {})
        self.dense_enabled = bool(ret.get("dense_enabled", False))
        self.backlink_hop = bool(ret.get("backlink_hop", True))
        self.default_k = int(ret.get("default_k", 10))

        self._validate()

    # ----------------------------------------------------------------- lookups

    @property
    def folder_to_type(self) -> dict[str, str]:
        """Top-level folder name -> type name. The folder/type invariant, as data."""
        return {t.folder.split("/")[0]: t.name for t in self.types.values()}

    def type_for_path(self, relpath: str) -> NoteType | None:
        """Which note type governs this vault-relative path."""
        top = relpath.split("/", 1)[0]
        name = self.folder_to_type.get(top)
        return self.types.get(name) if name else None

    def variant_for_path(self, relpath: str) -> Variant | None:
        """The most specific [types.X.variants.Y] block governing this path."""
        best = None
        for t in self.types.values():
            for v in t.variants.values():
                if v.folder and relpath.startswith(v.folder + "/"):
                    if best is None or len(v.folder) > len(best.folder):
                        best = v
        return best

    def find_variant(self, name: str) -> Variant | None:
        """Look a variant up by its bare name (`decision`, `paper`, `concept`)."""
        for t in self.types.values():
            if name in t.variants:
                return t.variants[name]
        return None

    @property
    def all_variants(self) -> dict[str, Variant]:
        return {n: v for t in self.types.values() for n, v in t.variants.items()}

    def env(self, suffix: str) -> str:
        return f"{self.env_prefix}_{suffix}"

    def env_flag(self, suffix: str) -> bool:
        val = os.environ.get(self.env(suffix), "").strip().lower()
        return val not in ("", "0", "false", "no", "off")

    def is_generated(self, relpath: str) -> bool:
        if relpath in self.generated_files:
            return True
        return relpath.startswith(self.wiki_domain_dir + "/")

    def domain_values(self, allow_meta: bool = False) -> list[str]:
        return self.domains + ([self.meta_domain] if allow_meta else [])

    # ----------------------------------------------------------------- checks

    def _validate(self) -> None:
        """Catch config mistakes here, once, with a clear message — rather than as a
        confusing failure three scripts downstream."""
        problems: list[str] = []

        if not self.types:
            problems.append("no [types.*] blocks defined")
        if not self.domains:
            problems.append("[vocab].domains is empty — automation groups by domain")
        if self.meta_domain in self.domains:
            problems.append(
                f"[vocab].meta_domain {self.meta_domain!r} also appears in domains; "
                "it is reserved for generated index files")

        seen_folders: dict[str, str] = {}
        for t in self.types.values():
            if t.filename not in FILENAME_PATTERNS:
                problems.append(
                    f"[types.{t.name}].filename={t.filename!r} is not one of "
                    f"{sorted(FILENAME_PATTERNS)}")
            top = t.folder.split("/")[0]
            if top in seen_folders:
                problems.append(
                    f"folder {top!r} is claimed by both [types.{seen_folders[top]}] "
                    f"and [types.{t.name}] — folder and type must agree 1:1")
            seen_folders[top] = t.name
            if top not in self.content_dirs:
                problems.append(
                    f"[types.{t.name}].folder={t.folder!r} is not under "
                    f"[paths].content_dirs — agents could not write it")
            for field in t.non_empty:
                if field not in t.required:
                    problems.append(
                        f"[types.{t.name}].non_empty lists {field!r}, which is not required")
            for field, values in t.enums.items():
                if field not in t.known_fields:
                    problems.append(
                        f"[types.{t.name}.enums].{field} constrains a field that is "
                        f"neither required nor optional for that type")
                if not values:
                    problems.append(f"[types.{t.name}.enums].{field} is empty")
            if t.archive_folder and not t.archive_status:
                problems.append(f"[types.{t.name}] sets archive_folder without archive_status")
            if t.archive_status and t.archive_status not in t.enums.get("status", []):
                problems.append(
                    f"[types.{t.name}].archive_status={t.archive_status!r} is not in "
                    f"its own status enum")

        # Variants must sit under their parent's folder, and variant names must be
        # globally unique so `vault.py new <name>` is unambiguous.
        seen_variants: dict[str, str] = {}
        for t in self.types.values():
            for v in t.variants.values():
                label = f"[types.{t.name}.variants.{v.name}]"
                if not v.folder:
                    problems.append(f"{label} has no folder")
                elif not v.folder.startswith(t.folder + "/"):
                    problems.append(
                        f"{label}.folder={v.folder!r} is not under "
                        f"[types.{t.name}].folder={t.folder!r}")
                if v.name in seen_variants:
                    problems.append(
                        f"variant name {v.name!r} is used by both {seen_variants[v.name]} "
                        f"and {label} — names must be unique so `vault.py new` is unambiguous")
                seen_variants[v.name] = label
                if v.filename and v.filename not in FILENAME_PATTERNS:
                    problems.append(f"{label}.filename={v.filename!r} is not one of "
                                    f"{sorted(FILENAME_PATTERNS)}")
            if t.variant_field and not t.variants:
                problems.append(
                    f"[types.{t.name}].variant_field={t.variant_field!r} but no variants "
                    f"are defined, so the field could never hold a valid value")
            if t.variant_field and t.variant_field not in t.required + t.optional:
                problems.append(
                    f"[types.{t.name}].variant_field={t.variant_field!r} is neither required "
                    f"nor optional for that type")

        for f in self.generated_files:
            top = f.split("/")[0]
            if "/" in f and top not in self.content_dirs:
                problems.append(f"[paths].generated_files entry {f!r} is outside content_dirs")

        if problems:
            raise ConfigError(
                f"{self.path} is inconsistent:\n" + "\n".join(f"  - {p}" for p in problems))


@lru_cache(maxsize=1)
def load(path: Path | None = None) -> Config:
    """Read config/lifeos.toml. Cached: config is read once per process."""
    p = path or CONFIG_PATH
    try:
        with open(p, "rb") as fh:
            data = tomllib.load(fh)
    except FileNotFoundError:
        raise ConfigError(
            f"missing {p}\nRun `python3 setup.py` to create a vault, or copy "
            "config/lifeos.toml from the framework.") from None
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{p} is not valid TOML: {e}") from None
    return Config(data, p)


def main(argv: list[str] | None = None) -> int:
    """`python3 scripts/lifeos_config.py` — validate the config and print a summary."""
    try:
        cfg = load()
    except ConfigError as e:
        print(f"ERROR  {e}", file=sys.stderr)
        return 1
    print(f"{cfg.path.name}: OK")
    print(f"  vault           {cfg.name} ({cfg.primary_language})")
    print(f"  domains         {', '.join(cfg.domains)}")
    print(f"  note types      {', '.join(sorted(cfg.types))}")
    for name in sorted(cfg.types):
        t = cfg.types[name]
        if t.variants:
            print(f"  {name + ' variants':<15} {', '.join(sorted(t.variants))}")
    print(f"  content dirs    {', '.join(cfg.content_dirs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
