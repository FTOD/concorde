# Framework scenarios

These scenarios describe whole flows that cross several Modules, seen from the developer and the
user session. Each has one outcome. The precise behaviour of every step belongs to the Module that
performs it; a scenario here promises only what the Modules achieve together. They are verified by
end-to-end acceptance tests of the Framework.

## Adopting Concorde

### scenario.concorde.adopt-initialize — Installing and initializing a new project

- GIVEN a project in which Concorde has never been installed
- WHEN the developer runs the installer
- AND the user session calls `concorde-init` to propose a first Spec and then to apply that exact proposal
- THEN the project's configuration binds the Protocol copy the installer placed under `.concorde/protocol/`
- AND the project validates without errors
- AND its root Module entry states that the project's purpose and behaviour are not yet specified
- AND the user session's `concorde` tool describes every public capability of the installed version

### scenario.concorde.adopt-conflict — A conflicting installation leaves the project unchanged

- GIVEN a project whose files conflict with what the installer would write
- WHEN the developer runs the installer
- THEN the installer refuses and names the conflicting files
- AND no project file is created, changed or removed
- AND a following `concorde-init` proposal fails with `not_installed`

### scenario.concorde.adopt-provision-failure — A failed upgrade restores the previous installation's files

- GIVEN an initialized project with a working installation
- WHEN the developer reinstalls a newer Concorde and provisioning or verifying its managed runtime fails
- THEN the installer reports the failure
- AND the previous installation's files, its receipt and its Protocol copy are restored byte for byte
- AND when the upgrade kept the existing runtime, capabilities keep running on the previous installation
- BUT when the upgrade had to rebuild the runtime, the previous runtime is not kept, and capabilities fail local verification until an installation succeeds ([runtime rebuild failure](distribution/scenarios.md#scenario.distribution.runtime-rebuild-failure))

### scenario.concorde.protocol-upgrade-refused — A newer Protocol is not adopted silently

- GIVEN an initialized project whose configuration binds the Protocol copy of the previous installation
- WHEN the developer installs a Concorde release with a newer Protocol and the user session calls any capability that loads the Specs
- THEN the call fails with `protocol_mismatch`
- BUT no Spec, configuration or registry file changes

### scenario.concorde.protocol-upgrade-accepted — Accepting a newer Protocol

- GIVEN a project whose installed Protocol copy is newer than its configuration's binding
- WHEN the user session calls `concorde-configure` with the explicit acceptance of the installed Protocol
- THEN the configuration binds the installed copy
- AND later capability calls load the Specs under it

### scenario.concorde.configure-apply — Configuring Agent calls

- GIVEN an initialized project
- WHEN the user session calls `concorde-configure` with a supported model, thinking level and time limit
- THEN the project configuration records them
- AND the next Agent call of any capability launches with that model, thinking level and time limit

### scenario.concorde.configure-reject — An unsupported configuration is refused

- GIVEN an initialized project
- WHEN the user session calls `concorde-configure` with a thinking level that Concorde does not support
- THEN the call fails with an explicit error naming the field
- AND the project configuration is unchanged

## Calling capabilities

### scenario.concorde.describe-capabilities — Describing what can be called

- GIVEN an initialized project open in a user session
- WHEN the user session asks the `concorde` tool to describe the capabilities
- THEN it lists every public capability of the installed Operation catalog with its purpose and inputs
- AND no request is admitted, no worktree is created and no Agent is launched

## Changing a project

### scenario.concorde.develop-change — A change reaches a ready candidate

- GIVEN a developer has agreed the intended behaviour in the owning Module's Spec
- AND the project's configured checks pass on the primary branch
- WHEN the user session calls context solving, planning, task writing, implementation and validation for that Module in that order
- THEN the change ends as one ready candidate whose configured checks pass on its exact files
- AND the primary branch and the primary worktree are unchanged
- AND nothing is delivered

### scenario.concorde.develop-gap — A missing promise stops dependent work

- GIVEN a change depends on a promise that the owning Module's Spec does not state
- WHEN the user session calls context solving for that Module
- THEN the answer reports a Spec gap naming the owning Module and the missing promise
- AND planning, task writing and implementation for the change refuse while the gap is pending
- BUT no Spec document is changed by Concorde

### scenario.concorde.develop-gap-repaired — Work resumes after the Spec is repaired

- GIVEN a change stopped on a pending Spec gap
- WHEN the developer and the user session state the missing promise in the owning Module's Spec
- AND the user session calls context solving again
- THEN context solving judges the Spec sufficient against the current documents
- AND planning for the change is admitted

### scenario.concorde.develop-failure — A failed implementation keeps its progress

- GIVEN a change with accepted tasks in a candidate
- WHEN the implementation call fails before the Host accepts its result
- THEN the call returns an execution failure distinct from any domain outcome
- AND the files the programmer changed stay in the candidate for inspection
- BUT the candidate is neither ready nor delivered

### scenario.concorde.review-required — A required review blocks readiness

- GIVEN a change for which a code review was recorded as required
- AND the Module's files changed after that review completed
- WHEN the user session calls validation
- THEN the candidate is not ready and the answer names the stale required review
- BUT the candidate keeps its files and its earlier evidence stays inspectable

### scenario.concorde.validate-record — Recording current evidence

- GIVEN a candidate whose tasks are complete and whose required reviews are current
- WHEN the user session calls validation
- THEN Spec validation and every configured check of the edited Modules run on the candidate's exact files
- AND their evidence is recorded for that candidate and the candidate is ready

### scenario.concorde.validate-failed-check — A failing check prevents readiness

- GIVEN a candidate whose tasks are complete
- AND one configured check of an edited Module fails on its files
- WHEN the user session calls validation
- THEN the candidate is not ready and the answer names the failing check
- BUT the failure's evidence is recorded, and the candidate keeps its files

### scenario.concorde.validate-stale — Changed files invalidate readiness

- GIVEN a ready candidate
- WHEN a file of the candidate changes and the user session calls delivery
- THEN delivery refuses because the validated evidence no longer matches the candidate's files
- AND nothing is published

## Delivering

### scenario.concorde.deliver-stage — Delivering a ready candidate

- GIVEN a ready candidate
- WHEN the user session calls delivery for its change
- THEN the verified combination of the candidate and the current primary branch is published on the change's own delivered branch
- AND the candidate's worktree is removed
- BUT the primary branch, its index and its files are unchanged

### scenario.concorde.deliver-merge — Merging a delivered change needs explicit authorization

- GIVEN a delivered change and a clean primary worktree
- WHEN the developer authorizes the merge and the user session in the primary worktree requests it
- THEN the primary branch is fast-forwarded to a verified merge of the delivered branch

## Recording and solving problems

### scenario.concorde.issue-reported — An Agent's report outlives its stage

- GIVEN a code review running for a Module
- WHEN the code reviewer reports an Issue about another Module's Spec and the review then fails
- THEN the Issue is recorded with its reporting Module and stage
- AND listing Issues through `concorde-issues` shows it
- BUT the review's own failure is reported unchanged

### scenario.concorde.issue-handback — Solving hands work back without editing

- GIVEN a committed open Issue whose fix needs a code change
- WHEN the user session calls `concorde-issues` to solve it
- THEN the answer hands the work back to the user session with the solver's stated intent
- AND the Issue stays open
- BUT no Spec or implementation file is changed

### scenario.concorde.issue-solved — A verified fix closes the Issue in its candidate

- GIVEN an open Issue whose fix the user session has made in a candidate
- WHEN the user session calls `concorde-issues` to solve it and independent review finds no blocking problem
- THEN the Issue is closed in the candidate with a recorded disposition
- AND the candidate is ready
- BUT the Issue stays open on the primary branch until the candidate is delivered and merged
