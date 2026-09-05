---
name: concorde-plan
description: "Run permission-bounded context resolution and temporal plan authorship in order."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "operations/concorde-plan/SKILL.md"
  kind: "operation"
  exposure: "public"
  entrypoint: "operations/concorde-plan/operation.py"
user-invocable: true
disable-model-invocation: false
---
# Concorde Plan Operation

## Isolated worktree gate

After applying any Protocol-evolution guard, read-only inspection may remain in the primary
worktree. Before planning, selection persistence, attempt/checklist/reflection creation, an external
mutation, or any other write, unless the maintainer explicitly authorizes primary-worktree mutation
for this request, resolve only the primary worktree's committed `HEAD`, create a unique branch and
linked worktree at that exact commit, and continue the complete request there. If already in an
isolated worktree, stay there and do not create a nested worktree. Treat every staged, unstaged,
untracked, or ignored primary-worktree path as another programmer's state: never use it as input,
stash it, copy it, commit it, reset it, clean it, or otherwise import or alter it. If required input
is absent from committed `HEAD`, stop and report the missing input. The Tools' `--allow-primary-worktree` switch (or an embedding host's
`allow_primary_worktree` authority) is valid only after an explicit instruction to modify the primary worktree; a generic task request is
not that authorization. A non-Git checkout likewise requires explicit current-directory mutation
authorization.

## Concorde Protocol evolution guard

Before policy description, graph construction, workspace resolution, or any leaf invocation, if this
is the Concorde repository and the request changes normative Concorde Protocol semantics, stop. Do
not select a feature, create an attempt, or dispatch either internal leaf. Report the direct isolated-
worktree route `feature.concorde.evolve-protocol`. Planning that only restores already specified
Protocol behavior remains eligible.

## JSON invocation

Normalize the user's request into the runtime input type below. Load the complete
`operation_configuration` TypedValue from `.concorde/config.json`; do not choose integration or
enforcement separately for each call. If it is absent, use the `configure --propose/--apply` Tool
with explicit configuration JSON before running an Operation. In an installed project that Tool is
`python3 ./scripts/concorde.py configure`.

Write one invocation JSON document at a safe project-relative path in the authorized worktree:

```json
{
  "type_id": "concorde-operation-invocation",
  "schema_version": 1,
  "operation_id": "concorde-plan",
  "mode": "execute",
  "configuration": {
    "type_id": "concorde-operation-configuration",
    "schema_version": 1,
    "data": {"integration": "codex", "enforcement": "native"}
  },
  "input": {
  "type_id": "concorde-plan-context",
  "schema_version": 1,
  "data": {
    "feature_path": "specs/example/features/001-change.md",
    "request": "Plan the selected change",
    "constraints": [],
    "source_artifacts": []
  }
}
}
```

The example configuration must be replaced by the project's stored value. Use
`mode: "describe-policy"` to inspect the reachable launch policies without running a model or
changing project state; use `mode: "execute"` for actual work. Invoke the paired Python graph:

```bash
python3 scripts/run-operation.py operations/concorde-plan/operation.py < invocation.json
```

The script accepts one JSON document on stdin and writes one `concorde-operation-result@1`
envelope to stdout. Policy descriptions go to stderr. Check the exit code, `status`, `errors`, and
typed `output`; `described` is not execution success. Old positional requests, `--feature-path`,
`--integration`, and `--execute` are rejected. The managed launcher's `--runtime-check` is only a
transport diagnostic. Project root, worktree authority, framework root, executor, and policy remain
host-derived; a JSON field cannot authorize primary-worktree mutation or widen permissions.

The runtime owns graph dispatch, structured handoffs, validation, and evidence checks. Do not
manually rerun leaves after the graph or infer domain data from a completion summary. All nested
Operations inherit the same configuration snapshot. Stop on any failed or blocked result and
report its actual effects; a failure does not imply that earlier authorized writes were rolled back.

## Planning handoff

The public Operation has exactly `context -> author`. Its internal Skills are implementation
leaves, never alternative user entry points. `feature_path` must select an existing direct feature;
`request` states the change; `constraints` is a string array (default `[]`). Optional
`source_artifacts` contains verified `{id, path, digest}` references within the feature's admitted
source context or its selected reflection documents/plans. References never grant read authority.

The read-only context leaf receives `concorde-plan-context@1`. The host binds Workspace Protocol 13, then resolves and validates
`concorde-planning-context@1`; the author receives `concorde-plan-author-context@1` containing
both `task` and `planning_context`. The author may write only the selected attempt and authorized
reflection state. The host verifies source freshness and required `plan.md`/`tasks.md`, then returns
`concorde-plan-result@1` with the feature identity, attempt path, source digest, and artifact refs.
No provider implementation becomes readable merely because its feature provides an interface.
