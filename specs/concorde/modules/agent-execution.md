```concorde-document
{
  "id": "document.module.agent-execution",
  "targets": ["module.agent-execution"],
  "main_visible": false
}
```

# Agent execution

## Required Agent and Harness boundary

The registered Shared Spec **Agents and Harnesses** defines A1–A5 for this Module. Execution MUST
receive a resolved Agent definition binding `spec.md`, Harness and Constraints/Permissions, and
operate the admitted model integration and local loop. It MUST preserve identity and effective
resource limits through Capability calls and feedback. The launch APIs below are existing native
adapter contracts; their presence alone does not establish a complete Agent/Harness implementation.

## api.execution.execute

`AgentProcessExecutor` executes one host-built `LaunchSpecification` in a fresh Codex or Claude
process and returns a validated `CapabilityExecutionResult`, or raises `CapabilityExecutionError`.
The registered Shared Spec **Agent runtime value and collaborator contracts** in this collection
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
CapabilityExecutionError(message: str, receipt: EnforcementReceipt | None = None)
```

`host_subprocess_runner` and `host_version_probe` label default behavior, not exported Python symbols.
An injected runner is called as `runner(argv: tuple[str, ...], *, cwd: str,
env: Mapping[str,str], input_text: str) -> subprocess.CompletedProcess[str]`. It must honor the exact
native enforcement arguments, use the supplied cwd/environment/stdin, capture text stdout/stderr,
and return the actual return code. The default uses a synchronous subprocess without shell expansion
or an automatic timeout. Hosts needing a time limit supply a runner that raises on timeout.
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
instructions; Profile 8 never passes predecessor transcripts. Spec review uses only its private
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

## Required collaborator promises and representative use

The permission compiler/renderer/finalizer contracts and value types are fully defined in the
registered Shared Spec. The wire collaborator provides `json_schema(type_id: str) -> dict` for a
self-contained typed result schema and `validate_typed(value: Any, expected: str | None = None,
field: str = "") -> dict` for strict type/version/property/uniqueness validation. Unknown type/version,
unsafe paths, invalid fields and mismatched expected types raise `TypedDataError(ValueError)`
with `code` and `field`. The executor must treat these as invalid completion, not successful output.
These calls perform no project mutation or remote schema resolution.

```python
executor = AgentProcessExecutor()
# launch is already built by the trusted host using the local Shared Spec's builder contract.
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

`AgentRuntime` is the trusted in-process host entry for recursive Agents. It does not expose a new
public stage Skill. `CapabilityHost.invoke_agent(runtime, agent_id, input, grant)` calls this entry
and retains its tree evidence. Existing stage launch APIs remain compatible single-decision paths;
they do not implicitly gain delegation. Hosts must explicitly install definitions and issue grants.

The Python API in `agent_runtime.py` has these frozen records (sets are `frozenset[str]`):

- `AgentConstraints(targets, delegates, max_steps=8)` declares selectable project targets, named
  child edges (including explicit self-edges) and the local decision bound.
- `AgentGrant(targets, agents)` is trusted host authority for the whole tree. Root admission requires the root ID in `grant.agents`. Each call intersects inherited targets with
  its definition's targets. The inherited tree Agent allowlist remains unchanged; direct edge checks
  are separate and never intersect this allowlist with the parent's delegates. Thus A→B→C works
  with edges A:{B}, B:{C} and host agents {A,B,C}. A child must be in both the parent's delegates and
  the inherited host allowlist before context resolution. Definitions cannot enlarge either set. A grant is never model input.
- `AgentDefinition(id, spec_path, harness, constraints, input_type, result_type)` binds one authored
  nonempty `spec.md`, one `Harness(id, decide, configuration_json)` and registered typed input/result contracts. A trusted
  Python module exports the definition; arbitrary model-supplied modules are never imported.
- `AgentLimits(max_calls=16, max_depth=4, max_decisions=64, timeout_seconds=300)` bounds a root tree.
  Depth starts at zero. All integers are positive except depth, which may be zero. Each admitted
  invocation consumes one call, each decision consumes one decision, and local steps never reset.
- `AgentFrame` supplies `invocation_id`, `parent_id`, `agent_id`, immutable serialized typed input and
  context, authored `spec`, typed child `feedback`, permitted child contract descriptions and
  `remaining_seconds`. No parent frame, grant object, transcript or private child context is passed.
- `AgentStep(source, action, agent_id=None, value=None, outcome="completed", details=None)` is the decision result.
  Source is `code-driven` or `model-driven`. `delegate` requires a permitted child ID and typed input;
  `complete` requires a typed result for `completed`, otherwise no result value. `details` is a typed `concorde-agent-interruption` for gaps/waiting only. Terminal outcomes are
  `completed`, `spec_incomplete`, `waiting`, `cancelled`, `failed`, `limit_exhausted` and `rejected`.
