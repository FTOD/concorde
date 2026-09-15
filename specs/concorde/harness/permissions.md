```concorde-document
{
  "id": "document.harness.permissions",
  "owner": "module.harness",
  "main_visible": true
}
```
# Permissions

## Required worker authority boundary

The local companion contract **Agents and Harnesses** defines A4 for this Module. Effective authority
MUST be a subset of the worker contract's effects and the host's invocation grant, including tool
use as well as file, process, network and credential effects. Resource availability in a Harness is
not permission. `compile_policy` compiles the contract's declared `EffectDeclaration` against a
host-supplied, narrowing `PolicyBinding` and the concrete role paths the host resolved, so it can only
produce a policy at or under that authority boundary, never beyond it.

The host supplies the role paths from the frozen context: the `spec-context` or `discovery-context`
role names the context index file and every document and Protocol file it lists; `implementation`
names the selected Module's bound implementation files, or its listed entries for a code writer; and
`references` names the Module's external reference roots. Context descriptions, installed resources
and caller task JSON cannot add paths or operations. The executor recompiles the grant against the
worker's contract before launch and rejects a policy that is wider, that grants writes to a worker
without a write effect, or that grants network or credential effects to any worker.

## Enforcement

The compiled policy becomes the Concorde worker extension's policy for the invocation. The extension
gates every tool call inside the worker's Pi process and inside every child session: a tool outside
the granted list is refused; `read`, `grep`, `find` and `ls` must target a canonical path, symlinks
resolved, under a read or write grant; `edit` and `write` must target a path under a write grant; a
child cannot delegate or submit a result. A capsule worker's workspace contains only its granted
copies, so its read grant also covers the workspace root.

This is a policy boundary inside the Pi process, not an operating-system sandbox. It does not confine
shell commands: a worker granted `bash` can reach whatever its operating-system user can, and the
host only removes the provider credential variables from each command. The Pi process itself reaches
its model provider over the network with the developer's Pi credentials. Running the whole worker
process inside an operating-system sandbox that mounts only the granted paths is the planned stronger
boundary. Configured deterministic checks already run under the host's OS-enforced read-only executor
([execution](execution.md)).

## Policy compilation

`compile_policy(effects, binding, role_paths, deny_paths=())` intersects declared role paths with
explicit host authority, producing a digest-bound policy. `verify_effective_subset(declared,
effective)` rejects an effective policy that widens a declared one. `require_isolated_worktree(project_root,
allow_primary_worktree=False)` rejects unsafe mutation environments unless the trusted host grants the
explicit exception. Task JSON cannot override any permission.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of permissions:

```text
compile_policy(effects: EffectDeclaration, binding: PolicyBinding, role_paths: Mapping[str, tuple[str, ...]], *, deny_paths: tuple[str, ...]=(), outer_sandbox_required: bool=False) -> NormalizedPolicy
verify_effective_subset(declared: NormalizedPolicy, effective: NormalizedPolicy) -> None
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
