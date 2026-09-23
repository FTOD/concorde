# Validation interface

This document gives the exact request, flow, recorded evidence, completion contract and gate table
of [Validation](module.md).

## Request and workspace

`concorde-validate` takes `target_id` and `task`, and optionally `focus_id`, `constraints`,
`change_id` and `run_checks` (boolean, default `true`). Its response is the common capability
response; `checks` holds the check results of this run and `outcome` is `failed`, `ready` or
`completed`.

The capability declaration states that the request mutates the change status, needs an existing
change and never gets a new candidate:

| Started in | `change_id` | What happens |
| --- | --- | --- |
| a candidate with a bound change | absent or equal to the bound change | runs in that candidate |
| a candidate with a bound change | another change | refused with `incompatible_handoff` |
| a linked worktree without a bound change | any | refused with `missing_change` |
| the primary worktree | names a change with a live candidate | relayed into that candidate |
| the primary worktree | absent, or names no live candidate | refused with `missing_change`; nothing is created |

## Flow

1. Record the change's phase as `validate` with status `active`, withdrawing any earlier ready state
   and validated tree.
2. Confirm pending realization entries whose files exist, as one file transaction bound to the
   digests of the metadata members it replaces, and reload the Specs. A stale transaction stops
   with `stale_proposal`.
3. Snapshot the candidate's deliverable tree.
4. Validate the project's Specs for the target Module, including Spec tooling's check that every
   explicit input of a configured check exists and is a regular file or directory reached without a
   symbolic link. On any error, mark the change `blocked` with outcome `invalid_spec`, mark a
   planned target's progress entry `blocked`, and answer `failed`; errors about check inputs are
   quoted in the answer with the check, its Module and the path, and no check runs.
5. Select the checked Modules: every Module for a direct candidate, otherwise the target's affected
   Modules (below). Record their Spec and implementation revisions.
6. With `run_checks`, have Check execution run the configured checks of each checked Module, in
   registry order.
7. For a planned target, store the check results, the affected revisions and the Spec source digest
   in the target's progress entry.
8. If any result is not `passed`, mark the change `blocked` with outcome `failed_checks`, mark a
   planned target's progress entry `blocked`, and answer `failed`.
9. Compare the deliverable tree and the affected revisions with those of steps 3 and 5. A difference
   stops with `stale_evidence`.
10. A direct candidate stores its evidence in Validation's section of the change status and
    proceeds to readiness. A planned target proceeds to readiness when all its accepted tasks are
    complete; otherwise the answer is `completed` with the note that semantic completeness is not
    proven.
11. Readiness runs the completion check, confirms the tree is unchanged (`stale_evidence`), sets the
    target's progress entry and the change to `ready`, and records the validated tree.

Steps 1 and 11 change the change's own lifecycle only for a request of the Module the change is
about; a component request of another Module records only its progress entry.

## Affected and edited Modules

For target Module T of change C:

```text
edited(C)    = { owner(D) : a reading or metadata member of document D differs }
             ∪ { M : M binds a path that differs }
               over the paths that differ between C.base_commit and C's deliverable tree
seed(T, C)   = {T} ∪ edited(C)   when T is C's recorded target, otherwise {T}
affected(T)  = ⋃ { binders(M) : M ∈ seed(T, C) }
binders(M)   = {M} ∪ { N : N binds a file in M's implementation scope }
```

The deliverable tree excludes the local control paths and the Host's worktree guidance, so they
edit no Module. A direct candidate checks every Module of the project instead.

## Recorded evidence

A planned target's progress entry holds, after validation:

| Field | Meaning |
| --- | --- |
| `checks` | the check results of this run, one per configured check of every affected Module |
| `implementation_impacts` | `{target_id, spec_digest, implementation_digest}` of every affected Module |
| `validation_spec_digest` | digest of the Spec sources the structural validation examined |
| `phase`, `status` | `validate` and `active`, `blocked` or `ready` |

