---
name: concorde-reflections-triage
description: "Investigate and route project reflections through a controlled LangGraph Operation."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "operations/concorde-reflections-triage/SKILL.md"
  kind: "operation"
  exposure: "public"
  entrypoint: "operations/concorde-reflections-triage/operation.py"
user-invocable: true
disable-model-invocation: false
---
# Concorde Reflection Triage

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

Protocol: `reflection-triage/v5`; JSON Operation data version 1.

Use the paired graph at `python3 scripts/run-operation.py operations/concorde-reflections-triage/operation.py` as the stage topology authority. The graph composes direct leaf
Skills and the public nested planner; investigation executes as the read-only analyze leaf, and the trusted parent alone persists
its validated structured findings.

Shared configuration is `.concorde/reflections/config.json`; its configured `plans_dir` defaults to
`.concorde/reflections/plans/`. All stages stay in the action's existing isolated worktree. Use the
installed deterministic Tool at `.concorde/framework/scripts/reflections_queue.py`; in a source
checkout use `scripts/reflections_queue.py`. The tracked allocation high-water is
`.concorde/reflections/index.json`; each `.concorde/reflections/<bucket>/R-NNN.md` is the sole
persisted prose record for one reflection. Never edit maintainer-owned `status`, `resolution_note`,
or `User Comments` while triaging.

## Concorde Protocol evolution guard

Status is read-only and the investigation leaf is read-only, but its parent persists triage results; but before any `implement`, nested lifecycle, merge,
or close action whose resolution changes normative Concorde Protocol semantics in this repository,
stop without creating an attempt or implementation worktree. Report
`feature.concorde.evolve-protocol`; the maintainer resolves the reflection through one explicitly
authorized isolated Protocol cutover and Git history records its disposition.

## Bucket layout

Every reflection document lives in exactly one tracked bucket folder, and the folder is a pure
function of its triage front matter:

| Folder | Meaning | Front matter |
|---|---|---|
| `pending/` | recorded; triage has not investigated it | `triage: pending` |
| `planned/` | triaged; its plan may proceed without a maintainer | `triage: complete`, `human_intervention: not-required` |
| `needs-comments/` | triaged; waiting for maintainer input in `User Comments` | `triage: complete`, `human_intervention: required` |

Recording phases always create a document under `pending/` at the exact `reflection_path` returned
by `--allocate-id`. Only the deterministic helper moves files: after the parent persists a validated
triage completion it must run `reflections_queue.py --relocate R-NNN`, which moves the document into
the folder its new front matter requires without changing a byte of its text. No agent moves, copies,
or renames a reflection by hand. A document whose folder disagrees with its front matter is a
placement breach (`CONCORDE-REFLECT-005`); every helper action except `--relocate` refuses such a
collection, so run `--relocate` with no IDs to repair drift before continuing. Buckets only ever hold
open reflections: once a maintainer closes one (`status: resolved | dismissed` plus a
`resolution_note`), the `close` action removes its document together with its plan through
`--remove-closed`, and Git history keeps the record. No plan outlives its reflection; `status` lists
any orphan plan whose document is gone.

## Verification before every attempt

A reflection's real status is never read from a stored field; the acting agent re-establishes it
each time work on that reflection begins. Every `investigate` and every `implement` therefore
starts by re-verifying, against the current checkout HEAD, that the recorded Observed behavior
still occurs. The investigator records that check in the plan (`verified: <YYYY-MM-DD>`,
`verified_commit: <full HEAD commit ID>`, and a `## Verification` section naming the method and
outcome); the parent confirms `verified_commit` equals the HEAD the investigator ran against before
writing the plan; and the implementer repeats the check in its worktree before editing. The queue
Tool derives each plan's `verification` on every read as `current` (verified at HEAD), `stale`
(verified at another commit), `unverified`, or `unknown`; refuses `status=approved` or
`status=implemented` without a recorded verification; accepts `--set R-NNN verified=<date>
verified_commit=<HEAD>`; and accepts `status=stale` from `proposed`, `approved`, or `hold`. A
problem that no longer reproduces is never implemented: the investigator routes it to `dismiss`
with the verification as evidence, and the parent marks any stale plan `stale` and re-investigates
before any further attempt.

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
  "operation_id": "concorde-reflections-triage",
  "mode": "execute",
  "configuration": {
    "type_id": "concorde-operation-configuration",
    "schema_version": 1,
    "data": {"integration": "codex", "enforcement": "native"}
  },
  "input": {
  "type_id": "concorde-reflections-triage-context",
  "schema_version": 1,
  "data": {
    "action": "status",
    "reflection_ids": []
  }
}
}
```

The example configuration must be replaced by the project's stored value. Use
`mode: "describe-policy"` to inspect the reachable launch policies without running a model or
changing project state; use `mode: "execute"` for actual work. Invoke the paired Python graph:

```bash
python3 scripts/run-operation.py operations/concorde-reflections-triage/operation.py < invocation.json
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

