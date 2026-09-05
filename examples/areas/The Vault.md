---
type: area
title: "The Vault"
status: active
created: "2026-01-04"
updated: "2026-09-01"
domain: personal
tags: [meta, productivity]
---

# The Vault

## Standard

The inbox empties weekly. `python3 scripts/vault.py check` passes. Every source I
keep is either cited by a page or deleted. The system serves the work; when it
starts generating work of its own, something gets removed.

## Current

Healthy. The weekly review is the only ritual that has survived, which is the
evidence that it is the only one worth having.

## Tasks

- [ ] Re-read [[Weekly Review Practice]] once a quarter and delete a rule

## Projects

```base
filters:
  and:
    - type == "project"
    - contains(areas, link(this.file.path))
views:
  - type: table
    name: Projects
    order:
      - file.name
      - status
      - question
      - updated
```

## Notes

- The vault itself is an area, not a project: it is never finished.
