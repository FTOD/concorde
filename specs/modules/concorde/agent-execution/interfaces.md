```concorde-document
{
  "id": "document.module.agent-execution",
  "targets": [
    "module.agent-execution"
  ],
  "main_visible": true
}
```

# Agent execution

## Required Agent and Harness boundary

The local companion contract **Agents and Harnesses** defines A1–A5 for this Module. Execution MUST
receive a resolved Agent definition binding `spec.md`, Harness and Constraints/Permissions, and
operate the admitted model integration and local loop. It MUST preserve identity and effective
resource limits through Capability calls and feedback. The executor's preflight
reconstructs and verifies the launch's declared `AgentBinding` — prompt, Harness, admitted
context/result types and policy — before starting any process, so the launch APIs below execute
only within a complete, checked Agent/Harness implementation.

## api.execution.execute

`AgentProcessExecutor` executes one host-built `LaunchSpecification` in a fresh Codex or Claude
process and returns a validated `CapabilityExecutionResult`, or raises `CapabilityExecutionError`.
The local companion contract **Agent runtime value and collaborator contracts** in this collection
defines the complete launch, policy, native configuration, bootstrap, receipt and completion records.
`LaunchSpecification` is the public type name; no separate `CapabilityLaunchSpecification` type exists.

## Interface signatures

The constructor is a frozen Python dataclass. Parameters may be supplied positionally or by name;
omitted parameters use the host defaults described below.

```python
ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]
VersionProbe = Callable[[str, str], str]
RuntimeBootstrapResolver = Callable[
    [str, str, str, Mapping[str, str]], tuple[RuntimeBootstrapFile, ...]]
RuntimeBootstrapVerifier = Callable[[tuple[RuntimeBootstrapFile, ...]], None]

AgentProcessExecutor(
    runner: ProcessRunner = host_subprocess_runner,
    version_probe: VersionProbe = host_version_probe,
    runtime_bootstrap_resolver: RuntimeBootstrapResolver = resolve_runtime_bootstrap,
    runtime_bootstrap_verifier: RuntimeBootstrapVerifier = verify_runtime_bootstrap,
    environment: Mapping[str, str] | None = None)
AgentProcessExecutor.__call__(specification: LaunchSpecification) -> CapabilityExecutionResult

resolve_runtime_bootstrap(integration: str, executable: str, project_root: str,
                          environment: Mapping[str, str]) -> tuple[RuntimeBootstrapFile, ...]
verify_runtime_bootstrap(files: tuple[RuntimeBootstrapFile, ...]) -> None
CapabilityExecutionError(message: str, receipt: EnforcementReceipt | None = None,
                         outcome: Literal["failed", "cancelled",
                                          "limit_exhausted", "invalid_completion"] = "failed")
```

`host_subprocess_runner` and `host_version_probe` label default behavior, not exported Python symbols.
An injected runner is called as `runner(argv: tuple[str, ...], *, cwd: str,
env: Mapping[str,str], input_text: str, timeout: float | None) -> subprocess.CompletedProcess[str]`.
It must honor the exact native enforcement arguments, use the supplied cwd/environment/stdin, capture
text stdout/stderr, and return the actual return code. The default uses a synchronous subprocess
without shell expansion; it passes `timeout` straight through to `subprocess.run`, which raises
`subprocess.TimeoutExpired` when the process runs longer. `timeout` is the bound Agent's effective
loop timeout (`AgentBinding.effective_loop.timeout_seconds`) for a structured (typed) launch, or
`None` for a legacy untyped launch that carries no Agent binding. An injected runner receives the
same `timeout` value and must raise `subprocess.TimeoutExpired` when it expires, so the executor can
distinguish a limit-exhausted execution from an ordinary failure.
The version probe receives `(integration, selected_executable)` and returns nonempty version text;
the default invokes that executable's `--version`. These injection hooks are trusted host interfaces,
not fields exposed to task JSON or agent-controlled tool proxies.

With `environment=None`, the host's environment is filtered to COMSPEC, HOME, LANG, LC_ALL, LC_CTYPE,
LOGNAME, PATH, PATHEXT, SYSTEMROOT, TEMP, TMP, TMPDIR, USER and WINDIR, retaining only string values.
An explicit mapping is filtered the same way. Model task credentials, config overrides and ambient
conversation are not added. Native client authentication is a host bootstrap concern and creates no
agent file or network grant.

## Preconditions, outcomes and effects

