# Concorde Framework scenarios

These precise specifications belong directly to the [Concorde Framework Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term                                             | Meaning / definition                           |
| ------------------------------------------------ | ---------------------------------------------- |
| [Module](module.md#terminology)                  | Defined in Concorde Framework.                 |
| [Spec](module.md#terminology)                    | Defined in Concorde Framework.                 |
| [Candidate](module.md#terminology)               | Defined in Concorde Framework.                 |
| [Ready](module.md#terminology)                   | Defined in Concorde Framework.                 |
| [Delivery](module.md#terminology)                | Defined in Concorde Framework.                 |
| [Evidence](module.md#terminology)                | Defined in Concorde Framework.                 |
| [Worker](module.md#terminology)                  | Defined in Concorde Framework.                 |
| [Worktree](module.md#terminology)                | Defined in Concorde Framework.                 |
| [Issue](module.md#terminology)                   | Defined in Concorde Framework.                 |
| [Disposition](issues/lifecycle.md#terminology)   | Defined in Solving a recorded problem.         |
| [Protocol binding](spec/values.md#terminology)   | Defined in Identities and versions.            |
| [Spec context](harness/context.md#terminology)   | Defined in What information a worker receives. |
| [Initialization](spec/initialize.md#terminology) | Defined in Project initialization.             |

## Concorde Framework

### scenario.concorde.develop-change — Successful development to a ready candidate

- GIVEN a developer supplies intended behavior and constraints
- WHEN the caller explicitly selects the owning Module, edits its contract as needed and invokes planning, tasks, implementation and required evidence Operations
- THEN the request completes with one ready candidate that meets its configured completion conditions
- AND delivery to a destination remains a separate, explicitly authorized transition

### scenario.concorde.develop-gap — Missing promise stops dependent work

- GIVEN an explicitly selected change depends on a Module promise that is not specified
- WHEN assessment or planning reaches that dependency
- THEN the Framework stops the dependent work and reports the gap against its owning Module
- AND the caller may select independent work in the same candidate
- BUT the candidate does not reach ready

### scenario.concorde.develop-failure — Failed step preserves inspectable progress

- GIVEN an explicit change fails during planning, implementation or evidence collection
- WHEN the failure occurs
- THEN the candidate's progress remains inspectable and resumable
- BUT the candidate is not represented as a completed delivery

### scenario.concorde.adopt-initialize — Initializing an uninitialized project

- GIVEN an uninitialized project and a supported integration
- WHEN the developer previews and applies installation, then explicitly proposes and applies initialization
- THEN initialization pins the accepted installed Protocol binding and creates an honest Module stub
- AND unspecified business behavior is recorded as an explicit draft gap

### scenario.concorde.adopt-conflict — Conflicting ownership prevents adoption

- GIVEN an installation target already owns conflicting state, or provisioning fails
- WHEN adoption is attempted
- THEN adoption does not complete
- AND the Framework recovers previously valid owned state
- BUT no partially applied owned state is left in place

### scenario.concorde.configure-apply — Applying Pi worker configuration

- GIVEN an initialized project and an explicit, supported Pi worker model/thinking/timeout configuration
- WHEN the developer applies it
- THEN the Framework updates the configured worker selection accordingly
- BUT an unsupported configuration value fails explicitly

### scenario.concorde.validate-record — Recording current deterministic evidence

- GIVEN a candidate under development
- WHEN the developer checks it
- THEN the Framework records current deterministic Spec and configured code check evidence for that candidate
- BUT a failed or stale check cannot establish readiness

### scenario.concorde.deliver-stage — Staging a verified change for delivery

- GIVEN a ready candidate
- WHEN the developer requests delivery
- THEN the Framework stages the change on an independent branch and removes its worktree by default
- BUT merging into the primary branch requires a further, separately authorized request by the sole primary writer

### scenario.concorde.issues — Working with recorded feedback

- GIVEN feedback or a persistent gap recorded against a Module or scenario identity
- WHEN the developer inspects it through concorde-issues
- THEN inspection is read-only
- AND any mutation follows its declared evidence and disposition conditions
