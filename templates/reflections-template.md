---
id: R-NNN
title: <short factual problem title>
phase: plan | tasks | implement | analyze | converge | fast-loop
date: YYYY-MM-DD
feature: <stable ID of the selected feature>
kind: specification | architecture | guidance | tooling | environment | implementation
concerns: <stable ID or project-relative path, optional #fragment or :line>
status: open
---

# R-NNN · <short factual problem title>

<!--
  Concorde Reflection Document v2. Canonical path: .concorde/reflections/<bucket>/R-NNN.md. The
  bucket directory is the only record of triage state: pending/ holds a document whose three triage
  sections are still empty, and planned/ or needs-comments/ hold a document whose three triage
  sections are filled, according to whether concorde-reflections-triage decided a developer must
  comment. Developer status never changes the bucket.

  Planning and task generation are the normal recording points. First reserve the identity through
  reflections_queue.py --allocate-id, then create exactly the returned reflection_path, which is
  always under pending/. Immediately after creating the document or appending an occurrence, run
  reflections_queue.py --validate-entry R-NNN and correct only that new entry until it reports valid.
  At recording time, describe only the problem in Context, Expected,
  Observed, Impact, and Evidence. Give enough detail for a later investigator to reproduce and
  understand it. Do not propose a fix and do not decide whether a developer is needed.

  Leave all three triage sections empty until concorde-reflections-triage investigates the
  reflection; never fill them in under pending/ by hand. Triage fills Triage Analysis, Proposed
  Resolution, and Intervention Rationale and moves the file into planned/ or needs-comments/ in one
  deterministic action; it never edits a bucketed document's sections in place. User Comments is
  always retained for developer input and may remain blank. A non-open status also requires a
  resolution_note in front matter; the close step then removes the document, and Git history
  keeps it.

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

<!-- Developer input when useful or requested. Do not remove this section. -->

## Occurrences

<!-- Optional. Use: - <phase> <YYYY-MM-DD> <feature-id> — <context and evidence> -->
