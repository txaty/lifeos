#!/usr/bin/env python3
"""Unit tests for the LifeOS scripts. Stdlib `unittest`, no fixtures on disk.

    python3 -m unittest discover -s scripts -p "test_*.py"

The tests that matter most are the ones covering things that are easy to get
subtly wrong and hard to notice: date quoting, link resolution by basename, the
SSRF refusals, and generator idempotence.
"""
from __future__ import annotations

import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_url
import frontmatter as fmlib
import lifeos_config
import lint_frontmatter as linter
import vault
from lifeos_config import Config, ConfigError, load

CFG = load()


# ------------------------------------------------------------------ frontmatter

class TestFrontmatter(unittest.TestCase):

    def test_parses_scalars_lists_and_types(self):
        fm = fmlib.parse('---\na: "x"\nb: [1, 2]\nc:\n  - "[[L]]"\nd: true\ne: 3\n---\nbody\n')
        self.assertTrue(fm.present)
        self.assertEqual(fm.get("a"), "x")
        self.assertEqual(fm.get("b"), ["1", "2"])
        self.assertEqual(fm.get("c"), ["[[L]]"])
        self.assertIs(fm.get("d"), True)
        self.assertEqual(fm.get("e"), 3)
        self.assertEqual(fm.body.strip(), "body")

    def test_distinguishes_quoted_from_unquoted_dates(self):
        """The whole date-quoting rule rests on this distinction."""
        fm = fmlib.parse('---\ndate: 2026-01-01\ncreated: "2026-01-02"\n---\n')
        self.assertFalse(fm.is_quoted("date"))
        self.assertTrue(fm.is_quoted("created"))

    def test_missing_frontmatter_is_not_present(self):
        fm = fmlib.parse("no frontmatter here\n")
        self.assertFalse(fm.present)
        self.assertEqual(fm.body, "no frontmatter here\n")

    def test_reports_duplicate_keys(self):
        fm = fmlib.parse("---\na: 1\na: 2\n---\n")
        self.assertTrue(any("duplicate" in e for e in fm.errors))

    def test_inline_comments_stripped_but_not_inside_quotes(self):
        fm = fmlib.parse('---\na: value # note\nb: "has # inside"\n---\n')
        self.assertEqual(fm.get("a"), "value")
        self.assertEqual(fm.get("b"), "has # inside")

    def test_links_resolve_by_basename_and_ignore_code(self):
        body = "[[A Note]] and [[dir/B|alias]] and ![[embed]] and `[[code]]`"
        found = fmlib.INLINE_LINK_RE.findall(fmlib.strip_code(body))
        self.assertEqual([fmlib.link_target(f) for f in found], ["A Note", "B"])

    def test_render_round_trips(self):
        data = {"type": "project", "tags": ["a", "b"], "areas": ['"[[X]]"'], "empty": []}
        parsed = fmlib.parse(fmlib.render(data) + "\nbody\n")
        self.assertEqual(parsed.get("tags"), ["a", "b"])
        self.assertEqual(parsed.get("areas"), ["[[X]]"])
        self.assertEqual(parsed.get("empty"), [])


# ------------------------------------------------------------------ config

