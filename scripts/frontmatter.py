#!/usr/bin/env python3
"""One YAML-frontmatter reader, shared by every script.

Deliberately a *subset* of YAML: flat key/value pairs, quoted and unquoted scalars,
flow arrays `[a, b]`, and block arrays of scalars. That is the whole of what note
frontmatter is allowed to be, and refusing anything richer is a feature — it keeps
notes portable, diff-friendly, and machine-checkable without a YAML dependency.

Callers need to distinguish `created: "2026-01-01"` (a quoted string) from
`date: 2026-01-01` (a YAML date), so parsing returns both the coerced value and the
raw source text of each line.

Stdlib only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.DOTALL)
BLOCK_ITEM_RE = re.compile(r"^[ \t]*-[ \t]*(.*)$")


@dataclass
class Frontmatter:
    """Parsed frontmatter plus enough provenance to report good errors."""

    data: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)      # key -> (lineno, raw value text)
    errors: list[str] = field(default_factory=list)
    present: bool = False
    body: str = ""
    body_offset: int = 0                          # 1-indexed line where the body starts

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __contains__(self, key) -> bool:
        return key in self.data

    def line(self, key: str, default: int = 1) -> int:
        return self.raw.get(key, (default, ""))[0]

    def raw_value(self, key: str) -> str:
        return self.raw.get(key, (0, ""))[1]

    def is_quoted(self, key: str) -> bool:
        v = self.raw_value(key)
        return len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]


def strip_inline_comment(val: str) -> str:
    """Drop a trailing ` # comment`. Quoted scalars and flow arrays keep their contents."""
    if not val:
        return val
    if val[0] == "#":
        return ""
    if val[0] in "\"'":
        end = val.find(val[0], 1)
        return val[: end + 1] if end != -1 else val
    if val.startswith("["):
        end = val.rfind("]")
        return val[: end + 1] if end != -1 else val
    return re.split(r"\s+#", val, maxsplit=1)[0].rstrip()


def unquote(s) -> str:
    if isinstance(s, str) and len(s) >= 2 and s[0] in "\"'" and s[-1] == s[0]:
        return s[1:-1]
    return s


def _coerce(text: str):
    """Turn one raw scalar into a Python value. Conservative on purpose."""
    if text.startswith(("\"", "'")):
        return unquote(text)
    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def parse(text: str) -> Frontmatter:
    """Split a note into frontmatter and body."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return Frontmatter(present=False, body=text, body_offset=1)

    block = m.group(1)
    fm = Frontmatter(present=True, body=text[m.end():],
                     body_offset=text[: m.end()].count("\n") + 1)

    lines = block.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        lineno = i + 2  # +1 for 1-indexing, +1 for the opening ---
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if stripped.startswith("- "):
            fm.errors.append(f"line {lineno}: list item outside a key")
            i += 1
            continue
        if ":" not in line:
            fm.errors.append(f"line {lineno}: expected 'key: value'")
            i += 1
            continue

        key, _, rest = line.partition(":")
        key = key.strip()
        if not key:
            fm.errors.append(f"line {lineno}: empty key")
            i += 1
            continue
        if key in fm.data:
            fm.errors.append(f"line {lineno}: duplicate key {key!r}")

        rest = rest.strip()
        if not rest:
            # A block list may follow, indented under this key.
            items: list[str] = []
            j = i + 1
            while j < len(lines):
                item_m = BLOCK_ITEM_RE.match(lines[j])
                if not item_m or not lines[j].startswith((" ", "\t")):
                    break
                items.append(unquote(item_m.group(1).strip()))
                j += 1
            if items:
                fm.data[key] = items
                fm.raw[key] = (lineno, "<block-list>")
                i = j
                continue
            fm.data[key] = ""
            fm.raw[key] = (lineno, "")
            i += 1
            continue

        val_text = strip_inline_comment(rest)
        fm.raw[key] = (lineno, val_text)
        if val_text.startswith("[") and val_text.endswith("]"):
            inner = val_text[1:-1].strip()
            fm.data[key] = [unquote(p.strip()) for p in inner.split(",") if p.strip()] if inner else []
        else:
            fm.data[key] = _coerce(val_text)
        i += 1

    return fm


def as_list(value) -> list:
    """Frontmatter fields that may be scalar-or-list, always as a list."""
    if value is None or value == "":
        return []
    return list(value) if isinstance(value, list) else [value]


WIKILINK_RE = re.compile(r"^\[\[([^\[\]]+)\]\]$")
# Inline [[links]], excluding ![[embeds]]; strips |alias and #heading.
INLINE_LINK_RE = re.compile(r"(?<!!)\[\[([^\[\]|#]+)(?:#[^\[\]|]*)?(?:\|[^\[\]]*)?\]\]")


def is_wikilink(value) -> bool:
    return isinstance(value, str) and bool(WIKILINK_RE.match(value.strip()))


def link_target(value: str) -> str:
    """`[[Some Note|alias]]` -> `Some Note`. Accepts bare titles too."""
    s = str(value).strip()
    m = WIKILINK_RE.match(s)
    if m:
        s = m.group(1)
    s = s.split("|", 1)[0].split("#", 1)[0].strip()
    return s.rsplit("/", 1)[-1]  # links resolve by basename, never by path


FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
CODESPAN_RE = re.compile(r"`[^`\n]*`")


def strip_code(text: str) -> str:
    """Remove fenced blocks and code spans so `[[links]]` in examples aren't counted."""
    return CODESPAN_RE.sub("", FENCE_RE.sub("", text))


PLAIN_LISTS = ("tags", "aliases")


def render(data: dict, plain_lists: tuple[str, ...] = PLAIN_LISTS) -> str:
    """Serialize a frontmatter dict back to the subset. Used by `vault new`.

    `plain_lists` render inline and unquoted (`tags: [a, b]`); every other list
    renders as a block of quoted items, which is what link fields need.
    """
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            elif key in plain_lists:
                lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
            else:
                lines.append(f"{key}:")
                lines.extend(f'  - "{v}"' if not str(v).startswith('"') else f"  - {v}"
                             for v in value)
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"
