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
`find_unreachable_prompts`, `check_reachability`) expands whole-line `@path.md` references, enforces
audience/layering rules, and detects unreachable or diamond-included sources; `resolve_model_instructions`
additionally rejects an Agent Spec that carries front matter. `package_validation` attributes its
findings to `module.distribution` and requires exactly one registered `concorde-operations` block
across all Module documents, equal to the typed code inventory of capabilities and canonical Agents, including kind, nullable State,
USES, the public `EXTERNAL_NAME` as `public_name` (null for private Agents), and profile. Agents have
no Python State/run aliases; no separate `concorde.agents` metadata extension is required. The retired `skill` metadata field
is rejected rather than aliased. Guidance membership is checked independently and must match
each public external name exactly once. These metadata edits leave wire versions unchanged.

Failures return structured findings or the declared exception; callers must stop the affected
transition. Repeating an unchanged read is side-effect free. Mutations require current
preconditions and explicit caller-owned paths. Local contract facts above remain authoritative
without reading the parent or collaborating Specs.

### Prompt reference grammar {#prompt-reference-grammar}

A reference occupies one complete line beginning in column one: `@` immediately followed by
an unquoted project-root-relative Markdown path, optionally followed by space/tab-separated
`key=value` bindings. For example:

```text
@prompts/workflow-host/gap-reporting.md
@prompts/workflow-host/invoke-operation-opener.md ACTION=validate
@prompts/workflow-host/invoke-operation-opener.md ACTION="review the selected Spec"
```

The spelling resembles Claude imports, not a claim of Claude semantic compatibility. There is
no inline import, home/absolute path expansion, implicit context expansion or search path.
Targets resolve from the supplied project root, never from the including file's directory.

Recognition is deliberately lexical: after column-one `@`, the first token has no whitespace,
`@`, backtick, quote, parenthesis or angle bracket, and either ends in `.md` or contains `/` or
backslash. A path-shaped token with a non-`.md` suffix is an invalid target, not literal output.
Targets must use canonical relative POSIX paths: no empty, dot or traversal components, home
prefix, colon, backslash, control characters or symlink components. Missing/non-file targets and
invalid paths fail with `CONCORDE-PROMPT-MISSING-001`. A bare `@`, mentions, email addresses,
decorators, inline references and indented lines remain literal Markdown. Backticks or indentation
can therefore present a literal example. As before, a column-one directive inside a code fence
is still processed; resolution is line-based, not a Markdown parser.

Bindings retain POSIX shell-style tokenization without comments; single/double quoted values may
contain spaces. Keys match `[A-Za-z_][A-Za-z0-9_]*` and cannot repeat. Malformed quoting, a token
without `=`, invalid/duplicate keys or an unbound variable fail with
`CONCORDE-PROMPT-UNRESOLVED-001`. Per-inclusion substitution precedes recursive resolution;
`OPERATION`, `SCRIPT` and `FRAMEWORK` remain reserved for the build's later substitution.

The retired column-one `@include` followed by whitespace or end of line fails explicitly with
`CONCORDE-PROMPT-UNRESOLVED-001`, including in nested sources; it is never an alias or silently
rendered instruction text. Inline/indented mentions of that spelling remain ordinary text.

Recursion preserves exact source provenance and the existing audience/layer boundaries: workers
cannot include ambient text or vice versa, shared text is allowed to either, Operation guidance
and project Specs cannot be included, and worker instruction Specs include only `prompts/` files.
Protocol adapters/chapters stay isolated from other prompts. Cycles fail with
`CONCORDE-PROMPT-CYCLE-001`; reaching the same file twice within one root fails with
`CONCORDE-PROMPT-DIAMOND-001`, including with different bindings. Audience, scope and Protocol
violations retain their existing rule IDs. No failing resolution returns a partial successful body.
Changing directive spelling changes source digests, not the intended expanded instruction bytes.

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
catalog schema 2 includes executable kind, while build-manifest schema 1 is unchanged. Changed source/build bytes still
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
The Pi catalog is schema 2 with explicit capability kind; the build manifest remains schema 1. Wire contracts, Profile, providers, credentials and runtime dependency pins are unchanged.

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

