# Distribution interface contracts

These precise specifications belong directly to the [Distribution Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term                                                | Meaning / definition                         |
| --------------------------------------------------- | -------------------------------------------- |
| [Pi integration](../module.md#terminology)          | Defined in Concorde Framework.               |
| [Worker](../module.md#terminology)                  | Defined in Concorde Framework.               |
| [Worker profile](../harness/module.md#terminology)  | Defined in Harness.                          |
| [Operation](../module.md#terminology)               | Defined in Concorde Framework.               |
| [Host](../module.md#terminology)                    | Defined in Concorde Framework.               |
| [Grant](../module.md#terminology)                   | Defined in Concorde Framework.               |
| [Installation](installation.md#terminology)         | Defined in Installing and updating Concorde. |
| [Installation receipt](installation.md#terminology) | Defined in Installing and updating Concorde. |

## Build

### Interface signatures {#build-interface-signatures}

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of build:

```text
render_model_instructions(project_root: Path, agent: str) -> BuildOutput
render_pi_session(project_root: Path, *, framework_prefix: str='') -> BuildOutput
render_langgraph(project_root: Path) -> BuildOutput
render_protocol_principles(project_root: Path) -> BuildOutput
render_protocol_kind(project_root: Path, kind: str) -> BuildOutput
render_protocol_schemas(project_root: Path) -> BuildOutput
build(project_root: str | Path, *, framework_prefix: str='') -> BuildResult
write_build(project_root: str | Path) -> BuildResult
check_build(project_root: str | Path) -> tuple[bool, tuple[str, ...]]
recompute_protocol_manifest(project_root: str | Path) -> dict
verify_fresh(project_root: str | Path) -> None
load_model_instructions(package_root: str | Path, name: str) -> ModelInstructions
```

Public functions of prompt_resolver:

```text
resolve_model_instructions(project_root: str | Path, relative_path: str) -> ResolvedPrompt
resolve_role_prompt(project_root: str | Path, relative_path: str) -> ResolvedPrompt
resolve_operation_guidance(project_root: str | Path, relative_path: str) -> ResolvedPrompt
find_unreachable_prompts(project_root: str | Path, roots: list[str] | tuple[str, ...]) -> tuple[str, ...]
check_reachability(project_root: str | Path, roots: list[str] | tuple[str, ...]) -> None
```

Public functions of package_validation:

```text
validate_package(root: Path) -> list[Finding]
```

`render_pi_session` embeds all public descriptions, resolved guidance and request schemas in one
Pi entry. `build` is pure and optionally renders an installed layout through `framework_prefix`;
`write_build` accepts only its own source root and writes the private layout, never an ambient
extension. There are no integration selectors, cross-root output arguments, Skill renderers or
publishing commands. Removed call shapes fail explicitly, without aliases or fallback.
The resolver (`resolve_model_instructions`, `resolve_role_prompt`, `resolve_operation_guidance`,
`find_unreachable_prompts`, `check_reachability`) expands `@include` directives, enforces
audience/layering rules, and detects unreachable or diamond-included sources; `resolve_model_instructions`
additionally rejects an Agent Spec that carries front matter. `package_validation` attributes its
findings to `module.distribution` and requires exactly one registered `concorde-operations` block
across all Module documents, equal to the single code inventory of Operations, including State,
USES, the public `EXTERNAL_NAME` as `public_name` (null for private Operations), and optional model
execution profiles; no parallel Agent inventory is required. The retired `skill` metadata field
is rejected rather than aliased. Guidance membership is checked independently and must match
each public external name exactly once. These metadata edits leave wire versions unchanged.

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

`ModelInstructions` is a frozen in-process record with exactly `name`, `description`,
`source_path`, `body`, `effects: EffectDeclaration` and `binding: WorkerBinding`, all required.
The string fields contain the external worker identity, description, authored role source path
and complete rendered instruction text. `load_model_instructions` verifies freshness before
resolving one worker and returns non-null effects and its complete current binding; a public
Operation name does not acquire worker instructions merely by appearing in the Pi catalog.
Effects have `reads` and `writes` string tuples, `network: bool` and
`credentials: "none"|"declared"`; these describe a ceiling that the host must narrow for a
concrete invocation, not automatically effective permissions.

The former `SkillPrompt` wrapper and its `kind="skill"` discriminator are retired, not aliases.
This is an explicit Python record/API change: new dataclass serialization has the six fields
above and no `kind`. A saved old wrapper is not an admitted instruction record and must be
reloaded from a fresh build, not reinterpreted by dropping or renaming its discriminator.
There is no instruction-wrapper deserialization API. The independently serialized `WorkerBinding`
retains all of its fields and digest meanings below; public request/result wire versions, Pi
catalog schema 1 and build-manifest schema 1 are unchanged. Changed source/build bytes still
invalidate bindings and dependent review evidence.

`WorkerBinding` has string fields `agent`, `spec_path`, `spec_digest`, `instructions_path`,
`instructions_digest`, `profile_digest`, `build_manifest_digest` and `digest`, plus
`timeout_seconds: int`. The profile digest covers the worker's task contract, workspace kind,
tools and timeout. Digest values identify exact admitted
bytes/configuration, using `sha256:` and 64 lowercase hex digits. The binding digest covers the
complete binding except its own digest field. Source locators remain provenance; they do not give
a caller permission to load additional project context.

Build and resolver failures stop the affected render/load and cannot be reinterpreted as an empty
successful output. `BuildError(ValueError)` carries its declared error code; include-resolution
errors use `PromptResolverError(ValueError)`. Filesystem errors can propagate. Repeated pure
renders with unchanged inputs preserve bytes; a write can fail after some generated outputs have
changed, so runtime freshness must be re-established before use. Rebuild from authored inputs to
repair projections, never edit generated output as a new source. Accepted bare, hyphenated and
`concorde-`-prefixed worker names resolve the same worker record and failure semantics;
unsupported asset identities require explicit repair.

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
`operations: tuple[str, ...]` inventory, and the string fields `pi_lock_sha256`
(the digest of `pi/package.json`, `pi/package-lock.json` and `pi/.npmrc`) and
`typebox_version` (the exact TypeBox version `pi/package.json` pins). Paths are explicit relative
locations; requirements identify the locked input and runtime digests identify the accepted
combination of the Python lock and the Pi worker lock. The current accepted Python requirement is
`>=3.11`, and installing the Pi worker extensions requires `npm` on the host.
Changing these pins is an explicit package revision, not an automatic upgrade during a task.

`runtime_python(venv)` returns the platform's Python path inside that environment; path
construction alone does not verify an installation. `plan_runtime(target, spec, receipt)` returns
string fields `path`, `role="runtime"`, `sha256` and `action`, with optional `reason`. Callers pass
the returned action to provisioning; a conflict is not an admissible provisioning action.

`provision_runtime` takes a trusted target, installed Framework root, loaded specification and
current reviewed action. Optional `bootstrap_python` chooses the host bootstrap interpreter that
creates the environment; omission uses the current interpreter. Operation verification never uses it:
each public Operation's `--runtime-check` runs with the managed runtime's own interpreter and must
report that runtime as its prefix. Success returns `path`, `python`, `python_version`,
`requirements`, `requirements_sha256`, `runtime_sha256`, `launcher`, `verified_operations` and a `pi`
object (`install_relative` = `share/concorde/pi`, `lock_sha256`, `typebox`).
The result records what was verified, not just requested. Accepted state has a schema-4,
owner-concorde marker binding its path, Concorde version, lock/runtime digests, observed Python
version, Pi worker lock digest and TypeBox version, and verified Operation inventory. The Pi
worker extensions are installed with `npm ci` from the package's own lock into `share/concorde/pi`
inside the runtime, where every terminal worker loads TypeBox; a changed Pi lock plans a
rebuild. Marker schema 4 replaces schema 3's `verified_skills` with `verified_operations`. Old markers
cannot attest current health; a receipt-owned runtime requires a verified rebuild, not a silent
field alias. Without an ownership receipt an old marker does not authorize deletion. The launcher
may still enter an owner-concorde environment for the installer's runtime checks; that locator
check is not schema-4 verification or permission to skip provisioning. The returned receipt runtime
object uses `verified_operations`; installation receipt schema 2 otherwise remains unchanged.
Pi catalog and build-manifest schema 1 remain unchanged because their existing fields retain their
meanings. Wire contracts, Profile, providers, credentials and runtime dependency pins are unchanged.

## Private session selection

`select_session(candidate: Path, *, mode: str, pi_entry: Path | None, runtime: Path) -> dict`
accepts `maintenance`, `test` and `task`. Maintenance requires null entry; test/task require exactly
`<candidate>/generated/session/pi/concorde-session.ts`. Runtime is exactly the absolute recorded
`<candidate>/scripts/run-operation.py`. All source/output paths and ancestors are regular/non-aliased;
new source links fail before the pure current render. All current build bytes must match, including
transitive Python implementations, all Pi source assets except installed node_modules/bytecode caches,
and runtime dependency lock inputs.

The closed schema-2 record has `schema_version`, `mode`, `candidate`, `fresh_context: true`,
`fork_context: false`, `discover_catalogs: false`, `inherit_catalogs: false`,
`task_delegation: false`, `build_digest`, `runtime`, `implementation`, `pi_entry`, `launch` and
`execution_evidence: null`. Runtime and implementation are `{path,digest}` records, the latter
identifying the authored session extension. Entry is null for maintenance, otherwise
`{path,digest,content,catalog:{digest,content}}`: content is the complete UTF-8 entry and the exact
embedded catalog JSON substring respectively, not a list of selected Operations. Digests use
`sha256:` over exact UTF-8 bytes. The manifest digest binds all current sources and outputs.
`launch` has `cwd` and `pi_args`: no session persistence, context files, Skills, prompt templates,
themes or discovered extensions, and only the explicit `-e` entry outside maintenance.
These flags describe host launch requirements; selection itself starts no process or model.

`save_selection(root, path, value)` writes only an exact absolute path under ignored
`.concorde/work/` using the atomic scratch writer. `load_selection(root, path)` strictly decodes
schema 2, recomputes selection from current sources and compares the entire record. Unknown fields,
schema 1, unsafe paths, changed provenance and legacy bodies fail closed. The CLI exposes
`--pi-entry`, `--runtime`, `--output` or the mutually exclusive read-only `--verify` path; `--skill`
is rejected, not an alias. A missing or failed selection never permits ambient/name-based fallback.
The caller owns freshness between verification and loading and must stop all writing before testing;
this is byte provenance under trusted candidate code, not a sandbox against a malicious code writer.
The Python environment and Pi SDK remain host infrastructure; dependency locks are bound, but
selection does not attest every installed third-party dependency byte or provider behavior.

The rendered shim supplies its exact entry filename as the third `concordeSession` argument.
A private source entry refuses absent `CONCORDE_SESSION_SELECTION`; consumer installed catalogs
remain independent of private selection. The extension verifies through the candidate CLI with a
30-second verification deadline before registration and each tool call. Verification failure
registers no tool at startup or fails the current call; the outer host treats a load error as a
blocked launch. A changed saved identity cannot refresh an existing tester in place.
