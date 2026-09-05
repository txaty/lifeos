---
type: area
title: "Fitness"
status: active
created: "2026-01-04"
updated: "2026-09-01"
domain: health
tags: [running, strength]
---

# Fitness

## Standard

Four sessions a week, most weeks. Sleep before training. Stop when something hurts
in a way that is sharp rather than tired.

## Current

Half marathon training is the whole of it right now. Strength work has quietly
dropped to zero, which is a known trade and not an accident.

## Tasks

- [ ] Put one strength session back in once the race is done

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

- Injury history lives here, not in a project: projects end, the body does not.
