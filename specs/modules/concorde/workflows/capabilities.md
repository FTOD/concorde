```concorde-document
{
  "id": "document.capability.registry",
  "targets": [
    "module.workflows"
  ],
  "main_visible": true
}
```

# Capability registry

A **Capability** is functionality available for Agent use or composition, with declared inputs,
results, effects and usage conditions. A Harness makes selected capabilities available by explicit
reference. A Tool is a callable operation interface; a Skill supplies instructions and methods.
[Agents and Harnesses](agents-and-harnesses.md) defines the required capability use,
composition and authority contract.

## Current host adapter

The following inventory describes the existing Python host adapter. Each entry is implemented by a
module under `capabilities/`, declaring launched Agents, effects, composed entries and typed requests
and responses. The Python module is an implementation of functionality, not the definition of the
Capability concept. Host-declared composition is distinct from capabilities available to an Agent.

Current public Skill files expose exactly one global or lifecycle entry through
`scripts/run-capability.py <skill>`. Stage entries have no public Skill.

| Capability | Class | Skill | Launches | Uses | Behavior |
| --- | --- | --- | --- | --- | --- |
| main | global | concorde-main | coordinator, reader, spec-author | — | Answer through fresh readers, or design, prepare and atomically apply an explicitly accepted topology |
| dev-loop | global | concorde-dev-loop | coordinator | specify, review, plan, tasks, implement, validate | Route one change, then specify unless `specify=false`, review the Spec, plan, task, implement, validate and review code to ready; `run_reviews=false` records explicit skips and cannot cancel a recorded requirement |
| reflections-triage | global | concorde-reflections-triage | implementation-worker | dev-loop | Report status, capture recorded gaps, investigate read-only, implement through the development loop, merge or close owned reflections |
| init | lifecycle | concorde-init | — | — | Propose and apply explicit project initialization with a pinned Protocol |
| configure | lifecycle | concorde-configure | — | — | Apply the initialized integration and enforcement configuration |
| validate | lifecycle | concorde-validate | — | — | Run deterministic Spec and configured code checks and record readiness |
| deliver | lifecycle | concorde-deliver | — | — | From either participating session, verify and merge a ready candidate; retain or clean up the source worktree |
| specify | stage | — | spec-author | — | Author the bound target's Spec replacements |
| review | stage | — | spec-reviewer, code-reviewer | — | Independent read-only Spec or code review of the bound target with version-bound findings and gaps |
| context-solve | stage | — | context-assessor | — | Validate Module participant routing, then assess information sufficiency without expanding the context |
| plan | stage | — | context-assessor, planner | — | Assess sufficiency, then create a revision-bound plan |
| tasks | stage | — | task-author | — | Author acceptance tasks from the accepted plan |
| implement | stage | — | implementation-worker | — | Implement component tasks or coordinate participating components |

Request and response types are `concorde-<capability>-request@1` and
`concorde-<capability>-response@1`; their promise-level meaning is defined in the workflow-host
boundary document.

## Agents and Harnesses

The nine identifiers a capability "Launches" above are its named Agents: each one Python module
under the top-level `agents/` package, binding an authored `agents/<name>/spec.md`, a registered
Harness, and its effective Constraints/Permissions (`spec.md` + Harness + Constraints/Permissions,
per [Agents and Harnesses](agents-and-harnesses.md)). `agents/__init__.py` declares the
inventory; each `agents/<name>/` directory belongs to the Module that launches it. A rendered
`generated/agents/<hyphenated>.md` projection remains traceable to its `spec.md` source; role
identity alone no longer stands in for this complete Agent model.

Every Agent is bound to exactly one of three registered Harnesses:

| Harness | Workspace | Reads | Writes | Admitted contexts | Loop timeout |
| --- | --- | --- | --- | --- | --- |
| discovery-capsule | capsule | discovery-context | — | concorde-main-stage-context | 900s |
| spec-capsule | capsule | spec-context | — | concorde-agent-stage-context, concorde-review-stage-context, concorde-topology-author-context | 1800s |
| implementation-workspace | project | spec-context, implementation | implementation | concorde-agent-stage-context, concorde-review-stage-context | 3600s |

