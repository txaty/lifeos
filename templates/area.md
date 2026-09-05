---
type: area
title: "{{title}}"
status: active
created: "{{date:YYYY-MM-DD}}"
updated: "{{date:YYYY-MM-DD}}"
domain: 
tags: []
---

# {{title}}

> An area is a standing responsibility with **no end date**. If it can be finished,
> it is a project. Keep areas under about ten; more than that and none get attention.

## Standard

<!-- What "kept up" looks like here. The bar you are holding yourself to. -->

## Current

<!-- Where this stands right now. Rewrite in place; this is not a log. -->

## Tasks

- [ ] 

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

- 
