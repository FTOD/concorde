---
name: speckit-concorde-ask
description: Answer a grounded, read-only question about Concorde
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: concorde:commands/speckit.concorde.ask.md
---

## User question

```text
$ARGUMENTS
```

# Ask Concorde

Answer from installed guidance and the smallest bounded project context. This surface is strictly
read-only: it does not invoke another lifecycle phase, change selection, write reflections, generate
projections, or edit any file.

## Source order

1. Read canonical installed extension guidance under `.specify/extensions/concorde/`, especially the
   manifest, README, and named command.
2. Read installed preset guidance under `.specify/presets/concorde/`, especially the manifest,
   README, relevant command, and template.
3. For a project-specific question, use `.concorde/config.json` and `.specify/feature.json` only to
   locate sources. Start with exactly one module's `architecture.md` or one direct `features/*.md` file:

   - module architecture owns responsibility, boundary, immediate module/feature inventory, typed
     entities, directed relationships, representative interactions, and diagram declarations;
   - the direct feature file owns outcome, scope, usage, requirements, embedded interfaces, failures,
     related-feature semantics, and Architecture Zoom; and
   - code/tests own implementation and executable evidence.

4. Follow bounded module ancestry or a related feature file only when the question requires that
   exact interface/relationship. Never read an unrelated feature body, descendant internals, or
   another feature's attempt merely because it exists.
5. Open `.concorde/reflections/log.md` only for questions about difficulties or provisional decisions
   met during work. It records tracked process memory, not required behavior.
6. Use generated pages, diagrams, indexes, and delivery results only as reproducible evidence or to
   locate their canonical sources.

## Answer format

Return a direct answer plus:

- `Basis`: distinguish framework rule, project observation, agent inference, and uncertainty; and
- `Sources`: project-relative paths for every installed-guidance or maintained-source fact used.

Name source kinds accurately: module architecture, direct feature file, source code, executable test,
temporal attempt, reflection log, or generated projection. When sources disagree, cite both and
describe the conflict. If the bounded sources do not support an answer, say so instead of relying on
model memory.