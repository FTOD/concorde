# Distribution interface contracts

These precise specifications belong directly to the [Distribution Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker profile](../harness/module.md#terminology) | Defined in Harness. |
| [Operation](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |
| [Installation](installation.md#terminology) | Defined in Installing and updating Concorde. |
| [Installation receipt](installation.md#terminology) | Defined in Installing and updating Concorde. |

## Build

### Interface signatures {#build-interface-signatures}

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of build:

```text
render_model_instructions(project_root: Path, agent: str) -> BuildOutput
render_skill(project_root: Path, name: str, integration: str, *, framework_prefix: str='') -> BuildOutput
render_langgraph(project_root: Path) -> BuildOutput
render_protocol_principles(project_root: Path) -> BuildOutput
render_protocol_kind(project_root: Path, kind: str) -> BuildOutput
render_protocol_schemas(project_root: Path) -> BuildOutput
build(project_root: str | Path, integration: str='all', *, framework_prefix: str='') -> BuildResult
write_build(project_root: str | Path, integration: str='all', *, framework_prefix: str='', integration_root: str | Path | None=None) -> BuildResult
check_build(project_root: str | Path, integration: str='all') -> tuple[bool, tuple[str, ...]]
recompute_protocol_manifest(project_root: str | Path) -> dict
verify_fresh(project_root: str | Path) -> None
load_model_instructions(package_root: str | Path, name: str) -> SkillPrompt
```

Public functions of prompt_resolver:

```text
resolve_model_instructions(project_root: str | Path, relative_path: str) -> ResolvedPrompt
resolve_role_prompt(project_root: str | Path, relative_path: str) -> ResolvedPrompt
resolve_skill_source(project_root: str | Path, relative_path: str) -> ResolvedPrompt
find_unreachable_prompts(project_root: str | Path, roots: list[str] | tuple[str, ...]) -> tuple[str, ...]
check_reachability(project_root: str | Path, roots: list[str] | tuple[str, ...]) -> None
```

Public functions of package_validation:

```text
validate_package(root: Path) -> list[Finding]
```

The resolver (`resolve_model_instructions`, `resolve_role_prompt`, `resolve_skill_source`,
`find_unreachable_prompts`, `check_reachability`) expands `@include` directives, enforces
audience/layering rules, and detects unreachable or diamond-included sources; `resolve_model_instructions`
additionally rejects an Agent Spec that carries front matter. `package_validation` attributes its
findings to `module.distribution` and requires exactly one registered `concorde-operations` block
across all Module documents, equal to the single code inventory of Operations, including State,
USES and optional model execution profiles; no parallel Agent inventory is required.

Failures return structured findings or the declared exception; callers must stop the affected
transition. Repeating an unchanged read is side-effect free. Mutations require current
preconditions and explicit caller-owned paths. Local contract facts above remain authoritative
without reading the parent or collaborating Specs.

### Returned records and compatibility {#build-returned-records-and-compatibility}

`BuildOutput` is a frozen record `{path: str, content: bytes, sources: tuple[str, ...]}`: path is
an exact output location, content is the complete rendered byte sequence, and sources names the
explicit authored inputs. `BuildResult` contains `outputs: tuple[BuildOutput, ...]` and
`manifest: bytes`, the serialized source/output identity manifest. An in-memory render does not
imply those outputs have been written. `ResolvedPrompt` contains expanded `body: str` and its
explicit `sources: tuple[str, ...]`; it carries no execution grant.

`SkillPrompt` retains the compatibility record name and fields `name`, `description`,
`source_path`, `kind="skill"`, `body`, nullable `effects`, and nullable `binding`. String fields
contain identity, provenance and complete instruction text. `load_model_instructions` supplies non-null effects
and a current Agent binding for a successfully admitted Agent. Effects have `reads` and `writes`
string tuples, `network: bool` and `credentials: "none"|"declared"`; these describe a ceiling that
the host must narrow for a concrete invocation, not automatically effective permissions.

`WorkerBinding` has string fields `agent`, `spec_path`, `spec_digest`, `instructions_path`,
`instructions_digest`, `profile_digest`, `build_manifest_digest` and `digest`, plus
`timeout_seconds: int`. The profile digest covers the worker's task contract, workspace kind,
tools, timeout and each declared child definition's bytes. Digest values identify exact admitted
bytes/configuration, using `sha256:` and 64 lowercase hex digits. The binding digest covers the
complete binding except its own digest field. Source locators remain provenance; they do not give
a caller permission to load additional project context.

Build and resolver failures stop the affected render/load and cannot be reinterpreted as an empty
successful output. `BuildError(ValueError)` carries its declared error code; include-resolution
errors use `PromptResolverError(ValueError)`. Filesystem errors can propagate. Repeated pure
renders with unchanged inputs preserve bytes; a write can fail after some generated outputs have
changed, so runtime freshness must be re-established before use. Rebuild from authored inputs to
repair projections, never edit generated output as a new source. Public aliases preserve the same
inputs, records and failure semantics; unsupported integration or asset identities require explicit
repair.

## Managed runtime

### Interface signatures {#runtime-interface-signatures}

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of managed_runtime:

```text
load_runtime_spec(package_root: Path, manifest: Mapping[str, Any]) -> ManagedRuntimeSpec
runtime_python(venv: Path) -> Path
plan_runtime(target: Path, spec: ManagedRuntimeSpec, receipt: Mapping[str, Any]) -> dict[str, str]
provision_runtime(target: Path, framework: Path, spec: ManagedRuntimeSpec, action: Mapping[str, str], *, bootstrap_python: str | None=None) -> dict[str, Any]
```

### Values and completion {#runtime-values-and-completion}

`ManagedRuntimeSpec` is a frozen record with string fields `venv`, `requirements`, `launcher`,
`python`, `requirements_sha256`, `runtime_sha256`, `langgraph_version` and `concorde_version`, a
`skills: tuple[str, ...]` inventory, `viewer: ViewerSpec`, and the string fields `pi_lock_sha256`
(the digest of `pi/package.json`, `pi/package-lock.json` and `pi/.npmrc`) and
`pi_subagents_version` (the exact pi-subagents version `pi/package.json` pins). Paths are explicit relative
locations; requirements identify the locked input and runtime digests identify the accepted
combination, including the Pi worker lock. `ViewerSpec` has string fields `provider`, `version`, `package`, `asset_url`,
`asset_sha256`, `node`, `npm_package`, `npm_lock`, `lock_sha256`, `integrity`, `install_relative`,
`entrypoint`, `launcher`, positive integer `asset_bytes`, and ordered `graph_paths: tuple[str, ...]`.
The package input binds an immutable official asset, size/hash and npm integrity; it does not
accept an arbitrary latest release. Current accepted requirements are Python >=3.11 and Node >=18.
Changing these pins is an explicit package revision, not an automatic upgrade during a task.

`runtime_python(venv)` returns the platform's Python path inside that environment; path
construction alone does not verify an installation. `plan_runtime(target, spec, receipt)` returns
string fields `path`, `role="runtime"`, `sha256` and `action`, with optional `reason`. Callers pass
the returned action to provisioning; a conflict is not an admissible provisioning action.

`provision_runtime` takes a trusted target, installed Framework root, loaded specification and
current reviewed action. Optional `bootstrap_python` chooses the host bootstrap interpreter;
omission uses the current interpreter. Success returns `path`, `python`, `python_version`,
`requirements`, `requirements_sha256`, `runtime_sha256`, `launcher`, `verified_skills`, a `pi`
object (`install_relative` = `share/concorde/pi`, `lock_sha256`, `pi_subagents`) and a
`viewer` object. That object carries provider/version/package, asset_url/asset_sha256/asset_bytes,
integrity/lock_sha256, node/node_version/npm_version, install_relative/entrypoint/launcher and
ordered graph_paths. All are strings except asset_bytes (integer) and the two string-array fields.
The result records what was verified, not just requested. Accepted state has a schema-2,
owner-concorde marker binding its path, Concorde version, lock/runtime digests, observed tool
versions, viewer version/entrypoint, Pi worker lock digest and pi-subagents version, and verified
Skill inventory. The Pi worker extensions are installed with `npm ci` from the package's own lock
into `share/concorde/pi` inside the runtime, where a worker with children loads pi-subagents; a
changed Pi lock plans a rebuild.
