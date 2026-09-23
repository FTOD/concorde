# Framework scenarios

These scenarios describe whole flows that cross several Modules, from the developer's point of
view. The acceptance tests bound to the root Module verify them.

## Changing a project

### scenario.concorde.develop-change — A change reaches a ready candidate

- GIVEN a developer has agreed the intended behaviour in the owning Module's Spec
- WHEN the user session calls planning, tasks, implementation, review and validation for that Module
- THEN the change ends as one ready candidate that meets its configured checks
- AND delivering it remains a separate request

### scenario.concorde.develop-gap — A missing promise stops dependent work

- GIVEN a change depends on a promise that the owning Module's Spec does not state
- WHEN assessment or planning reaches that dependency
- THEN the step stops and reports the gap against the owning Module
- AND the user session may still choose independent work in the same candidate
- BUT the candidate does not become ready

### scenario.concorde.develop-failure — A failed step keeps its progress

- GIVEN a change fails during planning, implementation or validation
- WHEN the failure is reported
- THEN the candidate's progress remains available to inspect and resume
- BUT the candidate is not reported as delivered

## Adopting Concorde

### scenario.concorde.adopt-initialize — Initializing a new project

- GIVEN an uninitialized project
- WHEN the developer installs Concorde and then proposes and applies initialization
- THEN the project records the installed Protocol version it accepted
- AND it receives a starting Spec whose unknown business behaviour is stated as an open gap

### scenario.concorde.adopt-conflict — A conflicting installation leaves the project unchanged

- GIVEN the target project already has conflicting files, or provisioning fails
- WHEN installation is applied
- THEN installation does not complete
- AND the previously installed state is restored
- BUT no partially applied state remains

### scenario.concorde.configure-apply — Configuring workers

- GIVEN an initialized project and a supported worker model, thinking level and time limit
- WHEN the developer applies that configuration
- THEN later workers use it
- BUT an unsupported value is rejected with an explicit error

## Checking and delivering

### scenario.concorde.validate-record — Recording current evidence

- GIVEN a candidate under development
- WHEN the developer validates it
- THEN the Spec checks and configured code checks run, and their evidence is recorded for that candidate
- BUT a failed or stale check cannot make the candidate ready

### scenario.concorde.deliver-stage — Delivering a ready candidate

- GIVEN a ready candidate
- WHEN the developer requests delivery
- THEN the change is staged on its own branch and its worktree is removed by default
- BUT merging into the primary branch needs a further, separate authorization

### scenario.concorde.issues — Inspecting recorded problems

- GIVEN a problem was recorded against a Module or scenario
- WHEN the developer lists or shows it through `concorde-issues`
- THEN nothing changes
- AND any change to the record follows the Issues Module's evidence and disposition rules
