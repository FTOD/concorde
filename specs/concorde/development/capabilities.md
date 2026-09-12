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

Current public Skill files expose exactly one global or lifecycle entry through
`scripts/run-capability.py <skill>`. Stage entries have no public Skill.

Distribution owns the Skill sources, shared invocation instructions, rendering and installation.
An installed Skill is an instruction artifact consumed by the developer's external agent runtime;
that runtime submits a typed capability request to Development. Development owns admission,
dispatch and workflow behavior, and records the public Skill-to-capability mapping below as an
interface agreement. It neither loads Skills into its workers nor owns their distribution assets.

| Capability | Class | Deterministic | Skill | Launches | Uses | Behavior |
| --- | --- | --- | --- | --- | --- | --- |
| main | global | `false` | concorde-main | coordinator, spec-engineer | — | Answer directly from complete injected Spec contexts, or design, prepare and atomically apply an explicitly accepted topology |
| dev-loop | global | `false` | concorde-dev-loop | coordinator | specify, review, plan, tasks, implement, validate | Route one change, then specify unless `specify=false`, review the Spec, plan, task, implement, validate and review code to ready; `run_reviews=false` records explicit skips and cannot cancel a recorded requirement |
| reflections-triage | global | `false` | concorde-reflections-triage | programmer | dev-loop | Report status, capture recorded gaps, investigate read-only, implement through the development loop, merge or close owned reflections |
| init | lifecycle | `true` | concorde-init | — | — | Propose and apply explicit project initialization with a pinned Protocol |
| configure | lifecycle | `true` | concorde-configure | — | — | Apply the initialized integration and enforcement configuration |
| validate | lifecycle | `true` | concorde-validate | — | — | Run deterministic Spec and configured code checks and record readiness |
| deliver | lifecycle | `true` | concorde-deliver | — | — | Stage a ready candidate on its own branch and clean up; explicitly merge later from the sole primary writer |
| specify | stage | `false` | — | spec-engineer | — | Author the bound target's Spec replacements |
| review | global | `false` | concorde-review | coordinator, spec-engineer, programmer | — | Route an observational task, then independently review its Spec or code read-only with version-bound findings and gaps |
| context-solve | stage | `false` | — | spec-engineer | — | Validate Module participant routing, then assess information sufficiency without expanding the context |
| plan | stage | `false` | — | spec-engineer | — | Assess sufficiency, then create a revision-bound plan |
| tasks | stage | `false` | — | spec-engineer | — | Author acceptance tasks from the accepted plan |
| implement | stage | `false` | — | programmer | — | Implement component tasks or coordinate participating components |

Request and response types are `concorde-<capability>-request@1` and
`concorde-<capability>-response@1`; their promise-level meaning is defined in the [Development host
boundary](interfaces.md).

## Capability classes
Each capability module MUST declare a boolean `DETERMINISTIC`, published as `deterministic` in
the metadata block below. This is independent of its context-selection class. `true` means no
supported execution path calls a model, directly or through host routing or transitive `USES`
composition. `false` means a model call is possible; a status, preview, skipped or early-exit path
that makes no model call does not change the capability's classification. Model calls run through
declared Agents, including the coordinator admitted by host routing. A deterministic capability
may read or change files, run processes and observe external state; this flag does not promise
purity, identical results or freedom from side effects.

Every capability in this host adapter belongs to exactly one class, distinguished by context selection:

- **Global** — receives only the caller's intent, at most with target/focus routing hints; the
  host's coordinator discovers complete Module Specs and selects the owning target, and
  the capability may span several targets and stages.
- **Lifecycle** — deterministic host behavior with no agent cognition and no context selection.
- **Stage** — receives an already bound `target_id` and one frozen context snapshot from the
  capability that composes it, coordinates only its declared Agent steps, and never reselects or expands its context.

Global and lifecycle capabilities are exposed as Skills. Stage capabilities are never projected as
Skills and have no executable entry; they are reachable only in-process from a capability whose
declared composition names them, and the host rejects an undeclared composition with
`undeclared_capability`. Main routing — discovering targets and binding one `target_id` to the
invocation — happens only inside global capabilities; every stage starts with `target_id` already
bound by its caller.

```concorde-capabilities
[
  {"id": "main", "class": "global", "deterministic": false, "skill": "concorde-main"},
  {"id": "dev-loop", "class": "global", "deterministic": false, "skill": "concorde-dev-loop"},
  {"id": "reflections-triage", "class": "global", "deterministic": false, "skill": "concorde-reflections-triage"},
  {"id": "init", "class": "lifecycle", "deterministic": true, "skill": "concorde-init"},
  {"id": "configure", "class": "lifecycle", "deterministic": true, "skill": "concorde-configure"},
  {"id": "validate", "class": "lifecycle", "deterministic": true, "skill": "concorde-validate"},
  {"id": "deliver", "class": "lifecycle", "deterministic": true, "skill": "concorde-deliver"},
  {"id": "specify", "class": "stage", "deterministic": false, "skill": null},
  {"id": "review", "class": "global", "deterministic": false, "skill": "concorde-review"},
  {"id": "context-solve", "class": "stage", "deterministic": false, "skill": null},
  {"id": "plan", "class": "stage", "deterministic": false, "skill": null},
  {"id": "tasks", "class": "stage", "deterministic": false, "skill": null},
  {"id": "implement", "class": "stage", "deterministic": false, "skill": null}
]
```

Deterministic validation requires this block to equal the capability inventory declared in code:
the same identifiers, classes, boolean `deterministic` values and Skill names, a Skill for every global or lifecycle capability and
none for a stage. The block is intentional redundancy so that this Spec explains the workflow
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

Agent identity follows stable capability and context boundaries. Stage, review and topology calls
select the explicit mode declared in the Harness contract; combining Agent definitions does not
combine capability names, workflow responsibilities, public Skills or callable authority. Each
phase and target remains a fresh invocation.
