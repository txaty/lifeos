# Security model

This vault reads untrusted third-party content using an agent that can write files. That is
Willison's "lethal trifecta" — untrusted input, plus the ability to act, plus access to private data
— and it is not a hypothetical here; it is the normal operating mode.

The defence is layered, cheapest and most reliable first. Every layer is deterministic code or a
structural property, because an instruction telling a model to be careful is the weakest control
available and the one most easily argued away by the content it is reading.

## Layer 0 — capability scoping

**Agent writes are confined to content folders.** A PreToolUse hook runs `scripts/guard_writes.py` on
every write, which allows the folders in `[paths].content_dirs` and refuses everything else:
`config/`, `docs/`, `scripts/`, `templates/`, `bases/`, `.github/`, and the guard itself.

**Instruction files are blocked at every depth**, not just at the root. `AGENTS.md`, `CLAUDE.md`,
`CLAUDE.local.md`, `.cursorrules`, and any `.claude/` or `.cursor/` directory are unwritable wherever
they appear. This is the non-obvious one: agents load nested instruction files on demand, so
`inbox/AGENTS.md` — a path an ingestion agent *can* otherwise write — would be a way for fetched
content to leave instructions for the next session. Blocking one level would be worse than useless,
because it would look like protection.

The guard reads only the destination path, never file content, so there is nothing in it for injected
text to influence. It fails **open** on a malformed hook payload — a weird message must not brick a
session — and fails **closed** on anything it can understand, which is the ratio that matters.

Deliberate human edits to system files need `LIFEOS_ALLOW_SYSTEM_WRITES=1` exported for that session.
Scheduled and unattended runs must never set it, and that is the single most important operational
rule in this document.

**Worst case after a successful injection:** attacker-chosen text sits in a local, git-tracked note.
No exfiltration channel, no self-modification, and a `git diff` that shows exactly what happened.

## Layer 1 — untrusted content stays data

Every fetched body is fenced with a per-run random nonce and framed explicitly as data
(`docs/ingestion.md`). The nonce is random per run so content cannot close its own fence.

**Trust order:** operator instructions > the existing vault > any source body. Applied at *both* the
extraction step and the compilation step — fencing one and not the other is theatre.

Injection attempts are logged under `## Injection attempts` in the run log and the run continues.
There is no blocking phrase-detector on purpose: legitimate writing about security contains every
phrase such a detector would look for, and a control that fires on good input gets disabled.

## Layer 2 — egress gating

`scripts/fetch_url.py` is the only sanctioned network access. It refuses:

- any scheme that is not `http`/`https` — no `file:`, `gopher:`, `data:`;
- loopback, private, link-local, multicast, reserved, and unspecified addresses;
- **CGNAT (`100.64.0.0/10`)** — Python's own `is_private` does not flag it, and it is where
  Tailscale and many ISPs put real private machines;
- the cloud metadata addresses, explicitly;
- documentation and benchmark ranges;
- IPv4-mapped IPv6 forms of all of the above — `::ffff:169.254.169.254` is the same address as
  `169.254.169.254`, and every range check normalizes before comparing;
- any host outside `publisher_allowlist` when `allowlist_only = true`.

**Every redirect hop is re-validated before it is followed.** A public URL that 302s to
`169.254.169.254` is the standard way a naive SSRF check is defeated, so redirects are handled
manually rather than by urllib.

**Known residual risk:** DNS rebinding between the check and the connection. Closing that needs
connection-level IP pinning, which urllib does not expose cleanly. The compensating control is Layer
0 — a rebind still only produces text in a git-tracked note.

Never fetch a URL discovered inside fetched content. That is the line between a tool and a crawler
an attacker can steer.

## Layer 3 — observability

Nothing is silently dropped. Every run writes `logs/YYYY-MM-DD-<run_type>.md` listing what was
written, what was skipped and why, and any injection attempts. `raw/` is append-only and git history
is reviewed by a human, so "what changed and when" always has an answer.

## Layer 4 — deterministic backstops

`lint_frontmatter.py`, `vault.py`, `guard_writes.py`, and the generators never interpret note content
as instructions. They read structure — paths, frontmatter keys, link targets. Combined with an
append-only `raw/`, a pre-commit hook, and CI, the mechanical layer keeps working even if a judgment
layer is compromised.

## The propose-only guardrail

Every consolidation, tidy, reflection, or instruction-evolution pass is **additive and propose-only**:
no deletes, no in-place overwrites, no auto-resolved `## Disagreements`, no auto-applied changes to
instructions. Proposals go in the run log for a human to apply.

This is a security control as much as a data-integrity one. It bounds the blast radius of a
compromised or simply mistaken run to "wrote a suggestion in a file", and it means an unattended
agent can never quietly restructure the vault.

## Local data hygiene

- `people/` and `meetings/` hold information about other people. Keep contact details minimal —
  this is a git repository, and history is forever.
- Never paste credentials into a note. If you catch yourself wanting to, the file belongs outside
  the vault. `.gitignore` refuses the obvious names as a backstop, not as a solution.
- If the vault lives in a cloud-synced folder, keep the retrieval index out of it:
  `export LIFEOS_INDEX_DIR=~/.cache/lifeos`. It is a rebuildable cache, and syncing it wastes
  bandwidth and invites conflicts.
- Think about whether the repository should be private before the first push. Almost always: yes.

## If you extend this

Adding a capability means re-asking the trifecta question: does this give an agent a new way to act
on untrusted input, or a new channel out? An MCP server with write tools, a shell escape, an email
sender, or a "just fetch this one extra URL" convenience are each enough on their own. Deny write
tools you do not need, and keep the number of doors small enough to count.
