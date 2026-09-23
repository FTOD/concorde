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

### scenario.review.preview — A preview lists the scope without reviewing

- GIVEN a review request for a Module
- WHEN it runs in `describe-policy` mode
- THEN the Host returns the scope's members with outcome `described`
- BUT no reviewer runs and no report is saved

### scenario.review.separate-entries — Each Operation selects its own reviewer

- GIVEN an initialized project and a review task
- WHEN the user session calls one of the two review Operations
- THEN `concorde-spec-review` runs only the Spec reviewer and `concorde-code-review` runs only the code reviewer

### scenario.review.terminology-consistency — Imported words are compared with their definitions

- GIVEN a Module whose documents import terms and explain how the Module uses them
- AND the documents defining those terms are in its context
- WHEN `concorde-spec-review` reviews the Module
- THEN the reviewer compares each local explanation with the term's canonical definition, including in documents the change did not touch
- AND a different wording with the same meaning is not reported
- AND an added condition, a dropped exception or a changed obligation is reported with both locations
- AND the coverage names the compared terms or states that there was nothing to compare

### scenario.review.reviewer-failure — A failed reviewer makes the review incomplete

- GIVEN a prepared review scope
- WHEN a reviewer's native run fails, is cancelled or exhausts its budget
- THEN the workflow stops at that reviewer
- AND polling the result returns an `incomplete` result for every member and the outcome `failed` while the scope is still current
- BUT no member is recorded as `no_findings` and no required review is satisfied

## Scopes

### scenario.review.native-scope — A scope is accepted only as a whole

- GIVEN a prepared review scope with the selected Module, a shared-file peer and a code-free parent's components
- WHEN the review workflow runs every reviewer and its final Host step accepts the scope
- THEN clean, advisory, blocking and incomplete results keep their distinct meanings and refer to genuine Issue receipts
- AND each member was reviewed in its own context
- AND a scope of more than thirty-two reviewers uses the same two Host steps

### scenario.review.native-scope-rejected — A mismatched or changed scope is not accepted

- GIVEN a review workflow whose reviewers all ran
- WHEN a proposal names a wrong context, mode or receipt, lacks coverage, or any member's input changed before the final Host step
- THEN the final Host step accepts no part of the scope as complete
- AND a scope that is no longer current is reported as `stale` without saving results

### scenario.review.explicit-components — A code-free parent is reviewed through its components

- GIVEN a Module that binds no files and whose change recorded completed component work
- WHEN the user session calls `concorde-code-review` for that Module
- THEN each recorded component that binds files receives a fresh reviewer with its component task
- AND the parent's result aggregates only the components' typed results, without the parent's reviewer reading component code
- AND the required code review is satisfied by the current component results without a local code review of the parent
- BUT review never marks implementation work complete

### scenario.review.explicit-components-stale — A changed component makes the aggregate stale

- GIVEN a code-free parent whose required code review was satisfied by its components' results
- WHEN a component's code or Spec changes, a component report is corrupted, or the parent's intent changes
- THEN the parent's required code review is no longer satisfied
- AND validation refuses readiness with `review_required`

### scenario.review.promise-impact — Only Modules relying on a changed promise are consumers

- GIVEN a managed change that edits a Module's documents
- AND one consumer uses the Module without `relies_on`, another narrows its `uses` to one concept with `relies_on`
- WHEN the Spec review scope is computed
- THEN the whole-document consumer is a member whenever a document it selects changed
- AND the narrowed consumer is a member only when a node it relies on or references changed its definition
- AND a changed `module` block concerns the Modules that relate to that Module
- BUT an unchanged document concerns nobody, whoever selects it

### scenario.review.multi-module — The change's own reviews cover every Module it edits

- GIVEN a managed change about one Module whose candidate also edits another Module's Spec and code, such as the consumer of a contract whose version the change raises
- WHEN the scope of a Spec review or code review of the change's Module is computed
- THEN the Spec review includes the edited Module and every Module the changed definitions concern
- AND the code review includes every Module binding a file the candidate changed
- BUT the Host's worktree guidance and local control records do not count as edits

## Required reviews

### scenario.review.consumer-currentness — A changed consumer input invalidates the required Spec review

- GIVEN a managed change with a required Spec review for a Module whose documents other Modules select
- WHEN a document, its metadata, a registration or the intent changes after the reviews were recorded
- THEN the Module and each current consumer need their own current complete-context result under the accepted intent
- AND a missing, corrupt, incomplete, blocking, empty-coverage or unrelated result does not satisfy the requirement
- AND an open pending gap for the same input prevents reusing an earlier result

### scenario.review.explicit-review-fresh — An explicit review always runs fresh

- GIVEN a Module with a current recorded review of the same kind and intent
- WHEN the user session requests that review again
- THEN fresh reviewers run for every member of the scope
- AND the earlier reports stay saved as history

### scenario.review.spec-gate — Planning and implementation wait for the required Spec review

- GIVEN a candidate that records a required Spec review of a Module whose latest result has a blocking finding
- WHEN the user session requests `concorde-plan`, `concorde-tasks` or `concorde-implement` for that Module
- THEN the Host refuses with `review_required` before any Agent starts
- BUT `concorde-context-solve` for the same Module is not refused

### scenario.review.no-downgrade — A later request keeps the requirement

- GIVEN a candidate that records a required code review of a Module
- WHEN the user session requests a code review of that Module with a different task
- THEN the review runs and its result is saved as evidence
- BUT the requirement stays recorded and the new result does not satisfy it
