```concorde-document
{
  "id": "document.specs.modules.concorde.spec-context.runtime-values",
  "targets": [
    "module.spec-context"
  ],
  "main_visible": true
}
```

# Agent runtime value and collaborator contracts

This registered local companion document defines the exact public value records used by the capability host,
permission compiler and executor. These are Python in-process contracts; they do not give an agent
permission to construct its own grant. Strings called digests are canonical `sha256:` plus 64 lower-case
hex digits. Paths in policies are project-relative POSIX paths without aliases or symlinks; an
attested runtime bootstrap path is the explicitly distinguished absolute native-client file.

## Policy construction

```python
EffectDeclaration(reads: tuple[str, ...] = (), writes: tuple[str, ...] = (),
                  network: bool = False, credentials: Literal["none", "declared"] = "none")
PolicyBinding(capability: str, stage: str, occurrence: int, role: str, agent: str,
              read_roles: tuple[str, ...] | None = None,
              write_roles: tuple[str, ...] | None = None,
              network: bool | None = None,
              credentials: Literal["none", "declared"] | None = None)
compile_policy(effects: EffectDeclaration, binding: PolicyBinding,
               role_paths: Mapping[str, tuple[str, ...]], *, deny_paths: tuple[str, ...] = (),
               outer_sandbox_required: bool = False) -> NormalizedPolicy
```

Effects declare the leaf role's maximum authority. A binding selects a subset; `None` retains that
field's declared effect. Every selected role must have a host-provided concrete path tuple. Writes
must also be readable. Unknown/duplicate roles, unsafe paths, widened reads/writes/network/credentials
raise `PermissionPolicyError(ValueError)`. Compile does not launch a process or write project files.
The default-deny result additionally denies common credential paths. Explicit path grants never
turn a task string, file link, registry relationship or returned ArtifactRef into authority.

`NormalizedPolicy` is a frozen record with these attributes:

| Attribute | Type and meaning |
|---|---|
| capability, stage, role, agent | str; the exact bound capability and role identities |
| occurrence | int; this stage occurrence |
| read_paths, write_paths, deny_paths | tuple[str, ...]; sorted, deduplicated concrete grants/denies |
| default_deny | bool; compiler results are true |
| network_enabled | bool; cannot exceed effects |
| credentials | Literal["none", "declared"]; cannot exceed effects |
| outer_sandbox_required | bool; host requires verified outer enforcement |
| digest | str; identity of this binding and effective policy |

Spec workers and Spec reviewers receive only `spec-context`. Implementation workers additionally
receive `implementation` with writes. Code reviewers receive the current target's enumerated
implementation files for reading, with an empty write-role tuple. Native review grants cannot
modify Spec, source, tests, context capsules, or lifecycle records.

## Native launch configurations

```python
render_codex_configuration(policy: NormalizedPolicy, *, native_enforcement: bool,
                           outer_sandbox: str | None = None) -> CodexLaunchConfiguration
render_claude_configuration(policy: NormalizedPolicy, *, native_enforcement: bool,
                            outer_sandbox: str | None = None) -> ClaudeLaunchConfiguration
verify_effective_subset(declared: NormalizedPolicy, effective: NormalizedPolicy) -> None
compare_effective_boundaries(first: NativeLaunchConfiguration,
                             second: NativeLaunchConfiguration) -> bool
```

`NativeLaunchConfiguration = CodexLaunchConfiguration | ClaudeLaunchConfiguration`. Both are
frozen records carrying `integration: Literal["codex", "claude"]`, `argv: tuple[str, ...]`,
`effective_read_paths/effective_write_paths/effective_deny_paths: tuple[str, ...]`,
`default_deny/network_enabled: bool`, `credentials: Literal["none", "declared"]`,
`policy_digest: str`, `enforcement: str` (`native` or `outer`), `outer_sandbox: str | None`,
`runtime_bootstrap: tuple[RuntimeBootstrapFile, ...]`, `runtime_bootstrap_digest: str`, and `digest: str`.
Codex additionally carries `permission_profile: str`, `approval_policy: Literal["never"]`,
`strict_config: bool` (true), and `configuration: Mapping[str, Any]`. Claude carries
`settings_json: str` and `permission_mode: Literal["dontAsk"]`.

