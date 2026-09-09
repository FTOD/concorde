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

## interface.distribution.build

`build(project_root, integration="all", *, framework_prefix="")` renders Agent instructions,
integration-specific Skill files (Codex `.agents/skills` and Claude `.claude/skills`),
`generated/langgraph.json`, the rule assets (`generated/protocol/principles.md`, its two
kind definitions, and `generated/protocol/schemas.json`), and documentation inventories
(`generated/docs/instructions.json` and `generated/docs/wire.json`) deterministically from
`agents/`, `protocol/`, `prompts/`, `skills/` and the capability contracts. The principles asset
bundles the Protocol principles, Spec management (including Spec and Context) and Required format
chapters with the separate Framework execution profile. The two kind assets contain the Module and Implementation chapters
and their canonical templates respectively; the Module asset also includes the Feature fragment.
Framework configuration, phase authority and Mermaid authoring conventions belong to the execution
profile, not the independent standard. These are build artifacts; installation decides
their destination in a consumer project. The render is byte-identical across repeated calls and performs no
network or process I/O. `write_build` also writes those outputs plus `generated/build-manifest.json`,
recording every recorded source path's sha256. `check_build` renders into a temporary directory and
reports every stale or drifted output without writing anything. `verify_fresh` raises
`BuildError(code="stale_build")` when a recorded source has changed since the last build; the host
calls it before every top-level capability invocation except a lifecycle capability. `load_agent`
returns one Agent's rendered body under `generated/agents/<hyphenated>.md`, effect declaration, and
complete `AgentBinding` from the current build, itself verifying freshness first
(`load_role_prompt` remains as a compatibility alias). The returned Agent binding identifies its Spec digest recorded in the build manifest, its registered Harness, and every
declared capability/context/result/effect/limit checked against that Harness, failing closed with
`BuildError` (`stale_build`, `unknown_agent`, or `invalid_agent_binding`). The resolver
(`resolve_agent_spec`, `resolve_role_prompt`, `resolve_skill_source`, `find_unreachable_prompts`,
`check_reachability`) expands `@include` directives, enforces audience/layering rules, and detects
unreachable or diamond-included sources; `resolve_agent_spec` additionally rejects an Agent Spec
that carries front matter.
`validate_package(root)` runs the complete prompt, capability-module, Agent, contract,
Spec-alignment and build-output checks behind `python -m concorde validate` and `build --check`.
`recompute_protocol_manifest`/`python -m concorde protocol-manifest` report, accept (`--write`), or
bind (`--bind-project`) the tracked `protocol/manifest.json` digest to the current build; accepting a
changed Protocol export is developer-only, and a consumer separately accepts the installed manifest
version/digest in its own project configuration. The reusable Package build Implementation Spec binds the build sources and Skill inventory.
Agent responsibility files are bound separately by Agent definitions. Protocol adapters and the
Framework execution profile are bound by Protocol assets; the independent standard under
`protocol/` is an external normative input, not a registered or implementation-bound Spec. Protocol
adapters alone may include its plain Markdown chapters, which require no audience front matter.
The build records included chapter bytes in source identities so edits invalidate runtime outputs. Modules refer to these Implementation Specs rather than owning
file prefixes themselves. write_build removes retired outputs only within its declared owned
subtrees (generated/agents, generated/protocol and generated/docs), preserving diagrams and
other generators' assets. This allows a Protocol change to retire old kind files coherently.


## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of build:

```text
render_agent(project_root: Path, agent: str) -> BuildOutput
render_role(project_root: Path, role: str) -> BuildOutput
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
load_agent(package_root: str | Path, name: str) -> SkillPrompt
load_role_prompt(package_root: str | Path, role_name: str) -> SkillPrompt
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

Failures return structured findings or the declared exception; callers must stop the affected transition. Repeating an unchanged read is side-effect free. Mutations require current preconditions and explicit caller-owned paths. Local contract facts above remain authoritative without reading the parent or collaborating Specs.

## Returned records and compatibility

`BuildOutput` is a frozen record `{path: str, content: bytes, sources: tuple[str, ...]}`: path is
an exact output location, content is the complete rendered byte sequence, and sources names the
explicit authored inputs. `BuildResult` contains `outputs: tuple[BuildOutput, ...]` and
`manifest: bytes`, the serialized source/output identity manifest. An in-memory render does not
imply those outputs have been written. `ResolvedPrompt` contains expanded `body: str` and its
explicit `sources: tuple[str, ...]`; it carries no execution grant.

`SkillPrompt` retains the compatibility record name and fields `name`, `description`, `source_path`,
`kind="skill"`, `body`, nullable `effects`, and nullable `binding`. String fields contain identity,
provenance and complete instruction text. `load_agent` supplies non-null effects and a current
Agent binding for a successfully admitted Agent. Effects have `reads` and `writes` string tuples,
`network: bool` and `credentials: "none"|"declared"`; these describe a ceiling that the host must
narrow for a concrete invocation, not automatically effective permissions.

`AgentBinding` has string fields `agent`, `spec_path`, `spec_digest`, `instructions_path`,
`instructions_digest`, `harness`, `harness_digest`, `constraints_digest`, `build_manifest_digest`
and `digest`, plus `effective_loop`. Its loop has `timeout_seconds: int` and nullable
`max_turns: int`; effective limits cannot exceed the bound Agent/Harness limits. Digest values
identify exact admitted bytes/configuration, using `sha256:` and 64 lowercase hex digits.
The binding digest covers the complete binding except its own digest field. Source locators remain
provenance; they do not give a caller permission to load additional project context.

Build and resolver failures stop the affected render/load and cannot be reinterpreted as an empty
successful output. `BuildError(ValueError)` carries its declared error code; include-resolution
errors use `PromptResolverError(ValueError)`. Filesystem errors can propagate. Repeated pure renders
with unchanged inputs preserve bytes; a write can fail after some generated outputs have changed,
so runtime freshness must be re-established before use. Rebuild from authored inputs to repair
projections, never edit generated output as a new source. Public aliases preserve the same inputs,
records and failure semantics; unsupported integration or asset identities require explicit repair.
