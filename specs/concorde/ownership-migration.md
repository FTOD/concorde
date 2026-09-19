# Historical operation ownership migration

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module](module.md#terminology) | Defined in Concorde Framework. |
| [Spec](module.md#terminology) | Defined in Concorde Framework. |
| [Operation](module.md#terminology) | Defined in Concorde Framework. |
| [Contract](module.md#terminology) | Defined in Concorde Framework. |
| [Requirement](module.md#terminology) | Defined in Concorde Framework. |
| [Scenario](module.md#terminology) | Defined in Concorde Framework. |
| [Entity](module.md#terminology) | Defined in Concorde Framework. |
| [Ownership](spec/registry.md#terminology) | Defined in Registry. |
| [Reference](spec/registry.md#terminology) | Defined in Registry. |
| [Implementation binding](spec/registry.md#terminology) | Defined in Registry. |
| [Evidence](module.md#terminology) | Defined in Concorde Framework. |

## Historical scope

This is a record of the earlier operation-ownership split, preserved from the pre-Protocol-8
source baseline. Version numbers and “current” entries below describe that migration, not the
current runtime agreement. Read each owning Module for present behavior.

In the later explanation-page consolidation, the Delivery, Development Graph, Query and Routing,
and Topology topics listed below were retired into their existing Module entries. Their historical
document IDs are not aliases for those entries. The table retains the migration's source locators
as text and links to the surviving reading entries; requirements, scenarios and contracts retain
their identities and ownership.

## Design

This ledger records the explicitly authorized direct Spec maintenance against the saved current-byte
baseline, not committed HEAD. Stable prefixes do not prescribe ownership. Every original document,
requirement, scenario, entity and canonical contract ID remains defined exactly once; the entries
below are the definitions whose owner or physical locator changed. Unlisted IDs retain ownership.
The three canonical contracts and their four participant bindings retain their versions and peers;
in particular Harness and Development remain the participants in context.selection version 2.
Review-result remains the same version-1 wire value, now owned by Review.

| Stable definition | Previous owner and source | Current owner and definition |
| --- | --- | --- |
| `document.development.delivery` | `module.development` · `specs/concorde/development/delivery.md` | `module.delivery` · `delivery/delivery.md` (now [Module entry](delivery/module.md)) |
| `document.development.development` | `module.development` · `specs/concorde/development/development.md` | `module.dev-loop` · `dev-loop/development.md` (now [Module entry](dev-loop/module.md)) |
| `document.development.query-and-routing` | `module.development` · `specs/concorde/development/query-and-routing.md` | `module.query-routing` · `query-routing/query-and-routing.md` (now [Module entry](query-routing/module.md)) |
| `document.development.review-result` | `module.development` · `specs/concorde/development/review-result.md` | `module.review` · [definition](review/review-result.md) |
| `document.development.topology` | `module.development` · `specs/concorde/development/topology.md` | `module.topology` · `topology/topology.md` (now [Module entry](topology/module.md)) |
| `req.development.check-isolation` | `module.development` · `specs/concorde/development/module.md` | `module.validation` · [`req.validation.check-isolation`](validation/requirements.md#req.validation.check-isolation) |
| `req.development.explicit-skip-sticky` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [`req.dev-loop.explicit-skip-sticky`](dev-loop/requirements.md#req.dev-loop.explicit-skip-sticky) |
| `req.development.global-discovery` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [`req.query-routing.global-discovery`](query-routing/requirements.md#req.query-routing.global-discovery) |
| `req.development.non-repair-stops-graph` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [`req.dev-loop.non-repair-stops-graph`](dev-loop/requirements.md#req.dev-loop.non-repair-stops-graph) |
| `req.development.primary-writes-serialized` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [`req.delivery.primary-writes-serialized`](delivery/requirements.md#req.delivery.primary-writes-serialized) |
| `req.development.repair-edge-only` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [`req.dev-loop.repair-edge-only`](dev-loop/requirements.md#req.dev-loop.repair-edge-only) |
| `req.development.routing-hint-no-grant` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [`req.query-routing.routing-hint-no-grant`](query-routing/requirements.md#req.query-routing.routing-hint-no-grant) |
| `req.development.routing-hint-not-context` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [`req.query-routing.routing-hint-not-context`](query-routing/requirements.md#req.query-routing.routing-hint-not-context) |
| `req.development.shared-document-agreement` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [`req.topology.shared-document-agreement`](topology/requirements.md#req.topology.shared-document-agreement) |
| `req.development.single-primary-writer` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [`req.delivery.single-primary-writer`](delivery/requirements.md#req.delivery.single-primary-writer) |
| `req.development.specify-loop-boundary` | `module.development` · `specs/concorde/development/module.md` | `module.specify-loop` · [`req.specify-loop.boundary`](specify-loop/requirements.md#req.specify-loop.boundary) |
| `req.development.specify-loop-composition` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [`req.dev-loop.specify-loop-composition`](dev-loop/requirements.md#req.dev-loop.specify-loop-composition) |
| `scenario.development.answer-gap` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [`scenario.query-routing.answer-gap`](query-routing/scenarios.md#scenario.query-routing.answer-gap) |
| `scenario.development.answer-question` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [`scenario.query-routing.answer-question`](query-routing/scenarios.md#scenario.query-routing.answer-question) |
| `scenario.development.deliver-branch` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [`scenario.delivery.branch`](delivery/scenarios.md#scenario.delivery.branch) |
| `scenario.development.deliver-conflict` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [`scenario.delivery.conflict`](delivery/scenarios.md#scenario.delivery.conflict) |
| `scenario.development.deliver-merge-primary` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [`scenario.delivery.merge-primary`](delivery/scenarios.md#scenario.delivery.merge-primary) |
| `scenario.development.deliver-session-rejected` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [`scenario.delivery.session-rejected`](delivery/scenarios.md#scenario.delivery.session-rejected) |
| `scenario.development.dev-loop-coordinated` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [`scenario.dev-loop.coordinated`](dev-loop/scenarios.md#scenario.dev-loop.coordinated) |
| `scenario.development.dev-loop-ready` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [`scenario.dev-loop.ready`](dev-loop/scenarios.md#scenario.dev-loop.ready) |
| `scenario.development.dev-loop-repair` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [`scenario.dev-loop.repair`](dev-loop/scenarios.md#scenario.dev-loop.repair) |
| `scenario.development.dev-loop-repair-exhausted` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [`scenario.dev-loop.repair-exhausted`](dev-loop/scenarios.md#scenario.dev-loop.repair-exhausted) |
| `scenario.development.dev-loop-spec-gap` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [`scenario.dev-loop.spec-gap`](dev-loop/scenarios.md#scenario.dev-loop.spec-gap) |
| `scenario.development.discovery-limit` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [`scenario.query-routing.discovery-limit`](query-routing/scenarios.md#scenario.query-routing.discovery-limit) |
| `scenario.development.resume-bound` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [`scenario.dev-loop.resume-bound`](dev-loop/scenarios.md#scenario.dev-loop.resume-bound) |
| `scenario.development.resume-unbound` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [`scenario.dev-loop.resume-unbound`](dev-loop/scenarios.md#scenario.dev-loop.resume-unbound) |
| `scenario.development.specify-loop` | `module.development` · `specs/concorde/development/module.md` | `module.specify-loop` · [`scenario.specify-loop.independent`](specify-loop/scenarios.md#scenario.specify-loop.independent) |
| `scenario.development.standalone-review` | `module.development` · `specs/concorde/development/module.md` | `module.review` · [`scenario.review.standalone`](review/scenarios.md#scenario.review.standalone) |
| `scenario.development.task-history-identities` | `module.development` · `specs/concorde/development/module.md` | `module.planning` · [`scenario.planning.task-history-identities`](planning/scenarios.md#scenario.planning.task-history-identities) |
| `scenario.development.task-scope-repair` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [`scenario.dev-loop.task-scope-repair`](dev-loop/scenarios.md#scenario.dev-loop.task-scope-repair) |
| `scenario.development.topology-accept` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [`scenario.topology.accept`](topology/scenarios.md#scenario.topology.accept) |
| `scenario.development.topology-apply` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [`scenario.topology.apply`](topology/scenarios.md#scenario.topology.apply) |
| `scenario.development.topology-design` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [`scenario.topology.design`](topology/scenarios.md#scenario.topology.design) |
| `scenario.development.topology-stale` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [`scenario.topology.stale`](topology/scenarios.md#scenario.topology.stale) |
| `scenario.development.validate-blocked` | `module.development` · `specs/concorde/development/module.md` | `module.validation` · [`scenario.validation.blocked`](validation/scenarios.md#scenario.validation.blocked) |
| `scenario.development.validate-check-isolation` | `module.development` · `specs/concorde/development/module.md` | `module.validation` · [`scenario.validation.check-isolation`](validation/scenarios.md#scenario.validation.check-isolation) |
| `scenario.development.validate-ready` | `module.development` · `specs/concorde/development/module.md` | `module.validation` · [`scenario.validation.ready`](validation/scenarios.md#scenario.validation.ready) |

### Compatibility and evidence scope

All new providers and graphs have Concorde Framework as their sole parent; uses and local dependency
promises describe reuse. The old Development package binding is retained and exact existing wrapper
entries are shared by new semantic owners. No runtime source is physically extracted. Original
checks remain registered unchanged; a missing scenario verification remains visible coverage evidence.
No new lifecycle-ready, review, delivery or arbitrary-composition implementation claim follows from
this editorial migration. Revisions, contexts, plans and reviews affected by ownership, references or
source bytes need fresh evidence under the normal runtime gates.

Common host transport, invocation permissions, gap history and compatibility stay in Development.
[Planning Module](planning/module.md) owns sufficiency, plan and tasks; [Implementation Module](implementation/module.md) owns bounded task fulfillment. Spec
Authoring, Review, Validation, Delivery, [Query and Routing](query-routing/module.md), and Topology own their cohesive effects.
[Specification Graph](specify-loop/module.md) and [Development Graph](dev-loop/module.md) own their sequencing and completion policy. Current repair
and component adapters still constrain reuse; broader graph adapters require separately implemented,
reviewed and verified support.

## Development dissolution

The `module.development` Module was later dissolved. After the earlier split it kept only the
common operation host: admission, dispatch, the Operation registry, the shared wire contracts and
gap history, together with the source package that still realized most providers. Admission,
workspace binding, the candidate relay, the wire contracts and the admission Graph now belong to
the [Harness Module](harness/module.md); the Operation catalog, public/internal exposure, declared
composition and the dispatch and target admission Graphs belong to the
[Operations Module](operations/module.md); task blockers and their history belong to the
[Issues Module](issues/module.md). The component coordination and stabilization Graphs moved to
[Implementation](implementation/module.md) and the project Graph to [Spec](spec/module.md). Each
provider's realization moved from `src/concorde/development/` into its own package, and its
adapter entity lists that package. The statements above that host transport, invocation permissions
and gap history stay in Development, and that the Development package binding is retained, describe
the earlier split only.

Transferred document units keep their identities, as ownership transfer requires. The entry, the
host coordination topic and the collaboration agreements were retired; their content now lives in
the owners above, and their identities `document.development.module`,
`document.development.graphs` and `document.development.collaborations` are not aliases of any
current document. The canonical `contract.context.selection` version 3 keeps its definition and
version; its required participant is now Operations, which binds a Module-bound invocation, with
Harness as the provider.

| Stable definition | Previous owner and source | Current owner and definition |
| --- | --- | --- |
| `document.development.interfaces` | `module.development` · `specs/concorde/development/interfaces.md` | `module.harness` · [admission contracts](harness/admission.md) |
| `document.development.execution-reference` | `module.development` · `specs/concorde/development/execution-reference.md` | `module.operations` · [catalog and dispatch contracts](operations/execution-reference.md) |
| `document.development.operations` | `module.development` · `specs/concorde/development/operations.md` | `module.operations` · [composition topic](operations/composition.md) |
| `document.development.requirements` | `module.development` · `specs/concorde/development/requirements.md` | `module.operations` · [requirements](operations/requirements.md) |
| `document.development.scenarios` | `module.development` · `specs/concorde/development/scenarios.md` | `module.operations` · [scenarios](operations/scenarios.md) |
| `document.development.review-and-gaps` | `module.development` · `specs/concorde/development/review-and-gaps.md` | `module.issues` · [blockers topic](issues/blockers.md) |
| `req.development.single-boundary` | `module.development` · `specs/concorde/development/requirements.md` | `module.harness` · [`req.harness.single-boundary`](harness/requirements.md#req.harness.single-boundary) |
| `req.development.project-root-is-working-directory` | `module.development` · `specs/concorde/development/requirements.md` | `module.harness` · [`req.harness.project-root-is-working-directory`](harness/requirements.md#req.harness.project-root-is-working-directory) |
| `req.development.distinct-outcomes` | `module.development` · `specs/concorde/development/requirements.md` | `module.harness` · [`req.harness.distinct-outcomes`](harness/requirements.md#req.harness.distinct-outcomes) |
| `req.development.langgraph-control-flow` | `module.development` · `specs/concorde/development/requirements.md` | `module.harness` · [`req.harness.langgraph-control-flow`](harness/requirements.md#req.harness.langgraph-control-flow) |
| `req.development.no-implementation-for-non-code` | `module.development` · `specs/concorde/development/requirements.md` | `module.harness` · [`req.harness.no-implementation-for-non-code`](harness/requirements.md#req.harness.no-implementation-for-non-code) |
| `req.development.stage-no-skill` | `module.development` · `specs/concorde/development/requirements.md` | `module.operations` · [`req.operations.stage-no-skill`](operations/requirements.md#req.operations.stage-no-skill) |
| `req.development.stage-in-process-only` | `module.development` · `specs/concorde/development/requirements.md` | `module.operations` · [`req.operations.stage-in-process-only`](operations/requirements.md#req.operations.stage-in-process-only) |
| `req.development.stage-no-reselect` | `module.development` · `specs/concorde/development/requirements.md` | `module.operations` · [`req.operations.stage-no-reselect`](operations/requirements.md#req.operations.stage-no-reselect) |
| `scenario.development.execute-operation` | `module.development` · `specs/concorde/development/scenarios.md` | `module.harness` · [`scenario.harness.execute-operation`](harness/scenarios.md#scenario.harness.execute-operation) |
| `scenario.development.execute-blocked-launch` | `module.development` · `specs/concorde/development/scenarios.md` | `module.harness` · [`scenario.harness.execute-blocked-launch`](harness/scenarios.md#scenario.harness.execute-blocked-launch) |
| `scenario.development.describe-policy` | `module.development` · `specs/concorde/development/scenarios.md` | `module.harness` · [`scenario.harness.describe-policy`](harness/scenarios.md#scenario.harness.describe-policy) |
| `scenario.development.invocation-worktree-binding` | `module.development` · `specs/concorde/development/scenarios.md` | `module.harness` · [`scenario.harness.invocation-worktree-binding`](harness/scenarios.md#scenario.harness.invocation-worktree-binding) |
| `scenario.development.workspace-inventory` | `module.development` · `specs/concorde/development/scenarios.md` | `module.harness` · [`scenario.harness.workspace-inventory`](harness/scenarios.md#scenario.harness.workspace-inventory) |
| `scenario.development.worktree-relay` | `module.development` · `specs/concorde/development/scenarios.md` | `module.harness` · [`scenario.harness.worktree-relay`](harness/scenarios.md#scenario.harness.worktree-relay) |
| `scenario.development.graph-specs` | `module.development` · `specs/concorde/development/scenarios.md` | `module.harness` · [`scenario.harness.graph-specs`](harness/scenarios.md#scenario.harness.graph-specs) |
| `scenario.development.graph-api-only` | `module.development` · `specs/concorde/development/scenarios.md` | `module.harness` · [`scenario.harness.graph-api-only`](harness/scenarios.md#scenario.harness.graph-api-only) |
| `scenario.development.graph-execution` | `module.development` · `specs/concorde/development/scenarios.md` | `module.harness` · [`scenario.harness.graph-execution`](harness/scenarios.md#scenario.harness.graph-execution) |
| `scenario.development.graph-bounds` | `module.development` · `specs/concorde/development/scenarios.md` | `module.harness` · [`scenario.harness.graph-bounds`](harness/scenarios.md#scenario.harness.graph-bounds) |
| `scenario.development.operation-state` | `module.development` · `specs/concorde/development/scenarios.md` | `module.harness` · [`scenario.harness.operation-state`](harness/scenarios.md#scenario.harness.operation-state) |
| `scenario.development.operation-result-state` | `module.development` · `specs/concorde/development/scenarios.md` | `module.harness` · [`scenario.harness.operation-result-state`](harness/scenarios.md#scenario.harness.operation-result-state) |
| `scenario.development.execute-unregistered` | `module.development` · `specs/concorde/development/scenarios.md` | `module.operations` · [`scenario.operations.execute-unregistered`](operations/scenarios.md#scenario.operations.execute-unregistered) |

## Identifier rename

After the dissolution every retired `development` prefix was renamed so that no identity names a
Module that no longer exists: each requirement, scenario and document identity takes its owner's
prefix, and a name that repeated the owner drops that part (`scenario.development.dev-loop-ready`
became `scenario.dev-loop.ready`, `scenario.development.validate-blocked` became
`scenario.validation.blocked`). The tables above keep the retired identities as historical text
and link to each renamed definition. Document identities changed as follows; the participation
anchor `participation.document.development.execution-reference.1` became
`participation.document.operations.execution-reference.1`.

| Retired document identity | Current document identity |
| --- | --- |
| `document.development.interfaces` | `document.harness.admission` |
| `document.development.execution-reference` | `document.operations.execution-reference` |
| `document.development.operations` | `document.operations.composition` |
| `document.development.requirements` | `document.operations.requirements` |
| `document.development.scenarios` | `document.operations.scenarios` |
| `document.development.review-and-gaps` | `document.issues.blockers` |
| `document.development.review-result` | `document.review.review-result` |

A rename is a project change like any other: every reference, test declaration and registry entry
changed in the same commit, no alias of a retired identity remains, and evidence bound to the
previous bytes is rebuilt.
