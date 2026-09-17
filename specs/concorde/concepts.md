# Concepts for reading Concorde

Start here if you know software development but not Concorde's implementation. These definitions
name the ideas used throughout the Specs. Individual Modules explain what they do with them;
implementation references define exact fields and algorithms.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| Module | One cohesive software responsibility, such as planning a change or publishing documentation. It need not be a separate package. |
| Spec | The agreed description of a Module's intended behavior and design, used to guide work and judge its result. |
| Module Specs | The explanation-first part of a Module's Spec: purpose, concepts, correct use, design and collaborations. |
| Implementation Specs | The same Module's precise requirements, acceptance situations and technical contracts. They are specifications, not source code. |
| Entity | A named participant, concept or record that matters to a Module's behavior or design. Its role is explained where it participates. |
| Requirement | A precise obligation applying across a Module, defined once with a stable identity. |
| Scenario | A concrete situation with preconditions, an action and an expected outcome, used as a basis for verification. |
| Registry | The explicit record of Modules, document owners, relationships and implementation-file bindings. |
| Context | The information explicitly made available for one task. Knowing that another document exists does not make it available. |
| Grant | Permission to use particular tools or read/write particular files for one invocation; information and permission are separate. |
| Snapshot | A record of exactly which inputs a task received, so later changes can be detected. |
| Evidence | A recorded check or review result tied to the inputs it examined, not a permanent guarantee about future revisions. |
| Capability | An executable operation with defined inputs and results. Some operations use a model; others run ordinary code. |
| Skill | Instructions that let a developer's agent client invoke a public Concorde capability. |
| Worker | One fresh agent execution for a bounded job, such as writing a plan or reviewing code. |
| Host | The non-model program that checks requests, chooses allowed work, runs workers and records accepted results. |
| Harness | The services that give a worker its inputs, tools, environment and limits, then check its result. |
| Flow | The declared sequence and branching of operations that pursue a goal. A loop is a feedback path within that execution. |
| Candidate | An isolated proposed project change together with its progress and verification records. It is not yet an update to the primary branch. |
| Worktree | A separate working directory of a Git repository, used here to keep candidate changes apart from primary work. |
| Ready | The candidate has met the required current checks and reviews; it has not thereby been delivered or merged. |
| Delivery | A separately requested operation that publishes a verified candidate and normally removes its source worktree; merging primary needs separate authorization. |
| Issue | A durable record of an observed bug, missing/conflicting promise or limitation. Recording it does not itself stop work or authorize repair. |
| Blocker | A task's recorded dependency on a problem that prevents a particular next step. Releasing it does not automatically close the Issue. |
| Contract | A precise agreement about inputs, effects, results, failures or constraints that callers and implementations rely on. |

## Follow one change

Suppose you ask to add retry behavior. Concorde selects the responsible Module and checks its Spec.
If the Spec does not say which failures may be retried, the task needs clarification before a useful
plan can be written. A worker records that missing promise rather than inferring it from code.

Once the contract is clear, planning produces tasks, implementation changes the allowed code, and
checks and independent review assess the candidate. If code changes after a successful review, that
old evidence no longer establishes the new revision's readiness. Ready ends development; delivery
and any primary merge are later, explicit choices.

## Use the vocabulary, not an inventory

A term explains a concept. It is not a declaration that a Module owns a file, depends on another
Module, or can read another worker's context. Those facts are separately recorded and explained by
the relevant Module. The [registry topic](spec/registry.md) illustrates these distinctions, and the
[Framework entry](module.md) helps choose an operation.
