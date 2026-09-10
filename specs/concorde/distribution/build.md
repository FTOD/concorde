```concorde-document
{
  "id": "document.distribution.build",
  "targets": [
    "module.distribution"
  ],
  "main_visible": true
}
```
# Build

`build(project_root, integration="all", *, framework_prefix="")` renders Agent instructions,
integration-specific Skill files (Codex `.agents/skills` and Claude `.claude/skills`),
`generated/langgraph.json`, the rule assets (`generated/protocol/principles.md`, its kind
definition, and `generated/protocol/schemas.json`), and documentation inventories
(`generated/docs/instructions.json` and `generated/docs/wire.json`) deterministically from
`agents/`, `protocol/`, `prompts/`, `skills/` and the capability contracts. The principles asset
bundles the Protocol principles, Spec management (including Spec and Context) and Required format
chapters with the separate Framework execution profile. The kind asset contains the Module chapter
and its canonical templates. Framework configuration, phase authority and Mermaid authoring
conventions belong to the execution profile, not the independent standard.

## Rendering and freshness

A **Skill** is an instruction artifact for the developer's external agent runtime. Distribution
owns its authored source under `skills/`, shared invocation instructions under
`prompts/workflow-host/`, and rendered integration-specific installation. Each public Skill maps to
one global or lifecycle Capability; stage capabilities have no Skill. The external runtime reads
the Skill and submits the declared typed request through `scripts/run-capability.py`; Development
admits and executes that request. Building or installing a Skill does not execute its Capability
or add it to a Concorde Agent's Harness. Capability behavior remains with its providing Module.

### scenario.distribution.build-render — Build renders deterministic projections from authored sources

- GIVEN the current `prompts/`, `skills/`, `capabilities/`, `agents/` and Protocol chapter sources
- WHEN build runs for a selected integration
- THEN it renders Agent instructions, Skill files, the Studio graph configuration, Protocol assets, schemas and documentation inventories deterministically
- AND repeated renders of unchanged inputs are byte-identical and perform no network or process I/O

### scenario.distribution.build-write — write_build records source and output digests in the manifest

- GIVEN a completed render
- WHEN write_build runs
- THEN it writes the rendered outputs plus `generated/build-manifest.json` recording every recorded source path's sha256
- AND it removes retired outputs only within its declared owned subtrees (`generated/agents`, `generated/protocol` and `generated/docs`), preserving other generators' assets

### scenario.distribution.build-check — check_build reports staleness without writing

- GIVEN the currently committed generated outputs
- WHEN check_build runs
- THEN it renders into a temporary directory and reports every stale or drifted output
- AND it writes nothing to the worktree

### scenario.distribution.build-stale-blocks-execution — A stale build fails closed

- GIVEN a recorded source has changed since the last build
- WHEN any ordinary capability invocation other than a lifecycle capability is attempted
- THEN verify_fresh raises a `stale_build` BuildError and the invocation does not proceed with stale instructions

### scenario.distribution.load-agent — load_agent returns one Agent's current admitted binding

- GIVEN a named Agent and a fresh build
- WHEN load_agent is called
- THEN it verifies freshness first and returns the Agent's rendered body, effect declaration and complete `AgentBinding`
- AND an unknown Agent or an invalid binding fails closed with a typed BuildError (`stale_build`, `unknown_agent`, or `invalid_agent_binding`)

`validate_package(root)` runs the complete prompt, capability-module, Agent, contract,
Spec-alignment and build-output checks behind `python -m concorde validate` and `build --check`.
`recompute_protocol_manifest`/`python -m concorde protocol-manifest` report, accept (`--write`), or
bind (`--bind-project`) the tracked `protocol/manifest.json` digest to the current build; accepting
a changed Protocol export is developer-only, and a consumer separately accepts the installed
manifest version/digest in its own project configuration. Agent responsibility files are bound
separately by Agent definitions. Protocol adapters and the Framework execution profile are bound by
Protocol assets; the independent standard under `protocol/` is an external normative input, not a
Module-bound Spec. Protocol adapters alone may include its plain Markdown chapters, which require
no audience front matter. The build records included chapter bytes in source identities so edits
invalidate runtime outputs. Modules refer to their own entity file listings rather than owning file
prefixes themselves.

### scenario.distribution.capability-determinism — Capability metadata accounts for model calls

- GIVEN capability modules declaring their class, Agents, host routing and acyclic `USES` composition
- WHEN package validation checks their metadata
- THEN each module must declare a boolean `DETERMINISTIC`, rejecting missing values, strings and integers
- AND the flag must be true exactly when neither its Agents, host routing nor any transitive composed capability can call a model
- AND lifecycle capabilities must remain deterministic
- AND the single registered `concorde-capabilities` block must contain the same boolean `deterministic` for every capability alongside its `id`, `class` and `skill`
- BUT a path that skips model execution does not make a model-backed capability deterministic

