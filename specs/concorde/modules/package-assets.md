```concorde-document
{
  "id": "document.module.package-assets",
  "targets": ["module.package-assets"],
  "main_visible": false
}
```

# Package assets

## api.assets.render

`build(project_root, integration="all", *, framework_prefix="")` renders every role's rendered
instructions, every Skill's `SKILL.md` (Codex `.agents/skills` and Claude `.claude/skills`),
`generated/langgraph.json`, and the Protocol assets (`generated/protocol/principles.md`, its three
kind definitions, and `generated/protocol/schemas.json`) deterministically from `prompts/`, `skills/`
and the capability contracts. The render is byte-identical across repeated calls and performs no
network or process I/O. `write_build` also writes those outputs plus `generated/build-manifest.json`,
recording every recorded source path's sha256. `check_build` renders into a temporary directory and
reports every stale or drifted output without writing anything. `verify_fresh` raises
`BuildError(code="stale_build")` when a recorded source has changed since the last build; the host
calls it before every top-level capability invocation except a lifecycle capability. `load_role_prompt`
returns one role's rendered body and effect declaration from the current build, itself verifying
freshness first. The resolver (`resolve_role_prompt`, `resolve_skill_source`,
`find_unreachable_prompts`, `check_reachability`) expands `@include` directives, enforces
audience/layering rules, and detects unreachable or diamond-included sources.
`validate_package(root)` runs the complete prompt, capability-module, contract, Spec-alignment and
build-output checks behind `python -m concorde validate` and `build --check`.
`recompute_protocol_manifest`/`python -m concorde protocol-manifest` report, accept (`--write`), or
bind (`--bind-project`) the tracked `protocol/manifest.json` digest to the current build; accepting a
changed Protocol export is maintainer-only, and a consumer separately accepts the installed manifest
version/digest in its own project configuration. This module owns `skills/` sources and
`capabilities/__init__.py` (the capability inventory declaration); it does not own the prompts of
other targets — `prompts/workflow-host`, `prompts/spec-context` and `prompts/protocol` belong to the
Services that use them.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of build:

```text
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
load_role_prompt(package_root: str | Path, role_name: str) -> SkillPrompt
```

Public functions of prompt_resolver:

```text
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
