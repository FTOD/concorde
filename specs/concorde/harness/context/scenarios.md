# Task context scenarios

Concrete situations of [Task context](module.md). Module-wide obligations are stated once in
[requirements](requirements.md).

## Freezing a snapshot

### scenario.harness.context-freeze — Freeze one Module's context for a step

- GIVEN a valid Spec repository and a registered Module
- AND a phase, a task, and optionally a scenario focus, constraints, instructions, stage inputs and workspace facts
- WHEN the host freezes a context snapshot
- THEN it returns an immutable snapshot identified by a digest of its content
- AND the snapshot lists every document of the Module's `SpecContext` with its identity, owner, digest and the relations that selected it, and names the Module's entry
- AND it lists the Module's implementation entries and bound file names for every phase
- AND it includes implementation file paths and digests only for the `implementation` and `code-review` phases
- BUT no document or file body is embedded in it

See [boundary sets](requirements.md#req.context.boundary-sets),
[focus never trims](requirements.md#req.context.focus-no-trim),
[names for every phase](requirements.md#req.context.names-every-phase) and
[contents for code phases](requirements.md#req.context.contents-code-phases).

### scenario.harness.shared-file-readers — A programmer reads the Modules that share its files

- GIVEN Module A binds a file that Module B also binds, and A does not select B's documents
- WHEN the host freezes a snapshot of A for the `implementation` phase
- THEN the snapshot's Spec context also lists both members of every document B owns, each with the relation `shares`, Module B and the shared file
- AND the programmer is granted those documents read-only, and its write paths stay A's implementation scope
- AND a byte change in one of B's documents makes that snapshot stale
- BUT a snapshot of A for any other phase, such as `plan` or `code-review`, lists none of B's documents

See [shared-file readers](requirements.md#req.context.shared-file-readers).

### scenario.harness.external-references — Deliver a Module's external references to the workers that read them

- GIVEN a Module whose entry includes pinned external material, such as the vendored documentation of a library it builds on
- WHEN the host freezes a snapshot for any phase
- THEN the snapshot lists each external inclusion with one digest over its readable files
- AND a worker whose profile reads external references is granted exactly those roots, copied into its capsule
- AND a worker whose profile does not read them sees the entries but receives no copy or grant
- AND a byte change below an entry makes every earlier snapshot of the Module stale, and a missing checkout fails freezing with `invalid_reference`
- AND a host-created candidate receives the primary's reference checkouts without network access
- BUT media and archive files below an entry are neither digested nor copied

### scenario.harness.context-invalid-input — Reject an unsupported phase or a blank task

- GIVEN an unsupported phase or a blank task
- WHEN the host freezes a snapshot
- THEN freezing fails with `invalid_phase` or `invalid_input`
- AND no snapshot is returned

### scenario.harness.context-stale-recheck — Reject reuse after an input changed

- GIVEN a snapshot frozen earlier
- AND since then a selected document, a selecting declaration, an ownership, a Protocol binding or another recorded byte has changed
- WHEN the host rechecks the snapshot
- THEN the recheck fails with `stale_context`
- AND the caller freezes a new snapshot before continuing

See [recheck](requirements.md#req.context.recheck).

### scenario.harness.context-gap — Stop assessment on incomplete collaboration declarations

- GIVEN a selected Module whose own collaboration declarations the Spec Module reports as missing or inconsistent
- WHEN the host prepares a context assessment for that Module
- THEN each missing declaration is reported once as a gap Issue, and the assessment returns `spec_incomplete` with those blockers and the blocked step
- AND a malformed, duplicate, unknown or unrelated declaration returns `conflicting`
- BUT no Agent is launched, and no relationship inventory is added to any snapshot

## Worker profiles and grants

### scenario.harness.agent-bind — Bind a named Agent's worker profile to the current build

- GIVEN a named Agent that declares a worker profile, and a fresh build
- WHEN the host binds the profile
- THEN it returns a reproducible binding with the digests of the instruction source, the rendered instructions, the profile and the build manifest, and the timeout
- AND the bare, hyphenated and `concorde-` prefixed spellings of the name resolve to the same profile
- AND changing the Agent's instructions makes the build stale until it is rebuilt

See [profile consistent](requirements.md#req.context.profile-consistent).

### scenario.harness.agent-bind-reject — Reject an unknown Agent or an inconsistent profile

- GIVEN an unknown Agent name, a stale build, missing rendered instructions, or a profile inconsistent with its contract or workspace kind
- WHEN the host resolves or binds the profile
- THEN it fails with `unknown_agent`, `stale_build` or `invalid_agent_binding`
- BUT a profile that names a delegation tool or child Agents is refused, because every worker is a terminal leaf

### scenario.context.contract-checks — A worker's input and result must match its profile

- GIVEN an Agent's worker profile and a snapshot frozen for it
- WHEN the host admits the worker's typed input and later its result
- THEN a mismatched phase or context type, an unadmitted or missing required stage input, implementation files for a profile without implementation reads, or a Spec review input that carries code changes is refused before launch
- AND a result with an outcome or a filled field the profile does not permit is refused, with `permission_denied` for fields it may not author and `invalid_completion` otherwise
- BUT a planner and a reviewer of the same Module receive different snapshots and share no stage inputs or write grant

These checks use only the profile and the typed values, never the prompt text. Native result
acceptance applies the result check; the input check is applied by the optional StateGraph
Operation, while native preparation relies on freezing the snapshot for the profile, which applies
the same stage input rules.

