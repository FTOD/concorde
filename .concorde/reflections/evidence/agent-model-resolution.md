# Agent-model refactor: R-066 – R-070 resolution evidence (phase P5)

- **Branch / worktree**: `agent-model` at `/home/zhenyu/concorde-worktrees/agent-model`
- **HEAD**: `2569066fd946f2a9babfb808da120008b3a8a355`
- **Baseline these reflections were recorded against**: `2fc199214e1cd98e6c998e28fbb84c18968c9d8e`
- **Commits since baseline** (`git log --oneline 2fc1992..HEAD`):
  ```
  2569066 feat(dev-loop): bounded code-review repair edge with attributed graph transitions
  69f7ab7 Merge branch 'main' into agent-model
  65086d7 feat(host): bind the Agent definition into every launch and bound its local loop
  72cc22e docs: make automatic agent handoff the default
  865e6c8 feat(agents): define Agents as spec.md + Harness + Constraints and bind them in the build
  a861f1f fix: align agent completion instructions with validation
  ```
- **Tests**: full suite (`.venv/bin/python -m unittest discover -s tests/concorde -t . -p 'test_*.py'`)
  — the plan recorded a progression of 625 → 647 → 657 tests across P1–P4; re-run against this HEAD
  after the P5 Spec-prose pass: **657 tests, OK (skipped=8)** — this phase adds no code, so the count
  is unchanged from P4's end state. `validate` reports `status: success`, zero findings, after the P5
  edits. Docsite: `npx vitest run` 28 files / 135 tests passed; `npx tsc --noEmit` reports no errors.
- **Probe evidence**: original (before) — `.concorde/reflections/evidence/agent-model-2fc1992-probes.py`
  / `.json` (primary worktree, unmodified). Adapted (after) —
  `.concorde/reflections/evidence/agent-model-2569066-probes-after.py` /
  `agent-model-2569066-probes-after.json`, run against this worktree's HEAD with no model service called (see
  §"Re-run of the design-review probe" below for why the script needed adaptation, not a bare re-run).

---

## R-066 · Ordinary Agent stages ignore narrowed role effect declarations

**Original Observed**: `Invocation.stage` built its `EffectDeclaration` from the phase and target
paths instead of the loaded role's own `prompt.effects`, so narrowing an Agent's declared writes to
`()` had no effect on the compiled policy — a policy-only probe still produced writable
`app/transfer.py`/`checks/transfer_check.py` paths.

**What changed**: `Invocation.stage` (`src/concorde/host/capability_host.py:1091-1109`) now derives
the workspace from `agent_definition(prompt.binding.agent).harness.workspace`, sets
`write_roles = ("implementation",) if implementation and not readonly else ()`, and compiles the
policy as `compile_policy(prompt.effects, PolicyBinding(capability, phase, 0, role, role,
write_roles=write_roles), roles, ...)` — i.e. from the *loaded Agent's own* declared effects, not a
phase-derived guess. `compile_policy` (`src/concorde/host/permissions.py:268-328`) is a narrowing
compiler: it raises `PermissionPolicyError` the moment a requested role would exceed the Agent's
leaf effects (`_role_selection`, line 251). `Invocation.stage` catches that and re-raises
`SpecError(str(error), "permission_denied")` (`capability_host.py:1108-1109`). The same pattern was
applied to `MainInvocation.stage` (`:295-302`) and `_topology_author` (`:720-727`), which previously
also hard-coded their own `EffectDeclaration` instead of consuming the loaded prompt's.

**Tests that pin the behavior**:
- `tests/concorde/specification/test_agent_binding.py::AgentBindingTests::test_narrowed_implementation_agent_write_authority_is_never_widened`
- `tests/concorde/specification/test_agent_binding.py::AgentBindingTests::test_readonly_investigation_path_has_empty_write_paths`
- `tests/concorde/host/unit/test_permissions.py::test_binding_can_narrow_but_never_widen_leaf_effects`

**After-probe confirmation**: the adapted probe's `narrowed_role_effects` scenario patches
`capability_host.load_role_prompt` to narrow the implementation Agent's writes to `()`, exactly as
the original probe did. With the new host this call no longer returns a policy at all: it raises
`SpecError(code="permission_denied")` before any model call, which the script now catches and
records (`error_code: "permission_denied"`, `model_calls: 0`) — the opposite of the original
`effective_write_paths` containing both implementation files. A second, unpatched variant
(`readonly_investigation`) shows the host's own built-in narrowing (`readonly=True`) also produces
`write_paths: []` for the `implementation-workspace` harness, with no need to patch anything.

