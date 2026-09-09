---
reflections: ["R-066", "R-067", "R-068", "R-069", "R-070"]
baseline_commit: "2fc199214e1cd98e6c998e28fbb84c18968c9d8e"
baseline_tests: "583 passed, 8 skipped (full suite, .venv/bin/python -m unittest discover -s tests/concorde -t . -p test_*.py)"
status: accepted-2026-09-08
date: 2026-09-08
worktree: /home/zhenyu/concorde-worktrees/agent-model
branch: agent-model
decisions:
  layout: "agents/<name>/{__init__.py, spec.md}; spec.md is the prompt root; capability modules use AGENTS"
  automatic_edges: "only review_code -> tasks; Spec gaps and failed checks stop (waiting/failed) for a human"
  spec_edits: "edited together with the code in each phase"
  execution: "this session owns the worktree and dispatches Sonnet implementers per phase, reviewing each"
progress:
  P1: "committed 865e6c8 on agent-model; 625 tests (617 pass, 8 skipped), validate clean, docsite 135 pass"
  P2+P3: "committed 65086d7; 647 tests (639 pass, 8 skipped), validate clean"
  merge: "main (72cc22e) merged into agent-model as 69f7ab7 without conflicts; rebuilt, validate clean"
  P4: "committed 2569066; 657 tests (649 pass, 8 skipped) after the spec_digest fix; Protocol export digest re-bound (schemas.json changed: concorde-review-result admitted as a stage input)"
  P5: "committed 40e6c58 (Spec prose, README, STUDIO docs; no code); evidence in agent-model-resolution.md and agent-model-2569066-probes-after.{py,json}"
  delivery: "main fast-forwarded to 40e6c58; rebuilt; validate clean; linked worktree removed, branch agent-model kept; R-066..R-070 triaged (complete, not-required) and relocated to planned/ awaiting human closure"
---

# Plan: bring the orchestration host up to the Agent/Harness/Graph model (R-066 – R-070)

This plan resolves the five reflections recorded against commit `2fc1992`, which introduced the
Agent model (`specs/concorde/workflow/agents-and-harnesses.md`, A1–A4) and the Graph/Loop model
(`specs/concorde/workflow/agent-graphs-and-loops.md`, G1–G4; `specs/concorde/workflow/development.md`).
Every observation in the five reflections was re-verified against the current source. Nothing in this
plan is implemented yet; it is the proposal to be confirmed before any code changes.

## 1. Verified findings

| Reflection | Verified root cause in current source |
| --- | --- |
| R-066 | `Invocation.stage` (`capability_host.py:1075`) builds `EffectDeclaration(read_roles, write_roles, ...)` from the phase and never reads `prompt.effects`. `MainInvocation.stage` (`:293`) and `_topology_author` (`:703`) hard-code an `EffectDeclaration` the same way. Only `review.py:212` compiles the loaded role's own declaration. The compiler's non-widening rule therefore protects nothing on the ordinary stage path: the Agent declaration is never the "declared constraints" side of A4. |
| R-067 | `Role` (`roles.py`) is `name + prompt + effects`. All nine roles point at root prompts under `prompts/`; there is no `spec.md`, no Harness reference, no Python module per Agent, and no validation that a launched identity resolves to a complete Agent definition. `capabilities/*.py` reference `roles.Role` objects; the build renders `generated/roles/<name>.md` directly from the prompt roots. |
| R-068 | No Harness entity exists anywhere in `src/concorde/host`. Execution environment facts are scattered: cwd policy (capsule vs project root) is decided inline in each launch path, tool/network posture lives in the two native renderers, admitted context/result contract types are implied by `_domain_type` in the executor, environment filtering is `_SAFE_ENVIRONMENT`. `LaunchSpecification` binds role/policy/context but carries no Harness or capability-reference identity. `CapabilityHost.executor` is an injected callable, not a named binding. |
| R-069 | `Invocation.loop` (`capability_host.py:1564`) builds a linear LangGraph: every node's conditional edge goes to the next node on `completed|ready` and to `END` otherwise. There is no `review_code → tasks`, `validate → tasks`, or `review_spec → specify` edge, no iteration budget, no record of which finding selected a transition, and no unchanged-feedback detection. The probe reproduces exactly one implementation and one code-review invocation followed by `status=blocked, outcome=conflicting`. |
| R-070 | `_default_runner` (`agent_executor.py:284`) calls `subprocess.run` with no timeout; the runner interface has no timeout parameter. `CapabilityExecutionError` distinguishes nothing beyond message and optional receipt; `run_capability` maps any non-`SpecError` exception to `execution_failed`. Neither `codex exec` (0.153.4) nor `claude -p` (2.1.263) exposes a turn limit on its command line (Claude has only `--max-budget-usd`), so the host cannot delegate the loop bound to the client. No wire or state record distinguishes waiting, cancelled or limit-exhausted from failed. |

