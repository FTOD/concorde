# Review contracts and records

This document holds the exact shapes and rules behind the [Review](module.md) explanation: the
public review result, the input each reviewer receives, how the Host checks and maps results, the
steps of the native review workflow, and the records the Host saves.

## Review result

Every accepted or failed review of one Module produces one review result. The capability's
response carries all results of the scope in its `reviews` array, and the Host saves each one as a
review report under the invocation's run directory.

```concorde-contract
{
  "id": "contract.review.result",
  "version": 2,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["type_id", "schema_version", "data"],
    "properties": {
      "type_id": {"const": "concorde-review-result"},
      "schema_version": {"type": "integer", "const": 2},
      "data": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "context_id", "input_digest", "review_mode", "status", "representative_tasks",
          "issues", "answer", "target_id", "focus_id", "revision", "semantic_completeness"
        ],
        "properties": {
          "context_id": {
            "anyOf": [
              {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
              {"type": "null"}
            ]
          },
          "input_digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
          "review_mode": {"enum": ["spec", "code"]},
          "status": {"enum": ["no_findings", "findings", "incomplete", "skipped", "not_run"]},
          "representative_tasks": {
            "type": "array",
            "uniqueItems": true,
            "items": {"type": "string", "minLength": 1}
          },
          "issues": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["issue_id", "report_id", "path", "severity", "affected_task"],
              "properties": {
                "issue_id": {"type": "string", "pattern": "I-[0-9a-f]{32}"},
                "report_id": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
                "path": {"type": "string", "minLength": 1},
                "severity": {"enum": ["blocking", "advisory"]},
                "affected_task": {"type": "string", "minLength": 1}
              }
            }
          },
          "answer": {"type": "string", "minLength": 1},
          "target_id": {"type": "string", "minLength": 1},
          "focus_id": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
          "revision": {
            "type": "object",
            "additionalProperties": false,
            "required": ["spec_digest", "implementation_digest", "baseline", "head"],
            "properties": {
              "spec_digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
              "implementation_digest": {
                "anyOf": [
                  {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
                  {"type": "null"}
                ]
              },
              "baseline": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
              "head": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]}
            }
          },
          "semantic_completeness": {"const": "not_proven"}
        }
      }
    }
  },
  "semantics": "One reviewer's conclusion about one Module for one review kind. context_id and input_digest identify the frozen context and the complete review input; context_id is null only when no reviewer context was admitted. status no_findings means the reviewer covered the listed representative_tasks and reported nothing; findings means at least one entry in issues; incomplete means the review did not finish and is never evidence of a clean Module. Each issues entry is the receipt of one Issue observation (issue_id, report_id, path) with this review's severity judgment for affected_task. revision records the Spec revision, the implementation revision for code review, and the baseline and head commits the changes were computed against. semantic_completeness is always not_proven.",
  "example": {
    "type_id": "concorde-review-result",
    "schema_version": 2,
    "data": {
      "context_id": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "review_mode": "spec",
      "status": "findings",
      "representative_tasks": ["Stop transfer retries after three failures"],
      "issues": [
        {
          "issue_id": "I-0123456789abcdef0123456789abcdef",
          "report_id": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "path": ".concorde/issues/I-0123456789abcdef0123456789abcdef.md",
          "severity": "blocking",
          "affected_task": "Stop transfer retries after three failures"
        }
      ],
      "answer": "The Spec does not say what happens to a transfer after its third failed retry.",
      "target_id": "module.transfer",
      "focus_id": null,
      "revision": {
        "spec_digest": "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "implementation_digest": null,
        "baseline": "4b17b96819c7217147d5138c099f2d244e1cab70",
        "head": "4b17b96819c7217147d5138c099f2d244e1cab70"
      },
      "semantic_completeness": "not_proven"
    }
  }
}
```

`skipped` and `not_run` are accepted by the schema, but the review service never produces them
today; a failed or interrupted review produces `incomplete` with an empty `issues` array and
`context_id` null. A result without a reviewer context carries no representative tasks.

Reports and answers describe problems at the level of the contract and name locations. They do not
copy raw code, patches or logs.

## Reviewer input

Each reviewer receives one `concorde-review-stage-context`: the frozen context snapshot of its
Module plus one `concorde-review-input` with these fields.

