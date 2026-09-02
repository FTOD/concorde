---
name: concorde-tasks
description: "Generate dependency-ordered tasks for one Concorde attempt."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-tasks/SKILL.md"
  kind: "skill"
user-invocable: true
disable-model-invocation: false
---
## User Input

```text
$ARGUMENTS
```

# Generate Concorde Tasks

Turn the selected plan into an executable, dependency-ordered, test-first checklist that reconciles
module architecture, feature file/interfaces, code, tests, and projections before delivery.

## Workspace gate

Run `python3 scripts/workspace.py --phase tasks` first. Require Protocol 13 and a canonical selected feature. Use only returned
`feature_path`, `module_architecture`, bounded ancestry/related summaries, `executable_context`,
`attempt_dir`, `plan`, `tasks`, `research`, `data_model`, `quickstart`, `validation`,
`checklists_dir`, and `reflections`. Seed a missing returned tasks file through
`./templates/tasks-template.md`; never create a copy beside the feature file.

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
   evidence path, scope, and limitation.

## Consistency and reflections

Check every requirement/interface/architecture change has task coverage, every task path is within
the user-authorized scope, dependencies are acyclic, and independently testable stories remain
independent. Record contradictions, missing path authority, workarounds, or provisional choices in
the project reflection log with `Phase: tasks`. Before appending a new entry, run the installed
`python3 ./scripts/reflections_queue.py --allocate-id`, use only its
`allocated_id`, and never derive an ID from the remaining log entries; update an existing occurrence
without allocating or duplicating an entry. Do not silently rewrite the feature file, architecture,
plan, or code during task generation.

Report total tasks by phase/story, parallel opportunities,
independent test criteria, MVP scope, and reflections added.
