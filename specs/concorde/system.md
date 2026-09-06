# Concorde: business scopes and operating principles

Concorde turns an explicitly specified change into bounded agent work and verifiable delivery.
The user owns intended behavior. The Protocol owns universal architectural and cognitive rules.
The project registry identifies the complete Spec of each target and grants implementation ownership.
A target is a Domain scope, Service boundary or Module interface; a Feature or API focuses use of
that target without reducing its complete context.

## Entities and relationships

| Entity | Meaning and responsibility | When it interacts |
| --- | --- | --- |
| Domain | A problem scope describing entities, ownership and rules | Explains collaborations; coordinates component changes through separately selected targets |
| Service | A capability with a self-contained consumer contract | Accepts and produces explicitly typed boundary data |
| Module | An implementation responsibility defined by its public API | Calls other interfaces under its local required contract |
| Spec collection | Ordered, explicit Markdown members for one target | Supplies all local facts needed by every non-implementation task |
| Protocol | Versioned global principles and kind definitions | Is pinned by initialization and injected by the context service |
| Operation | A public Skill paired with an executable host entry | Receives configuration and runtime input as distinct typed JSON values |
| Context snapshot | Immutable exact input to one agent invocation | Binds documents, Protocol, task, phase, instructions and typed stage artifacts |
| Discovery context | Ordered append-only Domain/Service collections for the main coordinator | Expands on demand and changes identity on every admitted target |
| Main coordinator | Global routing agent that never reads Module Specs or code | Selects fresh target workers and later synthesizes only typed results |
| Topology design | Complete candidate registry, local Spec tasks and acceptance conditions | Is authored by the coordinator without writing and requires maintainer acceptance |
| Topology application | Exact host-private registry/document replacements with before-digests | Is applied atomically only after a second maintainer acceptance |
| Change attempt | Plan, tasks and revision-bound completion evidence | Lives from successful planning until verified delivery |
| Spec gap | A named missing fact blocking the admitted task | Stops the workflow until an explicit authoring task supplies that fact |
| Reflection | A retained problem report with independent human disposition | Enters code investigation only through an implementation phase |

Workflow scopes the change lifecycle and the relationship between context, agent execution,
validation and delivery. Installation scopes distributing the same Protocol and public Operations
to every project. Publication scopes a human-readable projection of registered source documents.
These three scopes narrow Concorde's problem space. They are not three implementation containers.
The context Service participates in Workflow and Installation. Package assets participates in both
because the same executable/prompt pair must run in a source checkout and an installed project.
Publication reads registry metadata deterministically; it never grants an agent cross-target access.

## Main routing view

The main coordinator starts with this complete collection. It selects `domain.workflow` for tasks
about Spec contexts, Operations, planning, implementation, validation, delivery or Reflections;
`domain.installation` for package, installation, initialization, configuration, upgrade or runtime
provisioning behavior; and `domain.docsite` for documentation publication, navigation, diagrams or
the architecture graph. A task that changes the universal Protocol itself remains on
`domain.concorde`, focused on `feature.concorde.evolve-protocol`. These stable IDs and selection
conditions are routing facts only; opening a child Domain requires an explicit main-context
expansion.

The Operation host uses the context Service before each agent stage. It executes a fresh process,
receives typed completion, then either persists only authorized changes or reports the exact blocked
outcome. Code is available only to implementation stages. Business facts missing from the Spec may
not be reconstructed from code. The host runs separately configured checks and retains their logs;
only bounded check status and revision identities can cross back to Spec-only work.

The main coordinator is a distinct agent role. It may expand its append-only discovery context with
registered Domain and Service Specs, but never Module Specs or code. After it returns typed routes,
the host privately resolves each target and starts a different worker. Typed worker results may
return for synthesis; raw target snapshots do not.

The public `concorde-main` replaces the former standalone ask Operation. Its topology design action
may additionally inspect exact registry metadata and all global kind definitions, but no Module body
or code. The coordinator produces structure; fresh target-local authors produce complete Spec bytes
privately; the host validates an overlay and exposes only an application ArtifactRef. Maintainer
acceptance is required once before target authoring and again before the exact registry/document
transaction.

Delivery means all selected tasks are complete, required checks pass, local/shared contracts are
valid and evidence still matches current Spec and implementation bytes. It removes the completed
attempt. Delivery does not merge or publish a branch. Failure preserves an inspectable attempt;
retry requires the same intent and current evidence, or an explicitly new change after Spec edits.

## feature.concorde.evolve-protocol

A Protocol change affects all consumers, not just Concorde's self-description. A maintainer authors
principles and corresponding schemas, runtime admission, context grants, templates, installation
and publication behavior together. The distributable Protocol is versioned and hashed. Existing
projects do not silently acquire a new meaning: they must explicitly accept compatible bindings
or migrate their authored registry and self-contained documents. Source Profile 8 rejects Profile 7
for agent work. Legacy deterministic readers remain diagnostic utilities only.

Changing the Protocol is an explicitly authorized version cutover, not ordinary work performed
under the version being replaced. The previous Protocol remains authoritative for its published
version and for unrelated work, but it does not validate the incomplete intermediate state of its
own replacement. The maintainer first reconciles every normative asset, runtime boundary, self Spec,
consumer-facing migration and executable check. Only the completed candidate is validated under its
own proposed rules. Until that validation succeeds, the candidate is unpublished, cannot be bound by
consumer projects and cannot be described as the active Protocol. This bootstrap exception is limited
to the coordinated Protocol cutover and does not authorize ordinary changes to bypass the active
workflow.

Concorde's own code is changed under the user's authorized refactor task. Product agent workflows
must continue to obey these same rules. Structural checks cannot establish semantic completeness
for every future task; a successful task-specific assessment is bounded by its recorded context.