`coordinator` binds `discovery-capsule`; `reader`, `spec-author`, `context-assessor`, `planner`,
`task-author` and `spec-reviewer` bind `spec-capsule`; `implementation-worker` and `code-reviewer`
bind `implementation-workspace`. Each Agent's own Constraints/Permissions never widen its bound
Harness.

```concorde-agents
[
  {"id": "coordinator", "harness": "discovery-capsule", "capabilities": ["dev-loop", "main"]},
  {"id": "reader", "harness": "spec-capsule", "capabilities": ["main"]},
  {"id": "spec-author", "harness": "spec-capsule", "capabilities": ["main", "specify"]},
  {"id": "context-assessor", "harness": "spec-capsule", "capabilities": ["context-solve", "plan"]},
  {"id": "planner", "harness": "spec-capsule", "capabilities": ["plan"]},
  {"id": "task-author", "harness": "spec-capsule", "capabilities": ["tasks"]},
  {"id": "implementation-worker", "harness": "implementation-workspace", "capabilities": ["implement", "reflections-triage"]},
  {"id": "spec-reviewer", "harness": "spec-capsule", "capabilities": ["review"]},
  {"id": "code-reviewer", "harness": "implementation-workspace", "capabilities": ["review"]}
]
```

Deterministic validation requires this block to equal the Agent inventory declared in code: the
same identifiers, bound Harness names, and the sorted hyphenated names of every capability module
whose `AGENTS` includes that Agent. The block is intentional redundancy so that this Spec explains
the Agent/Harness binding without reading Python; it never adds an Agent that code does not
implement.

## Capability classes

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
  {"id": "main", "class": "global", "skill": "concorde-main"},
  {"id": "dev-loop", "class": "global", "skill": "concorde-dev-loop"},
  {"id": "reflections-triage", "class": "global", "skill": "concorde-reflections-triage"},
  {"id": "init", "class": "lifecycle", "skill": "concorde-init"},
  {"id": "configure", "class": "lifecycle", "skill": "concorde-configure"},
  {"id": "validate", "class": "lifecycle", "skill": "concorde-validate"},
  {"id": "deliver", "class": "lifecycle", "skill": "concorde-deliver"},
  {"id": "specify", "class": "stage", "skill": null},
  {"id": "review", "class": "stage", "skill": null},
  {"id": "context-solve", "class": "stage", "skill": null},
  {"id": "plan", "class": "stage", "skill": null},
  {"id": "tasks", "class": "stage", "skill": null},
  {"id": "implement", "class": "stage", "skill": null}
]
```

Deterministic validation requires this block to equal the capability inventory declared in code:
the same identifiers, classes and Skill names, a Skill for every global or lifecycle capability and
none for a stage. The block is intentional redundancy so that this Spec explains the workflow
without reading Python; it never adds a capability that code does not implement.

Target workers use `concorde-agent-stage-context@1`/`concorde-agent-stage-result@1` with explicit
document order, Target Spec and Shared Specs. Coordinator routing, topology design and synthesis
use `concorde-main-stage-context@1`/`concorde-main-stage-result@1` with an explicit complete Module discovery context and typed `concorde-main-worker-result@1` handoffs. Accepted topology design uses
`concorde-topology-proposal@1`, `concorde-topology-author-context@1`/`concorde-topology-author-result@1`
and a host-private `concorde-topology-application@1` artifact; shared replacements require every
reference and identical bytes. Plan artifacts, implementation tasks and selected reflections have
separate registered type identities. Fresh snapshots accompany every handoff. Deterministic outputs
carry identities and digests, never non-visible Module collections, code or logs into main or
unrelated cognition.

Reviewers use `concorde-review-stage-context@1` containing a full `concorde-context-snapshot@1`
and host-produced `concorde-review-input@1`; they return `concorde-review-stage-result@1`. The host
publishes `concorde-review-result@1` with target/focus/revision identity and
`semantic_completeness=not_proven`. Spec and code modes use different fresh roles, with no writes in
either mode. Complete collections remain distinct from the scoped change patches. Module candidate
review aggregates separately scoped results for its recorded participating components; it never
hands a project diff to one reviewer.