**Remaining limitations**: none specific to R-066; the compiler's non-widening guarantee is now the
actual authority path for every ordinary stage, review and topology-author launch.

---

## R-067 · Agent roles lack individual spec.md and Python Harness bindings

**Original Observed**: `Role` in `src/concorde/host/roles.py` was only `name + prompt + effects`;
all nine roles pointed at root prompts under `prompts/`, with no `spec.md`, no Harness reference, no
per-Agent Python module, and no validation that a launched identity resolved to a complete Agent
definition.

**What changed**: a new top-level `agents/` package, one directory per Agent —
`agents/{coordinator,reader,spec_author,context_assessor,planner,task_author,
implementation_worker,spec_reviewer,code_reviewer}/{__init__.py,spec.md}`. Each `__init__.py`
declares `AGENT = Agent(name=..., spec="agents/<name>/spec.md", harness=<HARNESS>,
constraints=Constraints(...))` (`src/concorde/host/agent_model.py:29-47`, the `Agent`/`Constraints`
dataclasses). `agents/__init__.py` declares the `AGENTS` inventory tuple.
`src/concorde/host/agent_model.py::resolve_agent(package_root, name) -> AgentBinding`
(`:171-314`) resolves one Agent's complete binding against the current build, failing closed
(`BuildError` `unknown_agent`/`invalid_agent_binding`/`stale_build`) when the `spec.md` is missing,
its digest is not the one recorded in the build manifest, the Harness is unregistered, a capability
reference is unknown, or a context/result type is not exported. The build renders each `spec.md` to
`generated/agents/<hyphenated-name>.md` (traceable through the manifest). `roles.py` is now a
*derived* compatibility projection: `ROLES` is built from `load_agents()` so `role`/`agent` wire
fields keep working without being the Agent definition itself. Capability modules declare
`AGENTS = (agents.spec_author.AGENT,)` instead of `ROLES = (roles.SPEC_AUTHOR,)`.

**Tests that pin the behavior**:
- `tests/concorde/host/unit/test_agent_model.py::ResolveAgentBuildTests` (in particular
  `test_resolve_agent_succeeds_for_every_inventory_agent_after_write_build`,
  `test_resolve_agent_accepts_external_hyphenated_and_underscored_names`,
  `test_load_agent_binding_and_effects_match_resolve_agent`)
- `tests/concorde/host/unit/test_agent_model.py::ResolveAgentInvalidBindingTests` (fails-closed cases:
  `test_wrong_spec_path_is_invalid`, `test_unknown_capability_reference_is_invalid`,
  `test_context_not_admitted_by_the_harness_is_invalid`,
  `test_constraints_that_widen_effects_beyond_the_harness_are_invalid`)
- `tests/concorde/host/unit/test_package_validation.py::AgentRuleTests` and
  `SpecAlignmentAgentsRuleTests` (missing/duplicate Agent, unknown Harness,
  registry `concorde-agents` block mismatch)
- `tests/concorde/host/unit/test_build.py` (updated for `generated/agents/*` rendering)

**After-probe confirmation**: the adapted probe's `agent_bindings` scenario resolves every name in
`agents.AGENTS` through `resolve_agent(<worktree>, name)` and records, for all 9 Agents, a real
`spec.md` path (`bound_spec_md_count: 9` of `9`, versus the original probe's `bound_spec_md_count: 0`
of `9` role sources pointing at root prompts), a bound Harness name, a binding digest and an
effective loop timeout — see `agent_bindings.bindings` in `agent-model-2569066-probes-after.json`.