- `AgentResult(invocation_id, parent_id, agent_id, outcome, value_json, error, details_json=None)` returns validated JSON
  only on completion. Other outcomes carry no result payload. `spec_incomplete` requires typed interruption details with
  nonempty gaps (question, blocked_step, needed_contract, target_id and context_id); `waiting`
  requires a nonempty human-decision question. Each gap must match this invocation's snapshot.
  The interruption has `gaps` and nullable `decision` fields; only the field appropriate to its
  outcome is populated. Other outcomes forbid details. Error is a stable host code, never raw logs.
  Its `wire()` representation is the feedback record defined below. `AgentRun(result, events)` adds
  host-only binding/decision evidence; events never enter model feedback.

`Harness.configuration_json: str` is a canonical, immutable JSON object. It requires exactly
six nonempty string references (`model_integration`, `context_assembly`, `control_loop`,
`state_handling`, `system_environment`, `implementation`) and three lists of unique nonempty string
references (`capabilities`, `tools`, `skills`). Empty lists explicitly admit no resources of that kind.
The trusted host must resolve these versioned policy/implementation references before installing the
definition and must describe its actual callback and executor configuration accurately. Native and
mixed callbacks remain trusted Python code; the runtime does not introspect their closures or grant
authority from these descriptions. Missing or malformed configuration raises `ValueError` before
any decision. `Harness` canonicalizes the JSON at construction and freezes its fields. A changed
configuration requires a newly constructed Harness/runtime and fresh admission; its full canonical
bytes participate in `binding_digest`, even when `Harness.id` is reused. Each host-only `admit` event
retains `harness_id` and `harness_configuration_json` for inspection. These records are not model
input or an execution grant.

`Harness.decide(frame: AgentFrame) -> AgentStep` receives these exact public fields:

```python
AgentFrame(
    invocation_id: str, parent_id: str | None, agent_id: str,
    input_json: str, context_json: str, spec: str,
    feedback: tuple[AgentResult, ...], children_json: str,
    result_schema_json: str, remaining_seconds: float, deadline: float)
```

`input_json` and `context_json` contain canonical JSON for the admitted typed input and complete
typed context snapshot. `spec` contains this Agent's authored Spec text. `result_schema_json`
contains the JSON Schema for this Agent's registered result type. `children_json` contains a JSON
array ordered by child Agent ID. Each entry has `agent_id`, `input_type`, `result_type`,
`input_schema_json` and `result_schema_json`, all strings; the schema fields serialize the child's
registered input and result JSON Schemas. Entries include only direct delegation edges admitted by
the host Agent allowlist whose target grant intersects the current invocation's effective targets.
They expose neither child context nor additional authority. `remaining_seconds` is the remaining
shared tree deadline at frame construction, not a new timeout budget.
`deadline` is that exact absolute deadline on Python's `time.monotonic()` clock, shared by every
invocation and continuation in the tree; it is a trusted host value, not model context.

`feedback` is initially empty. Each subsequent frame retains all results of this invocation's
direct child requests in request order, including rejected requests, with one appended
`AgentResult` per request. It does not flatten descendant results into the parent's history.
A child's `cancelled` or `limit_exhausted` outcome terminates the parent immediately, so there is
no subsequent decision frame for that outcome. `AgentResult.wire() -> dict` returns exactly
`invocation_id: str`, `parent_id: str | None`, `agent_id: str`, `outcome: str`,
`value_json: str | None`, `error: str | None` and `details: dict | None`. `value_json` retains the
serialized typed completion value; `details` decodes `details_json` to the typed interruption
object, or is null. Feedback contains no private child context or host event records.

`AgentRuntime(definitions, resolve_context, *, limits=AgentLimits(), cancelled=lambda: False)`
freezes the catalog. `invoke(agent_id, input, grant) -> AgentRun` creates fresh tree counters and IDs.
The trusted resolver is called with `(definition, validated_input, effective_grant)` and returns a
complete `concorde-context-snapshot`. The runtime validates its type, `ask` phase and target grant and
binds its canonical bytes, the definition's Spec, Harness ID and configuration, input, effective grant
and shared `AgentLimits` values into evidence.
Invalid definitions, absent/changed Spec bytes, unknown contracts and dangling child references fail
before starting any decision. Context admission failures return `rejected` with `admission_failed`.
The resolver must use the existing context service to select the appropriate complete closure;
it cannot use the task text or a supplied path as authority. Invocation ID is distinct even when
context content is equal. The runtime rechecks definition Spec bytes and calls the trusted resolver again before every
 decision, comparing the exact frozen snapshot. A change returns `rejected/stale_context`; no changed
 context silently enters a continuation. The snapshot ID must match its canonical content and an
 `ask` snapshot cannot carry implementation artifacts.