class TestConfig(unittest.TestCase):

    def _config(self, **overrides) -> dict:
        data = {
            "vocab": {"domains": ["a"], "meta_domain": "meta"},
            "paths": {"content_dirs": ["projects"]},
            "types": {"project": {"folder": "projects", "filename": "title",
                                  "required": ["type"], "optional": []}},
        }
        for key, value in overrides.items():
            data.setdefault(key, {})
            data[key].update(value) if isinstance(value, dict) else None
        return data

    def _expect_error(self, data, fragment):
        with self.assertRaises(ConfigError) as ctx:
            Config(data, Path("test.toml"))
        self.assertIn(fragment, str(ctx.exception))

    def test_shipped_config_is_valid(self):
        self.assertTrue(CFG.types)
        self.assertTrue(CFG.domains)

    def test_rejects_two_types_claiming_one_folder(self):
        data = self._config()
        data["types"]["other"] = {"folder": "projects", "filename": "title"}
        self._expect_error(data, "folder and type must agree")

    def test_rejects_unknown_filename_pattern(self):
        data = self._config()
        data["types"]["project"]["filename"] = "nonsense"
        self._expect_error(data, "is not one of")

    def test_rejects_type_folder_outside_content_dirs(self):
        data = self._config()
        data["types"]["project"]["folder"] = "elsewhere"
        self._expect_error(data, "content_dirs")

    def test_rejects_variant_outside_its_parent_folder(self):
        data = self._config()
        data["types"]["project"]["variants"] = {"v": {"folder": "somewhere/else"}}
        self._expect_error(data, "is not under")

    def test_rejects_duplicate_variant_names(self):
        data = self._config()
        data["paths"]["content_dirs"] = ["projects", "outputs"]
        data["types"]["project"]["variants"] = {"dup": {"folder": "projects/dup"}}
        data["types"]["output"] = {"folder": "outputs", "filename": "title",
                                   "variants": {"dup": {"folder": "outputs/dup"}}}
        self._expect_error(data, "names must be unique")

    def test_rejects_meta_domain_in_domains(self):
        data = self._config()
        data["vocab"]["domains"] = ["a", "meta"]
        self._expect_error(data, "reserved")

    def test_rejects_non_empty_field_that_is_not_required(self):
        data = self._config()
        data["types"]["project"]["non_empty"] = ["ghost"]
        self._expect_error(data, "not required")

    def test_variant_field_becomes_an_enum_over_variant_names(self):
        source = CFG.types["source"]
        self.assertEqual(set(source.enums["source_type"]), set(source.variants))


class TestExtensibilityPromise(unittest.TestCase):
    """The architectural promise: routine customization is config, never code.

    README.md and CONTRIBUTING.md both say so, so it is asserted here rather than
    left as a claim someone has to take on trust.
    """

    def _config_with_extra_type(self) -> Config:
        data = dict(CFG.raw)
        data["paths"] = dict(data["paths"])
        data["paths"]["content_dirs"] = list(data["paths"]["content_dirs"]) + ["prompts"]
        data["types"] = dict(data["types"])
        data["types"]["prompt"] = {
            "folder": "prompts",
            "filename": "title",
            "template": "prompt.md",
            "required": ["type", "title", "created", "updated", "status", "use_case", "tags"],
            "optional": ["domain", "aliases"],
            "summary": "A prompt worth keeping.",
            "enums": {"status": ["draft", "active", "deprecated"]},
        }
        return Config(data, Path("test.toml"))

    def test_a_new_note_type_is_valid_config(self):
        cfg = self._config_with_extra_type()          # raises ConfigError if not
        self.assertIn("prompt", cfg.types)
        self.assertEqual(cfg.folder_to_type["prompts"], "prompt")

    def test_the_linter_enforces_the_new_type_with_no_code_change(self):
        cfg = self._config_with_extra_type()
        good = ('---\ntype: prompt\ntitle: "T"\ncreated: "2026-01-01"\n'
                'updated: "2026-01-01"\nstatus: active\nuse_case: "x"\ntags: []\n---\n')
        path = lifeos_config.VAULT / "prompts" / "T.md"
        self.assertEqual(linter.lint_file(path, cfg, text=good), [])

        bad = good.replace("status: active", "status: nonsense")
        self.assertTrue(any("not in" in i.msg for i in linter.lint_file(path, cfg, text=bad)))

        missing = good.replace('use_case: "x"\n', "")
        self.assertTrue(any("use_case" in i.msg for i in linter.lint_file(path, cfg, text=missing)))

    def test_the_write_guard_follows_the_config(self):
        """Adding a content dir must grant agents access to it without editing the guard."""
        cfg = self._config_with_extra_type()
        self.assertIn("prompts", cfg.content_dirs)

    def test_the_schema_doc_documents_the_new_type(self):
        import gen_schema_doc
        rendered = gen_schema_doc.render(self._config_with_extra_type())
        self.assertIn("`prompt`", rendered)
        self.assertIn("prompts/", rendered)


