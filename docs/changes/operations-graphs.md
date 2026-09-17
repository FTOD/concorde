# Operations and graphs migration

This is a breaking Framework migration from the source baseline
`7af5a831220091693695fa92b71079d9f10c5bd7` (Protocol 9, Profile 14) to Protocol 10,
Profile 15. It is not a claim that old execution evidence remains valid.

## Current model

**Operation is the only executable entity.** An Operation declares input State, output State
updates, effects, conditions of use, execution policy and a permission ceiling. Its caller does
not reconstruct context selection, permissions, model execution or result checks to call it as a
LangGraph node. Trusted Runtime, Host and Harness services remain necessary and narrow the ceiling
to the actual task. State carries data, never execution authority.

An implementation may be deterministic code, model execution or a compiled graph. Composition
produces another Operation; dev-loop and specify-loop are composed Operations. Public/internal
only controls entry exposure. Module ownership, Operation composition and explicit context
references remain independent; one Module need not correspond to one Operation.

The root Spec now introduces this model directly. The Operations Module groups ten behavior
provider Modules, including development and specification composition. Their identities and
owned contracts remain independent of the shared Development Host and Harness infrastructure.
Shared providers need not be siblings of every consumer, but cannot be owned by a consumer.

## Naming and source boundaries

| Before | Current | Policy |
| --- | --- | --- |
| `capabilities/`, registry `CAPABILITIES` | `operations/`, `OPERATIONS` | No import alias or second registry. Rebuild and update callers. |
| `CapabilityNode`, `CapabilityHost` | `OperationNode`, `OperationHost` | Only current Python APIs are supported. |
| `scripts/run-capability.py` | `scripts/run-operation.py` | Old launcher is removed; update entry commands and reinstall generated Skills. |
| `*_flow.py`, `build_*_flow`, Flow Spec | `*_graph.py`, `build_*_graph`, graph Spec | LangGraph graph/node vocabulary; no second graph model. |
| `%% flow:` executable diagram binding | `%% graph:` | Update authored bindings and check against compiled graphs. |
| `concorde.capabilities` metadata | `concorde.operations` | Replace the extension explicitly; old names are not aliases. |
| `capability context` | resource context | Admitted Operation/Tool contracts and declared read-only external references, not execution authorization. |
| Agent Flows page | Agent Graphs page | Concorde-only inspection surface; consumer docsite templates remain independent. |

The historical compound context term was not renamed to “Operation context”: it includes resources
beyond Operations and must not imply authorization. Graph composition does not select Spec context.
Ordinary control/data flow, Mermaid `flowchart`, GitHub Actions workflows and external API names
retain their actual meanings.

## Spec identity reconciliation

Against the baseline above, 620 identity strings are retained and 14 are explicitly renamed as
listed below. No baseline Module, document, entity, requirement, scenario or canonical contract is
left without a current identity. These are breaking identity replacements, not runtime aliases;
old IDs are rejected by current lookup and old byte-bound evidence is not replayed.

| Previous identity | Current identity |
| --- | --- |
| `document.development.capabilities` | `document.development.operations` |
| `document.development.flows` | `document.development.graphs` |
| `entity.development.development-capabilities` | `entity.development.development-operations` |
| `entity.spec.init-capability` | `entity.spec.init-operation` |
| `req.views.agent-flows` | `req.views.agent-graphs` |
| `scenario.development.capability-result-state` | `scenario.development.operation-result-state` |
| `scenario.development.capability-state` | `scenario.development.operation-state` |
| `scenario.development.execute-capability` | `scenario.development.execute-operation` |
| `scenario.development.flow-bounds` | `scenario.development.graph-bounds` |
| `scenario.development.flow-execution` | `scenario.development.graph-execution` |
| `scenario.development.flow-specs` | `scenario.development.graph-specs` |
| `scenario.distribution.capability-determinism` | `scenario.distribution.operation-determinism` |
| `scenario.harness.flow-inspection` | `scenario.harness.graph-inspection` |
| `scenario.views.agent-flows` | `scenario.views.agent-graphs` |

The ten `entity.concorde.*` provider identities for delivery, dev-loop, implementation, planning,
query-routing, review, spec-authoring, specify-loop, topology and validation keep their identities
while their owner moves from `module.concorde` to `module.operations`. Their provider Module IDs
remain unchanged; only structural parentage changes. Ordinary control flow remains ordinary
language, so `req.development.langgraph-control-flow` keeps its stable identity.

## Compatibility gates

- **Protocol 10 / Profile 15:** repository admission rejects old profiles with `unsupported_profile`;
  configuration-field/type admission also rejects missing current settings or old type identities.
  Explicitly change
  `capability_configuration` to `operation_configuration`, whose TypedValue type is now
  `concorde-operation-configuration@1`. Review the new rules before explicitly rebinding. There is
  no automatic conversion on installation or ordinary invocation.