**Remaining limitations**: `LaunchSpecification` gained one field, `agent_binding_json`
(`launch_fields` in the after-probe now has 19 entries vs. the original's 18) — an additive,
backward-compatible wire change, not a limitation, but worth noting for anyone diffing the two
probe outputs field-by-field.

---

## R-068 · Agent Harness composition and available Capability references are absent

**Original Observed**: no Harness entity existed anywhere in `src/concorde/host`; execution
environment facts (workspace choice, tool/network posture, admitted context/result types,
environment filtering) were scattered inline across launch paths and renderers, with no inspectable,
named catalog.

**What changed**: `src/concorde/host/harness.py` defines the closed `Harness`/`LoopPolicy` record
shapes and the three registered instances — `DISCOVERY_CAPSULE`, `SPEC_CAPSULE`,
`IMPLEMENTATION_WORKSPACE` (`:170-207`) — each declaring `workspace`, `effects`
(`EffectDeclaration`), `capabilities` (explicitly `()`: host composition is not Agent-callable),
`tools`, `skills`, `contexts`, `results`, `loop` (`LoopPolicy`), `state` and `environment`
(`_SAFE_ENVIRONMENT`), plus a content-addressed `digest`. Every `Agent.harness` binds one of these
three by reference; `resolve_agent` verifies the Agent's `Constraints` never widen the bound
Harness's effects, contexts, results or loop bound (`agent_model.py:219-288`). Every structured
launch now carries the complete resolved identity: `Invocation.stage` puts `agent_binding_json=
binding_json(prompt.binding)` into the `LaunchSpecification` (`capability_host.py:1125`) and appends
`agent`, `harness`, `agent_binding_digest`, `instructions_digest` and `loop_timeout_seconds` to
`host.descriptions` (`:1130-1133`) — the `describe-policy` preview.

**Tests that pin the behavior**:
- `tests/concorde/host/unit/test_agent_model.py::HarnessDigestTests` (deterministic, order-independent
  digests; the three registered Harnesses are pairwise distinct)
- `tests/concorde/specification/test_agent_binding.py::test_describe_policy_descriptions_expose_agent_and_harness_identity`
- `tests/concorde/specification/test_agent_binding.py::test_description_agent_binding_digest_matches_resolve_agent`

**After-probe confirmation**: `agent_bindings.bindings` in the after-probe records, per Agent, the
exact bound `harness` name (`discovery-capsule` for `coordinator`; `spec-capsule` for `reader`,
`spec_author`, `context_assessor`, `planner`, `task_author`, `spec_reviewer`;
`implementation-workspace` for `implementation_worker`, `code_reviewer`) and a `binding_digest` —
the inspectable catalog the original probe found completely absent.

**Remaining limitations**: `capabilities=()` on every Harness is a deliberate design choice recorded
in the plan (§2.2, assumption 2), not a gap: Concorde capabilities are not Agent-callable today, so
the Harness makes that explicit rather than inventing a tool-call surface that nothing uses.

---

## R-069 · Development Agent Graph stops on review feedback without a revision loop

**Original Observed**: `Invocation.loop` built a linear stage sequence with no `review_code → tasks`
edge; a probe supplying one blocking code-review finding observed exactly one implementation and one
code-review invocation, then `status=blocked, outcome=conflicting` — no repair, no iteration budget,
no attribution of which finding selected which transition.

**What changed**: `Invocation.loop` (`src/concorde/host/capability_host.py`, the `StateGraph`
construction starting ~line 1573) is now a declared development Graph whose only automatic revision
edge is `review_code → tasks` (`route_review_code`, line 1725): blocking findings without a Spec
gap route back to `tasks`, which receives the completed tasks and the `concorde-review-result` as
declared stage inputs (added to the `stage_inputs` `anyOf` in `contracts.py`); the repaired
implementation is checked and reviewed again. The edge is bounded by
`capabilities/dev_loop.py`'s `GRAPH = {"max_repair_iterations": 2}`: unchanged blocking feedback
(same `(contract, problem, location)` set) stops the loop with status `waiting`; exhausting the
iteration limit stops it with `limit_exhausted`. Every selected transition — deterministic,
`ai-review`, `ai-assessment`, or `human` — is recorded per target under `graph.transitions` in
`.concorde/worktree.json` via `record_transition` (`capability_host.py:1718-1721`, `:1740-1745`),
with the review artifact reference, input digest and finding IDs. Spec gaps and failed checks still
stop the loop with `waiting`/`failed` for a human decision (`stop()`, line 1713) — that path is
unchanged by design.

**Tests that pin the behavior**: `tests/concorde/specification/test_review.py::RepairLoopTests` —
`test_blocking_then_clean_repairs_once_and_reaches_ready`,
`test_unchanged_blocking_feedback_stops_waiting_after_one_repair`,
`test_repeated_different_blocking_feedback_stops_at_the_declared_limit`,
`test_spec_gap_in_spec_review_stops_waiting_before_planning`,
`test_admitted_specify_spec_change_does_not_spuriously_reset_the_graph_record`,
`test_human_implementation_edit_resets_the_repair_record`,
`test_capability_execution_error_during_standalone_code_review_maps_to_execution_limit`.

**After-probe confirmation**: the original probe script's `blocking_ai_feedback` scenario could no
longer demonstrate the fix by itself (a *single* blocking review, unchanged, is exactly the
"unchanged feedback stops waiting" case, not repair) — the adapted script's `blocking_then_clean`
scenario reproduces the sequence `RepairLoopTests.test_blocking_then_clean_repairs_once_and_reaches_
ready` pins: one blocking finding on the first code review, a clean second review. The after-probe
records `status: "succeeded"`, `outcome: "ready"`, stages
`[specify, spec-review, context-solve, plan, tasks, implementation, code-review, tasks,
implementation, code-review]`, `implementation_invocations: 2`, `code_review_invocations: 2`,
`has_automatic_repair_iteration: true`, and one recorded `graph_transitions` entry:
`{"from": "review_code", "to": "tasks", "trigger": "ai-review", "outcome": "conflicting",
"finding_ids": ["daily-limit-check"], "iteration": 1, "artifact": {...}, "input_digest": "..."}` —
exactly the attributed repair edge the original probe found absent.

**Remaining limitations**: Domain-level code-review repair is delegated to component sub-loops — a
Domain target has no `implementation` scope of its own, so its top-level graph never grows a
`review_code` node; `implement()` routes a Domain to `implement_scope`
(`capability_host.py:1375`), and each participating component owns its own repair edge through
its own dev-loop graph. `waiting` and `limit_exhausted` are `.concorde/worktree.json` lifecycle
statuses and host error codes, not new wire `outcome` values — the `concorde-dev-loop-response`
`outcome` enum is unchanged (plan §5, assumption 4).

---

## R-070 · Agent execution lacks a bound local-loop policy and complete loop outcomes

**Original Observed**: `AgentProcessExecutor`'s default runner called `subprocess.run` with no
timeout; the launch contract had no Harness-bound local-loop configuration or per-invocation
iteration/time budget; worker outcomes omitted the complete waiting/cancellation/limit-exhausted
lifecycle.

**What changed**: `LoopPolicy(timeout_seconds, max_turns=None)` lives on every `Harness`
(`harness.py:42-57`) and may be tightened (never widened) by an Agent's `Constraints.limits`
(`agent_model.py:261-288` computes the effective, intersected loop). The runner interface gained a
`timeout` keyword; `_default_runner` passes it to `subprocess.run(timeout=...)`
(`agent_executor.py`). `AgentProcessExecutor.__call__` now derives `timeout =
binding.effective_loop.timeout_seconds` from the verified `AgentBinding` and passes it through
(`agent_executor.py:790-798`). `CapabilityExecutionError` distinguishes `failed`, `cancelled`,
`limit_exhausted` and `invalid_completion`: a `subprocess.TimeoutExpired` maps to
`limit_exhausted`, a `KeyboardInterrupt` during the process to `cancelled` (child already killed by
`subprocess.run`) — no retry, no wider permissions in either case. `run_capability` maps these to
error codes `execution_failed`/`execution_cancelled`/`execution_limit`, and worktree progress
records the matching `failed`/`cancelled`/`limit_exhausted` status. `EnforcementReceipt` and
`host.evidence` entries carry `agent_binding_digest`, so execution evidence is attributable to the
participating Agent, Harness and loop policy (G4).

**Tests that pin the behavior**:
- `tests/concorde/host/unit/test_agent_executor.py::test_runner_timeout_yields_limit_exhausted_outcome_with_binding_digest_and_no_retry`
- `tests/concorde/host/unit/test_agent_executor.py::test_runner_keyboard_interrupt_yields_cancelled_outcome`
- `tests/concorde/host/unit/test_agent_executor.py::test_tampered_binding_digest_is_refused`
- `tests/concorde/host/unit/test_agent_executor.py::test_successful_structured_run_carries_agent_binding_digest`
- `tests/concorde/specification/test_agent_binding.py::test_executor_receives_the_agents_effective_loop_timeout`
- `tests/concorde/specification/test_agent_binding.py::test_execution_limit_outcome_maps_to_execution_limit_and_records_change_status`
- `tests/concorde/specification/test_agent_binding.py::test_execution_cancelled_outcome_maps_to_execution_cancelled_and_records_change_status`
- `tests/concorde/specification/test_agent_binding.py::test_dev_loop_composition_records_child_limit_status_on_the_change`

**After-probe confirmation**: the after-probe's `agent_bindings.bindings` records
`effective_loop_timeout_seconds` for all 9 Agents (900s discovery-capsule / 1800s spec-capsule /
3600s implementation-workspace, matching the registered Harnesses — none of the nine `spec.md`
files declares a tighter `Constraints.limits`) and `effective_loop_max_turns: null` for every one.

**Remaining limitations**: native turn limits are not attested by either integration CLI (`codex
exec` 0.153.4, `claude -p` 2.1.263 — neither exposes a turn-limit flag), so `max_turns` stays `None`
for every registered Harness and every Agent's effective loop — confirmed by the after-probe (all
nine `effective_loop_max_turns` values are `null`). This is recorded as "not attested" per
`LoopPolicy`'s own docstring, not silently assumed unbounded. Wall-clock timeout remains the only
attestable, host-enforced loop bound.