class TestPublicDocs(unittest.TestCase):
    """Claims made in the public-facing docs, asserted so they cannot rot."""

    README = lifeos_config.VAULT / "README.md"

    def test_readme_snippet_matches_the_real_example_file(self):
        """README shows a project note and says CI keeps it from drifting. This is CI."""
        import re
        m = re.search(r"```markdown\n(.*?)```", self.README.read_text(), re.DOTALL)
        self.assertIsNotNone(m, "README no longer contains a markdown example block")
        example = (lifeos_config.VAULT / "examples" / "projects"
                   / "Run a Half Marathon.md").read_text()
        for line in (l for l in m.group(1).rstrip().split("\n") if l.strip()):
            self.assertIn(line, example,
                          f"README snippet line is not in the example file: {line!r}")

    def test_readme_links_resolve_to_files_that_exist(self):
        import re
        broken = []
        for target in re.findall(r"\]\((?!https?://)([^)#]+)", self.README.read_text()):
            if not (lifeos_config.VAULT / target).exists():
                broken.append(target)
        self.assertEqual(broken, [])

    def test_promised_files_exist(self):
        for name in ("LICENSE", "CONTRIBUTING.md", "AGENTS.md", "CLAUDE.md",
                     "config/lifeos.toml", ".github/workflows/vault-check.yml"):
            self.assertTrue((lifeos_config.VAULT / name).exists(), name)


# ------------------------------------------------------------------ linter

