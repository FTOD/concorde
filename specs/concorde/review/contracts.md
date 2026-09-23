# Review contracts and records

The exact shapes and rules behind the [Review](module.md) explanation: the public review result,
the input each reviewer receives, how the Host checks and maps results, how a review scope is
computed, the steps of the review workflow, the records the Host saves, and how required reviews
are recorded and checked.

## Review result

Every accepted or failed review of one Module produces one review result. The Operation's response
carries all results of the scope in its `reviews` array, and the Host saves each one as a review
report under the invocation's run directory.

```concorde-contract
{
  "id": "contract.review.result",
  "version": 3,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["type_id", "schema_version", "data"],
    "properties": {
      "type_id": {"const": "concorde-review-result"},
      "schema_version": {"type": "integer", "const": 3},
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
          "status": {"enum": ["no_findings", "findings", "incomplete"]},
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
  "semantics": "One reviewer's conclusion about one Module for one review kind. context_id and input_digest identify the frozen context and the complete review input; context_id is null only when no reviewer context was admitted, which happens only for an incomplete result. status no_findings means the reviewer covered the listed representative_tasks and reported nothing; findings means at least one entry in issues; incomplete means the review did not finish and is never evidence of a clean Module. Each issues entry is the receipt of one Issue report (issue_id, report_id, path) with this review's severity judgment for affected_task. revision records the Spec revision, the implementation revision for code review, and the baseline and head commits the changes were computed against. semantic_completeness is always not_proven.",
  "example": {
    "type_id": "concorde-review-result",
    "schema_version": 3,
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

A failed or interrupted review produces `incomplete` with an empty `issues` array, no
representative tasks and `context_id` null. Reports and answers describe problems at the level of
the contract and name locations. They do not copy raw code, patches or logs.

## Reviewer input

Each reviewer receives one `concorde-review-stage-context`: the frozen context snapshot of its
Module plus one `concorde-review-input` with these fields.

| Field | Meaning |
| --- | --- |
| `review_mode` | `spec` or `code`, fixed by the Operation's declared phase; never taken from the request |
| `input_digest` | digest of every value listed under [Input digest](#input-digest) |
| `revision` | the same object as the result's `revision` |
| `changes` | a list of `{path, patch}` for the reviewed paths that differ from the baseline |

For a Spec review the reviewed paths are both members of every document in the Module's Spec
context. For a code review they are the files the Module's realizations bind; a directory entry
limits history to that directory and admits only the files the entry binds. A file present now and
absent at the baseline appears as an addition from `/dev/null`, a deleted bound file as a removal,
and a binary file as `Binary change: <digest before> -> <digest after>`. A path whose only change is
that it became present or absent while empty carries the patch text `Empty file membership changed.`

The baseline is the change's recorded `base_commit` in a managed change, the current `HEAD` in an
unmanaged Git checkout, and null in a directory without Git, where every current file is new.
History is read only from Git objects of the reviewed worktree's repository.

A reviewer answers with one `concorde-review-stage-result`: `context_id`, `input_digest`,
`review_mode`, `status` (`no_findings`, `findings` or `incomplete`), `representative_tasks`,
`issues` and `answer`, with the same field types as the review result, except that `context_id` is
never null. The Host adds `target_id`, `focus_id`, `revision` and `semantic_completeness` when it
accepts the answer.

### Input digest {#input-digest}

The input digest covers: the target and focus, the absolute worktree path and branch, the task,
constraints and change ID, the review mode, the revision, the changes, the reviewer's canonical and
native instructions, the reviewer's declared effects and definition digest, the byte digests of the
Host runtime files that take part in review (a fixed list held by the review service, covering its
own realizations and the Host code it runs through), and the project configuration.

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

Blocking findings become blockers of the affected task, recorded as pending gaps of the review's
step and input digest unless the status is `incomplete`. The result is then mapped to the
Operation's outcome:

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

### Spec review

The members are the selected Module, its promise-level consumers, every consumer already recorded
for this Module in the change, and every recorded component. A consumer is asked the task
`Review this Module's reliance on the changed canonical Spec. <task>`; a component is asked its
component task.

**Promise-level impact.** With a managed change whose `base_commit` has a readable registry, the Host
loads the Specs of that commit from Git objects and compares them with the candidate's:

1. The compared documents are every document of the candidate when the selected Module is the one
   the change is about (its `target_id`), otherwise the documents the selected Module owns in
   either revision.
