# Review scenarios

These situations show how [Review](module.md) behaves. The obligations they demonstrate are
defined once in [Review requirements](requirements.md).

## Public review

### scenario.review.standalone — Review without a managed change

- GIVEN an initialized project in a worktree without a managed change or an existing Issue
- AND a request naming a Module, a task and optionally a scenario of that Module as focus
- WHEN the user session calls `concorde-spec-review` or `concorde-code-review` through the Pi `concorde` tool and invokes the returned native workflow call
- THEN a fresh reviewer receives the Module's complete context and, for code review, only the Module's bound files and their changes since `HEAD`
- AND the reviewer has no write, edit, shell or delegation tools
- AND the Host returns the review coverage, the findings and the outcome, and saves the review report
- BUT no change is created and no Spec document or implementation file changes

A `describe-policy` request for the same review lists the scope and returns `described` without
running a reviewer or saving a report.

### scenario.review.separate-entries — Each capability selects its own reviewer

- GIVEN an initialized project and a review task
- WHEN the user session calls one of the two review capabilities
- THEN `concorde-spec-review` runs only the Spec reviewer and `concorde-code-review` runs only the code reviewer
- AND a request that contains a `review_mode` field is rejected by the request schema

### scenario.review.terminology-consistency — Imported words are compared with their definitions

- GIVEN a Module whose documents import terms and explain how the Module uses them
- AND the documents defining those terms are in its context
- WHEN `concorde-spec-review` reviews the Module
- THEN the reviewer compares each local explanation with the term's canonical definition, including in documents the change did not touch
- AND a different wording with the same meaning is not reported
- AND an added condition, a dropped exception or a changed obligation is reported with both locations
- AND the coverage names the compared terms or states that there was nothing to compare
- BUT an unfinished comparison is reported as `incomplete` instead of as consistent

## Scopes

### scenario.review.native-scope — A scope is accepted only as a whole

- GIVEN a prepared review scope with the selected Module, a shared-file peer and a code-free parent's components
- WHEN the native review workflow runs every reviewer and its final Host step accepts the scope
- THEN clean, advisory, blocking and incomplete results keep their distinct meanings and refer to genuine Issue receipts
- AND each member was reviewed in its own context
- AND a scope of more than thirty-two reviewers uses the same two Host steps
- BUT a wrong context, mode, receipt or coverage, a changed input, or a missing or failed reviewer prevents accepting any part of the scope as complete

### scenario.review.explicit-components — A code-free parent is reviewed through its components

- GIVEN a Module that binds no files and whose change recorded completed component work
- WHEN the user session calls `concorde-code-review` for that Module
- THEN each recorded component that binds files receives a fresh reviewer with the task derived for it
- AND the parent's result aggregates only the components' typed results, without the parent's reviewer reading component code
- AND the required code review is satisfied by the current component results without a local code review of the parent
- BUT a changed component, a corrupt report or a different intent makes the aggregate stale, and review never marks implementation work complete

## Currentness

### scenario.review.consumer-currentness — Owner and consumers each need current evidence

- GIVEN a managed change with a required Spec review for a Module whose documents other Modules select
- WHEN the required review is checked after a document, its metadata, a registration or the intent changed
- THEN the Module and each consumer need their own current complete-context result under the accepted intent
- AND a missing, corrupt, incomplete, blocking, empty-coverage or unrelated result does not satisfy the requirement
- AND an unresolved blocker for the same scope prevents reusing an earlier result
- BUT an explicitly requested review always runs fresh reviewers and keeps the earlier reports as history