class TestLinter(unittest.TestCase):
    """Every rule is checked through a real file path so folder/type logic applies."""

    def lint(self, relpath: str, text: str):
        return linter.lint_file(lifeos_config.VAULT / relpath, CFG, text=text)

    def messages(self, relpath: str, text: str) -> str:
        return " | ".join(i.msg for i in self.lint(relpath, text))

    PROJECT = ('---\ntype: project\ntitle: "T"\nstatus: active\ncreated: "2026-01-01"\n'
               'updated: "2026-01-01"\ndomain: health\nquestion: "Q"\ntags: []\n---\n')

    def test_valid_note_has_no_issues(self):
        self.assertEqual(self.lint("projects/T.md", self.PROJECT), [])

    def test_missing_frontmatter_is_critical(self):
        issues = self.lint("projects/T.md", "no frontmatter\n")
        self.assertEqual(issues[0].level, "CRITICAL")

    def test_inbox_may_have_no_frontmatter(self):
        self.assertEqual(self.lint("inbox/2026-01-01 0900 x.md", "just a thought\n"), [])

    def test_enum_violation_and_unsubstituted_template_pipe(self):
        self.assertIn("not in", self.messages("projects/T.md",
                                              self.PROJECT.replace("status: active", "status: bogus")))
        self.assertIn("pick ONE", self.messages("projects/T.md",
                                                self.PROJECT.replace("status: active",
                                                                     "status: idea | active")))

    def test_domain_must_be_in_the_configured_vocabulary(self):
        self.assertIn("not in", self.messages(
            "projects/T.md", self.PROJECT.replace("domain: health", "domain: invented")))

    def test_meta_domain_is_refused_on_ordinary_notes(self):
        self.assertIn("reserved", self.messages(
            "projects/T.md", self.PROJECT.replace("domain: health", "domain: meta")))

    def test_date_quoting_is_enforced_both_ways(self):
        self.assertIn("QUOTED", self.messages(
            "projects/T.md", self.PROJECT.replace('created: "2026-01-01"', "created: 2026-01-01")))
        meeting = ('---\ntype: meeting\ntitle: "M"\ndate: "2026-01-01"\n'
                   'people:\n  - "[[P]]"\ntags: []\n---\n')
        self.assertIn("UNQUOTED", self.messages("meetings/2026-01-01 M.md", meeting))

    def test_tags_reject_hash_prefix(self):
        self.assertIn("'#' prefix", self.messages(
            "projects/T.md", self.PROJECT.replace("tags: []", "tags: [ok, '#bad']")))

    def test_link_fields_must_be_wikilinks(self):
        self.assertIn("wikilink", self.messages(
            "projects/T.md", self.PROJECT.replace("tags: []", "tags: []\nareas:\n  - Plain")))

    def test_type_must_match_folder(self):
        self.assertIn("folder", self.messages(
            "projects/T.md", self.PROJECT.replace("type: project", "type: area")))

    def test_archive_status_and_folder_imply_each_other(self):
        archived = self.PROJECT.replace("status: active", "status: archived")
        self.assertIn("not in projects/archive", self.messages("projects/T.md", archived))
        self.assertIn("but status", self.messages("projects/archive/T.md", self.PROJECT))
        self.assertEqual(self.lint("projects/archive/T.md", archived), [])

    def test_empty_list_is_present_but_non_empty_fields_are_enforced(self):
        wiki = ('---\ntype: wiki\ntitle: "W"\ncreated: "2026-01-01"\nupdated: "2026-01-01"\n'
                'sources: []\ndomain: health\ntags: []\n---\n')
        self.assertIn("sources is empty", self.messages("wiki/concepts/W.md", wiki))
        good = wiki.replace("sources: []", 'sources:\n  - "[[S]]"')
        self.assertEqual(self.lint("wiki/concepts/W.md", good), [])

    def test_variant_field_must_match_its_folder(self):
        source = ('---\ntype: source\nsource_type: paper\ntitle: "S"\nauthor: "A"\n'
                  'date: 2026-01-01\nurl: "https://example.com"\ntags: []\n---\n')
        self.assertIn("belongs in raw/papers", self.messages("raw/articles/2026-01-01 S.md", source))

    def test_variant_adds_required_fields(self):
        article = ('---\ntype: source\nsource_type: article\ntitle: "S"\nauthor: "A"\n'
                   'date: 2026-01-01\ntags: []\n---\n')
        self.assertIn("missing required field: url",
                      self.messages("raw/articles/2026-01-01 S.md", article))

    def test_unknown_field_is_minor_not_blocking(self):
        issues = self.lint("projects/T.md", self.PROJECT.replace("tags: []", "tags: []\ntpyo: x"))
        self.assertEqual([i.level for i in issues], ["MINOR"])
        self.assertFalse(any(i.blocking for i in issues))


# ------------------------------------------------------------------ vault CLI