2. A compared document is **changed** when either member's bytes differ or it exists in only one
   revision (Spec tooling's changed-documents index).
3. A node's **definition** is, together with the defining document's path: for a requirement or
   scenario, its heading section; for a contract, its parsed fence and its anchored or enclosing
   section; for a concept, its metadata record, Terminology definition row and anchor explanation;
   for a realization, its metadata record; and for a Module, its entry's `module` block. A node is
   **changed** when its definition differs between the revisions of the changed documents, or it
   exists in only one of them.
4. In either revision, a Module is a consumer when it selects a changed document without narrowing
   (it owns it, `contains` or `uses` its owner without `relies_on`, or `includes` its owner or the
   document), or when the `referenced-by` index names it for a changed node.

Consumers are limited to Modules registered in the candidate, and the selected Module is not its own
consumer. Without a managed change, a `base_commit` or a baseline registry, every Module whose Spec
context selects one of the selected Module's current documents is a consumer.

### Code review

The members are the selected Module when it binds files, every recorded component that binds files,
and every other Module that binds a changed file. The changed files are those the selected Module
binds that differ from the baseline, or, when the selected Module is the one the change is about,
every file of the candidate's deliverable tree that differs from the `base_commit` and that some
Module binds; the Host's worktree guidance and local control records are not part of that tree.
Without a baseline, every Module sharing one of the selected Module's files is a member. A peer is
asked the task `Check this Module's own contract against the shared implementation change. <task>`.

A recorded component outside the selected Module's change scope is refused with
`permission_denied`. For code review the Host also binds a scope identity: a digest of the selected
Module's Spec revision, task, focus and constraints. Aggregation refuses with `stale_context` when
it changed.

## The review workflow

**Prepare.** The Operation's run prepares every member: it freezes the member's context, computes
its reviewer input and issues a ticket and a native call. It saves the scope, including the
configuration, the members, their prepared descriptors and a digest of the candidate's inputs, and
returns the named workflow `concorde.review.<ticket>` built from `pi/workflows/review.js`.
`describe-policy` returns the member list with outcome `described` and prepares nothing. A scope
without an executable member is refused with `unsupported_target`.

The workflow's only inputs are the member calls, their output schema and two fixed Host-step
commands, each an invocation of `pi/native-review-host.mjs` with the step name, the path of the scope
descriptor and its digest. Every Host step speaks the
[Host-step protocol](../harness/execution/interfaces.md#contract.execution.host-step).

| Step | Kind | What happens | Time limit |
| --- | --- | --- | --- |
| `bind` | Host | Waits up to 15 seconds for the workflow's launch binding, runs the Host's `workflow-check` service, which verifies that the configuration, members, selected Module's Spec context, candidate inputs and every member descriptor are unchanged, then preflights every member's call | 30 min |
| `review-<i>` | Agent | One fresh reviewer per member, in order; its output schema requires the member's own ticket, and its staging gate records the proposal as staged and not accepted | the Agent's own limit |
| `finalize` | Host | Runs the Host's `workflow-finalize` service: verifies every reviewer's native terminal records, admits each member's proposal independently, rechecks the whole scope and every member's context and input, accepts each result as described under [Acceptance](#acceptance), aggregates them and saves a workflow receipt | 30 min |

**Stop conditions.** The workflow stops with a `concorde.failure` event at the first reviewer that
did not complete, was detached, interrupted or stopped, has not exactly one result, exited with an
error, lost its metadata, output or transcript, whose staging gate did not pass, whose gate output
is not a string of at most 8000 characters, or whose staging reports another ticket.

**Result and stop.** The user session polls with the action `result`. It receives the saved receipt;
`running` while the workflow runs; or, when the workflow failed or stopped before finalizing, an
`incomplete` result for every member if the scope is still current. A scope that is no longer
current is reported as `stale` without saving results. A stop request marks the workflow stopped,
and a later `finalize` refuses with `execution_cancelled`. A failure never falls back to another
execution path.

## Saved records

The Host saves, under `.concorde/runs/<invocation>/`: one review report per result, named after the
Module, the mode and a unique suffix; beside a failed report, a private record of the reviewer's
failure; and for the workflow, one record of the scope, the workflow binding, the admitted proposals
and the final output.

When the worktree has a change status record, the Host also writes:

- `review_intents` and `review_requirements` per Module: the accepted intent and the required review
  kinds;
- `reviews` per Module and kind: the latest report reference, input digest, status, task, focus and
  constraints, written only when the review's intent matches a recorded intent or none is recorded;
- `shared_spec_reviews` per Module: the current Spec consumers' report references and tasks;
- `shared_implementation_reviews` per Module: the code-review members' report references, tasks and
  scope identity.

Writing a result for a required review clears the change's `validated_tree` and returns a `ready`
change to `active` in that review's phase.

## Required reviews

**Recording.** Before a review runs in `execute` mode inside a candidate, when its task, focus and
constraints equal the candidate's accepted intent for the Module (the change's own intent for its
owner, or the recorded intent of the Module's work), the Host records the review's kind as required
for the Module and records that intent. Issue solving records the kinds its solving needs in the
same way. A later request never sets a recorded requirement back to not required.

**Currentness.** A recorded review result is current when its report bytes are intact, its recorded
status and input digest equal the report's, its input digest equals a fresh recomputation, its
target, focus and mode match, its status is `no_findings` or `findings` with representative tasks
and a nonblank answer, none of its findings is blocking, every finding's Issue receipt still
resolves, and no pending gap recorded for that input is open. A required Spec review is satisfied
when the Module's own result is current and the recorded consumer reviews cover exactly the current
consumers, each current under its consumer or component task. A required code review is satisfied
when the Module's own result (when it binds files) and every component's and changed-file peer's
result are current and carry the current scope identity.

**Checks.** The Spec gate runs when `concorde-plan`, `concorde-tasks` or `concorde-implement`
prepares a step for a Module with a required Spec review, before any Agent starts; it refuses with
`review_required`. The validation gate runs when `concorde-validate` records readiness: it checks
every recorded required review, Spec and code, of the Module and, for a candidate without planned
tasks, of every Module with a recorded requirement under that Module's recorded intent; it refuses
with `review_required`.