Validation checks declared model-call paths, not arbitrary Python or subprocess behavior. It
reports invalid metadata with `CONCORDE-CAPABILITY-CONSTANTS-001`, inconsistent classification
with `CONCORDE-CAPABILITY-DETERMINISTIC-001`, and Spec metadata drift with
`CONCORDE-SPEC-CAPABILITIES-001`. Unknown or cyclic composition remains a composition error;
validation cannot certify its determinism.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of build:

```text
render_agent(project_root: Path, agent: str, mode: str | None=None) -> BuildOutput
render_role(project_root: Path, agent: str, mode: str | None=None) -> BuildOutput
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
load_agent(package_root: str | Path, name: str, mode: str | None=None) -> SkillPrompt
load_role_prompt(package_root: str | Path, name: str, mode: str | None=None) -> SkillPrompt
```

Public functions of prompt_resolver:

```text
resolve_agent_spec(project_root: str | Path, relative_path: str) -> ResolvedPrompt
resolve_role_prompt(project_root: str | Path, relative_path: str) -> ResolvedPrompt
resolve_skill_source(project_root: str | Path, relative_path: str) -> ResolvedPrompt
find_unreachable_prompts(project_root: str | Path, roots: list[str] | tuple[str, ...]) -> tuple[str, ...]
check_reachability(project_root: str | Path, roots: list[str] | tuple[str, ...]) -> None
```

Public functions of package_validation:

```text
validate_package(root: Path) -> list[Finding]
```

The resolver (`resolve_agent_spec`, `resolve_role_prompt`, `resolve_skill_source`,
`find_unreachable_prompts`, `check_reachability`) expands `@include` directives, enforces
audience/layering rules, and detects unreachable or diamond-included sources; `resolve_agent_spec`
additionally rejects an Agent Spec that carries front matter. `package_validation` attributes its
findings to `module.distribution` and requires exactly one registered `concorde-capabilities` block
and one `concorde-agents` block across all Module documents, each equal to the current code
inventory of capabilities and Agents.

Failures return structured findings or the declared exception; callers must stop the affected
transition. Repeating an unchanged read is side-effect free. Mutations require current
preconditions and explicit caller-owned paths. Local contract facts above remain authoritative
without reading the parent or collaborating Specs.

## Returned records and compatibility

`BuildOutput` is a frozen record `{path: str, content: bytes, sources: tuple[str, ...]}`: path is
an exact output location, content is the complete rendered byte sequence, and sources names the
explicit authored inputs. `BuildResult` contains `outputs: tuple[BuildOutput, ...]` and
`manifest: bytes`, the serialized source/output identity manifest. An in-memory render does not
imply those outputs have been written. `ResolvedPrompt` contains expanded `body: str` and its
explicit `sources: tuple[str, ...]`; it carries no execution grant.

`SkillPrompt` retains the compatibility record name and fields `name`, `description`,
`source_path`, `kind="skill"`, `body`, nullable `effects`, and nullable `binding`. String fields
contain identity, provenance and complete instruction text. `load_agent` supplies non-null effects
and a current Agent binding for a successfully admitted Agent. Effects have `reads` and `writes`
string tuples, `network: bool` and `credentials: "none"|"declared"`; these describe a ceiling that
the host must narrow for a concrete invocation, not automatically effective permissions.

`AgentBinding` has string fields `agent`, `spec_path`, `spec_digest`, `instructions_path`,
`instructions_digest`, `harness`, `harness_digest`, `constraints_digest`, `build_manifest_digest`
and `digest`, nullable string fields `mode` and `mode_digest`, plus `effective_loop`. Its loop has `timeout_seconds: int` and nullable
`max_turns: int`; effective limits cannot exceed the bound Agent/Harness limits. Digest values
identify exact admitted bytes/configuration, using `sha256:` and 64 lowercase hex digits. The
binding digest covers the complete binding except its own digest field. Source locators remain
provenance; they do not give a caller permission to load additional project context.

Build and resolver failures stop the affected render/load and cannot be reinterpreted as an empty
successful output. `BuildError(ValueError)` carries its declared error code; include-resolution
errors use `PromptResolverError(ValueError)`. Filesystem errors can propagate. Repeated pure
renders with unchanged inputs preserve bytes; a write can fail after some generated outputs have
changed, so runtime freshness must be re-established before use. Rebuild from authored inputs to
repair projections, never edit generated output as a new source. Public aliases preserve the same
inputs, records and failure semantics; unsupported integration or asset identities require explicit
repair.

Agent builds publish three common responsibility projections and twelve independent mode
projections. Each mode projection concatenates only its Agent common source and selected mode
source; the manifest records both source sets. The instructions documentation exposes each mode
and its contract separately. Package validation compares sorted mode names in concorde-agents
with the Python inventory and rejects mode constraints wider than the owning Agent.

Mode instruction file membership must equal the declared mode inventory. Agent Python bindings,
mode bodies and available capability/wire sources are recorded build inputs; changing them makes
verify_fresh reject the old build even when a common instruction body is unchanged.