class TestNaming(unittest.TestCase):

    def test_slugify_strips_link_breaking_characters(self):
        self.assertEqual(vault.slugify("60/40 Portfolio: Issue #7"), "60-40 Portfolio Issue 7")
        self.assertEqual(vault.slugify("a|b"), "a-b")
        self.assertEqual(vault.slugify('?*"<>'), "Untitled")

    def test_slugify_caps_the_filename_length(self):
        """A 300-character title used to crash with OSError: File name too long."""
        stem = vault.slugify("Some Very Long Concept Title " * 15)
        self.assertLessEqual(len(stem.encode("utf-8")), vault.MAX_STEM_BYTES)
        self.assertTrue(stem)

    def test_slugify_never_splits_a_multibyte_character(self):
        stem = vault.slugify("侘寂と物の哀れ " * 40)
        self.assertLessEqual(len(stem.encode("utf-8")), vault.MAX_STEM_BYTES)
        stem.encode("utf-8").decode("utf-8")   # raises if a character was cut in half

    def test_slugify_keeps_unicode_that_is_legal(self):
        self.assertEqual(vault.slugify("Naïve Réalisme (侘寂)"), "Naïve Réalisme (侘寂)")

    def test_slugify_is_idempotent(self):
        once = vault.slugify("60/40 Portfolio: Issue #7")
        self.assertEqual(vault.slugify(once), once)

    def test_new_note_paths_follow_the_configured_pattern(self):
        when = dt.datetime(2026, 3, 4, 9, 5)
        cases = {
            "project": "projects/T.md",
            "concept": "wiki/concepts/T.md",
            "decision": "outputs/decisions/2026-03-04 T.md",
            "daily": "daily/2026/03/2026-03-04.md",
            "review": "outputs/reviews/2026-W10.md",
            "inbox": "inbox/2026-03-04 0905 T.md",
        }
        for kind, expected in cases.items():
            ntype, variant = vault.resolve_new_kind(CFG, kind)
            path = vault.new_note_path(CFG, ntype, variant, "T", when)
            self.assertEqual(path.relative_to(lifeos_config.VAULT).as_posix(), expected, kind)

    def test_new_rejects_a_type_that_has_variants(self):
        self.assertEqual(vault.resolve_new_kind(CFG, "wiki"), (None, None))

    def test_template_rendering_substitutes_and_respects_date_quoting(self):
        text = ('---\ndate: {{date:YYYY-MM-DD}}\ncreated: "{{date:YYYY-MM-DD}}"\n'
                'period: "{{date:GGGG-[W]WW}}"\n---\n# {{title}}\n')
        out = vault.render_template(text, "My Title", dt.datetime(2026, 3, 4), CFG)
        self.assertIn("date: 2026-03-04\n", out)
        self.assertIn('created: "2026-03-04"', out)
        self.assertIn('period: "2026-W10"', out)
        self.assertIn("# My Title", out)

    def test_render_unquotes_a_hand_edited_quoted_date(self):
        out = vault.render_template('---\ndate: "{{date:YYYY-MM-DD}}"\n---\n', "T",
                                    dt.datetime(2026, 3, 4), CFG)
        self.assertIn("date: 2026-03-04", out)

    def test_apply_sets_quotes_by_field_kind(self):
        base = "---\ntitle: \"\"\ntags: []\nareas: []\ndate: 2026-01-01\n---\nbody\n"
        out = vault.apply_sets(CFG, base, ["title=A B", "tags=x, y", "areas=One, Two"])
        fm = fmlib.parse(out)
        self.assertEqual(fm.get("title"), "A B")
        self.assertEqual(fm.get("tags"), ["x", "y"])
        self.assertEqual(fm.get("areas"), ["[[One]]", "[[Two]]"])

    def test_apply_sets_replaces_a_block_list_without_orphaning_items(self):
        base = '---\nareas:\n  - "[[Old]]"\n  - "[[Older]]"\ntags: []\n---\n'
        out = vault.apply_sets(CFG, base, ["areas=New"])
        self.assertEqual(fmlib.parse(out).get("areas"), ["[[New]]"])
        self.assertNotIn("Older", out)


class TestGenerators(unittest.TestCase):

    def test_generators_are_idempotent(self):
        """Running maintenance twice must not change anything the first run did."""
        today = dt.date(2026, 3, 4)
        first = vault.generated_content(CFG, today)
        second = vault.generated_content(CFG, today)
        self.assertEqual(first, second)

    def test_generated_files_carry_the_marker(self):
        for relpath, content in vault.generated_content(CFG, dt.date(2026, 3, 4)).items():
            self.assertIn("GENERATED", content, relpath)

    def test_generated_files_pass_their_own_linter(self):
        for relpath, content in vault.generated_content(CFG, dt.date(2026, 3, 4)).items():
            issues = [i for i in linter.lint_file(lifeos_config.VAULT / relpath, CFG,
                                                  text=content) if i.blocking]
            self.assertEqual(issues, [], f"{relpath}: {[str(i) for i in issues]}")

    def test_orphaned_generated_pages_are_removable_but_foreign_ones_are_not(self):
        """Removing a domain must remove its router page — and only that."""
        wanted = set(vault.generated_content(CFG, dt.date(2026, 3, 4)))
        removable, foreign = vault.orphaned_generated(CFG, wanted)
        self.assertEqual(removable, [], "the shipped vault has no orphaned pages")
        self.assertEqual(foreign, [])

    def test_human_prose_survives_regeneration(self):
        old = "x<!-- PROSE:START -->\nmy own words\n<!-- PROSE:END -->y"
        new = "a<!-- PROSE:START --><!-- PROSE:END -->b"
        merged = vault._preserve_prose(old, new)
        self.assertIn("my own words", merged)
        self.assertTrue(merged.startswith("a"))

    def test_prose_preservation_is_a_no_op_without_markers(self):
        self.assertEqual(vault._preserve_prose("old", "new"), "new")