A delegate action validates the edge and typed input before resolving any child context. The child
receives a fresh frame and zero local feedback. Only its typed result returns to the parent. A failed
or rejected child is feedback for the parent's next bounded decision. A cancelled or limit-exhausted
child immediately terminates ancestors with that outcome. Local completion cannot override root
cancellation or exhaustion. Unexpected exceptions produce `failed/execution_failed` without exception text.
Malformed decisions/results produce `rejected/invalid_step`; no permissive retry occurs.
`InvalidAgentStep(ValueError)` is the decision callback's explicit malformed-step signal. The
native adapter uses it when a successfully attested step contains undecodable serialized JSON or
claims a non-model-driven source. Runtime cancellation or exhaustion still takes precedence over
that rejection. Native launch, attestation or completion-envelope failures remain execution
failures, distinct from a malformed decision within a successfully attested completion.
Cancellation and deadlines are checked before and after host callbacks. Trusted synchronous Python
callbacks must return promptly or enforce their own interruption; they are host code, not a sandbox
for untrusted Python. The default native runner enforces the remaining tree time as subprocess timeout.
There is no durable resume or parallel scheduling in this initial runtime.

### Native Agent adapter and client boundary

`NativeAgentAdapter(integration="codex", executor=None)` implements a model-driven Harness decision.
It supports `codex` and `claude`. Every decision builds a new read-only private capsule, compiles a
policy granting only `context.json`, and invokes the existing `AgentProcessExecutor`. Project code,
network, credentials, ambient instructions and provider-native delegation are unavailable. The
adapter checks receipt and completion binding and returns only a validated `AgentStep`. Injected
executors remain trusted hooks. A supplied callable has signature
`executor(launch: LaunchSpecification, *, deadline: float) -> CapabilityExecutionResult`, where
the deadline is the tree's absolute `time.monotonic()` deadline. It must reject an already expired
deadline and bound its preflight and process work by the remaining time, raising a timeout exception
on expiration; the runtime reports `limit_exhausted` when the shared deadline has elapsed.
It must also honor the launch's policy and native completion/receipt contract. This adapter-specific
hook differs from the existing single-process `AgentProcessExecutor(launch)` interface: a trusted
wrapper can install deadline-bound runner and version-probe callbacks around that executor.
The default adapter does so itself, without extending the deadline for a new decision.

`concorde-agent-loop-context` contains invocation/parent/Agent IDs, the typed input serialized as
`input_json`, admitted snapshot serialized as `context_json`, declared child contracts, and feedback.
Each child contract identifies `agent_id`, `input_type`, `result_type` and their JSON Schemas. The
JSON strings are transport fields, not arbitrary input types: the host validates their contained
values against the installed definitions and revalidates feedback before constructing each frame.
`concorde-agent-loop-step` contains `source`, `action`, nullable `agent_id`, nullable `value_json`, nullable typed `details` and
`outcome`. Both types are version 1 and reject unknown properties. The native completion envelope
retains version 3 and must match the specific decision launch/invocation/context identity.

`agents.reader.definition(package_root, target_id, integration="codex", executor=None, *,
executor_reference=None)` binds
`prompts/agents/reader/spec.md` and the native adapter to the named `concorde-recursive-reader`.
It accepts `concorde-agent-task` (`task: nonempty string`, `target_id: nonempty string`) and returns
`concorde-agent-answer` (`answer: nonempty string`). Its explicit self-edge permits recursive task
decomposition within the same host-admitted target. The host factory requires `target_id`; the
reader cannot choose or discover another target. Its task `target_id` must equal the factory target
before context resolution; a mismatch is `rejected/admission_failed`. Its responsibility Spec instructs bounded analysis,
optional task decomposition, typed synthesis, and separate gap/waiting/failure outcomes. A leaf
reader call and a delegating reader call use the same definition.
Its Harness configuration identifies the chosen native integration, execution capability,
context-service policy, recursive read-only control loop, invocation-local feedback without resume,
and the default native-enforcement executor environment. The implementation reference is a digest
of the reader, runtime, native adapter, process executor and permission implementation source bytes
in `package_root`. An injected executor requires a nonempty, versioned `executor_reference` naming
its actual configuration; omission raises `ValueError`. The host is responsible for resolving and
honoring that reference and the existing executor policy/deadline contract.

A host can also supply a code-driven `Harness.decide(frame) -> AgentStep` or one that chooses a code
rule or the native adapter on each iteration. A code callback can delegate to the reader; the reader
can delegate to any explicitly declared code Agent. No special case prohibits either direction.


`agents.reader.runtime(project_root, package_root, target_id, *, integration="codex", executor=None,
executor_reference=None, limits=None, cancelled=lambda: False)` installs that definition with the existing context service.
It verifies build freshness and reconstructs the complete target snapshot on every admission and
freshness check. `limits=None` selects `AgentLimits()`; the factory itself starts no Agent and grants
no authority. A trusted enclosing host invokes it explicitly:

```python
from concorde.agents.reader import runtime
from concorde.host.agent_runtime import AgentGrant
from concorde.host.typed_data import typed

reader = runtime(host.project_root, host.package_root, target_id)
run = host.invoke_agent(reader, "concorde-recursive-reader",
    typed("concorde-agent-task", {"task": task, "target_id": target_id}),
    AgentGrant(frozenset({target_id}), frozenset({"concorde-recursive-reader"})))
# run.result is the typed return; run.events are host evidence, not child context.
```
