# Task context scenarios

Concrete situations of [Task context](module.md). Module-wide obligations are stated once in
[requirements](requirements.md).

## Freezing a snapshot

### scenario.context.freeze — Freeze one Module's context for an Agent call

- GIVEN a valid Spec repository, a registered Module and a bound Agent definition
- AND a task, and optionally a scenario focus, constraints and admitted stage inputs
- WHEN the Host freezes a context snapshot
- THEN it returns an immutable snapshot identified by a digest of its content
- AND the snapshot lists every document of the Module's `SpecContext` with its identity, owner, digest and the relations that selected it, and names the Module's entry
- AND it lists the Module's implementation entries and bound file names
- AND it records the Agent binding, the task, the stage inputs and the workspace facts
- BUT no document or file body is embedded in it

See [boundary sets](requirements.md#req.context.boundary-sets),
[focus never trims](requirements.md#req.context.focus-no-trim),
[names in every phase](requirements.md#req.context.names-every-phase) and
[identity](requirements.md#req.context.identity).

### scenario.context.implementation-contents — An Agent that reads code receives its paths and digests

- GIVEN a bound Agent definition that reads implementation, such as the code reviewer's
- WHEN the Host freezes a snapshot of a Module
- THEN the snapshot lists the path and digest of every file in the Module's `ImplementationScope`
- BUT a snapshot of the same Module for an Agent that does not read implementation lists no such paths or digests

See [contents only when read](requirements.md#req.context.contents-when-read).

### scenario.context.shared-file-binding — A programmer is bound to the Modules that share its files

- GIVEN Module A binds a file that Module B also binds, and A does not select B's documents
- WHEN the Host freezes a snapshot of A for the programmer
- THEN the snapshot is also bound to B and records B's `SpecContext` and the shared file
- AND the capsule receives B's selected documents as copies
- AND the programmer's intended write paths stay A's `ImplementationScope`

See [shared-file binding](requirements.md#req.context.shared-file-binding).

### scenario.context.shared-file-other-agents — Only code-writing calls are bound to sharing Modules

- GIVEN Module A binds a file that Module B also binds
- WHEN the Host freezes a snapshot of A for an Agent that does not write implementation, such as the planner or the code reviewer
- THEN the snapshot is bound to A alone and lists none of B's documents

### scenario.context.external-references — External references are recorded and delivered to readers

- GIVEN a Module whose entry includes pinned external material, such as the vendored documentation of a library it builds on
- WHEN the Host freezes a snapshot and assembles the capsule for an Agent whose definition reads references
- THEN the snapshot lists each external inclusion with one digest over its readable files
- AND the capsule holds copies of exactly those readable files
- BUT media and archive files below an inclusion are neither digested nor copied

### scenario.context.external-references-not-read — Agents that do not read references get no copies

- GIVEN a Module with pinned external material
- WHEN the Host freezes a snapshot and assembles the capsule for an Agent whose definition does not read references
- THEN the snapshot still lists the external inclusions with their digests
- BUT the capsule holds no copy of the external material

### scenario.context.external-reference-missing — A missing reference checkout stops freezing

- GIVEN a Module whose external inclusion is not checked out
- WHEN the Host freezes a snapshot of it
- THEN freezing fails with `invalid_reference` naming the missing path
- AND no snapshot is returned

### scenario.context.invalid-input — Reject an unsupported phase or a blank task

- GIVEN an unsupported phase or a blank task
- WHEN the Host freezes a snapshot
- THEN freezing fails with `invalid_phase` or `invalid_input`
- AND no snapshot is returned

### scenario.context.stage-input-refused — Reject stage inputs the definition does not admit

- GIVEN an Agent definition and a stage input of a type it does not admit, two inputs of the same type, or a launch without a required input
- WHEN the Host freezes a snapshot for it
- THEN freezing fails with `incompatible_handoff`
- AND no snapshot is returned

A policy preview may omit a required input that does not exist yet; a launch may not.

## Delivering and rechecking

### scenario.context.capsule — Assemble a capsule of exact copies

- GIVEN a frozen snapshot and its bound Agent definition
- WHEN the Host assembles the capsule
- THEN the capsule holds a byte-identical copy of every Protocol file and every Spec context document of the snapshot, verified against its digest
- AND the implementation files when the definition reads but does not write implementation, and the external material when it reads references
- AND `context.json` holding the snapshot, which for an Agent that writes implementation also names the project worktree and the intended write paths
- BUT no other project file is copied

See [capsule exact](requirements.md#req.context.capsule-exact).

### scenario.context.capsule-changed — A changed capsule copy stops acceptance

- GIVEN an assembled capsule whose copies were recorded with their digests
- WHEN a copy is changed before the result is accepted and the Host verifies the capsule
- THEN verification fails with `stale_context`

### scenario.context.stale-recheck — Reject a result after an input changed

- GIVEN a snapshot frozen earlier
- AND since then a selected document, a selecting declaration, an ownership, a Protocol binding, the current worktree's lifecycle position or another rechecked input has changed
- WHEN the Host rechecks the snapshot
- THEN the recheck fails with `stale_context`
- AND the provider must freeze a new snapshot before continuing

See [recheck](requirements.md#req.context.recheck).

### scenario.context.programmer-recheck — The programmer's own edits do not stale its snapshot

- GIVEN a snapshot frozen for the programmer
- AND since then only implementation files of the selected Module were created, changed or removed
- WHEN the Host rechecks the snapshot before accepting the programmer's result
- THEN the recheck passes
- BUT a changed Spec document of any bound Module still fails it with `stale_context`

### scenario.context.other-worktrees-move — Other worktrees may change while a call runs

- GIVEN a snapshot whose workspace facts list other live worktrees
- AND since then another worktree advanced, appeared or was removed
- WHEN the Host rechecks the snapshot
- THEN the recheck passes as long as the current worktree's own facts are unchanged

## Binding an Agent

### scenario.context.agent-bind — Bind an Agent definition to the current build

- GIVEN an Agent with a consistent definition, and a fresh build
- WHEN the Host binds the definition
- THEN it returns a reproducible binding with the digests of the instruction source, the rendered instructions, the definition and the build manifest, the tools, the effects and the time limit
- AND the bare, hyphenated and `concorde-` prefixed spellings of the Agent's name resolve to the same binding
- AND changing the Agent's instructions makes the build stale until it is rebuilt

### scenario.context.unknown-agent — An unknown Agent is refused

- GIVEN a name that no Agent definition has
- WHEN the Host binds it
- THEN binding fails with `unknown_agent`

### scenario.context.agent-bind-stale-build — A stale build stops binding

- GIVEN an Agent definition whose instruction source changed since the last build, or whose rendered instructions are missing
- WHEN the Host binds it
- THEN binding fails with `stale_build`

### scenario.context.definition-inconsistent — An inconsistent definition is refused

- GIVEN an Agent definition that writes a role it does not read, grants `edit` or `write` without a write role, reads implementation without a `project` workspace, names a delegation or unknown tool, lacks `read`, requires a stage input it does not admit, or has a nonpositive time limit
- WHEN the Host binds it
- THEN binding fails with `invalid_agent_binding`

See [definition consistent](requirements.md#req.context.definition-consistent).

### scenario.context.input-check — An Agent's typed input must match its definition

- GIVEN an Agent definition and a typed input prepared for it
- WHEN the Host admits the input before launch
- THEN a mismatched phase or context type, an unadmitted or missing required stage input, implementation files for a definition without implementation reads, or a Spec review input that carries code changes is refused before launch

### scenario.context.result-check — An Agent's result must stay within its definition

- GIVEN an Agent definition and a typed result submitted by that Agent
- WHEN the Host checks the result
- THEN an outcome the definition does not list is refused with `invalid_completion`
- AND a filled result field the definition does not permit, such as Spec documents, is refused with `permission_denied`

These checks use only the definition and the typed values, never the instructions or prompt text.

## Reference versions

### scenario.context.reference-versions — A LangGraph reference at another release fails the check

- GIVEN a checkout whose pinned LangGraph reference names a different version than the installed LangGraph or the lock file
- WHEN the reference version check runs
- THEN it prints the three versions and fails, telling the maintainer to move the reference checkout to the installed release

The check passes only when the reference and the installed version agree and the lock file, when it
names LangGraph, agrees with them. A missing reference checkout fails the check with instructions
to initialize the references.
