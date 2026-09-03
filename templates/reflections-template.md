---
id: R-NNN
title: <short factual problem title>
phase: plan | tasks | implement | analyze | converge | fast-loop
date: YYYY-MM-DD
feature: <stable ID of the selected feature>
kind: specification | architecture | guidance | tooling | environment | implementation
concerns: <stable ID or project-relative path, optional #fragment or :line>
status: open
triage: pending
---

# R-NNN · <short factual problem title>

<!--
  Concorde Reflection Document v2. Canonical path: .concorde/reflections/<bucket>/R-NNN.md, where
  <bucket> mirrors triage state: pending/ (triage: pending), planned/ (triage: complete and
  human_intervention: not-required), or needs-comments/ (triage: complete and human_intervention:
  required). Maintainer status never changes the bucket.

  Planning and task generation are the normal recording points. First reserve the identity through
  reflections_queue.py --allocate-id, then create exactly the returned reflection_path, which is
  always under pending/. At recording time, describe only the problem in Context, Expected,
  Observed, Impact, and Evidence. Give enough detail for a later investigator to reproduce and
  understand it. Do not propose a fix and do not decide whether a maintainer is needed.

  Keep triage: pending, omit human_intervention, and leave all three triage sections empty until
  concorde-reflections-triage investigates the reflection. Triage changes triage to complete, adds
  human_intervention: required | not-required, fills all three triage sections, and then moves the
  file with reflections_queue.py --relocate R-NNN; never move it by hand. User Comments is always
  retained for maintainer input and may remain blank. A non-open status also requires a
  resolution_note in front matter.

  index.json contains only {"schema_version": 1, "high_water": "R-NNN"}; it never contains
  reflection prose. Identifiers are permanent and never reused. On re-encounter, add an Occurrences
  item to the existing document instead of creating a duplicate. Never copy reflection prose into an
  attempt, feature, architecture, plan, task list, code, test, diagram, or generated artifact.
-->

## Context

<What work was underway, the relevant boundary, and the conditions in which the problem appeared.>

## Expected

<What the named authority, contract, tool, or environment led the agent to expect.>

## Observed

<What actually happened, including the important disagreement or missing information.>

## Impact

<How the problem affected planning or task generation, including any bounded assumption, workaround,
deferral, or stop. This describes the effect; it does not recommend a solution.>

## Evidence

<Project-relative paths, stable IDs, commands, concise outputs, and reproduction details. Link to
evidence rather than pasting secrets or bulk output.>

## Triage Analysis

<!-- Filled only by reflection triage. -->

## Proposed Resolution

<!-- Filled only by reflection triage. -->

## Intervention Rationale

<!-- Filled only by reflection triage after deciding whether human intervention is required. -->

## User Comments

<!-- Maintainer input when useful or requested. Do not remove this section. -->

## Occurrences

<!-- Optional. Use: - <phase> <YYYY-MM-DD> <feature-id> — <context and evidence> -->
