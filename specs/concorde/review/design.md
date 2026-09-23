# Review design notes

These notes extend the [Review entry](module.md) with a worked example and the reasons behind the
design. They define nothing; every term is defined in the entry, and the exact shapes and rules are
in [Review contracts and records](contracts.md).

## A worked review

The developer has changed the retry rules in Module `module.transfer` and asks for a Spec review
with the task "retries stop after three failures". The user session calls `concorde-spec-review`
through the Pi `concorde` tool. The Host checks the request, works out the review scope, freezes a
context for every member and returns a prepared native workflow call. The user session invokes that
call unchanged; the workflow runs one fresh reviewer per member. The user session then polls with
the action `result` and receives the accepted outcome, the saved review reports and one review
result per reviewed Module.

Suppose the Spec never says what happens to a transfer after its third failed retry. The reviewer
reports that as an Issue and cites it as a blocking finding for the retry task, while an unrelated
vague sentence about logging becomes an advisory finding. The result's status is `findings`, the
outcome is `spec_incomplete` because the blocking finding needs a Spec repair, and dependent work
pauses until the Spec is repaired. Every result also states that semantic completeness is not
proven: a clean review is evidence about those inputs and that task only.

## Why results are bound to a digest

Every result is bound to a digest of everything that could change the conclusion: the Module, task,
focus and constraints, the worktree and branch, the Spec revision, for code review the
implementation revision, the changes since the baseline, the reviewer's instructions and declared
effects, the Host's own review runtime files and the project configuration. This is why a review of
yesterday's code cannot pass today's gate, and why a change to the reviewer's instructions calls for
a fresh review. The reviewer sees the complete current documents of its context plus the changes
since a baseline (the change's starting commit, the current `HEAD` in an unmanaged Git checkout, or
none without Git); full documents always accompany the changes, because a problem often lies in
text the change did not touch.

## Why Spec review scopes follow promises

Document-level impact is too coarse: a Module that relies on one concept of a large provider would
otherwise be re-reviewed for every unrelated sentence the provider changes. Comparing definitions
between the change's starting commit and the candidate keeps the scope exactly as wide as the
promises that changed, and a narrowed `uses` is the declaration that makes that possible. When the
reviewed Module is the one the change is about, its scope covers the whole candidate, so a change
that edits several Modules together has each of them reviewed, and delivering the one candidate is
the atomic step.

## Why one reviewer per Module, in one workflow

Each Module keeps its own promises, so each member of a scope gets its own fresh reviewer against
its own Spec. A shared file changed for one Module is reviewed once per Module that binds it, and a
parent never receives its components' code. Fresh sessions keep the assumptions of whoever wrote the
change out of the review. The workflow has only two Host steps however large the scope, and its
final step reads every reviewer's native records itself, admits each proposal and rechecks every
input before saving anything: a reviewer that exited successfully is not yet an accepted review.
Review has no scope cap of its own; the native runtime's budgets apply, and exhausting them makes
the review incomplete.

## What the Host cannot check

The reviewer instructions, which Agents owns, ask each reviewer to report every blocking finding it
can establish in one pass, and to judge only the scenarios and declarations of its own admitted
context. The Host cannot verify either: it checks the shape, identity and coverage of the result.
Which files a reviewer opens is limited by its instructions and by the capsule or worktree it starts
in; Concorde deliberately does not confine a reviewer's reads.

## Why a required review is checked in two places

A required Spec review gates planning and implementation because work built on a Spec with a
blocking finding would be built on an unrepaired contract. A required code review is checked only
at validation, so implementation and code review may repeat freely until the change is declared
ready. A requirement is never removed during the change, and a review that answers a different
question is kept as evidence but never satisfies it.
