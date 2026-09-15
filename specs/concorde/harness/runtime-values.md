# Agent runtime value and collaborator contracts

This registered local companion document defines the exact public value records used by the
capability host, permission compiler and worker executor. These are Python in-process contracts;
they do not give a worker permission to construct its own grant. Strings called digests are
canonical `sha256:` plus 64 lower-case hex digits. Paths in policies are project-relative POSIX
paths without aliases or symlinks.

### Policy construction

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

Effects declare the contract's maximum authority. A binding selects a subset; `None` retains that
field's declared effect. Every selected role except `references` must have a host-provided concrete
path tuple. Writes must also be readable. Unknown or duplicate roles, unsafe paths and widened reads,
writes, network or credentials raise `PermissionPolicyError(ValueError)`. Compile does not launch a
process or write project files. The default-deny result additionally denies common credential paths.
Explicit path grants never turn a task string, file link, registry relationship or returned
ArtifactRef into authority.

`NormalizedPolicy` is a frozen record with these attributes:

| Attribute | Type and meaning |
| --- | --- |
| capability, stage, role, agent | str; the exact bound capability and worker identities |
| occurrence | int; this stage occurrence |
| read_paths, write_paths, deny_paths | tuple[str, ...]; sorted, deduplicated concrete grants/denies |
| default_deny | bool; compiler results are true |
| network_enabled | bool; cannot exceed effects |
| credentials | Literal["none", "declared"]; cannot exceed effects |
| outer_sandbox_required | bool; retained for a future host-attested sandbox, always false today |
| digest | str; identity of this binding and effective policy |

Spec-only workers receive only their context role. The programmer additionally receives
`implementation` with writes. Code review and investigation receive the current target's enumerated
implementation files for reading, with an empty write-role tuple.

### Agent definition and binding

```python
Contract(phase: str, context: str, result: str, effects: EffectDeclaration, action: str | None = None,
         stage_inputs: tuple[str, ...] = (), required_inputs: tuple[str, ...] = (),
         output_fields: tuple[str, ...] = (), outcomes: tuple[str, ...] = ())
Child(name: str, definition: str)
Agent(name: str, spec: str, workspace: Literal["capsule", "project"], contract: Contract,
      tools: tuple[str, ...], children: tuple[Child, ...] = (), timeout_seconds: int = 1800)
AgentBinding(agent: str, spec_path: str, spec_digest: str, instructions_path: str,
             instructions_digest: str, profile_digest: str, build_manifest_digest: str,
             timeout_seconds: int, digest: str)
```

All are frozen records. `name` is the catalog key (for example `code_reviewer`); its external name is
`concorde-code-reviewer`. `validate_agent(agent)` requires `agents/<name>/spec.md`, a known workspace,
a context type paired with its result type, required inputs among admitted inputs, known result
fields, writes that are also reads, no network or credential effects, implementation reads only in a
project workspace, discovery-context reads exactly for discovery contexts, distinct known tools
including `read`, `edit` or `write` only with a write effect, uniquely named children at
`agents/<name>/children/<child>.md` and a positive integer timeout; it raises
`BuildError/invalid_agent_binding`. `child_definitions(package_root, agent)` parses each child's
frontmatter and returns `ChildDefinition(name, description, tools, text)` records, rejecting a
missing file, a wrong name, missing description or prompt, tools outside `read`, `grep`, `find`,
`ls`, `bash` and `run_checks`, `run_checks` for a worker without a project workspace, other prompt
settings than replace with no inherited project context, global context or skills, and any `model`
or `thinking` key.

`agent_definition(name)` accepts the bare, hyphenated or external name and raises
`BuildError/unknown_agent`. `resolve_agent(package_root, name)` verifies build freshness, validates
the profile and its children, requires the Spec and every child definition to be recorded in the
build manifest, reads the rendered instructions and returns the binding. `profile_digest` covers the
complete profile and each child definition's bytes. `canonical_binding`/`binding_digest` hash every
field except `digest`; `binding_json` is the wire form including it, and `binding_from_json` is its
inverse.

The contract checks are independent of prompt text:

