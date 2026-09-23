# Review requirements

These are the Module-wide obligations of [Review](module.md). The exact shapes and checks they refer
to are in [Review contracts and records](contracts.md).

## Reviewers

### req.review.fresh-read-only — Reviewers are fresh and cannot change anything

Every reviewer SHALL run in a fresh native session without write, edit, shell or delegation tools.

A reviewer never inherits the conversation of whoever wrote the change. Which files it opens and
whether it uses the network are limited by its instructions only; the operating system does not
confine a reviewer's reads. A code reviewer may ask the Host to run its Module's configured checks
and receives their status and the tail of each log.

### req.review.own-context — Each Module is reviewed against its own Spec

Each Module in a review scope SHALL be reviewed by its own reviewer against its own Spec context and, for code review, only against the files its own realizations bind.

A parent never receives a component's code, and a Module that binds a shared file is reviewed
against its own promises, not those of the Module whose change touched the file. A Module never
gains a reference to another Module's documents only so that its reviewer can read them.

## Results

### req.review.admitted-contract — Results are bound to their exact inputs

Review SHALL accept a reviewer's answer only when it names the admitted reviewer's frozen context, input digest and review mode and passes the checks listed under [Acceptance](contracts.md#acceptance).

The input digest covers everything that can change a conclusion, including the reviewer's
instructions and the Host's own review code, so any such change makes the result stale.

### req.review.no-false-clean — An unfinished review is never clean

A review that is incomplete, failed, interrupted or missing any member of its scope SHALL NOT be recorded as `no_findings` or satisfy a required review.

The workflow's successful exit and a reviewer's staging gate are not acceptance; only the final Host
step accepts, and only for the complete scope. A failed scope saves an `incomplete` result for each
member while the scope is still current.

### req.review.no-project-writes — Review changes no project files

Review SHALL NOT change the project's Spec documents or implementation files.

The Host writes only review reports and records under `.concorde/runs/`, and review state in the
change status record, as listed under [Saved records](contracts.md#saved-records). Issues the
reviewers report are written by Issues.

## Scopes

### req.review.promise-impact — Spec review scope follows changed promises

Inside a managed change with a readable baseline, a Spec review's consumers SHALL be exactly the Modules that select a changed document without narrowing or reference a changed node definition.

A Module whose only selection of a changed document is a `relies_on` narrowing of unchanged nodes is
therefore not a consumer; consumers already recorded for the Module and its components stay members.
The comparison is defined under [Scope members](contracts.md#spec-review).

## Required reviews

### req.review.required-current — A required review needs current evidence for the whole scope

A required review SHALL count as satisfied only when the Module and every current member of its review scope have a current result for the same intent, as defined under [Required reviews](contracts.md#required-reviews).

### req.review.no-downgrade — A requirement is never removed

A review kind that a change has recorded as required for a Module SHALL remain required for the rest of that change.

A public review whose task, focus and constraints equal the change's accepted intent for the Module
records its kind as required before it runs. A later request with a different question neither
removes the requirement nor satisfies it.

### req.review.spec-gate — The required Spec review gates planning and implementation

Plan, task and implementation steps SHALL NOT prepare an Agent for a Module whose required Spec review is not satisfied.

This is the only review check before validation. `concorde-context-solve`, the reviews and Issue
bookkeeping check no requirement, and no stage before validation checks a required code review.

### req.review.validation-gate — Validation needs every required review

Validation SHALL NOT record a candidate as ready while any review recorded as required in it, Spec or code, is not satisfied.

### req.review.repair-feedback — Repair feedback comes only from the current blocking code review

Review SHALL admit a code review as repair feedback only when it is the current recorded code review of the same Module, intent and inputs and contains at least one blocking finding.

The feedback must be the exact report the change recorded, with intact bytes, status `findings`, a
nonempty coverage and answer, a matching focus, an input digest equal to a fresh recomputation and
resolvable Issue receipts. A replaced report, a changed Spec, code or instruction, or an incomplete
review is refused before any worker starts.