Renderers preserve the normalized effective boundary. Codex explicitly disables `multi_agent` and
`multi_agent_v2`; Claude denies the `Agent` and legacy `Task` tools. These native tools cannot bypass
the host's explicit Agent delegation protocol. Code-driven and model-driven Agent adapters request
children through the host, while the process executor remains a single-decision client interface. Native Codex uses a named default-deny
filesystem/network profile, ignores user configuration, and sets `project_doc_max_bytes=0` so
ambient AGENTS.md discovery neither supplements nor prevents the frozen host context. Claude
receives a native permission policy and disabled ambient settings. If native enforcement is not
available, rendering requires the trusted host's verified outer sandbox; otherwise it raises
`PermissionPolicyError`. A string supplied by task JSON is never evidence of outer enforcement.
`verify_effective_subset` rejects widening; `compare_effective_boundaries` compares effective grants.

`RuntimeBootstrapFile(path: str, sha256: str, size: int, mode: int, owner: int | None, digest: str)`
is a frozen attestation of one executable regular file. `size` is positive, `mode` records permissions,
`owner` is the uid where available, and `digest` covers all these properties. Its read grant is a
client bootstrap exception and grants neither its enclosing directory nor project knowledge.

```python
runtime_bootstrap_file(*, path: str, sha256: str, size: int, mode: int,
                       owner: int | None) -> RuntimeBootstrapFile
runtime_bootstrap_digest(files: tuple[RuntimeBootstrapFile, ...]) -> str
finalize_codex_configuration(configuration: CodexLaunchConfiguration,
                             runtime_bootstrap: tuple[RuntimeBootstrapFile, ...]) -> CodexLaunchConfiguration
finalize_launch_specification(specification: LaunchSpecification,
                              runtime_bootstrap: tuple[RuntimeBootstrapFile, ...]) -> LaunchSpecification
```

Attestations reject malformed digest/size/mode/owner fields. Native Codex finalization requires
exactly one attested binary, adds only that file's read rule, selects its exact executable path and
recomputes configuration/launch identities. Claude and verified outer configurations use no native
Codex bootstrap. Finalization preserves every task read/write/deny/network/credential field.

## Agent binding

The single canonical definition is `agent_model.Agent(name: str, spec: str, harness: Harness,
constraints: Constraints)`. `name` is its catalog key (for example `planner`); a native role uses
the external name `concorde-planner`. Its frozen `Constraints` has `effects: EffectDeclaration`,
`capabilities: tuple[str, ...]=()`, `contexts: tuple[str, ...]=()`, `results: tuple[str, ...]=()`,
`limits: LoopPolicy | None=None` and `allow_delegation: bool=False`. The last field permits only
host-mediated loop delegation through explicit graph edges and invocation grants; it does not
enable provider-native sub-agent tools or change existing coordinator routing contracts.
Enabling it requires the declared `concorde-agent-loop-context` and `concorde-agent-loop-step`
interfaces. `resolve_agent` rejects a non-boolean flag or missing loop interfaces with
`BuildError/invalid_agent_binding`. The flag participates in the existing constraints digest.

`harness.Harness` is the existing frozen configuration record: `name: str`,
`model: "project-configured"`, `integrations: tuple[str, ...]`, `workspace: "capsule"|"project"`,
`effects: EffectDeclaration`, string tuples `capabilities`, `tools`, `skills`, `contexts`, `results`
and `environment`, `loop: LoopPolicy`, `state: str` and `digest: str`. The `harness(...)` factory
normalizes unique tuple fields and hashes the complete configuration except its own digest.
`LoopPolicy(timeout_seconds: int, max_turns: int | None=None)` requires positive limits; a null
turn limit is not attested. Agent constraints may narrow the registered Harness. The existing
`discovery-capsule`, `spec-capsule` and `implementation-workspace` remain the configuration catalog.
The Spec capsule admits both ordinary stage contracts and the recursive task/answer and
loop-context/loop-step interfaces; an Agent must explicitly declare the subset it uses.
There is no separate recursive Agent or Harness definition model.

The host-only lookup API is `agent_definition(name: str) -> Agent`; it accepts the bare catalog
key, its hyphenated spelling or its `concorde-` external name and raises `BuildError/unknown_agent`
when absent. `external_agent_name(name: str) -> str` prefixes a bare key and replaces underscores
with hyphens. `resolve_agent(package_root: str|Path, name: str) -> AgentBinding` verifies the
current built Spec/instructions, registered Harness and narrowed constraints and returns the
immutable binding below. Unknown names, stale builds and inconsistent definitions raise
`BuildError` with `unknown_agent`, `stale_build` or `invalid_agent_binding`. These APIs do not
invoke an Agent, select a project target or grant its context.

