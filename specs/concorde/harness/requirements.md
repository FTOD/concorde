# Harness requirements

These precise specifications belong directly to the [Harness Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term                                    | Meaning / definition                           |
| --------------------------------------- | ---------------------------------------------- |
| [Worker](../module.md#terminology)      | Defined in Concorde Framework.                 |
| [Worker profile](module.md#terminology) | Defined in Harness.                            |
| [Context](../module.md#terminology)     | Defined in Concorde Framework.                 |
| [Grant](../module.md#terminology)       | Defined in Concorde Framework.                 |
| [Snapshot](../module.md#terminology)    | Defined in Concorde Framework.                 |
| [Host](../module.md#terminology)        | Defined in Concorde Framework.                 |
| [Spec context](context.md#terminology)  | Defined in What information a worker receives. |
| [Task context](context.md#terminology)  | Defined in What information a worker receives. |
| [Capsule](module.md#terminology)        | Defined in Harness.                            |
| [Tool gate](module.md#terminology)      | Defined in Harness.                            |
| [Module](../module.md#terminology)      | Defined in Concorde Framework.                 |
| [Entity](../module.md#terminology)      | Defined in Concorde Framework.                 |
| [Scenario](../module.md#terminology)    | Defined in Concorde Framework.                 |
| [Spec](../module.md#terminology)        | Defined in Concorde Framework.                 |
| [Registry](../module.md#terminology)    | Defined in Concorde Framework.                 |
| [Operation](../module.md#terminology)   | Defined in Concorde Framework.                 |
| [Graph](../module.md#terminology)       | Defined in Concorde Framework.                 |
| [Worktree](../module.md#terminology)    | Defined in Concorde Framework.                 |

## Harness

### req.harness.context-closure-nonempty — Non-empty frozen context closure

The frozen context closure SHALL never be empty even when one kind is empty for the phase.

### req.harness.context-focus-no-trim — Scenario focus never trims context

A scenario focus SHALL change only the question resolve_context answers, never the selected
Module's Spec context membership.

### req.harness.context-file-names-every-phase — File names visible to every phase

Every phase SHALL see the names, owning entity and pending status of the selected Module's
entity-bound files.

### req.harness.context-contents-code-phases-only — File contents limited to code phases

Only the implementation and code-review phases SHALL also receive the contents of the selected
Module's entity-bound files.

### req.harness.context-index-and-grant — Spec context is indexed and granted, never embedded

Every launch SHALL deliver the selected Module's Spec context and the Protocol rule bundle as an
index of the included files plus a read-only grant of exactly those files rather than as document
bodies in the invocation input.

The index is the frozen snapshot; the grant names project-relative paths, Spec documents where they
live and the installed Protocol copy under `.concorde/protocol/`, as byte-identical copies in a
capsule or the verified files in place in a project workspace. An agent opens what its task needs, starting from the reading
entry, and is forbidden by its task policy to read outside that grant. For every native Agent,
file/network/credential scope is prompt-level policy, not OS enforcement or proof of exclusive reads.
Actual native terminal tool/delegation ceilings, historical RPC diagnostic sandbox enforcement and
configured-check/tester OS read-only isolation are separate guarantees. The Protocol fixes the selected context;
this index and grant is the Framework's chosen delivery. Task context stays inline: a review's
typed changes carry diffs of the reviewed Module's own files, which add no path to the grant and
replace no granted file. See [Spec context grant](contracts.md#context-spec-context-grant).

### req.harness.context-recheck — Recheck rejects reuse after changes

recheck_context SHALL reject reuse whenever any admitted input has
changed since resolution.

### req.harness.profile-within-contract — A profile never exceeds its contract

A worker profile SHALL never grant a tool that its contract's effects and workspace kind do not
admit.

### req.harness.permission-no-widen — Effective permissions stay within both grants

Effective permissions SHALL be a subset of both the worker contract's declared effects and the
host's invocation grant.

### req.harness.permission-write-scope — Write authority limited to code-writing invocations

Only a code-writing invocation SHALL receive write authority, and only for the files the selected
Module's own entities list.

### req.harness.permission-no-spec-write — No write authority over Spec or registry

A code-writing invocation SHALL NOT gain authority to write Spec documents, entity declarations or
the registry.

### req.harness.permission-no-retry — No retry with a wider grant

No permission failure SHALL be retried with a wider grant.

### req.harness.check-project-read-only — Checks cannot mutate project files

The configured-check executor SHALL enforce project filesystem read-only access in the operating
system for the check and every descendant throughout execution.

### req.harness.check-fail-closed — Unavailable check isolation fails closed

The configured-check executor SHALL refuse execution when its read-only boundary cannot be enforced.

### req.harness.check-scratch — Checks receive independent external scratch space

Every configured check SHALL receive a fresh host-managed writable temporary directory outside the
project, removed after its process tree has terminated.

### req.harness.worker-gate — RPC diagnostic tool calls are gated by the compiled grant

Every tool call of a retained low-level RPC diagnostic/test worker SHALL be checked against the invocation's compiled
grant before it executes.

The gate is a policy boundary inside the Pi process over the model's tool calls; the process itself
is bounded by the worker sandbox ([req.harness.worker-sandbox](#req.harness.worker-sandbox)). See
[execution](execution-reference.md#execution-tool-gate).

### req.harness.worker-sandbox — RPC diagnostic processes run inside the boundary of their grant

Every retained low-level RPC diagnostic/test worker launch SHALL run its Pi process inside the operating-system sandbox derived from the
launch's grant, refusing the launch when that boundary cannot be enforced.

The boundary mounts the host read-only with the developer's secret locations, agent-client state and
other worktrees masked, makes only the write grant and the run directory writable, and gives the
process private temporary storage and namespaces; see
[worker sandbox](execution-reference.md#execution-worker-sandbox).

### req.harness.worker-selection — Each worker runs on its own configured selection

Every worker launch SHALL use the model, thinking level and timeout resolved for that worker from the project operation configuration.

### req.harness.capsule-closed — A capsule grants only its own snapshot

A capsule worker SHALL be granted read access only to its own snapshot and the copies that snapshot
indexes. For all native Agents this is intended read policy, not filesystem enforcement;
no claim of exclusive reads follows from delivery or digest checks.

### req.harness.process-inputs-closed — Worker processes receive only closed inputs

A retained low-level RPC diagnostic/test worker process SHALL receive only the allowlisted environment, its host-built Pi configuration,
its system prompt and its single typed context message.

### req.harness.execute-no-retry — No automatic retry after execution failure

No execution failure SHALL trigger an automatic retry with the same or wider permissions.

### req.harness.execute-exit-insufficient — Settling alone is not completion

A worker that settles without exactly one valid submitted result SHALL NOT be treated as completed.

### req.harness.delegation-one-level — Native workers are terminal leaves

A worker SHALL NOT delegate tasks, create subagents or recursively invoke Operations.

### req.harness.worker-single-result — Only the submitted result leaves the worker

Only a worker's independently admitted single submitted result SHALL become domain completion data.

Native transcripts and diagnostic envelopes may record failed tool attempts without admitting them
as results; separately admitted Issue observations remain distinct from completion.

### req.harness.typed-canonical — Canonical encoding digests identically

canonical(value) SHALL produce sorted-key, compact, ASCII-escaped JSON with no trailing newline,
so identical values always digest identically.

## Operation admission

### req.harness.single-boundary — Every invocation passes through admission

Every operation invocation SHALL pass through the Harness admission boundary, with no direct
agent-to-agent channel bypassing it.

### req.harness.project-root-is-working-directory — Project root is the entry process's working directory

The host SHALL bind every invocation's project root to the working directory of its entry
process, exactly as resolved and without searching parent directories.

The registry, Spec collections and listed implementation files an invocation
reads are therefore those of the worktree at that directory. The worktree in which the
developer's agent session started, the worktree whose Pi entry supplied the catalog
and every other linked worktree are not inputs; see
[invocation worktree binding](scenarios.md#scenario.harness.invocation-worktree-binding).

### req.harness.distinct-outcomes — Results distinguish admission, domain and execution outcomes

An operation result SHALL distinguish admission, domain and execution outcomes instead of collapsing
them into one generic failure.

### req.harness.langgraph-control-flow — Explicit Operation orchestration uses StateGraph

Explicitly selected StateGraph Operations SHALL execute their declared Graph transitions.

Public context assessment, tasks and implementation use direct native Agents; planning, review and
Issue solving use authored native workflows with finite Host checkpoints. None selects a legacy
Graph/Pi-RPC fallback. File scope is prompt-level policy for all native roles, not OS confinement.
Initialization, configuration, validation, delivery and Issue bookkeeping are finite Host services.
The optional Operation/Studio boundary is not a public capability mirror.

[Graphs and feedback](graphs-and-loops.md) explains Graph execution; the term's canonical definition is linked above.

### req.harness.no-implementation-for-non-code — No implementation contents for non-code phases

A planner, task author or Spec-only reviewer SHALL NOT receive the contents of the selected Module's or
any other Module's listed implementation files.

### req.harness.primary-persistence — One durable coordinator authority

The host SHALL persist task status and durable candidate run evidence only in the Git-identified primary worktree with serialized atomic writes and explicit legacy migration.

### req.harness.task-delegation — One fresh task-child layer

A task subagent SHALL remain in its assigned worktree without further task delegation under the outer task-host delegation limits; terminal Operation workers retain their separate file/tool grants.

### req.harness.local-execution — Consumer execution stays worktree-local

Harness SHALL admit consumer execution only with a verified complete worktree-local installation, never a cross-worktree Framework or dependency fallback.

Creation has explicit host bootstrap authority; adoption/resume missing or stale installation stops
for the supported installer. Source-private mode remains separate, without ambient installation.
Installation does not widen worker grants, accept Protocol or duplicate primary status/runs.

### req.harness.diagnostic-spans — Passive bounded timing

Timing diagnostics SHALL preserve actual authority and successful mutation outcomes while recording bounded, redacted, monotonic spans and wall timestamps with explicit unknown or incomplete observations.

The common record distinguishes outer sessions, runtime work and test execution; no span is a
workflow grant. No network telemetry, credentials, environment values, raw prompts, source bodies,
tool output or arbitrary command arguments are recorded. Concurrent/nested spans cannot be summed
as elapsed wall time; outside-tools and roundtrip time are not server thinking time. Existing
primary-only durable Operation persistence and private diagnostics remain unchanged.
