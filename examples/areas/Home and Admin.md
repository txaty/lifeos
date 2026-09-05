---
type: area
title: "Home and Admin"
status: active
created: "2026-01-04"
updated: "2026-08-19"
domain: personal
tags: [admin]
---

# Home and Admin

## Standard

Nothing important expires unnoticed. The house works. Paperwork gets handled the
week it arrives, not the month.

## Current

Steady. Renewals are in the calendar, not in my head.

## Tasks

- [ ] Check the smoke alarm batteries

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
