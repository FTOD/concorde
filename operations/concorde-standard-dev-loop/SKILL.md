---
name: concorde-standard-dev-loop
description: Run the standard Concorde development loop as a controlled LangGraph Operation.
exposure: public
operation: operation.py
capabilities:
  - concorde-specify
  - concorde-plan
  - concorde-tasks
  - concorde-implement
  - concorde-validate
  - concorde-deliver
---

# Concorde Standard Development Loop

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

Before graph construction, workspace resolution, or any direct/nested capability invocation, if this
is the Concorde repository and the request changes normative Concorde Protocol semantics, stop with
no completed prefix and no selection/attempt mutation. Report `feature.concorde.evolve-protocol` and
its direct isolated-worktree cutover. A change that only restores already specified Protocol behavior
remains normal standard-loop work.

## JSON invocation

Normalize the user's request into the runtime input type below. Load the complete
`operation_configuration` TypedValue from `.concorde/config.json`; do not choose integration or
enforcement separately for each call. If it is absent, use the `configure --propose/--apply` Tool
with explicit configuration JSON before running an Operation. In an installed project that Tool is
`python3 {FRAMEWORK}/scripts/concorde.py configure`.

Write one invocation JSON document at a safe project-relative path in the authorized worktree:

```json
{
  "type_id": "concorde-operation-invocation",
  "schema_version": 1,
  "operation_id": "concorde-standard-dev-loop",
  "mode": "execute",
  "configuration": {
    "type_id": "concorde-operation-configuration",
    "schema_version": 1,
    "data": {"integration": "codex", "enforcement": "native"}
  },
  "input": {
  "type_id": "concorde-standard-dev-loop-context",
  "schema_version": 1,
  "data": {
    "feature_path": "specs/example/features/001-change.md",
    "request": "Implement the selected change",
    "constraints": []
  }
}
}
```

The example configuration must be replaced by the project's stored value. Use
`mode: "describe-policy"` to inspect the reachable launch policies without running a model or
changing project state; use `mode: "execute"` for actual work. Invoke the paired Python graph:

```bash
{OPERATION} < invocation.json
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

## Development graph

The fixed stages and direct capabilities are:

1. `specify`: `concorde-specify`.
2. `plan`: public nested Operation `concorde-plan`.
3. `tasks`: `concorde-tasks`, then `concorde-implement`.
4. `deliver`: `concorde-validate`, then `concorde-deliver`.

`feature_path` must identify an existing canonical direct feature before the first stage. To create a
new feature, invoke `concorde-specify` independently, complete its post-front-matter workspace
resolution, and then invoke this Operation with the resulting path. The Operation's specify stage
reviews or revises that selected feature; it never treats a missing path as an implicit creation
request. The host copies `feature_path`, `request`, and `constraints` into the nested plan context, verifies
the returned feature identity/source digest/artifacts, and supplies each following leaf with a
fixed typed context and current artifact digests. Every leaf has a separate immutable launch policy.
The outer graph sees one plan result, while the inner Operation alone owns its context/author leaves.

Validation includes the deterministic architecture Tool. Delivery is admitted only by an eligible
Delivery Proposal 9; success additionally requires the selected attempt to be removed and retained
source/executable digests to remain unchanged. The terminal `concorde-standard-dev-loop-result@1`
records all six direct capabilities and this verified cleanup outcome.
