# Concorde Framework scenarios

These precise specifications belong directly to the [Concorde Framework Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Capability](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Concorde Framework

### scenario.concorde.develop-change — Successful development to a ready candidate

- GIVEN a developer supplies intended behavior and constraints
- WHEN the Framework routes the change to its providing Module and coordinates specification, planning, implementation and required evidence
- THEN the request completes with one ready candidate that meets its configured completion conditions
- AND delivery to a destination remains a separate, explicitly authorized transition

### scenario.concorde.develop-gap — Missing promise stops dependent work

- GIVEN a routed change depends on a Module promise that is not specified
- WHEN development reaches that dependency
- THEN the Framework stops the dependent work and reports the gap against its owning Module
- AND independent work in the same candidate continues
- BUT the candidate does not reach ready

### scenario.concorde.develop-failure — Failed step preserves inspectable progress

- GIVEN a routed change fails during specification, planning, implementation or evidence collection
- WHEN the failure occurs
- THEN the candidate's progress remains inspectable and resumable
- BUT the candidate is not represented as a completed delivery

### scenario.concorde.inspect-answer — Answering a Spec-grounded question

- GIVEN a developer asks a Spec-grounded question or requests a Spec or existing code-graph view
- WHEN the request is routed to Query and Routing or Views
- THEN the response is grounded in registered Spec documents and declared relationships, or in an existing raw code graph
- AND answering the question does not mutate any project contract

Project-owned custom documentation is a separate human reading surface outside Spec queries and
agent Spec context; it does not acquire authority as a registered Module contract.

### scenario.concorde.inspect-gap — Missing Spec promise reported

- GIVEN a requested answer depends on a promise that is not specified
- WHEN the query is answered
- THEN the selected interface reports the missing promise
- BUT does not guess or invent the missing behavior

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