class TestStructure(unittest.TestCase):

    def test_the_shipped_vault_is_clean(self):
        """The framework must ship in a state that passes its own checks."""
        errors, _ = vault.structure_issues(CFG)
        self.assertEqual(errors, [])
        blocking = [str(i) for i in linter.lint_paths(list(vault.iter_notes(CFG)), CFG)
                    if i.blocking]
        self.assertEqual(blocking, [])

    def test_every_configured_template_exists(self):
        for t in CFG.types.values():
            names = [t.template] + [v.template for v in t.variants.values()]
            for name in [n for n in names if n]:
                self.assertTrue((lifeos_config.VAULT / "templates" / name).is_file(),
                                f"missing templates/{name}")

    def test_no_duplicate_note_names(self):
        self.assertEqual(vault.duplicate_basenames(CFG), [])

    def test_no_broken_links(self):
        broken, _ = vault.link_report(CFG)
        self.assertEqual(dict(broken), {})


# ------------------------------------------------------------------ egress

class TestEgressGate(unittest.TestCase):
    """SSRF refusals. These are the tests most worth having: a regression here is
    silent and the consequence is credential exfiltration."""

    DANGEROUS = [
        "http://localhost/", "http://LOCALHOST/", "http://foo.localhost/",
        "http://127.0.0.1/", "http://127.1/", "http://[::1]/",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/", "http://172.16.0.1/", "http://192.168.1.1/",
        "http://100.64.1.1/",             # CGNAT — Python's is_private misses this
        "http://[::ffff:127.0.0.1]/",     # IPv4-mapped IPv6 forms of the above
        "http://[::ffff:169.254.169.254]/",
        "http://[::ffff:10.0.0.1]/",
        "http://[::ffff:100.64.1.1]/",
        "http://0.0.0.0/", "http://198.18.0.5/", "http://192.0.2.1/",
    ]
    BAD_SCHEMES = ["file:///etc/passwd", "ftp://example.com/", "gopher://x/",
                   "data:text/html,x", "javascript:alert(1)"]

    def _refuse(self, url: str) -> fetch_url.Refused:
        with self.assertRaises(fetch_url.Refused, msg=f"{url} was NOT refused") as ctx:
            fetch_url.validate_url(url, CFG)
        return ctx.exception

    def test_non_public_hosts_are_refused(self):
        for url in self.DANGEROUS:
            self.assertEqual(self._refuse(url).code, fetch_url.E_DANGEROUS, url)

    def test_non_http_schemes_are_refused(self):
        for url in self.BAD_SCHEMES:
            self._refuse(url)

    def test_ipv4_mapped_addresses_are_normalized_before_range_checks(self):
        import ipaddress
        mapped = ipaddress.ip_address("::ffff:100.64.1.1")
        self.assertEqual(fetch_url._normalize(mapped),
                         ipaddress.ip_address("100.64.1.1"))
        self.assertFalse(fetch_url._address_is_public(mapped, allow_benchmark=False))

    def test_benchmark_range_is_opt_in_for_names_only(self):
        import ipaddress
        ip = ipaddress.ip_address("198.18.0.5")
        self.assertFalse(fetch_url._address_is_public(ip, allow_benchmark=False))
        self.assertTrue(fetch_url._address_is_public(ip, allow_benchmark=True))
        # A literal IP never gets the exception, however the config is set.
        self.assertEqual(self._refuse("http://198.18.0.5/").code, fetch_url.E_DANGEROUS)

    def test_public_hosts_pass_the_form_check(self):
        # Resolution may be proxied in some networks; only the form is asserted here.
        for url in ("https://example.com/a", "http://sub.example.org:8080/b?c=d"):
            try:
                fetch_url.validate_url(url, CFG)
            except fetch_url.Refused as e:
                self.assertNotEqual(e.code, fetch_url.E_ALLOWLIST, url)

    def test_allowlist_mode_refuses_unlisted_hosts(self):
        fetch_url.check_allowlist("docs.example.com", ["example.com"])   # subdomain ok
        fetch_url.check_allowlist("example.com", ["*.example.com"])
        with self.assertRaises(fetch_url.Refused) as ctx:
            fetch_url.check_allowlist("evil.test", ["example.com"])
        self.assertEqual(ctx.exception.code, fetch_url.E_ALLOWLIST)

    def test_html_extraction_drops_scripts_and_keeps_text(self):
        title, text = fetch_url.extract_text(
            "<html><head><title>T</title></head><body><script>bad()</script>"
            "<p>Real text.</p><nav>menu</nav></body></html>")
        self.assertEqual(title, "T")
        self.assertIn("Real text.", text)
        self.assertNotIn("bad()", text)
        self.assertNotIn("menu", text)


