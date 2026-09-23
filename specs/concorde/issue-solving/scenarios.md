# Issue solving scenarios

Concrete situations that show the [requirements](requirements.md) at work. Shapes and error codes
are defined in [Solve workflow](workflow.md).

## Bookkeeping

### scenario.issue-solving.inspect — Inspect without starting work

- GIVEN an initialized project with or without Issues
- WHEN the user session calls `concorde-issues` with `list` or `show`
- THEN the current records are returned
- BUT no model runs, no candidate is created and no record changes

### scenario.issue-solving.report — The developer reports a problem

- GIVEN a registered Module and a classified report whose owner and evidence lie within that Module's Spec context
- WHEN the user session calls `concorde-issues` with `report`
- THEN the report is saved with the developer as reporter
- AND the answer returns the record
- BUT no candidate is created

### scenario.issue-solving.reopen — Reopen a closed Issue with a reason

- GIVEN a closed Issue
- WHEN the user session calls `concorde-issues` with `reopen` and a `note`
- THEN the Issue gets a `reopened` disposition with the developer as actor
- AND its reports stay unchanged

### scenario.issue-solving.reopen-without-note — Reopening needs a reason

- GIVEN a closed Issue
- WHEN the user session calls `reopen` without a `note`
- THEN the request is refused with `invalid_input`
- BUT the Issue stays closed

### scenario.issue-solving.foreign-target — A selection cannot name another Module

- GIVEN an Issue owned by one Module
- WHEN the user session selects it with a `target_id` of another Module
- THEN the request is refused with `permission_denied`
- BUT nothing is written and no candidate is created

### scenario.issue-solving.unknown-owner — An Issue of a removed Module can be shown but not solved

- GIVEN an Issue whose owner is no longer a registered Module
- WHEN the user session calls `solve` or `reopen` for it
- THEN the request is refused with `unknown_target`
- BUT nothing is written and no candidate is created

## Starting a solve

### scenario.issue-solving.relay — A committed Issue is solved in a new candidate

- GIVEN an open Issue committed on the primary branch
- WHEN the user session calls `solve` from the primary worktree
- THEN admission creates a candidate from the primary branch and relays the request into it
- AND the Host prepares the solve workflow there and returns its call
- AND the user session receives the candidate's result

### scenario.issue-solving.uncommitted-refused — An uncommitted Issue is not solved

- GIVEN an open Issue whose record file is untracked or differs from `HEAD` in the primary worktree
- WHEN the user session calls `solve` from the primary worktree
- THEN the request is refused with `uncommitted_issue`
- BUT no candidate is created and nothing is copied

### scenario.issue-solving.already-closed — Solving a closed Issue replays nothing

- GIVEN an Issue already closed in the current worktree, with no unfinished close
- WHEN the user session calls `solve` for it
- THEN the answer returns the existing disposition with decision `already-closed`
- BUT no candidate is created and no model runs

### scenario.issue-solving.preview — A policy preview launches nothing

- GIVEN an open Issue
- WHEN `solve` runs in `describe-policy` mode
- THEN the answer describes the bounded decisions, the reviews and the journaled close
- BUT no workflow is prepared, no model runs and no state changes

## Decisions

### scenario.issue-solving.develop-handback — Hand needed code work back

- GIVEN a solve whose solver decides `develop`
- WHEN the Host admits the decision
- THEN the solve stops with outcome `unsupported`, naming the Module, the intended work and the reason
- AND the decision is kept in the solve history
- BUT the Issue stays open and no file is changed

### scenario.issue-solving.spec-repair-handback — Hand a needed Spec change back

- GIVEN a solve whose solver decides `spec-repair`
- WHEN the Host admits the decision
- THEN the solve stops with outcome `unsupported`, naming the missing or conflicting promise and the needed Spec change
- BUT the Issue stays open and no file is changed

### scenario.issue-solving.needs-decision — Ask only when a choice is genuinely open

- GIVEN a selected Issue whose fix needs a product or design choice that its context does not settle
- WHEN the solver decides `needs-decision`
- THEN the solve stops with outcome `conflicting` and the precise question
- BUT the Issue stays open

### scenario.issue-solving.clarification — A clarification starts a fresh bounded attempt

- GIVEN a solve that stopped with `needs-decision` or at the attempt limit
- WHEN the user session calls `solve` again with a `note` carrying the developer's answer
- THEN the attempt count restarts
- AND the solver receives the clarification as feedback

### scenario.issue-solving.limit — The solver is asked at most six times

- GIVEN a solve whose inputs and clarification stay unchanged
- WHEN the solver has been asked six times without a closing or stopping decision
- THEN the solve stops with outcome `conflicting` and decision `limit-exhausted`
- BUT the solve history is kept

### scenario.issue-solving.resolved-unverified — A resolution without current verification is verified first

