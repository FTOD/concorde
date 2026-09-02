---
name: speckit-concorde-ask
description: "Answer a grounded, read-only question about Concorde"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "commands/speckit.concorde.ask.md"
---
# Speckit Concorde Ask

## User question

```text
$ARGUMENTS
```

# Ask Concorde

Answer from installed guidance and the smallest bounded project context. This surface is strictly
read-only: it does not invoke another lifecycle phase, change selection, write reflections, generate
projections, or edit any file.

## Source order

1. Read `./concorde.json`, the relevant file under `./commands/`, and any
   directly referenced format file under `./templates/`.
2. For a project-specific question, use `.concorde/config.json` and `.concorde/feature.json` only to
   locate sources. Start with exactly one module's `architecture.md` or one direct `features/*.md` file:

   - module architecture owns responsibility, boundary, immediate module/feature inventory, typed
     entities, directed relationships, representative interactions, and diagram declarations;
   - the direct feature file owns outcome, scope, usage, requirements, embedded interfaces, failures,
     related-feature semantics, and Architecture Zoom; and
   - code/tests own implementation and executable evidence.

3. Follow bounded module ancestry or a related feature file only when the question requires that
   exact interface/relationship. Never read an unrelated feature body, descendant internals, or
   another feature's attempt merely because it exists.
4. Open `.concorde/reflections/log.md` only for questions about difficulties or provisional decisions
   met during work. It records tracked process memory, not required behavior.
5. Use generated pages, diagrams, indexes, and delivery results only as reproducible evidence or to
   locate their canonical sources.

## Answer format

Return a direct answer plus:

- `Basis`: distinguish framework rule, project observation, agent inference, and uncertainty; and
- `Sources`: project-relative paths for every installed-guidance or maintained-source fact used.

Name source kinds accurately: module architecture, direct feature file, source code, executable test,
temporal attempt, reflection log, or generated projection. When sources disagree, cite both and
describe the conflict. If the bounded sources do not support an answer, say so instead of relying on
model memory.
