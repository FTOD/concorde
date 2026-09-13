```concorde-document
{
  "id": "document.development.capabilities",
  "owner": "module.development",
  "main_visible": true
}
```
# Capability registry

A **Capability** is functionality available for Agent use or composition, with declared inputs,
results, effects and usage conditions. A Harness makes selected capabilities available by explicit
reference. A Tool is a callable operation interface; a Skill supplies instructions and methods.
[Agents and Harnesses](../harness/agents-and-harnesses.md) defines the required capability use,
composition and authority contract.

**Capability** is the canonical term for a callable or composed Framework function. The former
**Operation** name is retired; it does not identify a separate layer, registry or contract kind.
Lowercase *operation* still describes an ordinary action, such as a filesystem or Git operation.

## Current host adapter
The following inventory describes the existing Python host adapter. Each entry is implemented by a
module under `capabilities/`, declaring launched Agents, effects, composed entries and typed requests
and responses. The Python module is an implementation of functionality, not the definition of the
Capability concept. Host-declared composition is distinct from capabilities available to an Agent.

Current public Skill files expose exactly one public Capability through
`scripts/run-capability.py <skill>`. Capabilities with PUBLIC=false have no public Skill.

Distribution owns the Skill sources, shared invocation instructions, rendering and installation.
An installed Skill is an instruction artifact consumed by the developer's external agent runtime;
that runtime submits a typed capability request to Development. Development owns admission,
dispatch and workflow behavior, and records the public Skill-to-capability mapping below as an
interface agreement. It neither loads Skills into its workers nor owns their distribution assets.

| Capability | Public | Context selection | Deterministic | Skill | Launches | Uses | Behavior |
| --- | --- | --- | --- | --- | --- | --- | --- |
| main | `true` | `discover` | `false` | concorde-main | coordinator, spec-engineer | — | Answer directly from complete injected Spec contexts, or design, prepare and atomically apply an explicitly accepted topology |
| dev-loop | `true` | `discover` | `false` | concorde-dev-loop | coordinator | specify-loop, review, plan, tasks, implement, validate | Route one change, call specify-loop, then plan, task, implement, validate and review code to ready; `run_reviews=false` records explicit skips and cannot cancel a recorded requirement |
| specify-loop | `true` | `discover` | `false` | concorde-specify-loop | coordinator | specify, review | Route one change, author or revise its Spec unless `specify=false`, independently review it, and return completed before planning or implementation; `run_reviews=false` records a Spec-only skip without cancelling an existing requirement |
| reflections-triage | `true` | `bound` | `false` | concorde-reflections-triage | programmer | dev-loop | Report status, capture recorded gaps, investigate read-only, implement through the development loop, merge or close owned reflections |
| init | `true` | `none` | `true` | concorde-init | — | — | Propose and apply explicit project initialization with a pinned Protocol |
| configure | `true` | `none` | `true` | concorde-configure | — | — | Apply the initialized integration and enforcement configuration |
| validate | `true` | `none` | `true` | concorde-validate | — | — | Run deterministic Spec and configured code checks and record readiness |
| deliver | `true` | `none` | `true` | concorde-deliver | — | — | Stage a ready candidate on its own branch and clean up; explicitly merge later from the sole primary writer |
| specify | `false` | `bound` | `false` | — | spec-engineer | — | Author the bound target's Spec replacements |
| review | `true` | `discover` | `false` | concorde-review | coordinator, spec-engineer, programmer | — | Route an observational task, then independently review its Spec or code read-only with version-bound findings and gaps |
| context-solve | `false` | `bound` | `false` | — | spec-engineer | — | Validate Module participant routing, then assess information sufficiency without expanding the context |
| plan | `false` | `bound` | `false` | — | spec-engineer | — | Assess sufficiency, then create a revision-bound plan |
| tasks | `false` | `bound` | `false` | — | spec-engineer | — | Author acceptance tasks from the accepted plan |
| implement | `false` | `bound` | `false` | — | programmer | — | Implement component tasks or coordinate participating components |

Request and response types are `concorde-<capability>-request@1` and
`concorde-<capability>-response@1`; their promise-level meaning is defined in the [Development host
boundary](interfaces.md).

## Capability properties

Every entry is a Capability. A Flow organizes capability calls, Agent invocations, branches and
loops. A Skill exposes a selected Capability to the developer's external agent runtime. The size
of a capability or its position in a Flow does not create another kind of capability.

Each Python module MUST declare these independent properties:

- **PUBLIC** is a boolean. True requires exactly one public Skill and launcher entry; false
  admits only declared in-process composition and creates no public Skill.