`AgentBinding` (module `agent_model`) is the reproducible identity of one resolved Agent definition
(the local companion contract **Agents and Harnesses** defines A1/A4, the Agent/Harness/Constraints
model this binding resolves). It is a frozen record with `agent: str`, `spec_path: str`,
`spec_digest: str`, `instructions_path: str`, `instructions_digest: str`, `harness: str`,
`harness_digest: str`, `constraints_digest: str`, `build_manifest_digest: str`,
`effective_loop: LoopPolicy`, and `digest: str`.

```python
canonical_binding(binding: AgentBinding) -> str   # sorted-key, compact JSON, digest field excluded
binding_digest(binding: AgentBinding) -> str      # sha256 of canonical_binding(binding)
binding_json(binding: AgentBinding) -> str        # sorted-key, compact JSON, digest field INCLUDED
binding_from_json(text: str) -> AgentBinding      # inverse of binding_json
```

`canonical_binding`/`binding_digest` follow the same self-referential-digest pattern as
`Harness.digest`: the digest is computed over every field except itself. `binding_json` is the
different, wire-facing form: it includes the already-computed `digest` field, because this is the
serialized identity a `LaunchSpecification` carries and an executor independently reverifies
(recomputing `binding_digest` over the decoded fields and comparing it against the carried `digest`
detects a tampered or substituted binding). `binding_from_json` reconstructs the frozen dataclass,
including its nested `LoopPolicy`, from that wire form.

## Host-built launch

```python
build_launch_specification(*, capability: str, stage: str, occurrence: int, role: str,
    integration: Literal["codex", "claude"], agent: str, project_root: str, request: str,
    prompt: str, prior_results: tuple[str, ...], workspace_receipt_json: str,
    workspace_digest: str, policy: NormalizedPolicy,
    native_configuration: NativeLaunchConfiguration, runtime_input_json: str | None = None,
    capability_configuration_json: str | None = None,
    invocation_id: str | None = None,
    agent_binding_json: str | None = None) -> LaunchSpecification
```

The returned frozen `LaunchSpecification` has exactly the parameters above as attributes plus
`digest: str`. JSON arguments are serialized objects, not paths. The workspace receipt must bind
`source_digest` to `workspace_digest` and contain the host role-path mapping. Typed Profile 9
launches supply runtime input, configuration and a fresh invocation ID together, use an empty
`prior_results` tuple and a context identity as the workspace digest. Input/configuration type and
version admission remains the host's obligation. A configuration/policy/integration mismatch or
unbound workspace receipt raises `PermissionPolicyError` before process execution.

A structured (typed) launch additionally requires `agent_binding_json`: the canonical JSON of one
resolved `AgentBinding` (`agent_model.binding_json`), including its own `digest` field -- unlike
`canonical_binding`, which excludes `digest` because it is that digest's own input. It must decode
to an object with exactly the `AgentBinding` field names (`dataclasses.fields(AgentBinding)`) and
use canonical serialization; a missing binding, wrong field set or non-canonical encoding raises
`PermissionPolicyError` before process execution. The decoded binding participates in the launch's
own digest, so a tampered or substituted binding changes the launch identity. A legacy untyped
launch (no `runtime_input_json`) carries no Agent binding. `agent_model.binding_from_json` is the
executor's inverse of `binding_json`, reconstructing the frozen `AgentBinding` (with its nested
`LoopPolicy`) from this wire form.

The host obtains these values in order: freeze context; compile its exact role/path policy; render
for the selected integration; build the launch; then call the executor. Consumers of the executor
may pass an already built launch and do not reconstruct its digest or grant. Bootstrap finalization
returns another launch: the original requested digest and finalized digest are intentionally distinct.

## Execution results and failure evidence

`CompletionGate(name: str, status: Literal["passed", "failed"], evidence: str)` has a unique nonempty
name and nonempty evidence. A `CapabilityCompletion` is a frozen record with:

