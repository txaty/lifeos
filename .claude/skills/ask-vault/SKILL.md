---
name: ask-vault
description: Answer a question from what the vault already knows, with citations, before going to the web. Use when the user asks "what do I know about X", "have I read anything on X", "what did I decide about X", or asks a question their notes might already answer.
---

# Ask the vault

The question a second brain exists to answer. Search it **before** searching the web — surprisingly
often the vault already knows, and finding out costs seconds.

**Inputs:** a question.
**Outputs:** an answer with citations; optionally a note in `outputs/answers/`.
**May modify:** `outputs/answers/` only, and only when the answer is worth keeping.

## Step 1 — Search

```
python3 scripts/retrieve.py "<the question>" --k 10
```

Narrow if the results are noisy:

```
python3 scripts/retrieve.py "<query>" --type wiki --domain health
python3 scripts/retrieve.py "<query>" --include-sources     # search raw sources too
```

Results marked `linked from a match` came in through the backlink hop — they did not contain the
words, but a neighbour did. Those are often the good ones.

## Step 2 — Read the top results

Open three to five. Do not read the whole vault; if retrieval did not surface it, say so rather than
grepping around to prove a negative.

For a question about a decision, go straight to `outputs/decisions/` — `## Context` and
`## Options` are the record of what was actually being weighed at the time.

## Step 3 — Answer

- **Cite every claim** with `[[Page]]`. An uncited claim in an answer is a guess wearing a citation's
  clothes.
- **Say what is missing.** "The vault has nothing on sleep" is a real and useful finding; a gap named
  is a gap that can be closed.
- **Surface disagreements** rather than resolving them. If a page has a `## Disagreements` section
  relevant to the question, the answer says both sides.
- Distinguish what the vault says from what you know generally. If you add outside knowledge, mark it
  as outside knowledge.

## Step 4 — File it, if it earns filing

An answer worth returning to:

```
python3 scripts/vault.py new answer "<Title>" \
    --set "query=<the question>" --set "sources_consulted=Page One, Page Two"
```

Then ask whether any *new, durable* insight should become a wiki page. Usually the answer is no —
restating what the vault already holds is the correct outcome for a question it already covers, and
saying so is more useful than manufacturing a page.
