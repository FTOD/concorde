```concorde-document
{
  "id": "document.concorde.ownership-migration",
  "owner": "module.concorde",
  "main_visible": true
}
```

# Capability ownership migration

This ledger records the explicitly authorized direct Spec maintenance against the saved current-byte
baseline, not committed HEAD. Stable prefixes do not prescribe ownership. Every original document,
requirement, scenario, entity and canonical contract ID remains defined exactly once; the entries
below are the definitions whose owner or physical locator changed. Unlisted IDs retain ownership.
The three canonical contracts and their four participant bindings retain their versions and peers;
in particular Harness and Development remain the participants in context.selection version 2.
Review-result remains the same version-1 wire value, now owned by Review.

| Stable definition | Previous owner and source | Current owner and definition |
| --- | --- | --- |
| `document.development.delivery` | `module.development` · `specs/concorde/development/delivery.md` | `module.delivery` · [definition](delivery/delivery.md) |
| `document.development.development` | `module.development` · `specs/concorde/development/development.md` | `module.dev-loop` · [definition](dev-loop/development.md) |
| `document.development.query-and-routing` | `module.development` · `specs/concorde/development/query-and-routing.md` | `module.query-routing` · [definition](query-routing/query-and-routing.md) |
| `document.development.review-result` | `module.development` · `specs/concorde/development/review-result.md` | `module.review` · [definition](review/review-result.md) |
| `document.development.topology` | `module.development` · `specs/concorde/development/topology.md` | `module.topology` · [definition](topology/topology.md) |
| `req.development.check-isolation` | `module.development` · `specs/concorde/development/module.md` | `module.validation` · [definition](validation/module.md#req.development.check-isolation) |
| `req.development.explicit-skip-sticky` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/module.md#req.development.explicit-skip-sticky) |
| `req.development.global-discovery` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [definition](query-routing/module.md#req.development.global-discovery) |
| `req.development.non-repair-stops-graph` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/module.md#req.development.non-repair-stops-graph) |
| `req.development.primary-writes-serialized` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [definition](delivery/module.md#req.development.primary-writes-serialized) |
| `req.development.repair-edge-only` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/module.md#req.development.repair-edge-only) |
| `req.development.routing-hint-no-grant` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [definition](query-routing/module.md#req.development.routing-hint-no-grant) |
| `req.development.routing-hint-not-context` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [definition](query-routing/module.md#req.development.routing-hint-not-context) |
| `req.development.shared-document-agreement` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [definition](topology/module.md#req.development.shared-document-agreement) |
| `req.development.single-primary-writer` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [definition](delivery/module.md#req.development.single-primary-writer) |
| `req.development.specify-loop-boundary` | `module.development` · `specs/concorde/development/module.md` | `module.specify-loop` · [definition](specify-loop/module.md#req.development.specify-loop-boundary) |
| `req.development.specify-loop-composition` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/module.md#req.development.specify-loop-composition) |
| `scenario.development.answer-gap` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [definition](query-routing/module.md#scenario.development.answer-gap) |
| `scenario.development.answer-question` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [definition](query-routing/module.md#scenario.development.answer-question) |
| `scenario.development.deliver-branch` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [definition](delivery/module.md#scenario.development.deliver-branch) |
| `scenario.development.deliver-conflict` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [definition](delivery/module.md#scenario.development.deliver-conflict) |
| `scenario.development.deliver-merge-primary` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [definition](delivery/module.md#scenario.development.deliver-merge-primary) |
| `scenario.development.deliver-session-rejected` | `module.development` · `specs/concorde/development/module.md` | `module.delivery` · [definition](delivery/module.md#scenario.development.deliver-session-rejected) |
| `scenario.development.dev-loop-coordinated` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/module.md#scenario.development.dev-loop-coordinated) |
| `scenario.development.dev-loop-ready` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/module.md#scenario.development.dev-loop-ready) |
| `scenario.development.dev-loop-repair` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/module.md#scenario.development.dev-loop-repair) |
| `scenario.development.dev-loop-repair-exhausted` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/module.md#scenario.development.dev-loop-repair-exhausted) |
| `scenario.development.dev-loop-spec-gap` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/module.md#scenario.development.dev-loop-spec-gap) |
| `scenario.development.discovery-limit` | `module.development` · `specs/concorde/development/module.md` | `module.query-routing` · [definition](query-routing/module.md#scenario.development.discovery-limit) |
| `scenario.development.resume-bound` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/module.md#scenario.development.resume-bound) |
| `scenario.development.resume-unbound` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/module.md#scenario.development.resume-unbound) |
| `scenario.development.specify-loop` | `module.development` · `specs/concorde/development/module.md` | `module.specify-loop` · [definition](specify-loop/module.md#scenario.development.specify-loop) |
| `scenario.development.standalone-review` | `module.development` · `specs/concorde/development/module.md` | `module.review` · [definition](review/module.md#scenario.development.standalone-review) |
| `scenario.development.task-history-identities` | `module.development` · `specs/concorde/development/module.md` | `module.planning` · [definition](planning/module.md#scenario.development.task-history-identities) |
| `scenario.development.task-scope-repair` | `module.development` · `specs/concorde/development/module.md` | `module.dev-loop` · [definition](dev-loop/module.md#scenario.development.task-scope-repair) |
| `scenario.development.topology-accept` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [definition](topology/module.md#scenario.development.topology-accept) |
| `scenario.development.topology-apply` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [definition](topology/module.md#scenario.development.topology-apply) |
| `scenario.development.topology-design` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [definition](topology/module.md#scenario.development.topology-design) |
| `scenario.development.topology-stale` | `module.development` · `specs/concorde/development/module.md` | `module.topology` · [definition](topology/module.md#scenario.development.topology-stale) |
| `scenario.development.validate-blocked` | `module.development` · `specs/concorde/development/module.md` | `module.validation` · [definition](validation/module.md#scenario.development.validate-blocked) |
| `scenario.development.validate-check-isolation` | `module.development` · `specs/concorde/development/module.md` | `module.validation` · [definition](validation/module.md#scenario.development.validate-check-isolation) |
| `scenario.development.validate-ready` | `module.development` · `specs/concorde/development/module.md` | `module.validation` · [definition](validation/module.md#scenario.development.validate-ready) |

## Compatibility and evidence scope

All new providers and flows have Concorde Framework as their sole parent; uses and local dependency
promises describe reuse. The old Development package binding is retained and exact existing wrapper
entries are shared by new semantic owners. No runtime source is physically extracted. Original
checks remain registered unchanged; a missing scenario verification remains visible coverage evidence.
No new lifecycle-ready, review, delivery or arbitrary-composition implementation claim follows from
this editorial migration. Revisions, contexts, plans and reviews affected by ownership, references or
source bytes need fresh evidence under the normal runtime gates.

Common host transport, invocation permissions, gap history and compatibility stay in Development.
Planning owns sufficiency, plan and tasks; Implementation owns bounded task fulfillment. Spec
Authoring, Review, Validation, Delivery, Query and Routing, and Topology own their cohesive effects.
Specification Flow and Development Flow own their sequencing and completion policy. Current repair
and component adapters still constrain reuse; broader flow adapters require separately implemented,
reviewed and verified support.