The native pi-subagents detached child may transport that same explicit saved selection via
`extensionBindings: {"concorde/1":{"selection":"<absolute path>"}}`. Its package-owned runner
supplies PI_SUBAGENT_EXTENSION_BINDINGS; Concorde reads only that closed namespace and never
mutates process environment. Direct and bound paths must agree when both occur. The launcher
subprocess receives the selected path through its own environment. This is an additional transport
for the unchanged schema-2 provenance record, not a fallback or new authority. Native testing uses
async true and fresh context; unsupported/missing binding delivery fails source entry loading.
Role-owned observation/check extensions are separately explicit and bound by current build sources.

The rendered shim supplies its exact entry filename as the third `concordeSession` argument.
A private source entry refuses absent `CONCORDE_SESSION_SELECTION`; consumer installed catalogs
remain independent of private selection. The extension verifies through the candidate CLI with a
30-second verification deadline before registration and each tool call. Verification failure
registers no tool at startup or fails the current call; the outer host treats a load error as a
blocked launch. A changed saved identity cannot refresh an existing tester in place.

## Full local installation service {#local-installation-service}

`concorde.distribution.installation` is the supported installer implementation, shared by the
public script and host bootstrap. The deployed package includes that implementation and the thin
`scripts/install-concorde.py` bootstrap, whose default package root is its own package, not a
name discovered globally. A source checkout is validated against its complete source build and
package contracts. An installed provider has no consumer copy of Concorde's source-project Specs;
it is instead checked against the complete receipt-owned Framework/Pi deployment and its pure
installed-layout render. No provider lookup searches primary, global packages or other worktrees.

```text
load_package(root: Path) -> Package
package_identity(package: Package) -> dict[str, str]
installation_plan(target: Path, package: Package, *, remove_protocol_guidance=False,
                  preserve_project=False) -> (actions, desired, prior_receipt)
apply_plan(target: Path, package: Package, actions, desired, *,
           remove_protocol_guidance=False, preserve_project=False) -> "installed"|"unchanged"
admit_package(root: Path) -> PackageSource
verify_installation(target: Path, *, expected: PackageSource | None=None) -> LocalInstallation
ensure_installation(target: Path, source: PackageSource, *, bootstrap=False,
                    preserve_project=True) -> LocalInstallation
installation_lock(target: Path) -> context manager
verify_runtime(target: Path, framework: Path, spec: ManagedRuntimeSpec, receipt) -> dict
```

The first four functions belong to `installation`; the next four belong to `local_installation`,
and `verify_runtime` belongs to `managed_runtime`. `Package` has `root: Path` and `manifest`.
The host explicitly supplies the package that admitted the invoking request to `admit_package`,
never a task-supplied alternative. The frozen `PackageSource` has `root: Path`, `version`, `digest`
and `build_digest`. Its `identity` property returns the three string fields. `digest` hashes the
canonical sorted, compact JSON mapping of every desired deployable output path to its role and
exact-byte SHA-256, including the bootstrap and dependency locks. `build_digest` hashes the pure
installed-layout build manifest. Both use `sha256:` plus 64 lowercase hex digits. Source and
installed providers of the same bytes have the same identity, independent of their absolute roots;
a version label alone never establishes equality. Re-admission after source edits is explicit.

`LocalInstallation` is a frozen in-process observation with Path fields `target`, `framework`,
`pi_entry`, `python`, `launcher`, `receipt`; the local `package: PackageSource`; string fields
`provider_root`, `receipt_digest`, `runtime_digest`, `status="verified"`; and boolean
`protocol_matches_package`. `provider_root` is historical installation provenance, never an
execution fallback or a path required to remain available. The Pi entry is the target's
`.pi/extensions/concorde-session.ts` and contains the embedded catalog. Framework, launcher,
managed interpreter, TypeBox and receipt are all target-local. System toolchains may be shared;
Framework and virtual environments are neither shared nor relocated from another worktree.

Verification reads every owned output and compares the complete Framework/extension inventory with
its current pure render, checks package and receipt identity, and runs local offline runtime health,
dependency-isolation and all eleven launcher runtime checks. The Python prefix and actual LangGraph
import belong to the local environment; an external `.pth` bridge or system-site-packages fallback
cannot attest local health. TypeBox's installed locks, version and entry are checked, with aliased
paths refused. This is not a cryptographic attestation of every third-party dependency byte.
Verification writes no marker or receipt and acquires no dependencies. Missing, stale, malformed,
aliased, incomplete or conflicting state raises `InstallError(ValueError)` (or the underlying I/O
error), with an explicit local install/update diagnostic and no successful observation.
`verify_runtime` uses `ManagedRuntimeError` and returns the existing runtime receipt shape, without
refreshing the marker. It has no alternate-runtime search.