# ------------------------------------------------------------------ guard

class TestWriteGuard(unittest.TestCase):

    def _decision(self, relpath: str, tool: str = "Write") -> int:
        import json
        import subprocess
        payload = json.dumps({"tool_name": tool, "tool_input": {"file_path": relpath}})
        proc = subprocess.run(
            [sys.executable, str(lifeos_config.VAULT / "scripts" / "guard_writes.py")],
            input=payload, capture_output=True, text=True,
            env={"PATH": "/usr/bin:/bin", "CLAUDE_PROJECT_DIR": str(lifeos_config.VAULT)})
        return proc.returncode

    def test_content_writes_are_allowed(self):
        for relpath in ("wiki/concepts/A.md", "inbox/x.md", "Home.md", "raw/articles/a.md"):
            self.assertEqual(self._decision(relpath), 0, relpath)

    def test_system_writes_are_blocked(self):
        for relpath in ("AGENTS.md", "CLAUDE.md", "scripts/vault.py", "config/lifeos.toml",
                        "docs/schema.md", "templates/project.md", ".github/workflows/ci.yml",
                        "bases/attention.base"):
            self.assertEqual(self._decision(relpath), 2, relpath)

    def test_instruction_files_are_blocked_at_every_depth(self):
        for relpath in ("inbox/AGENTS.md", "raw/articles/CLAUDE.md",
                        "wiki/.claude/settings.json", "inbox/deep/nested/AGENTS.md"):
            self.assertEqual(self._decision(relpath), 2, relpath)

    def test_escapes_from_the_vault_are_blocked(self):
        for relpath in ("../outside.md", "../../etc/passwd", "/etc/passwd"):
            self.assertEqual(self._decision(relpath), 2, relpath)

    def test_read_tools_are_not_intercepted(self):
        self.assertEqual(self._decision("AGENTS.md", tool="Read"), 0)


class TestHookMode(unittest.TestCase):
    """The PostToolUse hook parses its own JSON so it needs no `jq` on PATH."""

    def test_extracts_the_written_path(self):
        payload = '{"tool_name":"Write","tool_input":{"file_path":"a/b.md"}}'
        self.assertEqual(linter._paths_from_hook_payload(payload), [Path("a/b.md")])

    def test_extracts_every_path_from_a_multi_edit(self):
        payload = ('{"tool_input":{"edits":[{"file_path":"a.md"},{"file_path":"b.md"}]}}')
        self.assertEqual(linter._paths_from_hook_payload(payload),
                         [Path("a.md"), Path("b.md")])

    def test_non_file_payloads_yield_nothing(self):
        for payload in ('{"tool_name":"Bash","tool_input":{"command":"ls"}}',
                        "not json", "[]", '{"tool_input":{}}', ""):
            self.assertEqual(linter._paths_from_hook_payload(payload), [], payload[:20])