Related pending reflections that this plan deliberately does **not** absorb: R-055 (check authority),
R-061 (read-only code inspection entry), R-062 (component parentage), R-063 (outer enforcement).

## 2. Target design

### 2.1 Agent definitions (A1) — new top-level `agents/` package

One directory per Agent, mirroring how `capabilities/` holds one module per capability:

```
agents/
  __init__.py                 # AGENTS = ("coordinator", "reader", "spec_author", ...) inventory
  coordinator/
    __init__.py               # the Agent definition module (binds spec, harness, constraints)
    spec.md                   # the authored Agent Spec; also the root of the rendered instruction view
  reader/ …  spec_author/ …  context_assessor/ …  planner/ …  task_author/ …
  implementation_worker/ …  spec_reviewer/ …  code_reviewer/ …
```

`spec.md` is the behavioral authority **and** the single authoring source of the rendered prompt.
It is written with the sections A1 requires (Responsibilities, Goals, Accepted input and feedback,
Expected results, Completion conditions, Missing information / failure / required human decision) and
may `@include` shared snippets that stay under `prompts/` (`gap-reporting.md`,
`host-bound-invocation.md`, `review-scope-and-result.md`, …). The build renders it to
`generated/agents/<name>.md`; the build manifest records `agents/<name>/spec.md` as the source, which is
the A1 traceability requirement. The current root prompts under `prompts/workflow-host/*.md` and
`prompts/spec-context/*.md` that name a role move into the corresponding `spec.md` (their content is
restructured into the required sections, not merely copied).

The definition module:

```python
# agents/spec_author/__init__.py
from concorde.host.agent_model import Agent, Constraints
from concorde.host.harness import SPEC_CAPSULE

AGENT = Agent(
    name="spec_author",
    spec="agents/spec_author/spec.md",
    harness=SPEC_CAPSULE,
    constraints=Constraints(
        effects=EffectDeclaration(reads=("spec-context",), writes=(), network=False, credentials="none"),
        capabilities=(),                                    # no Concorde capability is callable by this Agent
        contexts=("concorde-agent-stage-context", "concorde-topology-author-context"),
        results=("concorde-agent-stage-result", "concorde-topology-author-result"),
        limits=LoopPolicy(timeout_seconds=1800),
    ),
)
```

`src/concorde/host/agent_model.py` defines the frozen records `Agent`, `Constraints`, `AgentBinding`
and `resolve_agent(package_root, name) -> AgentBinding`. Resolution fails closed (`BuildError`
`unknown_agent` / `invalid_agent_binding`) when the `spec.md` is missing or its digest differs from the
build manifest, the Harness is unknown, a capability reference is not in `capabilities.CAPABILITIES`, a
context/result type is not an exported wire type, or the constraints exceed the Harness
(`effects ⊄ harness.effects`, `limits > harness.loop`). `AgentBinding` carries: agent name, spec path
and digest, rendered instruction path and digest, harness name and digest, constraints digest, and the
build-manifest digest — the "sources and versions needed to reproduce execution".