`ensure_installation` reverifies the admitted provider identity, then reuses a verified local
installation without applying a plan, rewriting a marker or acquiring packages. `bootstrap=True`
is an explicit host installation grant, not automatic repair on a worker call. Only this grant
allows a current plan and the same public install transaction to run before final verification.
Modified owned or unowned conflicting runtime output still refuses bootstrap. Rechecks detect
changed provider bytes before receipt acceptance. Failure supplies no ready result; retry starts
from a new actual-state plan, never a saved partial-success claim. Acquisition and all runtime
checks must complete before the receipt records successful installation. The existing documented
runtime-rebuild rollback limitation remains applicable; no successful recovery is inferred.

The supported CLI and bootstrap serialize writes using a target-local `.concorde/install.lock`
regular lock file. POSIX advisory locking is required; concurrent acquisition fails explicitly,
and process exit releases the lock without replacing its inode. Low-level plan/apply callers own
exclusive target access and must use this lock; it does not stop an unrelated editor. Callers
also keep target/provider sources quiescent through verification and subsequent execution, and
must not provision into another active source-maintenance checkout. The service refuses a target
that is itself a Concorde source checkout. No API creates a worktree, starts an Operation, changes
a sandbox/task grant, grants delegation, accepts Protocol or writes lifecycle status/runs.

### Project preservation and receipt compatibility {#preserve-project-contract}

The public installer adds `--preserve-project`, not a client flag. Host worktree bootstrap selects
its equivalent `preserve_project=True`. Ordinary user-created Git worktrees can explicitly use
the same script/mode; ignored runtime binaries and receipts need not be committed. The default
installer retains its original unreceipted-root-block collision behavior. Preservation and
`--remove-protocol-guidance` are mutually exclusive.

In preservation mode an existing root instruction file is left byte-for-byte and mode-for-mode
unchanged, whether it contains arbitrary user instructions, inherited canonical Protocol guidance
or historical CLAUDE text. Its existence grants no new ownership. An absent AGENTS.md may receive
one newly receipt-owned entry; no CLAUDE entry is created. A prior local receipt's guidance block
must still match its owned digest; its original ownership and created-file flag remain, rather
than being dropped or replaced with a digest of edited content. Whole-file comparison used for
stale-plan detection is not ownership of surrounding user text.

An existing Protocol tree must have a real complete manifest with matching asset digests. The
whole existing bundle is preserved, never filled piecemeal with a different package version.
Missing/aliased/changed required assets fail before installation writes. Prior local receipt-owned
Protocol outputs retain their exact ownership records and must match them. Unreceipted inherited
Protocol files remain project-owned. A wholly absent bundle may be seeded from the package only
for an uninitialized project or when its exact manifest already matches the existing accepted
binding; no config, registry, Specs or accepted binding is rewritten. A complete different bundle
can remain preserved, but `protocol_matches_package` is false and real Operation admission must
still reject incompatible or unaccepted project state. Installation success is not that admission.

Receipt schema 2 retains the same exact-output/block ownership semantics and adds `package`
(the three-field identity above), `provider_root`, `preserve_project: bool`, and `preserved`
(path/role records for existing unowned project files left in place). Preserved records do not
carry ownership hashes. Locally owned preserved entries remain in `outputs`, never only in
`preserved`. Schema-1 and earlier schema-2 receipts remain valid inputs to explicit installer
migration under the old ownership/conflict rules; local verification requires current package
provenance and never infers it from an old version label. No wire, Pi catalog, build-manifest,
Protocol or managed-marker schema changes accompany these additive receipt fields.


## Typed executable catalog compatibility

Pi catalog schema2 adds an explicit kind for each compatibility public entry: host, agent-entry or
workflow. Eleven concorde-* names and operation_id/request/response wire spellings remain deliberate
compatibility names, not LangGraph identity. Seven canonical Agents are separately inventoried and
have no private Python model-operation run aliases. Optional StateGraph Operations are separately
selected. Old schema1 session entries require rebuild/reselection; stale private selection is not
silently upgraded. Native and compatibility rendered Agent paths contain the same canonical native
instruction bytes. Installed LangGraph dependency health remains required even when execution is native.


### Source-private to installed-output test handoff

A source-private selection attests only its exact candidate paths. Inheriting it into a newly
installed launcher is expected to fail even when installation bytes were generated correctly; it
must not be relaxed to attest another path. Source-only fixture helper `install_selected_fixture`
uses existing package admission, the supported installer and complete local installation verification
without introducing a production selection mode.