---

## Re-run of the design-review probe

The original script, `.concorde/reflections/evidence/agent-model-2fc1992-probes.py`, patches
`capability_host.load_role_prompt` to narrow the implementation worker's declared writes, then calls
`Invocation(...).stage("concorde-implement")` expecting a *widened, still-writable* policy back —
that was the R-066 bug. Against this worktree the same call now raises
`SpecError(code="permission_denied")` before returning anything (§R-066 above), so the unmodified
script cannot complete: it would need to catch that exception to make any further progress, and its
single blocking-review loop scenario (R-069) can only demonstrate the *old* stop-without-repair
behavior, not the new repair edge, since it never supplies a second, clean review. An adapted copy
was written instead of patching the original in place (the original is retained unmodified as the
before-baseline):

- **Script**: `.concorde/reflections/evidence/agent-model-2569066-probes-after.py`
- **Result**: `.concorde/reflections/evidence/agent-model-2569066-probes-after.json`
- **Invocation**: `cd /home/zhenyu/concorde-worktrees/agent-model && .venv/bin/python
  .concorde/reflections/evidence/agent-model-2569066-probes-after.py
  /home/zhenyu/concorde-worktrees/agent-model` (exit 0, no stderr; no model service called — same
  temporary fixture projects and `ModelProcessDouble` substitution as the original).