`roles.py` becomes a derived compatibility projection: `ROLES` is built from the agents inventory so
`role`/`agent` wire fields, `role_key`, `external_role_name` and `STAGE_ROLES` keep working. The
capability modules replace `ROLES = (roles.SPEC_AUTHOR,)` with `AGENTS = (agents.spec_author.AGENT,)`;
the validator rule `CONCORDE-CAPABILITY-ROLES-001` becomes `CONCORDE-CAPABILITY-AGENTS-001`.

### 2.2 Harnesses (A2, A3) — `src/concorde/host/harness.py`

Three named, inspectable Harness records, chosen by execution environment (the axis that actually
differs between launches today):

| Harness | Workspace | Path roles readable | Writes | Admitted contexts | Agents |
| --- | --- | --- | --- | --- | --- |
| `discovery-capsule` | private temp capsule | `discovery-context` | none | `concorde-main-stage-context` | coordinator |
| `spec-capsule` | private temp capsule | `spec-context` | none | `concorde-agent-stage-context`, `concorde-review-stage-context`, `concorde-topology-author-context` | reader, spec_author, context_assessor, planner, task_author, spec_reviewer |
| `implementation-workspace` | project root | `spec-context`, `implementation` | `implementation` (narrowable to none) | `concorde-agent-stage-context`, `concorde-review-stage-context` | implementation_worker, code_reviewer |

Each `Harness` record declares: `model="project-configured"` (integration from
`concorde-capability-configuration`, both Codex and Claude supported), `capabilities=()` (host
composition is *not* Agent-callable; this is stated explicitly rather than left implicit),
`tools=("native.filesystem", "native.shell")` restricted by the compiled policy and
`network=False`, `skills=()` (ambient discovery disabled by `project_doc_max_bytes=0` / restricted
settings), `contexts`, `results`, `loop=LoopPolicy(timeout_seconds, max_turns=None)`,
`state="fresh-process; typed completion persisted by host"`, `environment=_SAFE_ENVIRONMENT`,
`workspace="capsule"|"project"`, and a `digest`. The record references the existing renderers and
`_SAFE_ENVIRONMENT` by name instead of duplicating them (permitted by A2).

The Agent's `Constraints` restrict the Harness; the host binding restricts again per phase
(`PolicyBinding.read_roles/write_roles`). Effective policy is therefore
`host grant ∩ Agent constraints ∩ Harness surface`, and `compile_policy` already raises when a
binding asks for more than the Agent declares — which is exactly the A4 subset rule R-066 found
unenforced.

### 2.3 Binding every invocation (A4) — permissions, executor, host

- `build_launch_specification(..., agent_binding_json: str | None = None)` and a matching
  `LaunchSpecification.agent_binding_json` field, included in the launch digest payload. Structured
  (schema 3) launches must supply it; `finalize_launch_specification` preserves it.
- `AgentProcessExecutor._preflight` validates the binding before any process starts: the binding's
  agent name equals `specification.role`/`agent`; the rendered instruction digest equals
  `sha256(specification.prompt)`; the launch's context type (`_domain_type`) is in the binding's
  admitted contexts; the effective policy does not exceed the binding's effects (writes empty when the
  Agent declares none, network/credentials not widened). Failure raises `CapabilityExecutionError`
  before launch, satisfying "unavailable or unauthorized reference MUST fail before its effects occur".
- The four launch paths (`Invocation.stage`, `MainInvocation.stage`, `_topology_author`,
  `review.review`) all switch from `load_role_prompt` to `load_agent(package_root, name) ->
  BoundAgent(binding, body, constraints)`, pass `constraints.effects` as the declared maximum and a
  narrowing `PolicyBinding` (`write_roles=()` for reviewers and read-only investigation), select the
  workspace from `harness.workspace` instead of the inline `phase == "implementation"` test, and put
  the binding into the launch and into `host.descriptions` (so `describe-policy` exposes agent,
  harness and instruction identities alongside the policy digest).
