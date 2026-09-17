# Historical capability ownership migration

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Capability](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Contract](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Requirement](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Scenario](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Entity](concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Ownership](spec/registry.md#terminology) | Defined in Registry. |
| [Reference](spec/registry.md#terminology) | Defined in Registry. |
| [Implementation binding](spec/registry.md#terminology) | Defined in Registry. |
| [Evidence](concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Historical scope

This is a record of the earlier capability-ownership split, preserved from the pre-Protocol-8
source baseline. Version numbers and “current” entries below describe that migration, not the
current runtime agreement. Read each owning Module for present behavior.

In the later explanation-page consolidation, the Delivery, Development Flow, Query and Routing,
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
| `req.development.check-isolation` | `module.development` · `specs/concorde/development/module.md` | `module.validation` · [definition](validation/requirements.md#req.development.check-isolation) |
| `req.development.explicit-skip-sticky` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/requirements.md#req.development.explicit-skip-sticky) |
| `req.development.global-discovery` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [definition](query-routing/requirements.md#req.development.global-discovery) |
| `req.development.non-repair-stops-graph` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/requirements.md#req.development.non-repair-stops-graph) |
| `req.development.primary-writes-serialized` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [definition](delivery/requirements.md#req.development.primary-writes-serialized) |
| `req.development.repair-edge-only` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/requirements.md#req.development.repair-edge-only) |
| `req.development.routing-hint-no-grant` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [definition](query-routing/requirements.md#req.development.routing-hint-no-grant) |
| `req.development.routing-hint-not-context` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [definition](query-routing/requirements.md#req.development.routing-hint-not-context) |
| `req.development.shared-document-agreement` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [definition](topology/requirements.md#req.development.shared-document-agreement) |
| `req.development.single-primary-writer` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [definition](delivery/requirements.md#req.development.single-primary-writer) |
| `req.development.specify-loop-boundary` | `module.development` · `specs/concorde/development/module.md` | `module.specify-loop` · [definition](specify-loop/requirements.md#req.development.specify-loop-boundary) |
| `req.development.specify-loop-composition` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/requirements.md#req.development.specify-loop-composition) |
| `scenario.development.answer-gap` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [definition](query-routing/scenarios.md#scenario.development.answer-gap) |
| `scenario.development.answer-question` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [definition](query-routing/scenarios.md#scenario.development.answer-question) |
| `scenario.development.deliver-branch` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [definition](delivery/scenarios.md#scenario.development.deliver-branch) |
| `scenario.development.deliver-conflict` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [definition](delivery/scenarios.md#scenario.development.deliver-conflict) |
| `scenario.development.deliver-merge-primary` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [definition](delivery/scenarios.md#scenario.development.deliver-merge-primary) |
| `scenario.development.deliver-session-rejected` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [definition](delivery/scenarios.md#scenario.development.deliver-session-rejected) |
| `scenario.development.dev-loop-coordinated` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/scenarios.md#scenario.development.dev-loop-coordinated) |
| `scenario.development.dev-loop-ready` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/scenarios.md#scenario.development.dev-loop-ready) |
| `scenario.development.dev-loop-repair` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/scenarios.md#scenario.development.dev-loop-repair) |
| `scenario.development.dev-loop-repair-exhausted` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/scenarios.md#scenario.development.dev-loop-repair-exhausted) |
| `scenario.development.dev-loop-spec-gap` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/scenarios.md#scenario.development.dev-loop-spec-gap) |
| `scenario.development.discovery-limit` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [definition](query-routing/scenarios.md#scenario.development.discovery-limit) |
| `scenario.development.resume-bound` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/scenarios.md#scenario.development.resume-bound) |
| `scenario.development.resume-unbound` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/scenarios.md#scenario.development.resume-unbound) |
| `scenario.development.specify-loop` | `module.development` · `specs/concorde/development/module.md` | `module.specify-loop` · [definition](specify-loop/scenarios.md#scenario.development.specify-loop) |
| `scenario.development.standalone-review` | `module.development` · `specs/concorde/development/module.md` | `module.review` · [definition](review/scenarios.md#scenario.development.standalone-review) |
| `scenario.development.task-history-identities` | `module.development` · `specs/concorde/development/module.md` | `module.planning` · [definition](planning/scenarios.md#scenario.development.task-history-identities) |
| `scenario.development.task-scope-repair` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/scenarios.md#scenario.development.task-scope-repair) |
| `scenario.development.topology-accept` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [definition](topology/scenarios.md#scenario.development.topology-accept) |
| `scenario.development.topology-apply` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [definition](topology/scenarios.md#scenario.development.topology-apply) |
| `scenario.development.topology-design` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [definition](topology/scenarios.md#scenario.development.topology-design) |
| `scenario.development.topology-stale` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [definition](topology/scenarios.md#scenario.development.topology-stale) |
| `scenario.development.validate-blocked` | `module.development` · `specs/concorde/development/module.md` | `module.validation` · [definition](validation/scenarios.md#scenario.development.validate-blocked) |
| `scenario.development.validate-check-isolation` | `module.development` · `specs/concorde/development/module.md` | `module.validation` · [definition](validation/scenarios.md#scenario.development.validate-check-isolation) |
| `scenario.development.validate-ready` | `module.development` · `specs/concorde/development/module.md` | `module.validation` · [definition](validation/scenarios.md#scenario.development.validate-ready) |

### Compatibility and evidence scope

All new providers and flows have Concorde Framework as their sole parent; uses and local dependency
promises describe reuse. The old Development package binding is retained and exact existing wrapper
entries are shared by new semantic owners. No runtime source is physically extracted. Original
checks remain registered unchanged; a missing scenario verification remains visible coverage evidence.
No new lifecycle-ready, review, delivery or arbitrary-composition implementation claim follows from
this editorial migration. Revisions, contexts, plans and reviews affected by ownership, references or
source bytes need fresh evidence under the normal runtime gates.

Common host transport, invocation permissions, gap history and compatibility stay in Development.
[Planning Module](planning/module.md) owns sufficiency, plan and tasks; [Implementation Module](implementation/module.md) owns bounded task fulfillment. Spec
Authoring, Review, Validation, Delivery, [Query and Routing](query-routing/module.md), and Topology own their cohesive effects.
[Specification Flow](specify-loop/module.md) and [Development Flow](dev-loop/module.md) own their sequencing and completion policy. Current repair
and component adapters still constrain reuse; broader flow adapters require separately implemented,
reviewed and verified support.