The caller supplies the still-active exact source test selection and a fresh canonical destination
strictly within issued tester scratch. The parent verifies the source selection/build and admitted
package identity. Only installer and installed verification/execution subprocesses use a copied
environment separating source-private selection/binding, private data redirect and source Python
import overrides. Other environment and binding namespaces remain unchanged; no global setting or
parent environment is modified. Governing source selection stays active and is reverified after
installation. The installed managed interpreter verifies its own receipt-owned package against the
admitted source identity and observes its exact prefix. No copied assets or source/global runtime
substitute for this installation.

A bounded mode-0600 scratch record binds source selection/build, package identity, external target,
installed entry/catalog/launcher/build digests, receipt/runtime identity and managed interpreter.
This is installation-output provenance, not evidence of a model run or permission to write the
source. Subsequent explicitly granted installed fixture execution uses those exact paths and the
locally separated environment while the caller keeps source and installed bytes quiescent. A stale
source, nonempty/aliased/out-of-scratch target or mismatched installed identity refuses. No installer
or source-selection validation is patched. This source test recipe is not distributed to consumers.


## Source outer task lifecycle {#outer-task-lifecycle}

The explicit source-only `concorde-outer-lifecycle.ts` extension is separate from passive timing.
It loads only for source main and maintenance roles, never tester or terminal domain Agents.
Default/maintenance loading registers no model tool. Only the trusted generated source-main entry
selects `sourceMainLifecycle`, which registers `update_task_brief`; task text, environment role
claims and model arguments cannot select this entry. No catalog, provider, setting, scheduler,
delegation or model-callable compaction control is added. Consumer installation excludes this asset.
Explicit Host tool ceilings still apply; registration does not override a restrictive allowlist.
Pi's native threshold
check uses projected current tokens and resolved model reserve; its overflow recovery compacts
through the supported SDK. The extension does not duplicate those triggers. The explicit
`outer-compact` command waits for idle, calls `ctx.compact` and awaits onComplete/onError;
checkpoints or user messages merely saying compact are not compaction evidence.

Current task memory is one replaced concise brief, stored as native session custom entries, not
primary task status. The source-main model tool `update_task_brief` takes exactly `{brief: object}`,
replaces that session's current brief and returns its admitted copy in `details.brief` and JSON text.
It grants no filesystem, task/status, profile or compaction authority. Validation/persistence failures
are tool errors, not successful updates; identical admitted updates are no-ops. The `outer-brief`
slash command remains a user/Host convenience; assistant text naming it does not execute it.
Both update routes accept exactly scalar strings goal, grant, stage, objective, blocker and next,
plus string arrays decisions, completed, checks and evidence. Text is nonblank, at most 2000 characters; arrays at most 16 entries; the whole JSON at most 12000 characters.
Empty arrays and blocker "none" explicitly represent absence. The fields carry only current
accepted decisions and task facts; grant is a reminder, never executable authority. Main owns
actual task/grant admission. Duplicate identical updates do not append repeated memory entries.

Maintenance may include that JSON in one fenced `task-brief` block in the existing native
contact_supervisor progress_update message. The extension observes the outgoing tool call without
modifying or suppressing its transport, and records worker-reported memory, not delivery, acceptance
or correctness. Invalid optional memory clears the stale brief and records an observation failure;
the supervisor call still proceeds. Native supervisor status and original messages remain the
feedback transport; no parallel progress ledger or universal error schema is defined.

On `session_compact`, the extension uses the latest actual persisted branch compaction identity,
not matching summary text. At the next `context` hook it inserts the then-current brief exactly once
for that compaction, as a request-local custom message, and records the consumed identity in native
session entries. It never replays old system/task prompts or triggers another turn. This is injection
into the constructed provider context, not proof of provider receipt or a successful model response.
No brief means no fabricated memory. Failed/cancelled compaction creates no injection; the native
failure event retains its original diagnostic. Reload/resume restores only current branch memory and
consumed identities; tree navigation follows that branch. Already-injected identities are not replayed.
Frozen launch assets and terminal tool ceilings remain unchanged through compaction.

Host-observed lifecycle, tools, last activity, current context/cache and compaction remain distinct
from worker-reported stage/objective/artifacts/checks/blocker/next/evidence. Activity is not correctness
or server thinking. Native supervisor/events/status carry event-driven meaningful updates; main owns
primary durable persistence and exact stopped-owner release/bind, including new-stage handoffs.