- `load_role_prompt` remains as a thin wrapper (the package-assets Spec lists it) returning the same
  `SkillPrompt` shape, now sourced from the Agent.

### 2.4 Local loop policy and complete outcomes (G2, G4; R-070)

- `LoopPolicy(timeout_seconds: int, max_turns: int | None = None)` lives on the Harness and may be
  tightened by an Agent's `Constraints.limits`. Because neither native CLI accepts a turn limit, the
  host-enforced wall-clock timeout is the attested bound; `max_turns=None` records that no native turn
  limit is attested rather than pretending one exists.
- Runner interface gains a keyword: `runner(argv, *, cwd, env, input_text, timeout)`.
  `_default_runner` passes it to `subprocess.run(timeout=…)`. Test doubles (`ModelProcessDouble.run`,
  executor unit-test runners) accept the keyword.
- `CapabilityExecutionError` gains `outcome: Literal["failed", "cancelled", "limit_exhausted",
  "invalid_completion"]` (default `"failed"`). `subprocess.TimeoutExpired` → `limit_exhausted`
  with a failed receipt whose `limitations` names the policy and elapsed bound; `KeyboardInterrupt`
  during the process → `cancelled` (child already killed by `subprocess.run`). No retry, no wider
  permissions.
- Host mapping: `run_capability` catches `CapabilityExecutionError` explicitly and emits error codes
  `execution_failed` / `execution_cancelled` / `execution_limit`; worktree progress records status
  `failed` / `cancelled` / `limit_exhausted`. The dev-loop graph (2.5) records status `waiting` when it
  stops for a required human decision. All four statuses appear in `workspace` lifecycle metadata.
- `host.evidence` entries are annotated with the binding (agent, harness, loop policy) so execution
  evidence identifies the participating invocations as G4 requires.

### 2.5 Development graph with revision loops (G1–G3; R-069)

`Invocation.loop` is rewritten as a declared graph rather than a stage list:

```
specify ──completed──▶ review_spec ──completed──▶ plan ──▶ tasks ──▶ implement ──▶ validate ──▶ review_code ──▶ ready
   ▲                       │ gaps                                       │ failed checks    │ blocking findings
   └── (bounded re-author) ┘                                            └────────▶ tasks ◀─┘  (repair iteration)
```

- **Graph policy** declared in `capabilities/dev_loop.py`: `GRAPH = GraphPolicy(max_repair_iterations=2,
  max_reauthor_iterations=1)`. Recorded in `worktree.json → targets[<id>].graph.policy` so the loop
  "records its configured limits".
- **Repair edge** `review_code → tasks` when the review outcome is `conflicting` (blocking findings, no
  gaps): the `tasks` stage receives declared inputs `(concorde-plan-artifact, concorde-implementation-task
  {completed tasks}, concorde-review-result)`; `concorde-review-result` is added to the `stage_inputs`
  `anyOf` so the feedback travels as an existing typed artifact (G3 explicitly allows reusing review
  artifacts). The task author authors repair tasks (`complete:false`), then implement → validate →
  review_code run again. Previous tasks are retained under `targets[<id>].task_history`.
- **Repair edge** `validate → tasks` when configured checks fail after implementation
  ("Implemented → Tasks: failure needs implementation work"): feedback is the typed check results
  (`check_id/status/exit_code/digests`, never logs) carried by a new small type
  `concorde-check-feedback@1 {checks: [CHECK_RESULT]}` added to `stage_inputs`. *(Open question 4c —
  can be deferred.)*
- **Re-author edge** `review_spec → specify` (one bounded iteration) when Spec review returns necessary
  gaps and `specify=true`: the author receives the `concorde-review-result` as a declared input and may
  supply the missing contract or return `spec_incomplete` itself, in which case the graph stops with
  status `waiting`. *(Open question 4a.)*