The launch must be produced from matching capability/role/integration/policy/context identities.
The executor rejects mismatched effective read/write/deny/default-deny/network/credential fields,
missing enforcement, absent outer-sandbox evidence, an unexpected executable or stale policy digest.
Native Codex/Claude versions below 0.138.0/2.1.248 are rejected when their version text parses; an
empty version response always fails. A host-issued outer sandbox remains the authority for outer
execution. No failure retries with a more permissive configuration.

Codex bootstrap resolves the selected executable from the filtered PATH to one native executable
regular file outside project authority. Script/package shims, group/world-writable files and
untrusted owners are rejected. The owner must be root or the current uid where available. Its bytes,
path, size, permissions and owner are attested and checked again before use. Other integrations
return an empty bootstrap tuple. The permission Module's locally declared finalization API adds only
that attested file and rebinds the launch/configuration digests without widening task permissions.

Every call starts a new process. Its stdin contains the complete host snapshot, task and role
instructions; Profile 9 never passes predecessor transcripts. Spec review uses only its private
capsule. Code review uses a distinct read-only implementation grant. Codex automatic AGENTS.md
loading is disabled, and its generation schema is adapted to supported strict syntax while the host
continues to validate the original typed contracts. The executor parses the native lifecycle output
and requires an actual completed turn plus a valid completion envelope. Schema 3 domain-output type
is determined by the admitted stage-context type, including the separate review-stage context/result.
A successful process exit alone is not success.

Only a matching successful completion is returned. Invalid JSON/lifecycle, wrong role/invocation/
launch/workspace/bootstrap identity, wrong domain-output type, failed gates, a success limitations value other than `none`, nonzero exit or a reported failed completion raises `CapabilityExecutionError`. It has
`.receipt` after a process supplies exit/invalid completion evidence; preflight/runner failure may
have `receipt=None`. Callers stop the affected transition. A new call is a new execution, not replay
of a prior completion. Authorized implementation edits made before failure can remain in the
candidate; the executor does not promise rollback. Read-only reviewers cannot edit project files.
Raw stdout/stderr are host diagnostics and cannot substitute for typed downstream inputs.

## Local loop policy and outcomes