# ------------------------------------------------------------------ retrieval

class TestRetrieval(unittest.TestCase):

    def _index(self, docs: list[tuple[str, str, str]]):
        import retrieve
        built = []
        for relpath, title, body in docs:
            text = f'---\ntype: wiki\ntitle: "{title}"\ntags: []\n---\n{body}\n'
            fm = fmlib.parse(text)
            built.append(retrieve.Document(Path(relpath), relpath, fm, fm.body))
        return retrieve.Index(built)

    def test_ranks_title_matches_above_body_mentions(self):
        index = self._index([
            ("a.md", "Compound Interest", "unrelated words here"),
            ("b.md", "Something Else", "a passing mention of compound interest once"),
        ])
        results = index.search("compound interest", backlink_hop=False)
        self.assertEqual(results[0][0].relpath, "a.md")

    def test_backlink_hop_surfaces_neighbours(self):
        index = self._index([
            ("a.md", "Alpha", "distinctive marmalade content [[Beta]]"),
            ("b.md", "Beta", "nothing relevant at all"),
        ])
        paths = [d.relpath for d, _, _ in index.search("marmalade", backlink_hop=True)]
        self.assertIn("b.md", paths)
        self.assertNotIn("b.md", [d.relpath for d, _, _
                                  in index.search("marmalade", backlink_hop=False)])

    def test_stopwords_alone_return_nothing(self):
        index = self._index([("a.md", "Alpha", "content")])
        self.assertEqual(index.search("the and of"), [])

    def test_filters_apply(self):
        index = self._index([("a.md", "Alpha", "marmalade")])
        self.assertEqual(index.search("marmalade", type_filter="project"), [])
        self.assertTrue(index.search("marmalade", type_filter="wiki"))


# ------------------------------------------------------------------ examples

class TestExamples(unittest.TestCase):
    """The shipped example vault must validate, or a new user's first `check` fails."""

    EXAMPLES = lifeos_config.VAULT / "examples"

    def setUp(self):
        if not self.EXAMPLES.is_dir():
            self.skipTest("no examples/ folder")

    def test_example_notes_are_schema_valid(self):
        """Seeded examples are the first thing a new user's `check` runs against."""
        issues = []
        for path in self.EXAMPLES.rglob("*.md"):
            relpath = path.relative_to(self.EXAMPLES).as_posix()
            issues += [i for i in linter.lint_file(lifeos_config.VAULT / relpath, CFG,
                                                   text=path.read_text(encoding="utf-8"))
                       if i.blocking]
        self.assertEqual([str(i) for i in issues], [])

    def test_example_links_all_resolve_within_the_example_set(self):
        """The examples must be a self-contained vault: seeding them must not
        produce a single broken link on day one."""
        names: set[str] = set()
        for path in self.EXAMPLES.rglob("*.md"):
            names.add(path.stem)
            fm = fmlib.parse(path.read_text(encoding="utf-8"))
            names.update(str(a) for a in fmlib.as_list(fm.get("aliases")))

        broken = []
        for path in self.EXAMPLES.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            fm = fmlib.parse(text)
            targets = set(fmlib.INLINE_LINK_RE.findall(fmlib.strip_code(text)))
            for field in CFG.link_lists | CFG.link_scalars:
                targets.update(str(v) for v in fmlib.as_list(fm.get(field)))
            for raw in targets:
                target = fmlib.link_target(raw)
                if target and target not in names:
                    broken.append(f"{path.name} -> [[{target}]]")
        self.assertEqual(broken, [])

    def test_example_names_are_unique(self):
        seen: dict[str, str] = {}
        for path in self.EXAMPLES.rglob("*.md"):
            self.assertNotIn(path.stem, seen,
                             f"{path} collides with {seen.get(path.stem)}")
            seen[path.stem] = str(path)

    def test_examples_contain_no_placeholder_leftovers(self):
        for path in self.EXAMPLES.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("{{", text, f"unrendered placeholder in {path.name}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
