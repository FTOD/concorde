```concorde-document
{
  "id": "document.module.agent-execution",
  "targets": ["module.agent-execution"],
  "main_visible": false
}
```

# Agent execution

## Required Agent and Harness boundary

The registered Shared Spec **Agents and Harnesses** defines A1–A4 for this Module. Execution MUST
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
