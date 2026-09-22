# Operation runtime value and collaborator contracts

This registered local companion document defines the exact public value records used by the
operation host, permission compiler and worker executor. These are Python in-process contracts;
they do not give a worker permission to construct its own grant. Strings called digests are
canonical `sha256:` plus 64 lower-case hex digits. Paths in policies are project-relative POSIX
paths without aliases or symlinks.

## Terminology

| Term                                             | Meaning / definition                           |
| ------------------------------------------------ | ---------------------------------------------- |
| [Operation](../module.md#terminology)            | Defined in Concorde Framework.                 |
| [Host](../module.md#terminology)                 | Defined in Concorde Framework.                 |
| [Worker](../module.md#terminology)               | Defined in Concorde Framework.                 |
| [Worker profile](module.md#terminology)          | Defined in Harness.                            |
| [Grant](../module.md#terminology)                | Defined in Concorde Framework.                 |
| [Snapshot](../module.md#terminology)             | Defined in Concorde Framework.                 |
| [Capsule](module.md#terminology)                 | Defined in Harness.                            |
| [Spec context](context.md#terminology)           | Defined in What information a worker receives. |
| [Implementation context](context.md#terminology) | Defined in What information a worker receives. |
| [Issue](../module.md#terminology)                | Defined in Concorde Framework.                 |
| [Entity](../module.md#terminology)               | Defined in Concorde Framework.                 |
| [Module](../module.md#terminology)               | Defined in Concorde Framework.                 |
| [Reference](../spec/registry.md#terminology)     | Defined in Registry.                           |

### Policy construction

```python
EffectDeclaration(reads: tuple[str, ...] = (), writes: tuple[str, ...] = (),
                  network: bool = False, credentials: Literal["none", "declared"] = "none")
PolicyBinding(operation: str, stage: str, occurrence: int, role: str, agent: str,
              read_roles: tuple[str, ...] | None = None,
              write_roles: tuple[str, ...] | None = None,
              network: bool | None = None,
              credentials: Literal["none", "declared"] | None = None)
compile_policy(effects: EffectDeclaration, binding: PolicyBinding,
               role_paths: Mapping[str, tuple[str, ...]], *, deny_paths: tuple[str, ...] = (),
               outer_sandbox_required: bool = False) -> NormalizedPolicy
```

Effects declare the contract's maximum authority. A binding selects a subset; `None` retains that
field's declared effect. Every selected role except `references` must have a host-provided concrete
path tuple. Writes must also be readable. Unknown or duplicate roles, unsafe paths and widened reads,
writes, network or credentials raise `PermissionPolicyError(ValueError)`. Compile does not launch a
process or write project files. The default-deny result additionally denies common credential paths.
Explicit path grants never turn a task string, file link, registry relationship or returned
ArtifactRef into authority.

`NormalizedPolicy` is a frozen record with these attributes:

| Attribute                           | Type and meaning                                                      |
| ----------------------------------- | --------------------------------------------------------------------- |
| operation, stage, role, agent       | str; the exact bound operation and worker identities                  |
| occurrence                          | int; this stage occurrence                                            |
| read_paths, write_paths, deny_paths | tuple[str, ...]; sorted, deduplicated concrete grants/denies          |
| default_deny                        | bool; compiler results are true                                       |
| network_enabled                     | bool; cannot exceed effects                                           |
| credentials                         | Literal["none", "declared"]; cannot exceed effects                    |
| outer_sandbox_required              | bool; retained for a future host-attested sandbox, always false today |
| digest                              | str; identity of this binding and effective policy                    |

Spec-only workers receive only their context role. The programmer additionally receives
`implementation` with writes. Code review and investigation receive the current target's enumerated
implementation files for reading, with an empty write-role tuple.

### Model execution profile and binding

```python
Contract(phase: str, context: str, result: str, effects: EffectDeclaration,
         stage_inputs: tuple[str, ...] = (), required_inputs: tuple[str, ...] = (),
         output_fields: tuple[str, ...] = (), outcomes: tuple[str, ...] = ())
WorkerProfile(name: str, spec: str, workspace: Literal["capsule", "project"], contract: Contract,
      tools: tuple[str, ...], timeout_seconds: int = 1800)
WorkerBinding(agent: str, spec_path: str, spec_digest: str, instructions_path: str,
             instructions_digest: str, profile_digest: str, build_manifest_digest: str,
             timeout_seconds: int, digest: str)
```

All are frozen records. `name` is the catalog key (for example `code_reviewer`); its external name is
`concorde-code-reviewer`. `validate_worker_profile(agent)` requires `agents/<name>/spec.md`, a known workspace,
a context type paired with its result type, required inputs among admitted inputs, known result
fields, writes that are also reads, no network or credential effects, implementation reads only in a
project workspace, distinct known tools
including `read`, `edit` or `write` only with a write effect and a positive integer timeout;
it raises `BuildError/invalid_agent_binding`. Child catalogs and delegation tools are retired.

`worker_profile(name)` accepts the bare, hyphenated or external name and raises
`BuildError/unknown_agent`. `resolve_worker(package_root, name)` verifies build freshness, validates
the profile, requires the Spec to be recorded in the
build manifest, reads the rendered instructions and returns the binding. `profile_digest` covers the
complete terminal profile. `canonical_binding`/`binding_digest` hash every
field except `digest`; `binding_json` is the wire form including it, and `binding_from_json` is its
inverse.

The contract checks are independent of prompt text:

```python
validate_worker_input(agent: WorkerProfile, value: dict, *, phase: str) -> None
validate_worker_artifacts(agent: WorkerProfile, inputs, *, require_all: bool = True) -> None
validate_worker_policy(agent: WorkerProfile, value: dict, policy: NormalizedPolicy, receipt: dict) -> None
validate_worker_output(agent: WorkerProfile, value: dict) -> None  # raises ContractError(message, code)
```

`validate_worker_input` checks the typed context, phase, admitted artifacts, the absence of
implementation contents for a worker without implementation reads, review-mode binding and the
absence of implementation patches in a Spec review. `validate_worker_policy` requires one context index
granted with exactly its listed files, implementation grants inside the selected Module (and, for
read-only workers, inside the frozen files), reference grants inside the snapshot's references, and
a policy no wider than the contract recompiles. `validate_worker_output` checks the result type,
outcome and permitted populated fields; disallowed authored fields use code `permission_denied`,
other violations `invalid_completion`.

### Worker invocation and outcome

```python
WorkerSelection(model: str | None = None, thinking: str | None = None, timeout_seconds: int | None = None)
worker_selection(configuration: dict, agent: str) -> WorkerSelection
build_worker_invocation(*, operation: str, stage: str, agent: str, invocation_id: str, workspace: str,
    context_json: str, receipt_json: str, policy: NormalizedPolicy, binding_json: str,
    instructions: str, selection: WorkerSelection) -> WorkerInvocation
worker_instructions(rendered: str, protocol: list[tuple[str, bytes]]) -> str
WorkerExecutor(package_root: Path = <package root>, runtime=None)
WorkerExecutor.__call__(invocation: WorkerInvocation, *, checks=None, report_issue=None) -> WorkerOutcome
WorkerOutcome(value: dict, usage: ExecutionUsage, invocation_digest: str, binding_digest: str)
ExecutionUsage(model, thinking, input_tokens, cached_input_tokens, output_tokens, total_tokens,
               cost_usd, turns, wall_seconds, prompt_bytes, context_bytes)
OperationExecutionError(message: str, outcome: Literal["failed", "cancelled", "limit_exhausted",
                         "invalid_completion"] = "failed", code: str | None = None,
                         usage: ExecutionUsage | None = None)
```

`WorkerInvocation` is a frozen record with exactly the builder's fields plus `digest` and a
`context_id` accessor. The builder requires the policy's operation, stage, role and agent to equal
the invocation's and the worker's external name, canonical context and receipt JSON, a receipt naming
its `source_digest` and `role_paths`, a host-issued identity and an absolute workspace, and raises
`OperationExecutionError` otherwise. Its digest covers every identity, the typed context and
receipt, the policy digest, the binding, the instructions digest and every selection.

`worker_instructions` joins the rendered worker instructions with each Protocol file the context
lists, in order. The executor refuses to launch unless the carried binding matches its own digest and
equals the current build's resolution, each listed Protocol file in the workspace has its indexed
digest, the instructions equal that composition, the context's own instructions equal the rendered
file, and the contract input and policy checks pass; network and credential grants are always
refused. It then launches the worker through the Pi worker runtime with the profile's tools plus
`submit_result`, plus `report_issue` when its trusted reporting
callback is supplied, the policy's grants (plus the workspace root for a
capsule), the resolved selection and a timeout of
the selection's value or the binding's, and the profile-narrowed submission schema defined in
[Input and result](execution-reference.md#execution-input-and-result) as the result parameters.
The submitted value is still wrapped as the unchanged shared result type and independently checked
against the contract. `runtime` is a trusted test seam, never task input. The optional `report_issue` service
is a host-bound callable with a `schema` property; it grants no file writes and its durable reports
are independent of accepting the final result. Its protocol is defined in
[worker execution](execution-reference.md#execution-pi-worker-runtime).

`OperationExecutionError.outcome` distinguishes `failed` (a refused launch, a process failure or a
protocol break), `cancelled`, `limit_exhausted` (the timeout) and `invalid_completion` (no, several or
an invalid submitted result); `code` preserves a contract rejection class. None of them retries.
`ExecutionUsage` is diagnostic evidence about cost: a figure Pi did not report is `None`, and usage
gates nothing.

## Design

### Relationships diagrams

A Module's architecture diagram is an inline `mermaid` flowchart fence inside its `module.md`
Relationships subsection, or another registered document, with `accTitle` and `accDescr` accessible
text beside it. Its node labels form a nonempty subset of the Module's declared entity titles and every edge
carries a relationship label. Each Module's main diagram describes its principal entities and
directed relationships. The entire containing Markdown document is the diagram's only authored
source; there is no separate diagram source record or field.

The fence's bytes already occur in `documents` as ordinary content of that
document and participate in its document, revision and context digests. A changed fence is a
changed document like any other prose edit. Direct authorized edits preserve the paired model and
sole ownership, with fresh compatibility checks for affected consumers. Bounded workers cannot
replace these sources. Rendered SVG/HTML is never a cognitive input or another
authority.

A prior revision carried diagrams as external JSON sources referenced by a registry `diagrams`
declaration. That representation and registry field are retired: every current diagram is inline
Markdown, and Context(M) is the one-level union of owned and explicitly referenced documents.

## Direct Host runtime carrier

`InvocationRuntime(context: OperationRuntimeContext)` is a frozen, dependency-free carrier for
calling a registered Host tool through its existing `run(state, runtime)` interface. It carries
the same trusted Host and configuration outside caller-writable State, without importing LangGraph.
Explicit Graph adapters still receive LangGraph Runtime objects; both paths validate the same typed
request and preserve the same result envelope. This carrier does not schedule models or grant
additional effects.
