```concorde-document
{
  "id": "document.module.package-assets",
  "targets": ["module.package-assets"],
  "main_visible": false
}
```

# Package assets

## api.assets.render

`build(project_root, integration="all", *, framework_prefix="")` renders Agent instructions,
integration-specific Skill files (Codex `.agents/skills` and Claude `.claude/skills`),
`generated/langgraph.json`, the rule assets (`generated/protocol/principles.md`, its three
kind definitions, and `generated/protocol/schemas.json`), and documentation inventories
(`generated/docs/instructions.json` and `generated/docs/wire.json`) deterministically from
`agents/`, `prompts/`, `skills/` and the capability contracts. The principles asset bundles the Concorde Spec
Protocol with the Framework execution profile. These are build artifacts; installation decides
their destination in a consumer project. The render is byte-identical across repeated calls and performs no
network or process I/O. `write_build` also writes those outputs plus `generated/build-manifest.json`,
recording every recorded source path's sha256. `check_build` renders into a temporary directory and
reports every stale or drifted output without writing anything. `verify_fresh` raises
`BuildError(code="stale_build")` when a recorded source has changed since the last build; the host
calls it before every top-level capability invocation except a lifecycle capability. `load_agent`
returns one Agent's rendered body under `generated/agents/<hyphenated>.md`, effect declaration, and
complete `AgentBinding` from the current build, itself verifying freshness first
(`load_role_prompt` remains as a compatibility alias). `resolve_agent` (`agent_model.py`, owned by
`service.workflow-host` but depending on this module's `verify_fresh`) resolves one named Agent's
complete binding: its Spec digest recorded in the build manifest, its registered Harness, and every
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
version/digest in its own project configuration. This module owns `skills/` sources,
`capabilities/__init__.py` (the capability inventory declaration), and `agents/__init__.py` (the
Agent inventory declaration); it does not own the prompts of other targets, nor any individual
`agents/<name>/` directory — `prompts/workflow-host`, `prompts/spec-context`, `prompts/protocol`,
and each `agents/<name>/` belong to the Services that use or launch them.

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

Public functions of agent_model (`service.workflow-host`):

```text
resolve_agent(package_root: str | Path, name: str) -> AgentBinding
```

Public functions of package_validation:

```text
validate_package(root: Path) -> list[Finding]
```

Failures return structured findings or the declared exception; callers must stop the affected transition. Repeating an unchanged read is side-effect free. Mutations require current preconditions and explicit caller-owned paths. Local contract facts above remain authoritative without reading the parent or collaborating Specs.
