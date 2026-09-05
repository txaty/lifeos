# Privacy audit

This framework was distilled from a working personal vault of ~3,800 notes. That vault is private
and stays private. This document records what was taken, what was deliberately not, and how that was
verified — so anyone reading this repository can see the provenance rather than take it on trust.

## What was extracted

**Architecture and mechanics only:**

- the information architecture and the storage-versus-navigation split
- the folder layout, note-type registry, and frontmatter schema
- naming conventions, linking rules, and lifecycle state machines
- the capture → route → compile → review loops
- the determinism boundary and which concerns sit on which side of it
- the three-tier agent instruction model
- the security model: write confinement, content spotlighting, egress gating
- validation, hooks, and CI structure
- the design decisions and the rejected alternatives, with their reasoning

## What was not

No content of any kind was copied. Specifically excluded: names, contacts, relationships, employers,
organizations, locations, financial or health information, project and area names, goals, daily
notes, meeting records, calendar and travel information, credentials, tokens, identifiers, real task
text, private URLs, and proprietary documents.

Files most likely to contain personal information were never read for content. The source's
`auth.json` was never opened. `people/`, `meetings/`, `daily/`, `inbox/`, `projects/`, `areas/`,
`outputs/`, and `logs/` were examined only as *shapes* — file counts, folder structure, frontmatter
keys — never as text. `raw/` and `wiki/` were sampled for schema structure only; even where their
subject matter is public knowledge, the *selection* reveals what someone cares about, so nothing was
carried across.

## Every example here is synthetic

The example vault in `examples/` was written for this repository. Its subject matter — distance
running, a woodworking project, a home media server — was chosen to be ordinary, useful for
demonstrating the mechanics, and unrelated to the source vault's actual domains.

The domain vocabulary shipped in `config/lifeos.toml` (`career`, `engineering`, `finance`, `health`,
`learning`, `personal`, `projects`, `world`) is a generic default constructed for this framework, not
the source's list.

## What the source's data changed, without appearing in the output

Usage statistics from the source vault — how many notes were in each folder, not what they said —
drove several removals recorded in [`decisions.md`](decisions.md): a four-way output split holding
six files, a four-way prompt library holding twelve, three source types holding none. Those are
counts, not content, and the resulting decisions are about structure. Nothing about the source's
subject matter is recoverable from them.

## Verification

Before release, the repository was checked for content originating in the source vault: personal and
organization names, the source's domain vocabulary, its project and area titles, its folder-specific
terminology, platform-specific pipeline names, real URLs, email addresses, credentials, and
absolute filesystem paths.

The one intentional retention is *attribution of ideas*: `decisions.md` credits the source vault for
choices it made well, in the same way any design document credits its influences. It does so without
naming the vault, its owner, or anything in it.

## If you fork this

Your notes become personal data the moment you write them. Before making a vault public:

- read `people/` and `meetings/` line by line — those two folders are where private information about
  *other people* accumulates, and they are the ones you will forget;
- check `git log -p` as well as the working tree, since history keeps what you deleted;
- confirm `.gitignore` still covers `auth.json`, `*.key`, `*.pem`, and `.env`;
- prefer a private repository. Almost nobody needs their second brain to be public, and the decision
  is very hard to reverse.
