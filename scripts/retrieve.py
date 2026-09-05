#!/usr/bin/env python3
"""Search the vault: "what do I already know about X?"

A second brain that cannot answer that question is a folder of files. Retrieval is
therefore core, not a nice-to-have — and it is stdlib BM25 so it works on a fresh
clone with nothing installed.

Three signals, combined:
  1. **BM25** over note text — the workhorse. Handles "roughly these words".
  2. **Field boosts** — a match in the title or an alias means more than one in a
     footnote.
  3. **One backlink hop** — pages linked from a strong match get a fraction of its
     score. This is what a graph gives you that a search box does not: the note you
     wanted often does not contain your words, but its neighbour does.

Dense embeddings are optional and strictly additive (see requirements.txt). When
they are absent, retrieval degrades to BM25 rather than failing, so no workflow
depends on an optional dependency.

    python3 scripts/retrieve.py "how do I decide X" --k 10
    python3 scripts/retrieve.py "topic" --type wiki --domain learning
    python3 scripts/retrieve.py "topic" --json
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import frontmatter as fmlib
from lifeos_config import VAULT, Config, ConfigError, load

K1, B = 1.5, 0.75          # standard BM25 parameters
TITLE_BOOST = 3.0          # a title match is worth three body matches
ALIAS_BOOST = 2.0
TAG_BOOST = 2.0
BACKLINK_WEIGHT = 0.25     # a neighbour inherits a quarter of the score

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9'-]*")
STOPWORDS = frozenset("""
a an and are as at be but by do does for from had has have how i if in into is it
its of on or that the their then there these this to was were what when where which
who why will with you your about can could should would my me we our us not no
""".split())


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower())
            if t not in STOPWORDS and len(t) > 1]


class Document:
    __slots__ = ("path", "relpath", "title", "type", "domain", "tags",
                 "tokens", "length", "links", "snippet")

    def __init__(self, path: Path, relpath: str, fm, body: str) -> None:
        self.path = path
        self.relpath = relpath
        self.title = fmlib.unquote(str(fm.get("title", ""))) or path.stem
        self.type = str(fm.get("type", ""))
        self.domain = str(fm.get("domain", ""))
        self.tags = [str(t) for t in fmlib.as_list(fm.get("tags"))]
        aliases = [str(a) for a in fmlib.as_list(fm.get("aliases"))]

        clean = fmlib.strip_code(body)
        weighted = (
            tokenize(self.title) * int(TITLE_BOOST)
            + tokenize(" ".join(aliases)) * int(ALIAS_BOOST)
            + tokenize(" ".join(self.tags)) * int(TAG_BOOST)
            + tokenize(clean))
        self.tokens = Counter(weighted)
        self.length = sum(self.tokens.values()) or 1
        self.links = {fmlib.link_target(m) for m in fmlib.INLINE_LINK_RE.findall(clean)}
        for field in ("projects", "areas", "people", "sources", "related"):
            self.links |= {fmlib.link_target(str(v)) for v in fmlib.as_list(fm.get(field))}
        self.snippet = self._first_prose(body)

    @staticmethod
    def _first_prose(body: str) -> str:
        for line in body.splitlines():
            s = line.strip()
            if not s or s.startswith(("#", "<!--", "```", "|", ">")):
                continue
            s = re.sub(r"\[\[([^\[\]|]+)(?:\|[^\[\]]*)?\]\]", r"\1", s).lstrip("- ")
            if len(s) > 15:
                return s[:160] + ("…" if len(s) > 160 else "")
        return ""


class Index:
    """An in-memory BM25 index. Built on demand: a few thousand notes take well
    under a second, so there is no cache to invalidate or rebuild."""

    def __init__(self, docs: list[Document]) -> None:
        self.docs = docs
        self.df: Counter = Counter()
        for doc in docs:
            self.df.update(doc.tokens.keys())
        self.n = len(docs) or 1
        self.avg_len = sum(d.length for d in docs) / self.n
        self.by_title: dict[str, Document] = {}
        for doc in docs:
            self.by_title.setdefault(doc.path.stem, doc)
            self.by_title.setdefault(doc.title, doc)

    def idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def score(self, doc: Document, terms: list[str]) -> float:
        total = 0.0
        for term in terms:
            tf = doc.tokens.get(term, 0)
            if not tf:
                continue
            norm = tf * (K1 + 1) / (tf + K1 * (1 - B + B * doc.length / self.avg_len))
            total += self.idf(term) * norm
        return total

    def search(self, query: str, k: int = 10, backlink_hop: bool = True,
               type_filter: str = "", domain_filter: str = "") -> list[tuple[Document, float, str]]:
        terms = tokenize(query)
        if not terms:
            return []

        direct = {d.relpath: self.score(d, terms) for d in self.docs}
        scores = {p: s for p, s in direct.items() if s > 0}

        if backlink_hop and scores:
            # Pull in neighbours of strong hits. The note you want often does not
            # contain your words; the note that links to it does.
            by_path = {d.relpath: d for d in self.docs}
            inbound: dict[str, float] = defaultdict(float)
            top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:10]
            for relpath, score in top:
                doc = by_path[relpath]
                for target in doc.links:
                    neighbour = self.by_title.get(target)
                    if neighbour and neighbour.relpath not in scores:
                        inbound[neighbour.relpath] = max(inbound[neighbour.relpath],
                                                         score * BACKLINK_WEIGHT)
                for other in self.docs:  # who links TO this hit
                    if doc.path.stem in other.links and other.relpath not in scores:
                        inbound[other.relpath] = max(inbound[other.relpath],
                                                     score * BACKLINK_WEIGHT)
            for relpath, score in inbound.items():
                scores[relpath] = score

        by_path = {d.relpath: d for d in self.docs}
        results = []
        for relpath, score in scores.items():
            doc = by_path[relpath]
            if type_filter and doc.type != type_filter:
                continue
            if domain_filter and doc.domain != domain_filter:
                continue
            why = "match" if direct.get(relpath, 0) > 0 else "linked from a match"
            results.append((doc, score, why))
        results.sort(key=lambda r: (-r[1], r[0].relpath))
        return results[:k]


def build(cfg: Config, include: list[str] | None = None) -> Index:
    import lint_frontmatter as linter
    docs = []
    for path in linter.iter_notes(cfg, include):
        relpath = path.relative_to(VAULT).as_posix()
        if path.name.startswith("_") or cfg.is_generated(relpath):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fm = fmlib.parse(text)
        docs.append(Document(path, relpath, fm, fm.body))
    return Index(docs)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("query")
    ap.add_argument("--k", type=int, default=0, help="results to return")
    ap.add_argument("--type", default="", help="only this note type")
    ap.add_argument("--domain", default="", help="only this domain")
    ap.add_argument("--no-hop", action="store_true", help="disable the backlink hop")
    ap.add_argument("--include-sources", action="store_true",
                    help="search raw sources too (default: compiled notes only)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    try:
        cfg = load()
    except ConfigError as e:
        print(f"ERROR  {e}", file=sys.stderr)
        return 2

    include = None
    if not args.include_sources:
        source_folder = cfg.types["source"].folder if "source" in cfg.types else None
        include = [d for d in cfg.content_dirs if d != source_folder]

    index = build(cfg, include)
    results = index.search(args.query, k=args.k or cfg.default_k,
                           backlink_hop=cfg.backlink_hop and not args.no_hop,
                           type_filter=args.type, domain_filter=args.domain)

    if args.json:
        print(json.dumps([{"path": d.relpath, "title": d.title, "type": d.type,
                           "domain": d.domain, "score": round(s, 3), "why": why,
                           "snippet": d.snippet}
                          for d, s, why in results], indent=2))
        return 0

    if not results:
        print(f"Nothing matches {args.query!r} in {len(index.docs)} note(s).")
        if index.docs:
            print("Try fewer or different words, or --include-sources.")
        return 0

    print(f"{len(results)} result(s) from {len(index.docs)} note(s):\n")
    for doc, score, why in results:
        meta = " · ".join(x for x in (doc.type, doc.domain) if x)
        print(f"{score:6.2f}  [[{doc.path.stem}]]  ({meta})")
        print(f"        {doc.relpath}" + (f"  — {why}" if why != "match" else ""))
        if doc.snippet:
            print(f"        {doc.snippet}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
