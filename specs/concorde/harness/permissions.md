```concorde-document
{
  "id": "document.harness.permissions",
  "targets": [
    "module.harness"
  ],
  "main_visible": true
}
```
# Permissions

## Required Agent authority boundary

The local companion contract **Agents and Harnesses** defines A4 for this Module. Effective authority
MUST be a subset of the Agent definition's constraints and the host's invocation grant, including
admitted capability and tool use as well as file, process, network and credential effects. Resource
availability in a Harness is not permission. `compile_policy` compiles the Agent's declared
`EffectDeclaration` against a host-supplied, narrowing `PolicyBinding`, so the native policy APIs
below can only produce a policy at or under that complete Agent authority boundary, never beyond it.

The trusted calling host, rather than `compile_policy`, admits an Agent definition against an
invocation grant. The compiler does not accept `AgentGrant` or select a child Agent. For the initial
recursive read-only adapter, the calling execution host checks the root
Agent allowlist, each direct delegation edge and inherited Agent allowlist, and intersects target
grants before resolving a child's context. It enforces shared call/depth/decision/deadline limits,
local steps, cancellation and typed input/result contracts outside model discretion. A denied edge
must produce a rejected child result before context resolution or native launch. This prerequisite
does not authorize mutation or general-purpose tools.

After that admission, the native adapter supplies an explicit private `context.json` role path,
read-only effects, no network and no credentials to these policy APIs. The compiler binds that
host-issued path authority; the renderer restricts native process/tool access to the resulting
policy and disables provider-native delegation. Context descriptions, installed resources and
caller task JSON cannot add paths or operations. That caller verifies matching
launch/completion/receipt identities and enforces the remaining deadline before accepting a result.
Only its attested native executable may enter the separately declared bootstrap exception.
Trusted synchronous Python callbacks enforce their own timely return and are not sandboxed by
this Module. Supporting a different effectful Agent adapter requires an explicit host admission
and enforcement contract for its capabilities/tools; these compatibility APIs alone do not grant it.

## Policy compilation and rendering

compile_policy(effects,binding,role_paths,outer_sandbox_required=False) intersects declared role paths with explicit host authority, producing a digest-bound policy. render_codex_configuration and render_claude_configuration create native read/write/command/network restrictions or reject unenforceable grants. build_launch_specification binds the resulting native configuration, context identity and fresh invocation. require_isolated_worktree(project_root,allow_primary_worktree=False) rejects unsafe mutation environments unless the trusted host grants the explicit exception. Task JSON cannot override any permission.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of permissions:

```text
runtime_bootstrap_file(*, path: str, sha256: str, size: int, mode: int, owner: int | None) -> RuntimeBootstrapFile
runtime_bootstrap_digest(files: tuple[RuntimeBootstrapFile, ...]) -> str
compile_policy(effects: EffectDeclaration, binding: PolicyBinding, role_paths: Mapping[str, tuple[str, ...]], *, deny_paths: tuple[str, ...]=(), outer_sandbox_required: bool=False) -> NormalizedPolicy
verify_effective_subset(declared: NormalizedPolicy, effective: NormalizedPolicy) -> None
render_codex_configuration(policy: NormalizedPolicy, *, native_enforcement: bool, outer_sandbox: str | None=None) -> CodexLaunchConfiguration
finalize_codex_configuration(configuration: CodexLaunchConfiguration, runtime_bootstrap: tuple[RuntimeBootstrapFile, ...]) -> CodexLaunchConfiguration
render_claude_configuration(policy: NormalizedPolicy, *, native_enforcement: bool, outer_sandbox: str | None=None) -> ClaudeLaunchConfiguration
compare_effective_boundaries(first: NativeLaunchConfiguration, second: NativeLaunchConfiguration) -> bool
build_launch_specification(*, capability: str, stage: str, occurrence: int, role: str, integration: Literal['codex', 'claude'], agent: str, project_root: str, request: str, prompt: str, prior_results: tuple[str, ...], workspace_receipt_json: str, workspace_digest: str, policy: NormalizedPolicy, native_configuration: NativeLaunchConfiguration, runtime_input_json: str | None=None, capability_configuration_json: str | None=None, invocation_id: str | None=None, agent_binding_json: str | None=None) -> LaunchSpecification
finalize_launch_specification(specification: LaunchSpecification, runtime_bootstrap: tuple[RuntimeBootstrapFile, ...]) -> LaunchSpecification
```

Public functions of worktree:

```text
inspect_worktree(project_root: str | Path) -> WorktreeBoundary
require_isolated_worktree(project_root: str | Path, *, allow_primary_worktree: bool=False) -> WorktreeBoundary
```

`WorktreeBoundary` is a frozen record with string fields `project_root`, `repository_root`, `head`,
`git_dir` and `common_dir`, and boolean `isolated`; `to_dict() -> dict[str, Any]` returns those exact
fields. Successful Git inspection uses resolved absolute paths and a verified commit ID for `head`.
`isolated` means that the worktree's Git directory differs from its shared common directory.
`inspect_worktree` observes this identity without changing files or checking for local dirt; it
does not require isolation and may inspect a directory within a worktree. A symlink root, missing
directory, unavailable/failing Git command, empty Git identity or absent committed HEAD raises
`WorktreeBoundaryError(ValueError)`.

`require_isolated_worktree` returns the inspected record for a committed linked worktree. With
`allow_primary_worktree=False`, it rejects a primary worktree or non-worktree directory with the
same exception. The trusted host's explicit `True` exception also accepts a committed primary
worktree. If the initial Git probe cannot establish any worktree (including an unavailable Git
executable), this exception returns the resolved `project_root`, empty other string fields and
`isolated=False`. It never accepts a symlink or missing directory, and a subsequent inspection
failure inside an identified Git worktree still raises. The exception is not a task-input
permission and does not alter delivery's separate preservation requirements.

Failures return structured findings or the declared exception; callers must stop the affected transition. Repeating an unchanged read is side-effect free. Mutations require current preconditions and explicit caller-owned paths. Local contract facts above remain authoritative without reading the parent or collaborating Specs.
