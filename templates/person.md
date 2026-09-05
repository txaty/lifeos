---
type: person
title: "{{title}}"
created: "{{date:YYYY-MM-DD}}"
updated: "{{date:YYYY-MM-DD}}"
tags: []
---

# {{title}}

<!-- People you actually interact with. Someone you only read about is a wiki
     entity instead. If both, set `entity: "[[Their Wiki Page]]"` above. -->

## Context

<!-- How you know them, and what they care about. -->

## Notes

<!-- Dated bullets. Keep contact details minimal — this file is in a git repo. -->

- {{date:YYYY-MM-DD}} — 

## Threads

```base
filters:
  and:
    - contains(people, link(this.file.path))
views:
  - type: table
    name: Meetings and notes
    order:
      - file.name
      - type
      - date
```