- **Unchanged blocking feedback**: the finding set `{(contract, problem, location)}` of the new code
  review is compared with the previous iteration's; identical feedback stops the loop with status
  `waiting` ("waits for new information") instead of consuming another iteration.
- **Iteration limit**: exceeding `max_repair_iterations` stops with status `limit_exhausted`,
  outcome `conflicting`, and the latest review artifact retained.
- **Attribution**: every taken transition is appended to `targets[<id>].graph.transitions` as
  `{from, to, trigger: deterministic|ai-review|ai-assessment|human, artifact?, input_digest?, finding_ids?,
  iteration}`; human transitions are recorded when a resumed loop observes a repaired Spec revision.
- **Resume revalidation** (G4): on re-entry the recorded graph state is checked against the current
  Spec/implementation digests and task intent; a changed Spec resets the iteration count, a changed
  intent is still rejected (`incompatible_handoff`, unchanged behavior).
- **Domain loops**: for a Domain target a blocking component code review routes to `implement`
  (`implement_scope`) instead of `tasks`; component dev-loops own the repair through their own graphs,
  and `verify_completion` already forces a re-run for a component whose required review is not current.
- **Studio**: no graph-shape change; the transition records surface as `stage_started/finished`
  events with the `trigger` field.

### 2.6 Deterministic validation and docs (encode the rules, not just apply them)

New `package_validation` rules: `CONCORDE-AGENT-INVENTORY-001` (inventory equals `agents/*`),
`CONCORDE-AGENT-SPEC-001` (`spec.md` present, resolvable, with the six A1 sections),
`CONCORDE-AGENT-HARNESS-001` (harness known, capability refs resolve, contexts/results exported,
constraints ⊆ harness), `CONCORDE-CAPABILITY-AGENTS-001` (capability `AGENTS` are `Agent` objects).
`capability-registry.md` gets a machine-readable `concorde-agents` block (agent → harness → capability)
checked by `CONCORDE-SPEC-AGENTS-001` the same way the existing `concorde-capabilities` block is.
`generated/docs/instructions.json` renames `roles` → `agents` and adds `spec` and `harness` fields; the
docsite projection follows.

## 3. Work breakdown (each phase ends green: build, `build --check`, `validate`, full unittest)

