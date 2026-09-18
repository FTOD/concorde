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
| State | The declared data channels an Operation accepts and updates when invoked as a graph node. State carries task information and results, never execution authority. |
| Operation | Concorde's only executable entity: a complete callable with an input State, output State updates, effects, use conditions and execution policy. It can run as a LangGraph node using deterministic code, a model or a compiled graph. |
| Skill | Instructions that let a developer's agent client invoke a public Concorde operation. |
| Worker | One fresh agent execution for a bounded job, such as writing a plan or reviewing code. |
| Host | The non-model program that checks requests, chooses allowed work, runs workers and records accepted results. |
| Harness | The services that give a worker its inputs, tools, environment and limits, then check its result. |
| Graph | LangGraph's declared nodes, edges and State channels for executing and composing Operations. A compiled graph can implement another Operation; a loop is a feedback path, not another executable kind. |
| Candidate | An isolated proposed project change together with its progress and verification records. It is not yet an update to the primary branch. |
| Worktree | A separate working directory of a Git repository, used here to keep candidate changes apart from primary work. |
| Ready | The candidate has met the required current checks and reviews; it has not thereby been delivered or merged. |
| Delivery | A separately requested operation that publishes a verified candidate and normally removes its source worktree; merging primary needs separate authorization. |
| Issue | A durable record of an observed bug, missing/conflicting promise or limitation. Recording it does not itself stop work or authorize repair. |
| Blocker | A task's recorded dependency on a problem that prevents a particular next step. Releasing it does not automatically close the Issue. |
| Contract | A precise agreement about inputs, effects, results, failures or constraints that callers and implementations rely on. |

## Complete Operations, bounded execution

A caller selects an Operation and supplies its declared State. The Operation carries the policy
for selecting context, limiting effects, executing any model work and checking results. The caller
does not reassemble those steps to make an internal building block safe or meaningful. Public and
internal Operations have the same completeness obligation; exposure only decides which entries a
developer may invoke directly.

Completeness does not mean self-sufficiency from trusted infrastructure. The common Host and
Harness apply the Operation's declared policy and permission ceiling to the actual task, narrowing
the effective grant. Trusted Runtime context supplies those services. State carries information,
never a Host, credential, permission grant or authority to expand one.

For example, planning is an Operation with Spec-only reasoning and an admitted plan result.
`dev-loop` composes it with specification, implementation and verification Operations. The compiled
composition is still an Operation: it has its own input, result, effects and stopping conditions.
`specify-loop` is likewise a composed Operation, not a different executable category.

## Three independent relationships

- **Module ownership** identifies who promises behavior and owns its Spec. One Module can provide
  several Operations; one composed Operation can rely on several provider Modules.
- **Operation composition** identifies which Operations call others in a graph. It does not make
  a provider Module a child of the caller's Module.
- **Context references** select knowledge supplied to a task. They neither compose Operations nor
  grant execution permission or transfer ownership.

The [Operations layer](operations/module.md) organizes the responsibilities that provide reusable
and composed Operations. The common execution infrastructure serves that layer; it is not a second
inventory of executable entities.

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
