# Execution permissions

## api.permissions.compile

compile_policy(effects,binding,role_paths,outer_sandbox_required=False) intersects declared role paths with explicit host authority, producing a digest-bound policy. render_codex_configuration and render_claude_configuration create native read/write/command/network restrictions or reject unenforceable grants. build_launch_specification binds the resulting native configuration, context identity and fresh invocation. require_isolated_worktree(project_root,allow_primary_worktree=False) rejects unsafe mutation environments unless the trusted host grants the explicit exception. Task JSON cannot override any permission.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of operation_permissions:

```text
runtime_bootstrap_file(*, path: str, sha256: str, size: int, mode: int, owner: int | None) -> RuntimeBootstrapFile
runtime_bootstrap_digest(files: tuple[RuntimeBootstrapFile, ...]) -> str
compile_policy(effects: EffectDeclaration, binding: PolicyBinding, role_paths: Mapping[str, tuple[str, ...]], *, deny_paths: tuple[str, ...]=(), outer_sandbox_required: bool=False) -> NormalizedPolicy
verify_effective_subset(declared: NormalizedPolicy, effective: NormalizedPolicy) -> None
render_codex_configuration(policy: NormalizedPolicy, *, native_enforcement: bool, outer_sandbox: str | None=None) -> CodexLaunchConfiguration
finalize_codex_configuration(configuration: CodexLaunchConfiguration, runtime_bootstrap: tuple[RuntimeBootstrapFile, ...]) -> CodexLaunchConfiguration
render_claude_configuration(policy: NormalizedPolicy, *, native_enforcement: bool, outer_sandbox: str | None=None) -> ClaudeLaunchConfiguration
compare_effective_boundaries(first: NativeLaunchConfiguration, second: NativeLaunchConfiguration) -> bool
build_launch_specification(*, operation: str, stage: str, occurrence: int, capability: str, integration: Literal['codex', 'claude'], agent: str, project_root: str, request: str, prompt: str, prior_results: tuple[str, ...], workspace_receipt_json: str, workspace_digest: str, policy: NormalizedPolicy, native_configuration: NativeLaunchConfiguration, runtime_input_json: str | None=None, operation_configuration_json: str | None=None, invocation_id: str | None=None) -> LaunchSpecification
finalize_launch_specification(specification: LaunchSpecification, runtime_bootstrap: tuple[RuntimeBootstrapFile, ...]) -> LaunchSpecification
```

Public functions of worktree:

```text
inspect_worktree(project_root: str | Path) -> WorktreeBoundary
require_isolated_worktree(project_root: str | Path, *, allow_primary_worktree: bool=False) -> WorktreeBoundary
```

Failures return structured findings or the declared exception; callers must stop the affected transition. Repeating an unchanged read is side-effect free. Mutations require current preconditions and explicit caller-owned paths. Local contract facts above remain authoritative without reading the parent or collaborating Specs.