- GIVEN a solve with no completed verification of the current inputs
- WHEN the solver decides `resolved`
- THEN the Host runs verification instead of closing
- AND asks the solver again with the result

## Verification

### scenario.issue-solving.verification-passes — A clean verification returns to the solver

- GIVEN a solve whose solver asked for verification
- WHEN every Issue-specific and ordinary review completes without a blocking finding on unchanged inputs
- THEN the Host records the reviews' input digests as the verification of the current inputs
- AND asks the solver again with that verification

### scenario.issue-solving.verification-blocking — Blocking findings go back to the solver

- GIVEN a verification in which a review reports a blocking finding
- WHEN the Host admits the reviews
- THEN the verification does not count
- AND the solver is asked again with feedback and the Issue context of the findings' reports

### scenario.issue-solving.reviewer-failed — A reviewer that fails stops the solve

- GIVEN a verification in which a reviewer fails to complete
- WHEN the Host admits the reviews
- THEN the solve stops with outcome `failed`
- BUT the Issue stays open

## Closing

### scenario.issue-solving.resolved-ready — Close as resolved and stop at ready

- GIVEN a selected open Issue that the user session has already fixed in the candidate
- AND a completed verification of the current inputs
- WHEN the solver decides `resolved`
- THEN the Host saves the journal, writes the disposition and validates the candidate including it
- AND the answer is outcome `ready` with the disposition and the checks
- BUT nothing is delivered or merged

### scenario.issue-solving.duplicate-close — Close as a duplicate of an offered Issue

- GIVEN a solve that offered another open Issue as a possible duplicate
- WHEN the solver decides `duplicate` naming that Issue, which is unchanged
- THEN the Host closes the selected Issue as a duplicate of it through the journal and final validation
- AND the other Issue stays open
- BUT no human approval is required

### scenario.issue-solving.not-actionable-close — Close a mistaken report

- GIVEN a selected Issue whose report the admitted contract shows to be mistaken
- WHEN the solver decides `not-actionable` with a contract-grounded reason
- THEN the Host closes the Issue as not actionable through the journal and final validation
- BUT no human approval is required

### scenario.issue-solving.validation-fails — A close that fails validation is undone

- GIVEN a solve that wrote a closing disposition
- WHEN the final validation does not answer ready
- THEN the Host restores the Issue's open bytes and removes the journal
- AND marks the change blocked and answers `failed`
- BUT other work in the candidate is untouched

## Staleness

### scenario.issue-solving.stale-issue — A changed Issue stops the solve

- GIVEN a solve in progress
- WHEN the selected Issue's bytes change before a dependent step
- THEN that step is refused with `stale_issue`
- BUT earlier solve history is kept and nothing is closed

### scenario.issue-solving.stale-inputs — Changed Module inputs stop a step

- GIVEN a solve step in progress
- WHEN the Module's Specs or implementation files change during the step
- THEN the step is refused as stale
- BUT nothing is closed

### scenario.issue-solving.duplicate-changed — A changed duplicate target is refused

- GIVEN a solver decision `duplicate` naming an offered Issue
- WHEN that Issue changed after it was offered, or was never offered
- THEN the close is refused with `stale_issue`
- BUT the selected Issue stays open

### scenario.issue-solving.step-replayed — A stale or duplicated Host step is refused

- GIVEN a running solve workflow
- WHEN a Host step arrives whose name or iteration does not match the saved session state
- THEN it is refused with `invalid_completion`
- BUT no decision or review is admitted

### scenario.issue-solving.uncorrelated-child — A result without its native child is not admitted

- GIVEN a solve workflow
- WHEN a solver or reviewer result cannot be correlated with exactly one finished native child of this workflow's ticket and slot
- THEN the Host refuses it
- BUT nothing is closed

### scenario.issue-solving.workflow-run — The whole solve runs in one workflow

- GIVEN one selected Issue in its candidate and the prepared solve workflow
- WHEN the workflow runs the solver and every reviewer of a verification
- THEN each call is a fresh native child of the same workflow, launched only after its slot passed prelaunch admission
- AND each solver attempt is counted before the solver starts
- BUT no call starts another workflow or a nested child

## Recovery

### scenario.issue-solving.recover-close — Recover an interrupted close

- GIVEN a solve that saved its closing journal
- WHEN the process failed before the disposition was written, after it was written, or before completion was saved
- THEN the next solve of the Issue in the same candidate withdraws any earlier ready state
- AND restores exactly the journal's open bytes, or does nothing if they are already on disk
- AND continues with a fresh solve and fresh validation
- BUT no other candidate is created

### scenario.issue-solving.recovery-unprovable — Refuse recovery that cannot be proven

- GIVEN an interrupted solver close
- WHEN the next solve finds Issue bytes that match neither journal image, a corrupt journal, or a solver close without any journal
- THEN it refuses without overwriting the record
- BUT no solver is launched
