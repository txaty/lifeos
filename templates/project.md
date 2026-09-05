---
type: project
title: "{{title}}"
status: idea
created: "{{date:YYYY-MM-DD}}"
updated: "{{date:YYYY-MM-DD}}"
domain: 
kind: build
question: ""
areas: []
tags: []
---

# {{title}}

> **question:** the one sentence this project answers, or the outcome it delivers.
> If you cannot write it, this is not a project yet — it is an idea or an area.

## Status

<!-- Where things stand and what happens next. If paused, what would unblock it. -->

## Scope

<!-- What is in, what is explicitly out, and how you will know it is done. -->

## Tasks

- [ ] 

## Log

<!-- Dated bullets, newest first. This is what you read when you return in March. -->

- {{date:YYYY-MM-DD}} — created

## Notes and sources

```base
filters:
  and:
    - contains(projects, link(this.file.path))
views:
  - type: table
    name: Attached
    order:
      - file.name
      - type
      - domain
      - date
```

## Findings

<!-- Your synthesis. Anything durable here should become a wiki page. -->

- 

## Outcome

<!-- Written when status becomes `done`: what shipped or was learned, and what you
     would do differently. An unfinished project with an honest outcome is a success. -->
