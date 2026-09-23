# Solve workflow

The exact request, response, solve state, closing journal, workflow step table and call layout of
[Issue solving](module.md). Issue shapes and store operations are those of the
[Issue interface](../issues/interface.md).

## Request and response

`concorde-issues-request@1` carries:

| Field | Type | Used by |
| --- | --- | --- |
| `action` | `list`, `show`, `report`, `reopen` or `solve` | all |
| `target_id` | Module identity | `report` (required, the reporting Module); `list` (filter by reporting Module or owner); others must equal the bound owner if given |
| `task`, `focus_id`, `constraints`, `change_id` | the common task fields | `solve` |
| `issue_id` | `I-` and 32 lowercase hex digits | `show`, `reopen`, `solve` (required) |
| `report` | an Issue report | `report` only |
| `expected_revision` | SHA-256 digest | `show`, `reopen`, `solve`; refused with `stale_issue` when it differs from the file |
| `note` | nonblank string | `reopen` (required rationale); `solve` (developer clarification) |

`concorde-issues-response@2` is the common capability response plus:

| Field | Meaning |
| --- | --- |
| `issues` | complete records returned by the action: every matching record for `list`, the one record otherwise |
| `decision` | `null` for bookkeeping; for `solve`, the closing action or a stop reason: `already-closed`, `develop`, `spec-repair`, `needs-decision`, `limit-exhausted`, `blocked`, `failed` or `verification-failed` |

`blockers` in the common response is the list of Blockers the last solver or reviewer returned.

## Binding

Before a worktree is chosen, the capability's binding step:

1. for `show`, `reopen` and `solve`, reads the record and its revision (`unknown_issue`), compares a
   supplied `expected_revision` (`stale_issue`), sets `target_id` to the Issue's owner and refuses a
   different supplied `target_id` with `permission_denied`; for `reopen` and `solve` the owner must
   be a registered Module (`unknown_target`);
2. for `solve` of an open Issue without a closing journal, requires the record file to be tracked
   and unchanged against `HEAD` of the worktree the request starts in (`uncommitted_issue`);
3. for `solve`, finds a closing journal of this Issue in the worktree's change status; its presence
   requires the Issue's bytes to equal the journal's open or closed image (`stale_issue`) and keeps
   the request in this worktree (recovery never creates a candidate);
4. for `solve` of a closed Issue without a journal, answers from the existing disposition; if the
   last disposition is a solver's close of this change's solve that never completed, refuses with
   `invalid_worktree_state` instead;
5. for `report`, requires `target_id` and a valid report; for `reopen`, a nonblank `note`;
6. when `task` is absent for `solve`, writes one from the latest report's title, description and
   impact.

`solve` of an open Issue is a mutation and runs in a candidate; every other action, and `solve` of
a closed Issue, runs in the current worktree without a candidate.

## Bookkeeping actions

| Action | Behaviour |
| --- | --- |
| `list` | `list_issues` with the optional filter, then every matching record |
| `show` | `read_issue` of the selected Issue |
| `report` | a reporting service with provenance `{agent: developer, phase: report, target_id}`, the context identity of the Module's Spec context, admitted owners the Module, the Modules it uses and the owners of its selected Spec documents, evidence paths the selected Spec documents and the Module's bound files, and, for an append, the named Issue as selected |
| `reopen` | `dispose_issue` with reason `reopened`, the `note`, evidence `["Explicit developer request"]` and actor `developer` |

## Solve state

Issue solving keeps its records in its provider section `issue-solving` of the change status, a
typed value `concorde-issue-solving-records@1` whose `data` is `{solutions}`. `solutions[<issue_id>]`
is the solve state of one selected Issue:

| Field | Meaning |
| --- | --- |
| `revision` | the selected Issue's revision when the solve began |
| `attempts` | solver launches for the current `inputs`; at most 6 |
| `inputs` | digest of the Module's Spec revision and implementation revision |
| `clarification` | the last `note` supplied with `solve` |
| `history` | one `{context_id, decision, inputs}` per accepted solver decision |
| `verified_inputs`, `verification` | the inputs a completed verification covered and the reviews' input digests |
| `status` | `active`, `closing`, `verifying-candidate`, `completed`, `verification-failed` or a stop reason |
| `answer` | the answer of the last stop |
| `pending_disposition` | the closing journal while a close is unfinished |
| `disposition`, `closed_revision` | set when the solve completed |

`attempts` returns to 0 when `inputs` differ from the stored value or a new `clarification` is
given. The attempt count is saved before each solver launch. Every save of the solve state also
returns a `ready` change to `active`, so no earlier ready state survives a solve step.

## Closing journal

The journal is `{schema_version: 1, change_id, issue_id, before, before_digest, after,
after_digest}`. It is valid only when both digests match their texts, both texts parse as records
of this Issue within the record size limit, `before` is open, `after` is closed and equals `before`
plus exactly one disposition whose actor is `concorde-issue-solver`, and `before_digest` equals the
solve's `revision`. An invalid journal fails with `invalid_worktree_state`. The prepared
`created_at` is reused for the actual write, so the written bytes equal `after`.

Closing runs: prepare `after`; save the journal and status `closing`; `dispose_issue` over
`revision`, which must return `after_digest`; save status `verifying-candidate`; run
`concorde-validate` for the change's Module. On `ready`: status `completed`, `disposition`,
`closed_revision`, journal removed. Otherwise: mark the change `blocked`, `restore_issue` of
`before` over the closed revision, journal removed, status `verification-failed`, answer `failed`.