Validation keeps its own records in its provider section `validation` of the change status, a
typed value `concorde-validation-records@1` whose `data` is `{validated_tree, evidence}`. For a
direct candidate `evidence` holds `target_id`, `focus_id`, `task`, `constraints`, `spec_digest`
(the target's Spec revision), `source_digest` (the Spec sources digest) and `checks`;
`validated_tree` is the deliverable tree recorded when the change became ready, or null. A
planned target's progress entry belongs to Planning's section and is updated through Planning.

A Module's Spec revision is the digest of its record, the bound Protocol and its resolved Spec
context; its implementation revision is the digest of its realization entries and of the bytes of
every file they currently bind.

## Completion contract

The completion check is the gate that Validation's readiness step and Delivery share. It runs in
the candidate worktree, starts no worker, runs no configured check and writes nothing. It evaluates
the conditions of the gate table in order and stops at the first that is not met.

```concorde-contract
{
  "id": "contract.validation.completion",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["request", "answer"],
    "properties": {
      "request": {
        "type": "object",
        "additionalProperties": false,
        "required": ["change_id", "target_id", "task", "constraints"],
        "properties": {
          "change_id": {"type": "string", "minLength": 1},
          "target_id": {"type": "string", "minLength": 1},
          "focus_id": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
          "task": {"type": "string", "minLength": 1},
          "constraints": {"type": "array", "items": {"type": "string", "minLength": 1}}
        }
      },
      "answer": {
        "type": "object",
        "additionalProperties": false,
        "required": ["complete", "code", "checks"],
        "properties": {
          "complete": {"type": "boolean"},
          "code": {
            "anyOf": [
              {"type": "null"},
              {"enum": ["review_required", "spec_incomplete", "stale_evidence", "stale_context",
                        "incompatible_handoff", "incomplete_change"]}
            ]
          },
          "checks": {"type": "array", "items": {"type": "object"}}
        }
      }
    }
  },
  "semantics": "Decide whether one Module's part of an existing change is complete for the candidate's current bytes. request names the change and the Module part to check: target_id with the focus_id, task and constraints recorded for it. The check reads the change status, the recorded evidence and the candidate's current files; it starts no worker, runs no configured check and writes nothing. answer.complete is true only when every condition of the gate table holds; code is then null and checks are the recorded check results that satisfied the gate, each a Check execution check result. Otherwise complete is false, checks is empty and code is the code of the first unmet condition, or the code a failing component answered. The same request against unchanged bytes and records always gives the same answer.",
  "example": {
    "request": {
      "change_id": "change.8f14e45f-ceea-467a-9575-7f1d1e2c3a4b",
      "target_id": "module.transfer",
      "focus_id": null,
      "task": "Stop transfer retries after three failures",
      "constraints": []
    },
    "answer": {
      "complete": false,
      "code": "review_required",
      "checks": []
    }
  }
}
```

In the Host the answer is carried as the check's return value on success and as an error with the
same code on failure; a caller that receives an error treats it as `complete: false`.

## Gate table

| Condition | Code |
| --- | --- |
| every required review of the change, with its consumers and components, is current | `review_required` |
| no open Blocker exists for this Module and its task scope | `spec_incomplete` |
| *direct candidate:* validation evidence exists for this Module, focus, task and constraints | `stale_evidence` |
| *direct candidate:* Spec validation passes with the recorded source digest and Spec revision | `stale_evidence` |
| *direct candidate:* every configured check of the project passed for its current input digest | `stale_evidence` |
| *planned target:* the Module's Spec revision equals the one its plan was written for | `stale_context` |
| *planned target:* the task and constraints equal the planned ones | `incompatible_handoff` |
| *planned target:* every completed component's revisions are unchanged and it passes this check with its own task | `stale_evidence` or the component's code |
| *planned target:* accepted tasks exist and all are complete | `incomplete_change` |
| *planned target:* the implementation revision is unchanged since the tasks completed | `stale_evidence` |
| *planned target:* Spec validation passes with the recorded source digest | `stale_evidence` |
| *planned target:* every affected Module's revisions equal the recorded ones | `stale_evidence` |
| *planned target:* every check of the affected Modules passed for its current input digest | `stale_evidence` |

A check result counts only when its recorded measured-input digest equals the digest Check
execution computes for the current files; the set of results must equal the set of configured
checks the gate requires, recomputed from the candidate's current configuration.

## Errors

| Code | Meaning |
| --- | --- |
| `missing_change` | no existing change to validate |
| `incompatible_handoff` | `change_id` names another change than the worktree's, or the task differs from the planned one |
| `stale_proposal` | the pending confirmation's inputs changed |
| `check_sandbox_unavailable` | Check execution could not set up its boundary; no result is recorded |
| `stale_evidence`, `stale_context`, `review_required`, `spec_incomplete`, `incomplete_change` | a gate of the completion check is not met |