- **CONTEXT_SELECTION** is `discover`, `bound` or `none`. Discover admits coordinator discovery of
  complete Module contexts and one owning target for mutations; a composed invocation may reuse
  its already bound target. Bound consumes the selected Module and never reselects or expands
  its frozen context. None performs deterministic host work without Agent context selection.
- **DETERMINISTIC** is a boolean. True means no supported path calls a model, directly, through
  discovery or through transitive `USES`. False means a model call is possible, even when one
  particular invocation skips it. This does not promise identical output or absence of effects.
- **AGENTS** names the Agents launched directly, and **USES** names composed capabilities. A
  composition edge does not grant new context or write authority.

Public exposure does not imply discovery: reflections-triage is public and consumes a bound
Module. Conversely, being composed does not require private exposure: dev-loop calls the public
specify-loop, which calls specify and review. The host rejects undeclared composition with
`undeclared_capability` and preserves every participant's own invocation constraints.

The former CLASS declaration is removed. Existing wire identities and event fields containing
`stage` continue to identify an execution phase, not a capability type. Stable Spec anchors retain
their identities when their titles or terminology change.

```concorde-capabilities
[
  {"id": "main", "public": true, "context_selection": "discover", "deterministic": false, "skill": "concorde-main"},
  {"id": "specify-loop", "public": true, "context_selection": "discover", "deterministic": false, "skill": "concorde-specify-loop"},
  {"id": "dev-loop", "public": true, "context_selection": "discover", "deterministic": false, "skill": "concorde-dev-loop"},
  {"id": "reflections-triage", "public": true, "context_selection": "bound", "deterministic": false, "skill": "concorde-reflections-triage"},
  {"id": "init", "public": true, "context_selection": "none", "deterministic": true, "skill": "concorde-init"},
  {"id": "configure", "public": true, "context_selection": "none", "deterministic": true, "skill": "concorde-configure"},
  {"id": "validate", "public": true, "context_selection": "none", "deterministic": true, "skill": "concorde-validate"},
  {"id": "deliver", "public": true, "context_selection": "none", "deterministic": true, "skill": "concorde-deliver"},
  {"id": "specify", "public": false, "context_selection": "bound", "deterministic": false, "skill": null},
  {"id": "review", "public": true, "context_selection": "discover", "deterministic": false, "skill": "concorde-review"},
  {"id": "context-solve", "public": false, "context_selection": "bound", "deterministic": false, "skill": null},
  {"id": "plan", "public": false, "context_selection": "bound", "deterministic": false, "skill": null},
  {"id": "tasks", "public": false, "context_selection": "bound", "deterministic": false, "skill": null},
  {"id": "implement", "public": false, "context_selection": "bound", "deterministic": false, "skill": null}
]
```

Deterministic validation requires this block to equal the capability inventory declared in code:
the same identifiers, boolean `public` and `deterministic` values, `context_selection` values and
Skill names, exactly one Skill for each public capability and none for a non-public capability. The block is intentional redundancy so that this Spec explains the workflow
without reading Python; it never adds a capability that code does not implement.

Target workers use `concorde-agent-stage-context@2`/`concorde-agent-stage-result@1` with explicit
document order, owned and directly referenced Specs. Coordinator questions, routing and topology design
use `concorde-main-stage-context@2`/`concorde-main-stage-result@1` with explicit complete Module contexts, deduplicated original source pools and per-Module resolution provenance. Accepted topology design uses
`concorde-topology-proposal@1`, `concorde-topology-author-context@2`/`concorde-topology-author-result@1`
and a host-private `concorde-topology-application@1` artifact; shared replacements require sole-owner authoring and compatibility evidence for each affected consumer. Plan artifacts, implementation tasks and selected reflections have
separate registered type identities. Fresh snapshots accompany every handoff. Deterministic outputs
carry identities and digests, never non-visible Module collections, code or logs into main or
unrelated cognition.

Reviewers use `concorde-review-stage-context@2` containing a full `concorde-context-snapshot@2`
and host-produced `concorde-review-input@1`; they return `concorde-review-stage-result@1`. The host
publishes `concorde-review-result@1` with target/focus/revision identity and
`semantic_completeness=not_proven`. Spec and code modes use different fresh roles, with no writes in
either mode. Complete collections remain distinct from the scoped change patches. Module candidate
review aggregates separately scoped results for its recorded participating components; it never
hands a project diff to one reviewer.

Agent identity follows stable capability and context boundaries. Worker, review and topology calls
select the explicit mode declared in the Harness contract; combining Agent definitions does not
combine capability names, workflow responsibilities, public Skills or callable authority. Each
phase and target remains a fresh invocation.