| Phase | Scope | Files (new / changed) | Acceptance |
| --- | --- | --- | --- |
| P1 Agent model | `agents/` package with nine definitions and nine `spec.md`; `agent_model.py`; `harness.py`; build renders `generated/agents/*`; `roles.py` derived; capability modules `AGENTS`; validator rules; golden fixtures moved | new: `agents/**`, `src/concorde/host/agent_model.py`, `src/concorde/host/harness.py`; changed: `build.py`, `roles.py`, `package_validation.py`, `capabilities/*.py`, `prompt_resolver.py` (spec root without `audience` front matter), tests + `tests/concorde/fixtures/build/golden/agents/*` | `resolve_agent` fails closed for missing spec / unknown harness / unresolved capability / over-wide constraints; `validate` reports the new rules on fixtures; byte-identical build |
| P2 Binding & authority | all four launch paths use `load_agent`, declared effects + narrowing binding; `agent_binding_json` in launch; executor preflight validation; describe-policy exposes identities | `capability_host.py`, `review.py`, `permissions.py`, `agent_executor.py`, `build.py` | the R-066 probe's narrowed role yields `PermissionPolicyError` (host asked for more than the Agent declares) and a narrowed binding yields empty writes; a launch with a tampered prompt or wrong context type is refused before the process starts |
| P3 Loop policy & outcomes | `LoopPolicy`, runner `timeout`, executor outcomes, host error codes and progress statuses, evidence annotation | `agent_executor.py`, `harness.py`, `capability_host.py`, `change_worktree.py`, `contract_shapes.py` (workspace status enum if constrained), test doubles | runner raising `TimeoutExpired` → `execution_limit` and status `limit_exhausted`; `KeyboardInterrupt` → `execution_cancelled`; evidence names agent/harness/policy |
| P4 Development graph | rewritten `Invocation.loop`, repair/re-author edges, feedback inputs, attribution, limits, unchanged-feedback wait, resume revalidation, Domain path | `capability_host.py`, `capabilities/dev_loop.py`, `contracts.py` (stage-input `anyOf`, `concorde-check-feedback`), `change_worktree.py`, `tests/concorde/specification/test_review.py`, `test_worktree_lifecycle.py`, `test_scoped_protocol.py` | the R-069 probe scenario (blocking then clean review) shows two implementation and two code-review invocations ending `ready`; identical repeated findings end `waiting` after one repair; third blocking iteration ends `limit_exhausted`; recorded transitions name the review artifact and finding IDs |
| P5 Specs, registry, reflections | Spec updates listed in §4; `.concorde/specs.json` ownership for `agents/**`, `agent_model.py`, `harness.py`; README/STUDIO/docsite wording; re-run the probe script and store the post-change result; fill Triage Analysis / Proposed Resolution / Intervention Rationale in R-066–R-070 | specs, `.concorde/specs.json`, `README.md`, `scripts/development/STUDIO.md`, `docsite/plugins/scoped-content/projections.ts`, `.concorde/reflections/**` | `python3 scripts/concorde.py validate` clean; docsite tests pass; reflections close (and are deleted) after delivery |

Estimated size: P1 ≈ 25 files, P2 ≈ 8, P3 ≈ 8, P4 ≈ 6 (but the densest logic), P5 ≈ 12.

## 4. Spec documents this plan needs to touch (confirm before editing)

- `specs/concorde/shared/agent-runtime-contracts.md`: `build_launch_specification(..., agent_binding_json)`,
  `LaunchSpecification.agent_binding_json`, `CapabilityExecutionError(message, receipt=None, outcome="failed")`,
  runner `timeout` keyword, `AgentBinding` record.
- `specs/concorde/modules/agent-execution.md`: default runner now enforces the Harness timeout; outcome vocabulary.
- `specs/concorde/modules/permissions.md`: updated signature line.
- `specs/concorde/modules/package-assets.md`: `load_agent`, `resolve_agent`, `generated/agents/`, ownership of `agents/**`.
- `specs/concorde/services/capability-registry.md`: replace the "compatibility bindings" paragraph with the agent/harness inventory and the `concorde-agents` block.
- `specs/concorde/services/workflow-host-boundary.md`: new error codes (`execution_cancelled`, `execution_limit`, `unknown_agent`, `invalid_agent_binding`), `concorde-check-feedback@1`, `concorde-review-result@1` as a stage input, graph policy and recorded transitions, `waiting`/`limit_exhausted` statuses.
- `specs/concorde/workflow/development.md` and `review-and-gaps.md`: only if the answers to the open questions change the drawn transitions (otherwise unchanged).

## 5. Assumptions made where the Spec leaves room

1. `spec.md` is both the Agent Spec and the prompt root (one source, rendered view traceable through the manifest).
2. Concorde capabilities are not Agent-callable today; every Harness declares `capabilities=()` explicitly instead of inventing a tool-call surface.
3. Wall-clock timeout is the only attestable loop bound; defaults `spec-capsule` 1800 s, `discovery-capsule` 900 s, `implementation-workspace` 3600 s, tightened per Agent if wanted.
4. Wire `outcome` enums stay unchanged; `waiting` / `cancelled` / `limit_exhausted` are worktree lifecycle statuses plus host error codes, not new response outcomes.
5. A human clarification still arrives as a Spec repair or a new change; a changed task string in the same worktree keeps raising `incompatible_handoff` (existing rule, not revisited here).
