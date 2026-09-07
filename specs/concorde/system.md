```concorde-document
{
  "id": "document.concorde.system",
  "targets": ["domain.concorde"],
  "main_visible": true
}
```

# Concorde: business scopes and operating principles

Concorde turns an explicitly specified change into bounded agent work and verifiable delivery.
The user owns intended behavior. The Protocol owns universal architectural and cognitive rules.
The project registry indexes the complete resolved Spec of each target and grants implementation ownership.
A target is a Domain scope, Service boundary or Module interface; a Feature or API focuses use of
that target without reducing its complete context.

## Entities and relationships

| Entity | Meaning and responsibility | When it interacts |
| --- | --- | --- |
| Domain | A problem scope describing entities, ownership and rules | Explains collaborations; coordinates component changes through separately selected targets |
| Service | A capability with a self-contained consumer contract | Accepts and produces explicitly typed boundary data |
| Module | An implementation responsibility defined by its public API | Calls other interfaces under its local required contract |
| Spec document | One stable physical Markdown truth with explicit target references and main visibility | Appears as Target Spec when local or Shared Specs when collectively referenced |
| Resolved Spec context | Ordered Target Spec plus one-hop Shared Specs for one target | Must be self-contained without expanding any related entity's remaining collection |
| Protocol | Versioned global principles and kind definitions | Is pinned by initialization and injected by the context service |
| Operation | A public Skill paired with an executable host entry, or an internal stage reachable only through a composing public Operation | Receives configuration and runtime input as distinct typed JSON values |
| Context snapshot | Immutable exact input to one agent invocation | Binds documents, Protocol, task, phase, instructions and typed stage artifacts |
| Discovery context | Ordered append-only main-visible Domain/Service documents for the main coordinator | Expands on demand and changes identity on every admitted target |
| Main coordinator | Global routing agent that never directly expands Module targets or reads code | Selects fresh target workers and later synthesizes only typed results |
| Participant declaration | A Domain-local routing description of one Service or Module | Binds a registry participation edge to stable ID, kind, local responsibility, selection condition and relied-upon promises |
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
Every direct component participation edge is repeated as one machine-readable declaration in that
Domain's own collection. This intentional redundancy lets Domain workers select exact component IDs
without reading the registry or component Specs; deterministic validation keeps both views aligned.

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
outcome. Code is available to implementation stages and their dedicated read-only code-review role. Business facts missing from the Spec may
not be reconstructed from code. The host runs separately configured checks and retains their logs;
only bounded check status and revision identities can cross back to Spec-only work.

The main coordinator is a distinct agent role. It may expand its append-only discovery context with
only main-visible Domain and Service Target Spec/Shared Specs, but never directly expands a Module or reads code. After it returns typed routes,
the host privately resolves each target and starts a different worker. Typed worker results may
return for synthesis; raw target snapshots do not.

The public `concorde-main` replaces the former standalone ask Operation. Its topology design action
may additionally inspect exact registry metadata and all global kind definitions, but no Module
target expansion or code. The coordinator produces structure; fresh target-local authors produce complete Spec bytes
privately; the host validates an overlay and exposes only an application ArtifactRef. Maintainer
acceptance is required once before target authoring and again before the exact registry/document
transaction.

Shared truth has no unique owner. A normal single-target author can read but not change it. A
topology change tasks every affected reference and accepts a shared replacement only when all
candidate referencing authors return identical bytes; the resulting transaction intentionally
invalidates every referencing context.

A candidate becomes ready only when selected tasks, required checks and required reviews complete,
local/shared contracts are valid, concrete task gaps are resolved and evidence still matches current
Spec, code and review inputs. The standard loop reviews Spec before planning and code after checks;
fast loops explicitly record disabled review and cannot downgrade prior requirements. A review with
no findings is bounded evidence, not proof of universal semantic completeness. Delivery is a separate
action available from either participating worktree that verifies the actual merge and merges into
the primary worktree's current branch. It retains the source when requested or hosting the active
session, and otherwise removes it. Failure preserves the candidate and its
recorded progress; repair resumes with current contexts and invalidated stale evidence.

## feature.concorde.evolve-protocol

A Protocol change affects all consumers, not just Concorde's self-description. A maintainer authors
principles and corresponding schemas, runtime admission, context grants, templates, installation
and publication behavior together. The distributable Protocol is versioned and hashed. Existing
projects do not silently acquire a new meaning: they must explicitly accept compatible bindings.
Source Profile 8 rejects Profile 7 for agent work, and there is no migration Operation; Profile 7
projects are rejected outright. Legacy deterministic readers remain diagnostic utilities only.

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
