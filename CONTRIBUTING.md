# Contributing

The intended use of this repository is to **fork it and make it yours**. A second brain is personal;
a framework that tries to be everyone's ends up being nobody's. So the most useful thing you can do
is adapt it, and tell me where it fought you.

## The one rule that shapes everything

**Routine changes should never require editing `scripts/`.**

Adding a note type, a source type, a field, a domain, or a folder is a `config/lifeos.toml` edit plus
a template. [`docs/customization.md`](docs/customization.md) has worked examples, and there is a test
asserting that a complete new note type needs no code change.

If you hit something that forces you into `scripts/`, that is the interesting bug. Please open an
issue saying what you were trying to model — that is more valuable than a patch, because the fix is
usually to make the config express it rather than to add a special case.

## Good issues

- "I tried to model X and the config could not express it."
- "The setup failed on <OS / Python version> with <error>."
- "The routing tree gave me no good answer for <thing>, or two equally good ones."
- "A doc claims something the code does not do." — these are the highest priority, because the whole
  design rests on documentation and enforcement agreeing.

## Less useful

- Adding a note type to the default config. The default set is deliberately small; if your type is
  genuinely universal, argue for it in an issue first, with the reason it clears the bar in
  [`docs/decisions.md`](docs/decisions.md).
- Re-adding something the ADR rejected, without engaging with why it was rejected and what it costs.
- Anything that adds a runtime dependency. Zero-dependency is a feature, not an oversight.

## If you send a patch

```bash
python3 -m unittest discover -s scripts -p "test_*.py"
python3 scripts/vault.py docs      # regenerate docs/schema.md if you touched the config
python3 scripts/vault.py check
```

All three run in CI, and the second one matters: `docs/schema.md` is generated, so a config change
with a stale doc will fail.

For anything structural, add an entry to [`docs/decisions.md`](docs/decisions.md) saying what you
decided, why, and **what it costs**. The cost is the part that tells future readers whether the
trade still holds; a decision with no stated cost usually was not one.

## Security

If you find a way to get an agent to write outside the content folders, escape the egress gate, or
get untrusted content treated as instructions, please report it privately via a GitHub security
advisory rather than a public issue. [`docs/security.md`](docs/security.md) describes the model,
including the residual risks it does not close.
