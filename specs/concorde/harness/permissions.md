# Permissions

### Required worker authority boundary

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

### Enforcement

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

### Policy compilation

`compile_policy(effects, binding, role_paths, deny_paths=())` intersects declared role paths with
explicit host authority, producing a digest-bound policy. `verify_effective_subset(declared,
effective)` rejects an effective policy that widens a declared one. `require_isolated_worktree(project_root,
allow_primary_worktree=False)` rejects unsafe mutation environments unless the trusted host grants the
explicit exception. Task JSON cannot override any permission.

## Precise specifications

The Harness Module owns the exact obligations and interface details in [contracts](contracts.md).
These companions are part of the same complete Module specification, not separate topic owners.