| Field | Meaning |
| --- | --- |
| `review_mode` | `spec` or `code`, fixed by the capability; never taken from the request |
| `input_digest` | digest of every value listed under [Input digest](#input-digest) |
| `revision` | the same object as the result's `revision` |
| `changes` | a list of `{path, patch}` for the reviewed Module's own files that differ from the baseline |

For a Spec review the changed paths are the documents of the Module's Spec context. For a code
review they are the files the Module's realizations bind; a directory entry limits history to that
directory and admits only the files the entry binds. A file present now and absent at the baseline
appears as an addition from `/dev/null`, a deleted bound file as a removal, and a binary file as
`Binary change: <digest before> -> <digest after>`. A file whose only change is empty membership
carries the patch text `Empty file membership changed.`

The baseline is the change's recorded `base_commit` in a managed change, the current `HEAD` in an
unmanaged Git checkout, and null in a directory without Git, where every current file is new.
History is read only from Git objects of the reviewed worktree's repository.

A reviewer answers with one `concorde-review-stage-result`: `context_id`, `input_digest`,
`review_mode`, `status` (`no_findings`, `findings` or `incomplete`), `representative_tasks`,
`issues` and `answer`, with the same field types as the review result. The Host adds `target_id`,
`focus_id`, `revision` and `semantic_completeness` when it accepts the answer.

### Input digest {#input-digest}

The input digest covers: the target and focus, the absolute worktree path and branch, the task,
constraints and change ID, the review mode, the revision, the changes, the reviewer's canonical and
native instructions, the reviewer's declared effects and definition digest, the byte digests of the
Host runtime files that take part in review (the review service and workflow, context, evidence,
result, admission, invocation, dispatch, planning, task, implementation, validation, Issue reporting,
permissions, worker and change-status code), and the project configuration.

The Spec revision is a digest of the Module's declaration, the configured Protocol and its resolved
Spec context. The implementation revision is a digest of the Module's realization entries and the
bytes of every file they bind.

## Acceptance

The Host accepts a reviewer's answer only when all of the following hold:

- `context_id`, `input_digest` and `review_mode` equal the admitted reviewer's frozen context, input
  digest and mode;
- `answer` and every representative task are nonblank;
- no two findings share an `issue_id`;
- `no_findings` has no findings, and `findings` has at least one;
- a status other than `incomplete` lists at least one representative task;
- every finding names a nonblank affected task.

Blocking findings become blockers of the affected task, recorded for the review's phase and input
digest unless the status is `incomplete`. The result is then mapped to the capability outcome:

| Result | Outcome |
| --- | --- |
| `incomplete` | `failed` |
| blocking findings, at least one needing a Spec repair | `spec_incomplete` |
| other blocking findings | `conflicting` |
| no findings, or advisory findings only | `completed` |

The outcome of a whole scope is the first of `failed`, `spec_incomplete`, `conflicting`,
`unsupported`, `described` that any member produced, otherwise `completed`.

An execution failure produces an `incomplete` result whose answer names the failure code. A
cancelled or limit-exhausted reviewer also marks the invocation and the change status as
`cancelled` or `limit_exhausted`; other failures mark them `failed`. The review's own outcome stays
`failed` in every case.

## Scope members

The scope is computed by the review service when the scope is prepared and recomputed before
acceptance; any difference makes the scope stale.

- **Spec review.** The selected Module, then every Module whose Spec context selects one of its
  documents in the current Specs, every Module that did so at the change's `base_commit`, every
  consumer already recorded for this Module, and every recorded component. A consumer is asked the
  task `Review this Module's reliance on the changed canonical Spec. <task>`.
- **Code review.** The selected Module when it binds files, every recorded component that binds
  files, and every other Module that binds a file of the selected Module that differs from the
  baseline. Without a baseline, every Module binding one of its files is a member. A peer is asked
  the task `Check this Module's own contract against the shared implementation change. <task>`.
  A component is asked the task Implementation derived from the accepted tasks it received.

A recorded component outside the selected Module's children and used Modules is refused with
`permission_denied`. For code review the Host also binds a scope identity: a digest of the selected
Module's Spec revision, task, focus and constraints. Aggregation refuses with `stale_context` when it
changed.

## Native review workflow

1. **Prepare.** The capability's run prepares every member: it freezes the member's context,
   computes its reviewer input and issues a ticket and a native call. It saves the scope, including
   the configuration, the members, their prepared descriptors and a digest of the candidate's
   inputs, and returns the named workflow `concorde.review.<ticket>` built from
   `pi/workflows/review.js`. `describe-policy` returns the member list with outcome `described` and
   prepares nothing. A scope without an executable member is refused with `unsupported_target`.
2. **Check.** The workflow's first Host step verifies that the configuration, members, parent Spec
   context and candidate inputs are unchanged and that each prepared member still passes its
   preflight.
3. **Review.** The workflow runs one reviewer per member, in order. A member counts as finished only
   when the native child exited cleanly with exactly one result, saved its metadata, output and
   transcript, and passed its staging gate, which reports the member's own ticket as staged and not
   accepted. The workflow stops with a failure event at the first member that does not.
4. **Finalize.** The workflow's second Host step verifies every native child's terminal records,
   admits each member's proposal independently, rechecks the whole scope and every member's
   context and input, accepts each result as described under [Acceptance](#acceptance), aggregates
   them and saves a workflow receipt.
5. **Result.** The user session polls the capability with the action `result`. It receives the
   saved receipt, `running` while the workflow runs, or, when the workflow failed or stopped before
   finalizing, an `incomplete` result for every member if the scope is still current. A scope that
   is no longer current is reported as `stale` without saving results.

A stop request marks the workflow stopped; a later finalize step refuses with
`execution_cancelled`. A failure never falls back to another execution path.

## Saved records

The Host saves, under `.concorde/runs/<invocation>/`: one review report per result, named after the
Module, the mode and a unique suffix; beside a failed report, a private record of the reviewer's
usage and failure; and for the native workflow, one record of the scope, the workflow binding, the
admitted proposals and the final output.

When the worktree has a change status record, the Host also writes:

- `review_intents` and `review_requirements` per Module: the accepted intent and the required review
  kinds;
- `reviews` per Module and kind: the latest report reference, input digest, status, task, focus and
  constraints, written only when the review's intent matches a recorded intent or none is recorded;
- `shared_spec_reviews` per Module: the current Spec consumers' report references and tasks;
- `shared_implementation_reviews` per Module: the code-review members' report references, tasks
  and scope identity.

Writing a result for a required review clears the change's `validated_tree` and returns a `ready`
change to `active` in that review's phase.