- **Invocation transport:** new `concorde-operation-invocation@3` and
  `concorde-operation-result@3` have new type identities and `operation_id`. Old type identities
  and field sets are rejected, not reinterpreted as the new envelope.
- **Operation results:** responses with renamed `completed_operations` use version 3; the Issue
  response advances from 1 to 2. Init request and configure request/response advance to version 2
  because their configuration type changed. Unchanged inputs/results retain their versions.
- **Discovery:** `concorde-discovery-context@6` uses `operation` instead of `capability`; its
  `concorde-main-stage-context` wrapper is version 5. Old contexts are rejected and must be rebuilt.
- **Worktree progress:** `.concorde/worktree.json` and new target progress use schema 2. Schema-1
  worktree state is rejected with `unsupported_worktree_version`. Explicitly archive old local
  progress, preserve code and Specs, and establish new validation/review evidence. Renaming saved
  completion fields is not a supported resume migration.
- **Issues:** new records use schema 2 with `operation` provenance. Schema-1 records are supported
  only as historical read-only evidence, with exact observation hashes and receipts preserved.
  Mutation fails with `unsupported_issue_version`; explicitly create a new Issue referencing the
  old one if further work is needed. Current reporting never accepts the old provenance spelling.
  No Issue is silently closed, rewritten or assigned new historical evidence.
- **Usage diagnostics:** new JSONL records and summaries use schema 2. Historical unversioned
  records with the old label remain read-only and are counted in `historical_records`; their step
  labels are preserved. Unsupported records are counted explicitly, excluded from totals and set
  `complete: false`. Diagnostic compatibility grants no execution or readiness authority.
- **Evidence:** changed document bytes, IDs, references, topology, instructions and Protocol binding
  invalidate dependent contexts, plans and reviews. Workspace protocol metadata advances to 16.
  An old check log is history, not evidence for the migrated revision.

Registry serialization stays at schema 5 and document metadata at schema 2: their structural
representation did not change. The project explicitly reconciles parentage, entities, references
and file listings together. Public Skill names such as `concorde-dev-loop` are unchanged.

## Preparing a source checkout

Stay in the worktree that supplied the session's instructions. Do not load an affected project-local
Skill body while maintaining its sources. Update authoring sources, never generated assets.

```sh
python3 scripts/concorde.py build
python3 scripts/development/init-references.py
python3 scripts/concorde.py protocol-manifest --write --bind-project
python3 scripts/concorde.py build --check
python3 scripts/concorde.py validate
.venv/bin/python scripts/development/check-graph-specs.py
.venv/bin/python scripts/development/check-spec-v5.py
python3 scripts/development/run-tests.py --jobs 4
npm --prefix docsite run check
```

Run formatting before final verification and confirm a second pass changes no bytes. The
`check-spec-v5.py` command retains its historical filename for configured check compatibility;
its active audit is for Protocol 10. Source maintenance does not create lifecycle readiness or
perform delivery.

## Deliberate exclusions

- `reference/` is pinned third-party material. Do not edit it for Concorde terminology.
- `pi/extensions/concorde-worker.ts` calls the external
  `pi-subagents/capability-ceiling` API and `registerSubagentCapabilityCeiling`. Those names express
  a third-party permission ceiling and cannot be renamed by Concorde.
- GitHub Actions uses `.github/workflows`, `workflow_dispatch` and workflow templates. These are
  external platform terms, not Concorde executable entities.
- `docs/reports/`, earlier `docs/changes/spec-protocol-v*.md`, `SPEC_REVISION_DECISIONS.md` and
  `.concorde/archive/` describe earlier committed revisions. Their old words, paths, logs and
  historical probe scripts are retained as evidence, not current instructions or runnable APIs.
- Negative compatibility tests deliberately use old names to prove rejection, including retired
  launcher/package identities, envelope fields and reading bindings. They are not supported aliases.
- Historical unversioned usage JSONL is read-only diagnostic data, interpreted only by the explicit
  historical branch of the usage reader/summary, never an alternative Operation API.
- Schema-1 `.concorde/issues/` provenance is immutable history as specified above. Current record
  validation still verifies its digests; exclusion from renaming does not excuse corruption.
- Build fixture goldens are test expectations, not distributed generated assets. Refresh them
  through the build fixture mechanism when authored output changes; never edit `generated/` or
  installed Skill projections directly.

A remaining occurrence in current owned reading, code, configuration or test expectations outside
these boundaries needs semantic examination, not a blanket allowlist or a textual substitution.
