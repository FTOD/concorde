---
name: concorde-tasks
description: "Generate dependency-ordered tasks for one Concorde attempt."
exposure: public
effects:
  reads:
    - selected-feature
    - module-architecture
    - module-ancestry
    - related-summaries
    - required-feature-specs
    - owned-implementation
    - attempt
    - checklists
    - constitution
    - reflections
    - framework
    - templates
  writes:
    - attempt
    - reflections
  network: false
  credentials: none
scripts:
  py: scripts/workspace.py --phase tasks
---

## User Input

```text
$ARGUMENTS
```

# Generate Concorde Tasks

Turn the selected plan into an executable, dependency-ordered, test-first checklist that reconciles
module architecture, feature file/interfaces, code, tests, and projections before delivery.

## Concorde Protocol evolution guard

Before workspace resolution or any write, if this is the Concorde repository and the requested work
changes normative Concorde Protocol semantics, stop without reading/writing an attempt or generating
tasks. Report the direct isolated-worktree route `feature.concorde.evolve-protocol`. A task set that
only restores already specified Protocol behavior remains normal lifecycle work.

## Workspace gate

Run `{SCRIPT}` first. Require Protocol 13 and a canonical selected feature. Use only returned
`feature_path`, `module_architecture`, bounded ancestry/related summaries, `executable_context`,
`attempt_dir`, `plan`, `tasks`, `research`, `data_model`, `quickstart`, `validation`,
`checklists_dir`, and `reflections`. Seed a missing returned tasks file through
`{FRAMEWORK}/templates/tasks-template.md`; never create a copy beside the feature file.

Read the complete feature file, module architecture, implementation plan, research/data model/
quickstart when present, and current code/test inventory. Related-feature summaries are navigation;
open a related feature file only when the plan names its interface as affected. Never inspect another
attempt.

## Task generation

1. Extract user stories/priorities, requirements, interface obligations, architecture entities and
   interactions, planned decisions, source/test paths, and runnable acceptance journeys.
2. Organize phases as Setup, Foundational, one phase per independently testable user story,
   Integration, and Polish/Delivery Readiness. Tests precede their implementation work.
3. Give every task one stable task ID and one requirement or acceptance-outcome trace, then use the
   exact format:

   ```text
   - [ ] T001 [P?] [US?] Action with exact project-relative path [FR-NNN or acceptance trace]
   ```

4. Mark `[P]` only when tasks touch different files and have no unmet dependency. Use story labels
   only inside story phases. Every task must be executable without rereading the conversation.
5. Include explicit tasks when the change affects:

   - a module architecture entity/type/locator, relationship, interaction, immediate module/feature
     inventory, or architecture-owned diagram;
   - a selected or named related feature's outcome, usage, embedded interface, failure behavior,
     requirements, or Architecture Zoom;
   - code and executable tests/evidence;
   - source/test interface fixtures, generated projections, public docs, manifests, or package
     freshness; or
   - deterministic validation and cleanup-only delivery eligibility.

6. Do not create standalone interface documents, feature wrapper directories, diagram sources beside a
   feature file, or prose implementation records. Architecture/feature-file edits are valid implementation
   tasks only when the plan names the owning change and the task carries its trace and tests.
7. For each affected module include its required Archify `architecture` system overview and trace
   entity/relationship changes into that view. For each created or changed architecture diagram include
   textual architecture parity, maintained source, normalized unique output check,
   `meta.quality_profile: showcase`, `meta.legend.mode: hidden`, nine-check Archify showcase validation,
   delivery/freshness, and publication evidence.
8. A setup mutation task must name its requirement/acceptance trace, detected tool, exact setup file,
   and authorized action. Detection alone is never a write authorization.
9. End each phase with a proportionate verification task where useful. Every completion task must
   require compact evidence in the returned `validation` file: task/trace, actual check, passed outcome,
   evidence path, scope, and limitation. Require the exact delivery-readable form:

   ```markdown
   - **T### · <trace>**
     - **Outcome**: passed|failed|skipped
     - **Check**: <actual command or check>
     - **Evidence**: <project-relative path or concise output>
     - **Scope**: <behavior or boundary proved>
     - **Limitation**: <material limit or none>
   ```

   The task boundary must be one unwrapped top-level line with no trailing prose. The nested
   `**Outcome**` field, not status wording in the boundary or narrative, is what delivery reads;
   only `passed` authorizes completion.

## Consistency and reflection recording

Check every requirement/interface/architecture change has task coverage, every task path is within
the user-authorized scope, dependencies are acyclic, and independently testable stories remain
independent. Planning and task generation are the normal points at which reflections are created.
Create one for a concrete contradiction, missing path authority, unsafe dependency, or tooling
problem encountered while decomposing the plan; do not use reflections as a second task backlog.

Inspect the per-file collection under the returned `reflections` directory first (its `pending/`,
`planned/`, and `needs-comments/` buckets). A repeated problem receives an `Occurrences` item in its
existing `R-NNN.md`, wherever it is filed. For a new problem, run `python3
{FRAMEWORK}/scripts/reflections_queue.py --allocate-id`, use only its `allocated_id`, never derive an
ID from existing files, and create exactly the returned `reflection_path` (always under
`pending/`) from `templates/reflections-template.md`. Use `phase: tasks`, `status: open`,
and `triage: pending`. Fill only Context, Expected, Observed, Impact, and Evidence, with enough
specific detail for later investigation. Do not analyze root cause, recommend a change, or decide
whether human intervention is needed. Omit `human_intervention`; leave Triage Analysis, Proposed
Resolution, and Intervention Rationale blank; and retain the blank `User Comments` section. Those
details and the intervention decision belong exclusively to `concorde-reflections-triage`. Do not
silently rewrite the feature file, architecture, plan, or code during task generation.
Immediately after creating the document or appending an occurrence, run `python3
{FRAMEWORK}/scripts/reflections_queue.py --validate-entry <id>`; correct only that new entry until
it reports `valid`. Findings on other entries are reported separately as unrelated and are not this
phase's to fix; a reserved ID stays retired even if the entry is abandoned.

Report total tasks by phase/story, parallel opportunities,
independent test criteria, MVP scope, and reflections added.