## Actions

Choose exact IDs before dispatch; only `status` accepts an empty selection (the visible queue).
Do not parse action or route from a prose request inside the runtime.

| Action | Runtime fields beyond `action` and `reflection_ids` | Reachable capabilities and effects |
|---|---|---|
| `status` | None; task fields and route forbidden. | No model; returns per-record dispositions. Use the queue Tool's `--json` for counts and orphan-plan details. |
| `investigate` | Existing `feature_path`, `request`, optional `constraints`. | Analyze only, read-only. Parent validates and persists each finding, plan, and relocation. |
| `implement`, route `fast-loop` | Same task fields plus `route: "fast-loop"`. | Analyze, fast-loop, validate, then mark the verified plans implemented. |
| `implement`, route `plan` | Same task fields plus `route: "plan"`. | Analyze, public nested plan, tasks, implement, validate, then mark plans implemented. |
| `merge` | Existing `feature_path`, `request`, optional `constraints`. | Validate the integrated checkout, then remove only matching merged small fast-loop records through `--remove-merged`. Git integration and recorded canonical commit are prerequisites; the JSON invocation does not choose or merge branches. |
| `close` | None; task fields and route forbidden. | No model; remove exactly the named maintainer-closed records and plans through `--remove-closed`. |

Investigate/implement/merge selections must all belong to the selected feature. A zero-length
selection for a mutating action is rejected. `close` never changes maintainer disposition.

The analyze leaf receives `concorde-analyze-context@1`: the typed task, workspace identity,
captured HEAD, verification date, and selected reflection document/plan refs. Return exactly one
`concorde-reflection-investigation-result@1` finding per selected ID in Completion Envelope 2's
`domain_output`. Include verification, analysis, resolution, intervention rationale, route, effort,
files, steps, validation, risks, and `protocol_change`. The host rejects wrong IDs/HEAD, stale refs,
invalid sections, or protected Protocol changes before persistence. Original problem sections,
Occurrences, maintainer disposition, and User Comments are preserved. It alone writes the plan,
updates triage fields, calls `--relocate R-NNN`, and checks `--validate-entry R-NNN`.

A non-reproduced problem produces a stale dismissal plan requiring maintainer input and blocks
implementation. Required comments, a changed route, or an unapproved plan when the project sets
`require_approval` also stop all downstream nodes. Both routes must pass this gate; fast-loop
additionally requires small effort. Implementation runs under current selected-feature/task
permissions in the same isolated worktree, with no nested worktree or permission union.

For the plan route the parent copies task fields into `concorde-plan-context@1` and includes the
selected reflection documents and saved plans as `source_artifacts`. Later leaves receive freshly
verified refs too. The final `concorde-reflections-triage-result@1` covers exactly the selected IDs;
optional `plan_result` is included only while its attempt exists and admitted durable sources remain
current. The result never serializes private planner traces into a text field.

## Triage completion boundary

Recording phases deliberately leave `triage: pending`, omit `human_intervention`, and leave Triage
Analysis, Proposed Resolution, and Intervention Rationale empty. Triage is the only workflow that may
complete them. Investigation must establish root cause with concrete evidence, propose the smallest
appropriate resolution, choose exactly one route, decide `human_intervention: required |
not-required`, and explain that decision. Set `triage: complete` only when all of those details are
present and the plan agrees with them. Preserve the original Context, Expected, Observed, Impact,
Evidence, and all Occurrences. Never fill or remove `User Comments`; it remains available for the
maintainer when intervention is required. Relocation is the final step of completion: a reflection
that keeps `triage: pending` stays under `pending/`, and a completed one is moved by the helper,
never by hand.

The parent remains the only plan-file and triage-completion writer and the only caller of
`--relocate`. Never run parallel implementers in one worktree or any implementer in the primary
checkout without the explicit override, never change maintainer
disposition, and never maintain a second integration-specific queue.