A structured launch's control-loop timeout is the bound Agent's effective loop (`AgentBinding.
effective_loop.timeout_seconds`, itself never wider than its Harness's declared loop); a legacy
untyped launch has no bound Agent and passes no timeout, so the default runner waits without a
limit. `CapabilityExecutionError.outcome` distinguishes four cases so a caller need not parse
message text: `failed` (default) for a nonzero exit or a launch/preflight failure; `cancelled` when
the injected runner raised `KeyboardInterrupt`, with the child process already terminated by
`subprocess.run` before the interrupt propagates; `limit_exhausted` when the runner raised
`subprocess.TimeoutExpired`, meaning the bound Agent's loop timeout was exceeded; and
`invalid_completion` when a zero-exit process returned a completion that failed validation or was
itself reported as a domain failure. None of these outcomes triggers an automatic retry, with the
same or any wider permissions; native provider turn limits are not attested by either integration's
lifecycle output, so `LoopPolicy.max_turns` stays `None` unless a caller explicitly narrows it.

## Required collaborator promises and representative use

The permission compiler/renderer/finalizer contracts and value types are fully defined in the
registered local companion document. The wire collaborator provides `json_schema(type_id: str) -> dict` for a
self-contained typed result schema and `validate_typed(value: Any, expected: str | None = None,
field: str = "") -> dict` for strict type/version/property/uniqueness validation. Unknown type/version,
unsafe paths, invalid fields and mismatched expected types raise `TypedDataError(ValueError)`
with `code` and `field`. The executor must treat these as invalid completion, not successful output.
These calls perform no project mutation or remote schema resolution.

```python
executor = AgentProcessExecutor()
# launch is already built by the trusted host using the local runtime-value document's builder contract.
try:
    result = executor(launch)
except CapabilityExecutionError as failure:
    failed_receipt = failure.receipt  # nullable; retain host diagnostics and stop the transition
else:
    assessment = result.completion.domain_output
    receipt = result.receipt         # binds both requested and finalized launch identities
```

Consumers retain the original launch to verify receipt binding and consume the typed completion
rather than raw process output. A process double can test these boundary mechanics but cannot
establish that a model detected a semantic gap or behavior defect.

## api.execution.invoke-agent

`AgentRuntime` is the host's recursive scheduling layer over the existing canonical
`agent_model.Agent`, `harness.Harness` and `AgentBinding` records in the admitted local companion document.
`CapabilityHost.invoke_agent(runtime, agent_id, input, grant)` invokes it and retains its events.
The normal stage executor and the development graph's bounded review/repair edge remain intact.
A registered Agent may run as a one-decision stage or participate in an explicitly assembled
recursive graph; neither Codex nor Claude is a fixed leaf kind.

### Host graph bindings and authority

```python
RuntimeAgent(agent: Agent, decide: Callable[[AgentFrame], AgentStep], package_root: Path,
             targets: frozenset[str], delegates: frozenset[str], decision_reference: str,
             input_type: str = "concorde-agent-task", result_type: str = "concorde-agent-answer",
             max_steps: int = 8, binding: AgentBinding | None = None)
AgentGrant(targets: frozenset[str], agents: frozenset[str])
AgentLimits(max_calls: int = 16, max_depth: int = 4, max_decisions: int = 64,
            timeout_seconds: float = 300)
AgentRuntime(definitions: Iterable[RuntimeAgent], resolve_context, *,
             limits=AgentLimits(), cancelled=lambda: False)
AgentRuntime.invoke(agent_id: str, input: dict, grant: AgentGrant) -> AgentRun
```

`RuntimeAgent` binds one existing Agent to its host decision callback and a project-specific graph
scope; it is not another Agent definition or Harness. Its `id` is `agent.name`, `spec_path` resolves
`agent.spec` under `package_root` (an explicitly supplied absolute Agent Spec path remains absolute),
and `timeout_seconds` is the smaller of the canonical Harness and Agent constraint timeouts.
`decision_reference` is a nonblank versioned reference identifying the trusted callback and its
configuration. The host must supply an accurate reference and resolve its callback before
construction; task JSON never names Python modules to import. Code callbacks may use canonical
Agent records defined by trusted Python modules with an explicit authored `spec.md`. Native
callbacks additionally require the registered Agent's current resolved binding and rendered prompt.

Construction rejects duplicate/empty Agent names, unresolved child names, absent/empty Agent Specs,
symlink Spec files, unknown typed contracts, malformed target/edge sets and nonpositive local steps.
Each canonical Harness must equal its registered configuration. Effective Agent effects must remain
read-only with no network/credentials and within the Harness; context/result declarations must be
subsets of the Harness and include the graph binding's input/result types. Nonempty delegation
edges require `agent.constraints.allow_delegation`. Native bindings must match the actual catalog
Agent and current package resolution; the built-in native adapter cannot start without one.
Invalid construction raises `ValueError` or the collaborator's `BuildError` before any decision.

The root must be in `grant.agents`. Each invocation intersects inherited targets with the graph
binding's targets. The tree's inherited Agent allowlist stays unchanged: direct-edge checks do not
intersect it with the parent's delegates. A child must satisfy both the parent's explicit edge and
that allowlist before context resolution. Thus A→B→C and explicit self-edges are supported without
implicit authority. Every child starts with fresh invocation identity, context and empty feedback.
Malformed grants raise `ValueError`; insufficient valid grants return `rejected`.

All integer tree limits are positive except depth may be zero; timeout is positive and finite.
Root depth is zero. Calls, decisions and depth share one tree budget, and local steps never reset.
Each invocation's deadline is also bounded by its canonical Agent/Harness timeout and inherited
ancestor deadline. Descendants and continuations cannot extend those deadlines.

The resolver receives `(node: RuntimeAgent, validated_input: dict, effective_grant: AgentGrant)`
and returns a complete typed `concorde-context-snapshot@1`. Its target must be admitted, its phase
must be `ask`, its context ID must match its bytes and implementation artifacts must be empty.
For `concorde-agent-task`, the task target must also match the snapshot. The host uses the existing
context service to resolve the complete collection; task text and paths are not authority.
Admission failures return `rejected/admission_failed`. The runtime freezes Agent Spec bytes and
rechecks them and the exact resolved context before each decision. Changed context is
`rejected/stale_context`; changed Agent Spec/native binding is `rejected/stale_definition`.

### Decisions, feedback and results

```python
AgentFrame(invocation_id: str, parent_id: str | None, agent_id: str,
           input_json: str, context_json: str, spec: str,
           feedback: tuple[AgentResult, ...], children_json: str,
           result_schema_json: str, remaining_seconds: float, deadline: float,
           agent_binding_json: str | None = None)
AgentStep(source: str, action: str, agent_id: str | None = None, value: dict | None = None,
          outcome: str = "completed", details: dict | None = None)
AgentResult(invocation_id: str, parent_id: str | None, agent_id: str, outcome: str,
            value_json: str | None, error: str | None, details_json: str | None = None)
AgentRun(result: AgentResult, events: tuple[dict, ...])
```

These records are frozen. Frame input/context fields are canonical typed JSON. `spec` is the
registered Agent's exact rendered instructions for native decisions, or its authored Spec for a
trusted code callback. `agent_binding_json` is the canonical native binding, never model input.
`result_schema_json` describes the bound result type. `children_json` is ordered by Agent name;
each entry has string `agent_id`, `input_type`, `result_type`, `input_schema_json` and
`result_schema_json`. Only admitted direct edges with nonempty target intersection are advertised.
No private child context, parent frame, host grant object or transcript enters a child frame.
`deadline` uses Python's absolute `time.monotonic()` clock; `remaining_seconds` is its remaining
budget at frame creation, not a fresh duration.

`source` is `code-driven` or `model-driven`; `action` is `delegate` or `complete`. Delegation requires
a child name and typed input, outcome `completed`, and no interruption details. Completion cannot
name a child. A completed result requires the bound typed value and no details; other outcomes have
no value. Terminal outcomes are `completed`, `spec_incomplete`, `waiting`, `cancelled`, `failed`,
`limit_exhausted` and `rejected`. Spec incompleteness requires typed
`concorde-agent-interruption@1` details with nonempty gaps and null decision; each gap has nonblank
question/blocked_step/needed_contract/target_id and the invocation's sha256 context_id. Waiting
requires only a nonblank decision question. Other outcomes forbid interruption details.

Feedback starts empty and retains all direct child results in request order, including rejected
requests, with one appended record per child request. Descendant results are not flattened into
this history. A failed/rejected child permits another bounded parent decision; cancellation or
limit exhaustion terminates ancestors immediately. `AgentResult.wire()` returns exactly
`invocation_id`, `parent_id`, `agent_id`, `outcome`, `value_json`, `error` and `details`; the last
field decodes `details_json` to its typed object or null. Error strings are stable host codes, not
raw process diagnostics. No successful value accompanies an unsuccessful outcome.

Unexpected callback exceptions yield `failed/execution_failed`. A native
`CapabilityExecutionError` preserves cancelled/limit-exhausted outcomes; invalid native completion
is `failed/invalid_completion`. `KeyboardInterrupt` during a decision cancels the invocation.
Malformed actions/results and callback `InvalidAgentStep(ValueError)` yield `rejected/invalid_step`.
Shared cancellation/exhaustion takes precedence over an otherwise successful or rejected step.
Synchronous callbacks are trusted host code, not an untrusted Python sandbox; they must return
promptly or enforce their own interruption. There is no persistent resume or parallel scheduling
in this initial recursive layer.

Admission evidence binds the canonical Agent/Harness/Constraints, graph edges and targets,
callback reference, current native binding when present, Spec, input/context and shared limits.
Host events distinguish admission, decision source/action and return. Admission retains the
Harness name and complete canonical Harness configuration for inspection. Events do not become
model feedback and do not replace the native execution receipt.

### Native decisions

`NativeAgentAdapter(integration="codex", executor=None)` uses the same registered Agent and
`AgentProcessExecutor` as ordinary stages. Every decision creates a new private read-only capsule,
passes the resolved `agent_binding_json`, compiles a no-network/no-credentials policy, and requires
matching native completion and Agent-binding evidence. It consumes `concorde-agent-loop-context@1`
and returns `concorde-agent-loop-step@1`; their task/feedback/child/value fields are the typed
transport records described above. Provider-native delegation remains disabled.

An injected callback has signature `executor(launch: LaunchSpecification, *, deadline: float)
-> CapabilityExecutionResult`. It must enforce the supplied policy and exact absolute monotonic
deadline, reject expiry before launch, and bound preflight/process work to the remaining time.
The default adapter installs runner/probe callbacks that also respect the canonical Agent's native
loop timeout. It never renews the tree deadline. A successfully attested step with malformed
serialized JSON or a non-model-driven source raises `InvalidAgentStep`; failed native attestation
remains an execution failure. Existing single-process runner and executor interfaces are unchanged.

A trusted host composes RuntimeAgent records and a resolver callback explicitly, then invokes
the graph through CapabilityHost.invoke_agent. The generic runtime provides no question-reading
factory. Ordinary question answering uses the coordinator's directly injected Spec contexts.