```python
validate_agent_input(agent: Agent, value: dict, *, phase: str) -> None
validate_agent_artifacts(agent: Agent, inputs, *, require_all: bool = True) -> None
validate_agent_policy(agent: Agent, value: dict, policy: NormalizedPolicy, receipt: dict) -> None
validate_agent_output(agent: Agent, value: dict) -> None          # raises ContractError(message, code)
```

`validate_agent_input` checks the typed context, phase, action, admitted artifacts, the absence of
implementation contents for a worker without implementation reads, review-mode binding and the
absence of implementation patches in a Spec review. `validate_agent_policy` requires one context index
granted with exactly its listed files, implementation grants inside the selected Module (and, for
read-only workers, inside the frozen files), reference grants inside the snapshot's references, and
a policy no wider than the contract recompiles. `validate_agent_output` checks the result type,
outcome and permitted populated fields; disallowed authored fields use code `permission_denied`,
other violations `invalid_completion`.

### Worker invocation and outcome

```python
WorkerSelection(model: str | None = None, thinking: str | None = None, timeout_seconds: int | None = None)
worker_selection(configuration: dict, agent: str, child: str | None = None) -> WorkerSelection
build_worker_invocation(*, capability: str, stage: str, agent: str, invocation_id: str, workspace: str,
    context_json: str, receipt_json: str, policy: NormalizedPolicy, binding_json: str,
    instructions: str, selection: WorkerSelection,
    child_selections: tuple[tuple[str, WorkerSelection], ...] = ()) -> WorkerInvocation
worker_instructions(rendered: str, protocol: list[tuple[str, bytes]]) -> str
WorkerExecutor(package_root: Path = <package root>, runtime=None)
WorkerExecutor.__call__(invocation: WorkerInvocation, *, checks=None) -> WorkerOutcome
WorkerOutcome(value: dict, usage: ExecutionUsage, invocation_digest: str, binding_digest: str)
ExecutionUsage(model, thinking, input_tokens, cached_input_tokens, output_tokens, total_tokens,
               cost_usd, turns, wall_seconds, prompt_bytes, context_bytes)
CapabilityExecutionError(message: str, outcome: Literal["failed", "cancelled", "limit_exhausted",
                         "invalid_completion"] = "failed", code: str | None = None,
                         usage: ExecutionUsage | None = None)
```

`WorkerInvocation` is a frozen record with exactly the builder's fields plus `digest` and a
`context_id` accessor. The builder requires the policy's capability, stage, role and agent to equal
the invocation's and the worker's external name, canonical context and receipt JSON, a receipt naming
its `source_digest` and `role_paths`, a host-issued identity and an absolute workspace, and raises
`CapabilityExecutionError` otherwise. Its digest covers every identity, the typed context and
receipt, the policy digest, the binding, the instructions digest and every selection.

`worker_instructions` joins the rendered worker instructions with each Protocol file the context
lists, in order. The executor refuses to launch unless the carried binding matches its own digest and
equals the current build's resolution, each listed Protocol file in the workspace has its indexed
digest, the instructions equal that composition, the context's own instructions equal the rendered
file, and the contract input and policy checks pass; network and credential grants are always
refused. It then launches the worker through the Pi worker runtime with the profile's tools plus
`submit_result` (and `subagent` with children), the policy's grants (plus the workspace root for a
capsule), the child definitions with their selected models, the resolved selection and a timeout of
the selection's value or the binding's, and the self-contained JSON schema of the contract's result
type as the result parameters. The submitted value is wrapped as that type and checked against the
contract. `runtime` is a trusted test seam, never task input.

`CapabilityExecutionError.outcome` distinguishes `failed` (a refused launch, a process failure or a
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
changed document like any other prose edit, so authors return it inside `documents`. Shared
Markdown changes require one proposal from the sole owner and compatibility checks for every affected context consumer. Non-author
roles cannot replace these sources. Rendered SVG/HTML is never a cognitive input or another
authority.

A prior revision carried diagrams as external JSON sources referenced by a registry `diagrams`
declaration. That representation and registry field are retired: every current diagram is inline
Markdown, and Context(M) is the one-level union of owned and explicitly referenced documents.