```python
schema_version: int                       # 3 for typed Profile 9; legacy untyped launches use 1
capability: str
stage: str
occurrence: int
role: str
launch_digest: str                         # finalized launch
workspace_digest: str
runtime_bootstrap_digest: str
status: Literal["success", "failed"]
output: str                               # bounded audit summary, never a raw log channel
limitations: str
gates: tuple[CompletionGate, ...]          # nonempty
# Optional Python attributes, required by the typed completion wire envelope:
domain_output: dict[str, Any] | None = None
invocation_id: str | None = None
```

Success has `limitations == "none"` and only passed gates; failure has a nonempty limitation other
than `none` and a failed gate. A task gap is a valid bounded assessment, represented in typed
`domain_output`, rather than a native process failure. Review coverage uses its own
`no_findings|findings|incomplete` status. The executor validates the original wire schema even when
its native generation schema requires optional fields, adds scalar types or omits provider-unsupported
`uniqueItems`; duplicate arrays and invalid output remain rejected by host validation.

`EnforcementReceipt` is a frozen record containing `requested_launch_digest`, `launch_digest`,
`policy_digest`, `config_digest`, `integration`, `client_version`, `enforcement`, `exit_code: int`,
`status: Literal["success", "failed"]`, `runtime_bootstrap_digest`, `completion_schema_version: int`,
`completion_status: Literal["success", "failed"]`, `limitations: str = "none"`, and
`agent_binding_digest: str = ""` (last field; empty for a legacy untyped launch that carries no
Agent binding, otherwise the bound `AgentBinding.digest`). All unspecified field types in this list
are strings. Receipt identities bind the native configuration and exact requested/finalized launch;
an exit-zero subprocess without valid completion is still failure.

```python
CapabilityExecutionResult(output: str, receipt: EnforcementReceipt,
                         completion: CapabilityCompletion,
                         domain_output: dict[str, Any] | None = None)
CapabilityExecutionError(message: str, receipt: EnforcementReceipt | None = None,
                         outcome: Literal["failed", "cancelled",
                                          "limit_exhausted", "invalid_completion"] = "failed")
```

The executor returns `CapabilityExecutionResult` only for a successful native process and validated
successful completion. Its `output` equals `completion.output`; consume typed results from
`completion.domain_output`. The optional result-level `domain_output` is a compatibility slot and
is not populated by `AgentProcessExecutor`. `CapabilityExecutionError` is a `RuntimeError`; `receipt`
is available after a completed process fails exit/status/schema checks, and may be absent on
preflight/launch failure. Its `outcome` classifies why, for a host that must distinguish these
cases rather than treat every executor failure alike: `failed` (default) for a nonzero exit or a
launch/preflight failure; `cancelled` when the injected runner raised `KeyboardInterrupt` (the
subprocess is already terminated by the time this is raised); `limit_exhausted` when the runner
raised `subprocess.TimeoutExpired` -- the Agent's effective loop timeout was exceeded; and
`invalid_completion` when a zero-exit process returned an invalid or domain-reported-failed
completion. The default runner enforces the Agent's effective loop timeout; an injected runner
receives `timeout` and must raise `subprocess.TimeoutExpired` when it expires. No executor failure
silently retries with wider permissions or rolls back already authorized implementation edits. The
host stops the affected transition and preserves the candidate for repair. Raw subprocess
stdout/stderr remain host execution evidence, not downstream Spec-agent inputs or public review
findings.

## Declared architecture sources

Architecture source in this project is an inline `mermaid` fence in a registered Markdown
member. Its source path, kind (`mermaid`) and title are stated beside the fence; `accTitle` and
`accDescr` provide accessible text. Each Module's main diagram describes its principal entities
and directed relationships. The entire containing Markdown document is the authored source.

The source bytes already occur in `target_spec` or `shared_specs` and participate in document,
revision and context digests. They are never duplicated in `diagram_sources`. The retained
`diagram_sources` snapshot field is `[]` for this representation. Authors return changed fences
inside `documents`; the optional separate `diagrams` result is omitted or empty. Shared Markdown
changes require coordinated authoring from every explicitly registered owner. Non-author roles
cannot replace these sources. Rendered SVG/HTML is never a cognitive input or another authority.

New authoring and initialization use this Markdown representation. The registry's retained
`diagrams` array is empty. Previously registered external JSON sources require explicit migration
into registered Markdown before using this revised authoring/publication contract; the host must
not silently discard them or reinterpret their bytes. No external diagram source format is added
by this revision.
