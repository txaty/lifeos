#!/usr/bin/env python3
"""Render docs/schema.md from config/lifeos.toml.

The schema exists twice by necessity: once as something a human reads, once as
something a linter enforces. Writing it twice is how the two drift. Here the config
is the single source and both the document and the checks are derived from it, so a
disagreement between doc and linter is not a bug you can have.

The cost of this choice: the schema document cannot carry free-form prose about any
individual field, because it is overwritten. Rationale lives in two places instead —
the comments in config/lifeos.toml (next to the values they explain) and
docs/architecture.md (for the reasoning behind the shape). See docs/decisions.md
(ADR-003).

Invoked by `python3 scripts/vault.py docs`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lifeos_config import Config, load

MARK = ("<!-- GENERATED from config/lifeos.toml by `python3 scripts/vault.py docs` — "
        "edit the config, not this file -->")


def _filename_help(pattern: str, folder: str) -> str:
    return {
        "title": "`Title.md`",
        "dated": "`YYYY-MM-DD Title.md`",
        "daily": f"`{folder}/YYYY/MM/YYYY-MM-DD.md`",
        "week": "`YYYY-Www.md`",
        "log": "`YYYY-MM-DD-<run_type>.md`",
        "capture": "`YYYY-MM-DD HHmm Title.md`",
        "free": "free-form",
    }.get(pattern, f"`{pattern}`")


def _fields_block(cfg: Config, required: list[str], optional: list[str],
                  enums: dict[str, list[str]]) -> list[str]:
    lines = ["```yaml"]
    for field in required:
        lines.append(f"{field}: {_example(cfg, field, enums)}")
    if optional:
        lines.append("")
        lines.append("# optional")
        for field in optional:
            lines.append(f"# {field}: {_example(cfg, field, enums)}")
    lines.append("```")
    return lines


def _example(cfg: Config, field: str, enums: dict[str, list[str]]) -> str:
    if field in enums:
        return f"{enums[field][0]}    # one of: {' | '.join(enums[field])}"
    if field == "domain":
        return f"{cfg.domains[0]}    # exactly one of: {' | '.join(cfg.domains)}"
    if field == "tags":
        return "[]    # lowercase-kebab, no '#'"
    if field in cfg.dates_quoted:
        return '"YYYY-MM-DD"    # quoted'
    if field in cfg.dates_unquoted:
        return "YYYY-MM-DD    # unquoted"
    if field in cfg.link_lists:
        return '[]    # list of "[[wikilinks]]"'
    if field in cfg.link_scalars:
        return '"[[Wiki Page]]"'
    if field == "type":
        return "<the type name below>"
    if field in ("title", "question", "query", "use_case", "author", "publisher", "url", "org"):
        return '"..."'
    return "..."


def render(cfg: Config) -> str:
    L: list[str] = []
    add = L.append

    add("# Metadata schema")
    add("")
    add(MARK)
    add("")
    add(f"The contract every note in this vault keeps. `scripts/lint_frontmatter.py` enforces")
    add("it on every write (PostToolUse hook), every commit (pre-commit hook), and in CI")
    add("(`vault.py check`). Both this file and the linter are generated from — or read —")
    add("`config/lifeos.toml`, so they cannot disagree.")
    add("")
    add("**To change the schema, edit `config/lifeos.toml`, then run:**")
    add("")
    add("```")
    add("python3 scripts/vault.py docs && python3 scripts/vault.py check")
    add("```")
    add("")

    add("## How to read this")
    add("")
    add("- Enum fields hold **exactly one** value. The `a | b | c` notation lists what is")
    add("  allowed; never write the `|` into a note.")
    add(f"- `tags:` is a list of bare lowercase-kebab names. Never a `#` prefix.")
    add("- **Date quoting is not cosmetic.** Obsidian and YAML treat these differently:")
    quoted = ", ".join(f"`{f}`" for f in sorted(cfg.dates_quoted))
    unquoted = ", ".join(f"`{f}`" for f in sorted(cfg.dates_unquoted))
    add(f"  - {quoted} are **quoted strings**: `created: \"2026-01-31\"` (bookkeeping stamps)")
    add(f"  - {unquoted} are **unquoted YAML dates**: `date: 2026-01-31` (real-world dates)")
    add(f"- Link fields are lists of quoted wikilinks: `- \"[[Some Note]]\"`. Links resolve by")
    add("  **basename**, never by path, so moving a note never breaks a link.")
    link_fields = ", ".join(f"`{f}`" for f in sorted(cfg.link_lists | cfg.link_scalars))
    add(f"  Link fields: {link_fields}")
    add("- `aliases:` is optional on every type (Obsidian reserved).")
    add("- Fields not listed for a type are flagged as MINOR — harmless, usually a typo.")
    add("")

    add("## Type registry")
    add("")
    add("`type` in the frontmatter and the folder on disk must agree. That single invariant")
    add("is what lets every script know what a file is without reading it.")
    add("")
    add("| `type` | Folder | Filename | Lifecycle | What it is |")
    add("|---|---|---|---|---|")
    for name in sorted(cfg.types):
        t = cfg.types[name]
        life = " → ".join(t.enums["status"]) if "status" in t.enums else "—"
        add(f"| `{name}` | `{t.folder}/` | {_filename_help(t.filename, t.folder)} "
            f"| {life} | {t.summary} |")
    add("")
    add("Files starting with `_` are registries or generated indexes and are exempt from the")
    add("frontmatter requirement.")
    add("")

    add("## Controlled vocabularies")
    add("")
    add(f"### `domain` — the one axis automation groups by")
    add("")
    add("Every project, area, and wiki page picks **exactly one**. If a note spans two,")
    add("pick the primary and let `tags` carry the rest.")
    add("")
    for d in cfg.domains:
        add(f"- `{d}`")
    add("")
    add(f"`{cfg.meta_domain}` is reserved for generated index files.")
    add("")
    add("### `tags` — everything else")
    add("")
    add("Free-form, lowercase-kebab, no `#`. Tags are for discovery; `domain` is what")
    add("automation relies on. Suggested starting points: "
        + ", ".join(f"`{t}`" for t in cfg.suggested_tags) + ".")
    add("")
    for tname in sorted(cfg.types):
        t = cfg.types[tname]
        if not (t.variants and t.variant_field):
            continue
        add(f"### `{t.variant_field}`")
        add("")
        add("| Value | Folder | What it is |")
        add("|---|---|---|")
        for name in sorted(t.variants):
            v = t.variants[name]
            add(f"| `{name}` | `{v.folder}/` | {v.summary} |")
        add("")

    add("## Per-type frontmatter")
    add("")
    for name in sorted(cfg.types):
        t = cfg.types[name]
        add(f"### `{name}` — `{t.folder}/`")
        add("")
        add(t.summary)
        add("")
        if t.frontmatter_optional:
            add("Frontmatter is **optional** here: a capture from a phone is plain text and")
            add("still valid. If present, it must validate.")
            add("")
        if t.immutable:
            add("**Immutable.** Bodies are written once and never edited afterwards.")
            add("")
        L.extend(_fields_block(cfg, t.required, t.optional, t.enums))
        add("")
        if t.archive_folder:
            add(f"`status: {t.archive_status}` if and only if the file lives in "
                f"`{t.archive_folder}/`. The linter enforces both directions.")
            add("")
        if t.variants:
            if t.variant_field:
                add(f"`{t.variant_field}` names the variant, and the linter checks that the")
                add("value and the folder agree. Create one with "
                    f"`vault.py new <variant> \"Title\"`:")
            else:
                add("Variants share the schema above and differ only by folder and template.")
                add(f"Create one with `vault.py new <variant> \"Title\"`:")
            add("")
            for vname in sorted(t.variants):
                v = t.variants[vname]
                extra = []
                if v.required:
                    extra.append("adds " + ", ".join(f"`{f}`" for f in v.required))
                if v.optional:
                    extra.append("may add " + ", ".join(f"`{f}`" for f in v.optional))
                for field, values in v.enums.items():
                    extra.append(f"`{field}`: {' | '.join(values)}")
                if v.filename:
                    extra.append(f"named {_filename_help(v.filename, v.folder)}")
                add(f"- **`{vname}`** → `{v.folder}/` — {v.summary}"
                    + (f" _({'; '.join(extra)})_" if extra else ""))
            add("")

    add("## Field semantics worth knowing")
    add("")
    add("- `updated` is bumped when **content** changes. Sweeps, index regeneration, and")
    add("  link rewrites never touch it — otherwise staleness detection becomes noise.")
    add("- `sources:` on a wiki page must point at notes under "
        f"`{cfg.types['source'].folder}/`. A wiki claim without provenance does not belong.")
    add("- `projects:` on a source propagates to wiki pages compiled from it — merged,")
    add("  never overwritten.")
    add("- Tasks are inline `- [ ]` checkboxes inside the note that owns them. There is no")
    add("  task note type and no task database; `vault.py tasks` collects them.")
    add("")

    add("## Thresholds")
    add("")
    add("| Setting | Value | Effect |")
    add("|---|---|---|")
    add(f"| `stale_active_days` | {cfg.stale_active_days} | an active project untouched this "
        "long is flagged |")
    add(f"| `stale_idea_days` | {cfg.stale_idea_days} | an idea this old is flagged "
        "activate-or-delete |")
    add(f"| `decision_review_days` | {cfg.decision_review_days} | a decision this old with "
        "`outcome: unknown` is flagged |")
    add(f"| `stale_wiki_days` | {cfg.stale_wiki_days} | a wiki page uncorroborated this long "
        "shows in `doctor` |")
    add("")
    return "\n".join(L).rstrip() + "\n"


def main() -> int:
    print(render(load()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
