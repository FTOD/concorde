# Package assets

## api.assets.render

resolve_skill_prompt(path,kind,framework_prefix) parses one canonical internal role or paired Operation. render_capabilities(package_root,integration,framework_prefix="") returns target-path to rendered public-wrapper text; only public paired Operations are projected. capability_projection_roles supplies exact receipt ownership roles. validate_package(root) checks Manifest 3 inventory, literal executable dependencies, prompt pairing and exported wire schemas without executing entrypoints. Reflection compatibility roles invoke the host and cannot investigate in ambient cognition. Protocol asset export is maintainer-only; changing a consumer binding requires explicit --bind-project.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of skill_assets:

```text
capability_name(path: Path) -> str
target_path(name: str, integration: str) -> str
resolve_skill_prompt(path: Path, kind: CapabilityKind, framework_prefix: str='.concorde/framework') -> SkillPrompt
load_skill_prompt(package_root: str | Path, name: str, framework_prefix: str='.concorde/framework') -> SkillPrompt
render_skill(path: Path, integration: str, framework_prefix: str='.concorde/framework', *, kind: CapabilityKind='skill') -> str
public_capabilities(package_root: str | Path, framework_prefix: str='.concorde/framework') -> tuple[SkillPrompt, ...]
capability_projection_roles(package_root: str | Path, integration: str, framework_prefix: str='.concorde/framework') -> dict[str, CapabilityKind]
render_capabilities(package_root: str | Path, integration: str, framework_prefix: str='.concorde/framework') -> dict[str, str]
```

Public functions of profile8_validation:

```text
validate_package(root: Path) -> list[Finding]
```

Public functions of validation:

```text
capability_source_paths(project_root: str | Path) -> tuple[str, ...]
validate_capabilities(package: Any) -> list[Finding]
```

Public functions of agent_assets:

```text
source_digest(asset_root: Path) -> str
render_projection(asset_root: Path, integration: str) -> dict[str, str]
projection_roles(asset_root: Path, integration: str) -> dict[str, str]
preview_agent_assets(project_root: Path, asset_root: Path, integration: str, concorde_version: str='source') -> ToolResult
sync_agent_assets(project_root: Path, asset_root: Path, integration: str, concorde_version: str='source') -> ToolResult
verify_agent_assets(project_root: Path, asset_root: Path, integration: str) -> ToolResult
remove_agent_assets(project_root: Path, integration: str) -> ToolResult
```

Public functions of render-capability-surfaces:

```text
main() -> int
```

Public functions of sync-protocol-assets:

```text
main()
```

Failures return structured findings or the declared exception; callers must stop the affected transition. Repeating an unchanged read is side-effect free. Mutations require current preconditions and explicit caller-owned paths. Local contract facts above remain authoritative without reading the parent or collaborating Specs.
