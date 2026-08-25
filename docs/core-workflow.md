---
title: Core Workflow
sidebar_position: 6
---

# Core Workflow

Concorde wraps the normal Spec Kit lifecycle with architectural ownership, bounded context,
validation, and durable-design review. It does not replace specification, planning, tasks, or
implementation.

## 1. Establish the root architecture

Run the Concorde initialization command in a Spec Kit project. Review the proposed root module ID,
responsibility, top-level features, immediate submodules, boundary contracts, and one-level
architecture view. Concorde writes only after explicit approval.

The result establishes where architecture and nested feature specifications live; it is not a
complete decomposition of the future system.

## 2. Find the right ownership level

Request bounded context for the root or a child module. At each level, ask whether the desired
behavior belongs to the current module or one of its immediate children. Descend only when the next
level owns a meaningful boundary.

This decision determines where the feature workspace lives and which contracts its implementation
must respect.

## 3. Create or select the feature

Create the feature beneath its providing module, or select an existing feature by stable ID. The
feature root contains durable `spec.md` and `design.md`; Concorde records the active selection so
normal Spec Kit phases do not depend on a flat directory convention or branch name.

## 4. Specify behavior and representative scenarios

Use the normal specification, clarification, and checklist phases. Describe the feature in text:
actors, value, observable behavior, boundaries, failures, and measurable outcomes. Scenarios are
examples, not the exhaustive definition.

For cross-component behavior, add a core component-interaction view or state why the bounded module
view and prose are sufficient. Use supplemental sequence or workflow diagrams only when timing or
order adds information. Requirements-quality checklists belong to the temporary implementation
attempt.

## 5. Agree on architecture before planning code

Review the owning module, affected contracts, immediate participants, dependency direction, and
current-level architecture view. If the feature changes a boundary, update the architecture sources
as part of the same reviewed change.

This gate gives the coding agent freedom over code details without making module structure
accidental.

## 6. Plan and execute one implementation attempt

Normal planning reads both durable documents: `spec.md` for required behavior and `design.md` for the
accepted realization baseline. It writes research, plan, tasks, technical models, quick-start
instructions, checklists, and validation records under `implementation/`.

During implementation, provide only the selected feature, its owning module level, relevant
contracts, and necessary evidence. Use convergence and analysis to expose omissions rather than
silently changing intent to match the code.

## 7. Validate and reconcile

Run Concorde validation throughout the attempt. It checks stable identities, hierarchy, references,
contract declarations, views, scenario traces, evidence status, and freshness deterministically.

Validation reports disagreement or unknown evidence; it does not infer that code is correct merely
because it exists. Review behavioral, architectural, implementation, and evidence changes together.

## 8. Harden an accepted milestone

When all tasks and checklist items are complete and the user is satisfied, request feature
hardening. The agent synthesizes the accepted realization into a proposed `design.md`. The runtime
checks eligibility, binds the proposal to current source digests, and shows both the design update
and files to remove.

Explicit approval atomically promotes the design and removes the temporary implementation attempt.
If work is incomplete, sources changed after the proposal, or approval is absent, nothing is
applied.

## 9. Publish the read model

The docsite presents module and contract sources, feature specifications and accepted designs, and
hand-written guides in one read-only website. Publication is a projection: correct the canonical
source, rebuild, and never edit generated pages.

The [command reference](commands.md) maps these stages to installed commands. The canonical
[Feature 001 specification](../specs/concorde/features/001-concorde-starter-workflow/spec.md) defines
the complete workflow and acceptance criteria.
