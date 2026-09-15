# Topology evolution Agent Flow

Use this Flow when registered targets, document ownership and references, shared truth or routing structure
must change together. The developer supplies intended behavior and constraints. Main designs a
candidate registry; fresh target-local authors supply the affected Specs after design acceptance.
A second acceptance binds the exact prepared transaction before application.

Human acceptance is a Flow control input tied to the exact design or prepared application. A
rejection may select another design or authoring loop, but cannot authorize the rejected effects.
The loop waits for a required decision and re-admits revised intent and current source identity.
Topology-designer and target-author invocations retain separate Agent definitions and Harness bindings.

## Design

### Topology preparation Flow (`topology_flow`)

State: `occurrence` (the author being run), `route`, `output` (the main response), `result`.
The accepted design supplies the candidate registry and one Spec task per new or changed Module.

| Node | Executes | in | out |
| --- | --- | --- | --- |
| `prepare_authors` | Deterministic: validates the accepted design against the current registry and orders the target-local authors so providers precede consumers. | accepted design, registry | ordered authors |
| `author_module` | One topology-author invocation for the current author; its replacements join the candidate overlay. | Module descriptor, candidate context | candidate documents |
| `validate_candidate` | Deterministic repository validation of the complete candidate overlay. | candidate registry, candidate documents | validated candidate |
| `review_contexts` | Sequential work items: every affected old or candidate context receives an independent Spec compatibility review. | candidate, affected contexts | review evidence |
| `persist_application` | Deterministic: the exact prepared application (registry and document bytes with before-digests) is written for the second acceptance. | validated candidate | prepared application |

```mermaid
flowchart TB
    %% flow: topology_flow
    accTitle: Topology preparation Flow
    accDescr: Authors are ordered and run one at a time; the complete candidate is validated and every affected context reviewed before the application is persisted; a gap, invalid candidate or review blocker ends the Flow.
    __start__["start"]
    prepare_authors["prepare_authors<br/>in: accepted design, registry<br/>out: ordered authors"]
    author_module["author_module<br/>in: Module descriptor, candidate context<br/>out: candidate documents"]
    validate_candidate["validate_candidate<br/>in: candidate registry, candidate documents<br/>out: validated candidate"]
    review_contexts["review_contexts<br/>in: candidate, affected contexts<br/>out: review evidence"]
    persist_application["persist_application<br/>in: validated candidate<br/>out: prepared application"]
    __end__["end"]
    __start__ --> prepare_authors
    prepare_authors -->|authors remain| author_module
    prepare_authors -->|no author needed| validate_candidate
    prepare_authors -->|error| __end__
    author_module -->|more authors remain| author_module
    author_module -->|every author completed| validate_candidate
    author_module -->|author gap, failure or error| __end__
    validate_candidate -->|candidate valid| review_contexts
    validate_candidate -->|candidate invalid| __end__
    review_contexts -->|every affected context reviewed| persist_application
    review_contexts -->|review blocked| __end__
    persist_application --> __end__
```

### Topology application Flow (`topology_apply_flow`)

State: `route`, `output`, `result`.

| Node | Executes | in | out |
| --- | --- | --- | --- |
| `admit_application` | Deterministic: the referenced application is inside the proposal area, matches the accepted design, base registry and Protocol binding; describe-policy stops here. | application reference, registry | admitted application |
| `validate_application` | Deterministic validation of the application's complete overlay. | admitted application | validated application |
| `apply_atomically` | Deterministic: one file transaction with before-digests and final repository validation, bound to this worktree's owning task. | validated application | applied files |
| `cleanup` | Deterministic: removes the consumed proposal artifacts and records the applied topology. | applied files | main response |

```mermaid
flowchart TB
    %% flow: topology_apply_flow
    accTitle: Topology application Flow
    accDescr: An admitted, validated application is applied as one transaction and cleaned up; a rejected or stale application, a validation failure or a transaction error ends the Flow.
    __start__["start"]
    admit_application["admit_application<br/>in: application reference, registry<br/>out: admitted application"]
    validate_application["validate_application<br/>in: admitted application<br/>out: validated application"]
    apply_atomically["apply_atomically<br/>in: validated application<br/>out: applied files"]
    cleanup["cleanup<br/>in: applied files<br/>out: main response"]
    __end__["end"]
    __start__ --> admit_application
    admit_application -->|application admitted| validate_application
    admit_application -->|policy described, rejected or stale| __end__
    validate_application -->|overlay valid| apply_atomically
    validate_application -->|validation failed| __end__
    apply_atomically -->|applied| cleanup
    apply_atomically -->|transaction failed| __end__
    cleanup --> __end__
```

No target author writes project files. A gap or unresolved consumer compatibility leaves the
pre-design project unchanged. Prepared
artifacts contain full proposed bytes, but only their path/digest enters the topology designer's cognition.
Application is one host transaction with current before-digests and final repository validation.

Every new Concorde Module includes a local `module.md` with an inline Mermaid entity diagram
whose `accTitle` and `accDescr` describe it for readers who cannot see it. Its author returns the
complete registered Markdown replacements, including diagram fences. The host checks all proposed
files as one overlay before exposing the prepared application. Diagram content cannot widen Spec
membership or agent permissions. Only the sole owner proposes shared source bytes; all affected consumers receive separate compatibility checks.