Differences from the original, and why each was necessary:
1. **`agent_bindings`** now resolves every `agents.AGENTS` entry through `resolve_agent` (spec path,
   harness, binding digest, effective loop) instead of introspecting `roles.Role` — the `Role`
   record still exists (compatibility projection) but no longer carries the Agent definition R-067
   asked about.
2. **`narrowed_role_effects`** catches the now-raised `SpecError` and records its `error_code`
   (`permission_denied`) and that the declaration was enforced, instead of reading
   `policy["write_paths"]` off a call that no longer returns a policy. A second, unpatched
   `readonly_investigation` scenario (`readonly=True`) was added to show the host's own narrowing
   mechanism (not a test patch) also yields empty `write_paths`.
3. **`blocking_ai_feedback`** now runs a blocking-then-clean two-round scenario (copied from
   `RepairLoopTests` in `tests/concorde/specification/test_review.py`) instead of a single blocking
   round, because a single round no longer demonstrates anything about the repair edge — it would
   only reproduce the (still-present, by design) "unchanged feedback stops waiting" path. It also
   records the `graph_transitions` array from `.concorde/worktree.json`, which did not exist in the
   original schema.
4. **`source_sha256`** adds `agent_model.py` and `harness.py`, the two modules R-067/R-068 required
   and which did not exist at the baseline commit.
5. **`verified_commit`** is computed via `git rev-parse HEAD` inside the script rather than
   hard-coded, so it always reflects the worktree it was actually run against
   (`2569066fd946f2a9babfb808da120008b3a8a355`).

The `source_sha256` digests recorded in `agent-model-2569066-probes-after.json` are for the current worktree
HEAD; they differ from every digest in the original `agent-model-2fc1992-probes.json` because all
eight files changed (six modified, two new) between the two baselines.