Recovery, in the Host's preparation of a solve that finds a valid journal: mark the change active in
phase `issue-recovery` and withdraw its ready state, `restore_issue` of `before` over
`after_digest`, remove the journal, clear `verified_inputs` and `verification`, and continue as a
fresh solve.

## Workflow

The workflow script `pi/workflows/issues.js` is named `concorde.issues.<ticket>` and runs up to six
iterations `i` (0 to 5):

| Step | Kind | What it does | Next |
| --- | --- | --- | --- |
| `next-i` | Host step | stops at the attempt limit or on a changed Issue; otherwise counts the attempt, builds the selection, adds the Issue context of the previous verification's blocking findings, and issues solver slot `d-i` | `decide`, or `finished` |
| `d-i` | Agent call | the Issue solver returns a solve decision | `decision-i` |
| `decision-i` | Host step | admits the decision; finishes on hand-back, question or stop; closes and validates on a closing decision; otherwise issues review slots `v-i-g-m` | `verify`, or `finished` |
| `v-i-g-m` | Agent calls | reviewers of group `g`, member `m`, run one after another | `verified-i` |
| `verified-i` | Host step | admits every review of the iteration together | `decide` (to `next-(i+1)`), or `finished` |

Review groups are `0` Issue-specific Spec review, `1` Issue-specific code review, `2` ordinary Spec
review and `3` ordinary code review; a Module without implementation files uses groups 0 and 2. The
workflow stops with an error when a Host step answers a route the step table does not allow, and
when a model call is not a single successful, attached, uninterrupted child whose staged proposal
carries this workflow's ticket and slot. If iteration 5 ends at `verified-5` with route `decide`,
the Host has already finished the solve at the attempt limit; reaching the end of the loop is an
error.

**Stop conditions.** The workflow finishes when a Host step answers `finished`: a hand-back
(`develop`, `spec-repair`), a question (`needs-decision`), the attempt limit, a solver result that is
not a decision, a failed reviewer, a completed close with its final validation, or a failed final
validation. A stopped workflow, a stale or duplicated Host step, or an uncorrelated child raises an
error that no disposition follows.

## Host steps

Each Host step is the command `node pi/native-issue-host.mjs <step> <descriptor> <digest>`, speaking
the [Host-step protocol](../harness/execution/interfaces.md#contract.execution.host-step). The
command:

1. for `next-0`, waits up to 15 seconds for the workflow's launch binding to exist;
2. runs the Python step `workflow-<step>` under the workflow's Host lock; the step refuses a
   workflow that is stopped or not running (`execution_cancelled`), a foreign run
   (`incompatible_handoff`), and a step whose name or iteration does not match the saved session
   state (`invalid_completion`), and re-reads the Issue, the solve state and the inputs
   (`stale_issue`, `stale_context`);
3. for each slot the step issued, checks that the call it would launch equals the slot's exclusive
   binding, runs the slot's prelaunch admission and records the preflight contract of the call;
4. prints the control message.

The control message is one line of ASCII JSON of at most 2048 bytes with exactly the keys `groups`,
`iteration`, `route`, `schema_version`, `ticket`, in that order: `schema_version` 1, the workflow's
`ticket`, the current `iteration`, `route` in `decide`, `verify` or `finished`, and `groups` as four
non-negative review counts. The script rejects anything else.

When the workflow finishes, the Host saves the result for the user session to poll and a copy under
`.concorde/runs/<invocation_id>/native-issue.json` in the primary worktree.

## Slot calls

A slot key is `d-i` for the solver or `v-i-g-m` for a reviewer. `pi/issue-call.mjs` builds the one
call for a key, used both by the Host's preflight and by the workflow script:

| Field | Value |
| --- | --- |
| `agent` | `concorde-issue-solver` for `d-i`; `concorde-spec-reviewer` for even groups, `concorde-code-reviewer` for odd groups |
| `task` | `Assess context.json for invocation_id <ticket>:<key>` |
| `cwd` | the slot's context directory |
| `agentScope`, `context`, `async`, `mission`, `artifacts`, `artifactDir` | `project`, `fresh`, `false`, `false`, `true`, `session` |
| `intercomBridge`, `agentContract` | `{mode: off}`, `{version: 1}` |
| `outputSchema` | the stage result schema for the solver, the review stage result schema for reviewers, with `invocation_id` fixed to `<ticket>:<key>` |
| `gate` | the Workflow's slot gate command followed by the key: the Host's `slot-gate` for this slot, which stages the child's proposal |

A slot is issued at most once; issuing it again fails with `invalid_completion`.

## Errors

| Code | Meaning |
| --- | --- |
| `unknown_issue` | the selected Issue does not exist |
| `stale_issue` | the Issue, an offered duplicate or the solve state changed |
| `stale_context` | the Module's Specs or implementation files changed during a step |
| `stale_evidence` | a resolution's verification no longer covers the current inputs |
| `uncommitted_issue` | `solve` of an Issue whose file is not committed as it is on disk |
| `unknown_target` | `reopen` or `solve` of an Issue whose owner is not a registered Module |
| `permission_denied` | a `target_id` that differs from the Issue's owner |
| `invalid_worktree_state` | an invalid journal, or a solver close without a journal |
| `invalid_completion` | a stale, duplicated or foreign Host step or slot, or a solver result without a decision |
| `review_required` | a verification whose results are incomplete |
| `execution_cancelled` | the workflow was stopped |
