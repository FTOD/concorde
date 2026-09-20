# Harness scenarios

These precise specifications belong directly to the [Harness Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term                                              | Meaning / definition                           |
| ------------------------------------------------- | ---------------------------------------------- |
| [Worker](../module.md#terminology)                | Defined in Concorde Framework.                 |
| [Worker profile](module.md#terminology)           | Defined in Harness.                            |
| [Context](../module.md#terminology)               | Defined in Concorde Framework.                 |
| [Grant](../module.md#terminology)                 | Defined in Concorde Framework.                 |
| [Snapshot](../module.md#terminology)              | Defined in Concorde Framework.                 |
| [Host](../module.md#terminology)                  | Defined in Concorde Framework.                 |
| [Graph](../module.md#terminology)                 | Defined in Concorde Framework.                 |
| [Operation](../module.md#terminology)             | Defined in Concorde Framework.                 |
| [Spec context](context.md#terminology)            | Defined in What information a worker receives. |
| [Task context](context.md#terminology)            | Defined in What information a worker receives. |
| [Capsule](module.md#terminology)                  | Defined in Harness.                            |
| [Tool gate](module.md#terminology)                | Defined in Harness.                            |
| [Candidate](../module.md#terminology)             | Defined in Concorde Framework.                 |
| [Worktree](../module.md#terminology)              | Defined in Concorde Framework.                 |
| [Protocol binding](../spec/values.md#terminology) | Defined in Identities and versions.            |
| [Entity](../module.md#terminology)                | Defined in Concorde Framework.                 |
| [Reference](../spec/registry.md#terminology)      | Defined in Registry.                           |
| [Pi integration](../module.md#terminology)        | Defined in Concorde Framework.                 |
| [Spec](../module.md#terminology)                  | Defined in Concorde Framework.                 |
| [Issue](../module.md#terminology)                 | Defined in Concorde Framework.                 |

## Harness

### scenario.harness.graph-inspection — Inspect execution without acquiring authority

- GIVEN the executable Graph factories and host-bound public Studio entries
- WHEN a viewer compiles them and requests their LangGraph nodes and edges
- THEN it sees the actual admission, operation branches and composed Graph transitions without invoking an Agent or resolving project Spec contexts
- AND private stages gain no public entry or additional permissions
- AND the public checkpoint contains only JSON input and output while internal host objects and callbacks remain ephemeral
- AND replay of the public operation revalidates the input and expected workspace before any effects

### scenario.harness.context-freeze — Freeze one Module's context for a bounded phase

- GIVEN a fresh, successfully admitted Spec repository and a registered Module target_id
- AND a phase, a task, and optional focus_id, constraints, instructions, stage_inputs and workspace
- WHEN resolve_context is called
- THEN the host returns an immutable concorde-context-snapshot identified by a content digest
- AND the snapshot always indexes the Module's complete Spec context, every document with its identity, owner, digest, inclusion reasons and the reading entry, and carries its task context
- AND a launch under that snapshot grants the indexed documents and the Protocol files read-only at their paths, as byte-identical copies in a capsule, instead of embedding their bodies
- AND the snapshot includes implementation file contents only when the phase is implementation or code-review

See [the non-empty closure bound](requirements.md#req.harness.context-closure-nonempty),
[the focus bound](requirements.md#req.harness.context-focus-no-trim) and
[index and grant](requirements.md#req.harness.context-index-and-grant). File visibility follows a fixed per-phase
rule: see [names for every phase](requirements.md#req.harness.context-file-names-every-phase) and
[contents for code phases only](requirements.md#req.harness.context-contents-code-phases-only).

### scenario.harness.external-references — Grant a Module's external references to the workers that read them

- GIVEN a Module whose registration declares `references` of kind `external`, such as the vendored documentation and source of a library it builds on
- WHEN the host resolves a context for any phase
- THEN the snapshot lists each external reference with one digest over its readable files, and a launch of a worker whose contract declares the `references` effect grants exactly those entries read-only, copied as the same readable files into the capsule when the worker runs in one
- AND a worker without that effect, such as the spec reviewer or context assessor, sees the entries but receives no grant
- AND a change to an entry's readable bytes makes every admitted snapshot of the Module stale, while a missing entry fails resolution
- AND a host-created candidate worktree receives the primary worktree's reference checkouts without network access
- BUT no phase receives network access or an installed dependency's sources in place of the declared references, and media and archives below an entry are neither digested nor copied

### scenario.harness.agent-node — Run a worker as a LangGraph node typed by its contract

- GIVEN a canonical worker definition and its task contract
- WHEN the host binds it as an OperationNode and executes an invocation through its compiled Graph
- THEN the node's input schema is exactly the top-level fields of the contract's admitted context type and its output schema exactly those of the contract's result type
- AND the node revalidates the admitted context before the launch and the returned data against the result type after it, so the launcher can neither admit an unexpected context nor return an unexpected result
- AND the same factory compiled without a launcher is inspectable inside the Graphs that run it and starts no process
- BUT the Pi worker launch, its admission checks and usage recording stay in the host's launcher, outside the graph's public state

### scenario.harness.context-invalid-input — Reject an unsupported phase or a blank task

- GIVEN an unsupported phase value or a blank task string
- WHEN resolve_context is called
- THEN the call raises SpecError with code invalid_phase or invalid_input
- AND no partial or reusable snapshot is returned

### scenario.harness.context-stale-recheck — Reject reuse after an admitted input changed

- GIVEN a previously resolved context snapshot
- AND a document, ownership, reference declaration, inclusion reason, Protocol binding or other admitted byte has since changed
- WHEN recheck_context is called with that snapshot
- THEN the call raises SpecError with code stale_context
- AND the caller must resolve a fresh snapshot before continuing

See [the changed-input recheck bound](requirements.md#req.harness.context-recheck).

### scenario.harness.context-gap — Report a missing local dependency promise as a Spec gap

- GIVEN a selected Module whose local dependency metadata entries do not match its registered uses and parent relationships
- WHEN the host compares them before launching the context assessor for that Module
- THEN a missing direct entry yields a Module-owned structured Spec gap, and a malformed, duplicate, unknown or unrelated entry yields a conflicting outcome
- AND planning stops only for the dependent step while independent reasoning continues
- BUT no relationship inventory is injected into the worker snapshot when this comparison stops planning

### scenario.harness.agent-bind — Bind a named worker's Spec and terminal profile

- GIVEN a named worker registered in the Operation inventory and a current, fresh build
- WHEN resolve_worker is called for that name
- THEN the host returns a reproducible WorkerBinding covering spec_digest, instructions_digest, profile_digest, build_manifest_digest and timeout_seconds
- AND worker_profile resolves that same name, its hyphenated spelling or its concorde- external name to the Operation's model execution profile
- AND resolve_worker verifies the binding against the current build before returning it

See [the profile-within-contract bound](requirements.md#req.harness.profile-within-contract).

### scenario.harness.agent-bind-reject — Reject an unknown worker or a stale or inconsistent build

- GIVEN an unregistered worker name, a stale package build, a profile inconsistent with its contract or workspace, or a profile requesting a retired delegation tool or child catalog
- WHEN worker_profile or resolve_worker is called
- THEN the call raises BuildError with code unknown_agent, stale_build or invalid_agent_binding
- AND no invocation starts from an unverified binding

### scenario.harness.permission-compile — Compile an effective policy within declared and host authority

- GIVEN a worker contract's EffectDeclaration, a host-supplied narrowing PolicyBinding and concrete role paths
- WHEN compile_policy is called
- THEN the host returns a digest-bound NormalizedPolicy whose reads, writes, network and credentials are each a subset of both the declaration and the binding
- AND the worker executor hands exactly its read and write paths to the worker's tool gate

See [the declared-and-granted subset bound](requirements.md#req.harness.permission-no-widen), [write authority
scoped to code-writing invocations](requirements.md#req.harness.permission-write-scope) and [no write authority
over Spec or the registry](requirements.md#req.harness.permission-no-spec-write).

### scenario.harness.permission-reject — Reject unknown roles, unsafe paths or widened grants

- GIVEN an unknown or duplicate role, an unsafe path, a widened read, write, network or credential effect, or an invocation granting writes, network or credentials its worker contract does not declare
- WHEN compile_policy is called or the worker executor admits the invocation
- THEN the call raises PermissionPolicyError or OperationExecutionError before any worker process starts
- AND no failure retries with a more permissive configuration

See [the no-wider-retry bound](requirements.md#req.harness.permission-no-retry).

### scenario.harness.change-owner — Preserve and validate candidate ownership

- GIVEN primary-owned candidate state bound to the current worktree, possibly interrupted before binding its explicit initial target
- WHEN the host reads, restores or binds its owner
- THEN an unbound owner remains distinct from an absent or malformed record, and persisted change, path, branch, owner and intent fields are validated before use
- AND a requested existing change cannot silently create replacement state in another worktree
- AND schema-1 candidate progress is refused with unsupported_worktree_version without rewriting its bytes or reusing its readiness evidence
- AND missing binding task or target returns a structured invalid_input error instead of a field lookup exception
- AND a retained explicit-target mutation restores omitted focus and constraints for that same owner before selection and rejects conflicting task, focus, constraints or initial target with incompatible_handoff and its field before progress writes
- AND an unknown recorded owner is rejected as invalid_worktree_state rather than used as authority
- AND only separately admitted component work under a current parent plan and matching derived intent may use a distinct component intent without rewriting the root owner
- AND independent read-only reviews keep their explicit intent without replacing root ownership
- AND lifecycle metadata supplies recovery identity but never grants implementation access or waives readiness checks

### scenario.harness.worktree-guidance — Pi-only creation preserves historical ownership

- GIVEN a consumer candidate and any existing user-owned root guidance files
- WHEN the host registers a new Operation change
- THEN it creates or appends its transient block only in `AGENTS.md`, preserving pre-existing bytes and modes, and leaves `CLAUDE.md` untouched
- AND failure to register status rolls back the guidance bytes and modes without claiming successful registration
- AND existing schema-2 status naming a historically owned `CLAUDE.md` block remains admissible with the same change identity, ownership map and created flags
- AND a deliverable snapshot strips only recorded blocks, preserving unrelated bytes and Git file modes, omitting a host-created file only if it becomes empty
- AND ambiguous or modified markers block the snapshot rather than discarding content
- AND snapshot cleanup leaves working files, the caller's index and the status record unchanged

### scenario.harness.worktree-boundary — Require an isolated worktree before unsafe mutation

- GIVEN a project root and an explicit allow_primary_worktree flag
- WHEN require_isolated_worktree is called
- THEN it returns the inspected WorktreeBoundary for a committed linked worktree, or for a committed primary worktree only when the trusted host passes allow_primary_worktree=True
- AND a symlink root, missing directory or unavailable Git identity raises WorktreeBoundaryError instead
- BUT allow_primary_worktree is set only by a trusted host decision, never by task input

### scenario.harness.execute-success — Execute a bound worker and accept its typed result

- GIVEN a host-built WorkerInvocation carrying a verified WorkerBinding, frozen context, compiled policy and model selection
- WHEN WorkerExecutor is called with it
- THEN its preflight reverifies the binding against the current build, the instructions against the rendered worker and its indexed Protocol files, and the context and policy against the worker contract before starting any process
- AND it launches one Pi worker with the profile's tools, the policy's grants and the contract's result schema narrowed to the profile's authored-field permissions as submit_result's parameters
- AND it returns a WorkerOutcome bound to the invocation and binding digests only for a single submitted result that satisfies the result type and the contract

See [the no-automatic-retry bound](requirements.md#req.harness.execute-no-retry) and [the
settling-is-not-completion bound](requirements.md#req.harness.execute-exit-insufficient).

### scenario.harness.execute-failure — Distinguish failed, cancelled, limit-exhausted and invalid outcomes

- GIVEN a refused preflight or a Pi process that fails before settling, a host interrupt, a run past its timeout, or a run whose submitted result is missing, repeated or outside the contract
- WHEN WorkerExecutor is called
- THEN it raises OperationExecutionError with outcome failed, cancelled, limit_exhausted or invalid_completion respectively
- AND a contract rejection keeps its code, permission_denied for disallowed authored fields
- AND the caller stops the affected transition rather than retrying automatically

### scenario.harness.worker-contract — A worker runs only its own task contract

- GIVEN the seven catalog workers and an explicitly selected Module
- WHEN the host binds a worker and the executor admits its launch and its result
- THEN only the common worker rules, that worker's role Spec and the Protocol rule bundle form its system prompt
- AND a mismatched phase, context or result type, unadmitted or missing required stage artifacts, implementation contents for a worker without implementation reads and a policy wider than the contract are rejected before a process starts
- AND the submission tool omits unauthorized optional authored fields and constrains required unauthorized compatibility fields to their empty values, without changing authorized fields or the shared wire type
- AND an unauthorized tool submission is rejected without ending the run, so a corrected submission can succeed within the same invocation and unchanged deadline
- AND a result with an outcome or a populated field its contract does not permit is independently rejected by the host, disallowed authored fields as permission_denied
- AND a planner and a reviewer of the same Module have different invocation and context identities with no shared conversation, stage artifacts or write grant

### scenario.harness.usage-accounting — Record what every worker launch consumed, per step

- GIVEN a Pi worker that settled and reported its session statistics
- WHEN the host accepts the WorkerOutcome of a stage or review launch
- THEN the outcome carries an ExecutionUsage record with the reported input, cached and output tokens, cost and turns, the configured model and thinking level, the host-measured wall time and the prompt and context sizes
- AND the host appends one schema-2 JSON line labelled with the operation, stage, target, worker, change and launch identity to `.concorde/runs/<root invocation>/usage.jsonl`, where the root invocation is the top-level operation invocation of the whole Graph run
- AND the host observer receives the same record as an `agent_usage` event, and the `usage` Tool and the executable boundary summarize those lines per step, stage, target and worker
- AND historical unversioned usage retains its original step labels and is counted explicitly without rewriting its bytes
- AND unsupported record formats are excluded from totals and reported in an explicitly incomplete schema-2 summary
- BUT a figure Pi did not report is recorded as unknown rather than zero, and a persistence failure never fails the launch

### scenario.harness.worker-selection — Launch each terminal worker on its configured model

- GIVEN operation configuration with default model, thinking and timeout and per-worker overrides
- WHEN the host binds a worker invocation
- THEN each value comes from the worker entry, else the default, with absent timeout falling back to its profile
- AND Pi receives model and thinking flags and the selected deadline
- AND selection is part of invocation identity and policy preview
- BUT no child selection is supported and absent model/thinking retain Pi defaults

See [worker selection](requirements.md#req.harness.worker-selection).

### scenario.harness.worker-selection-reject — Reject a selection no worker can run

- GIVEN an operation configuration whose `workers` map names an unknown worker or any worker-child key, a nonpositive timeout, a model that is not a Pi `provider/id` or an unknown thinking level
- WHEN the configuration is proposed, applied or loaded
- THEN it is rejected with a typed field error naming the offending entry
- AND a rejected proposal or application leaves the stored configuration unchanged

### scenario.harness.typed-validate — Validate a named registered wire type or contract schema

- GIVEN a type_id registered in the wire schema catalog and a candidate value
- WHEN validate_typed or typed is called
- THEN it returns a deep-copied, schema-checked value for a conforming input
- AND json_schema and schema.admit export or admit only the supported offline JSON Schema subset with local $defs references
- AND schema admission and validation resolve no remote reference and grant no fallback authority

See [the canonical-encoding bound](requirements.md#req.harness.typed-canonical).

### scenario.harness.typed-reject — Reject unknown types, duplicate keys or unsafe paths

- GIVEN an unknown or unsupported type or version, duplicate JSON object keys, a non-finite numeric constant, or a path outside the safe project-relative form
- WHEN decode, validate_typed, safe_path or checked_path is called
- THEN it raises TypedDataError with a stable code and a JSON-pointer field identifying the problem
- AND the caller stops the affected transition rather than substituting a default

## Native Agent acceptance

### scenario.harness.native-result-gate — Native submission is a proposal, not completion

- GIVEN a native Pi Agent with a Host-issued invocation identity and proposal location
- WHEN it submits its bounded result and a native post-run gate validates that proposal
- THEN submission and gate success change no task-completion state, and the gate checks exact proposal bytes, schema, business identity and current inputs before returning a staged, explicitly unaccepted control value
- AND a separate Host finalization checks independently correlated native execution evidence and current proposal inputs before trusted persistence
- AND missing, malformed, oversized, foreign, aliased or changed proposals cannot be accepted
- AND a duplicate accepted finalization rechecks current inputs without repeating persistence, while failed or uncertain persistence requires fresh admission or explicit provider recovery
- AND cancellation or failed child execution revokes unsettled acceptance without promising rollback of implementation edits; cancellation after durable commit does not erase committed domain evidence
- AND the bounded typed control result is rejected rather than truncated; proposal digests and post-run checks do not establish exclusive reads or preventative filesystem confinement

### scenario.harness.native-terminal-evidence — Reconcile terminal children before domain commit

- GIVEN a Host-bound native workflow run and session with issued child keys, Agent identities, proposal digests and exact gate commands
- WHEN finalization reads the native async status and independently published child metadata before the enclosing workflow receipt exists
- THEN it requires exact nonempty child coverage, matching workflow/run/Agent/proposal identities, completed child status, successful native exit and the matching verified staging gate
- AND failed native execution cannot be overridden by a passing gate or an emitted success boolean
- AND incomplete, missing, foreign, duplicated, cancelled or stale evidence blocks acceptance without inventing coverage
- AND a scope of forty children needs no per-child Host command or artificial thirty-two-review limit
- AND these files establish cooperative runtime provenance, not protection against an arbitrary same-user process tampering with native artifacts

## Agent execution

### scenario.harness.check-read-only — Project mutation is denied during execution

- GIVEN a configured command with project read access
- WHEN it or a descendant attempts creation, modification, deletion, rename or modification followed by restoration
- THEN the operating system rejects the operation before project bytes or directory entries change
- AND alternative pathnames, inherited descriptors and nested namespace remounts cannot grant project writes

### scenario.harness.check-scratch — Each check can read inputs and write disposable output

- GIVEN an admitted command and an available external temporary directory
- WHEN the host executes the check
- THEN project reads and writes to the issued temporary and cache/report directories succeed
- AND repeated calls receive separate scratch directories that are removed after execution
- AND an ambient project-local temporary path cannot become a writable project mount
- AND the trusted tester-only private-tmp profile allows an installed fixture Operation and its unchanged terminal Pi sandbox to prepare temporary files and submit a result without making real host temporary storage writable
- AND governing/runtime paths under host /tmp remain read-only at their canonical names, other host-/tmp inputs remain readable through the explicit read-only view, and ordinary configured checks retain their default boundary
- AND private /tmp, fixture, policy and socket data share the command's descendant-cleanup lifetime without runtime-asset staging or a task-selected mount source

### scenario.harness.check-result — Output and exit status are returned only to the host

- GIVEN a check that writes standard output and standard error and exits with a specified code
- WHEN its isolated execution finishes
- THEN the executor returns both byte streams and that exit code without exposing a project log descriptor
- AND large output on both pipes is drained without blocking command completion

### scenario.harness.check-unavailable — Unsupported enforcement prevents execution

- GIVEN an unsupported OS, missing sandbox backend or a real sandbox setup failure
- WHEN the host requests a configured check
- THEN execution fails closed with CheckSandboxError and host-only diagnostics
- AND no ordinary subprocess fallback runs the configured command

### scenario.harness.check-lifetime — Descendants cannot outlive their check

- GIVEN a check that spawns detached descendants
- WHEN the initial command completes or its deadline expires
- THEN the host terminates every descendant before returning and removes scratch afterward
- AND a timeout preserves partial output with timeout status instead of successful evidence

### scenario.harness.pi-rpc-client — Read one Pi RPC run to settlement

- GIVEN a process speaking Pi's RPC protocol
- WHEN the host runs one prompt through run_prompt
- THEN records are split on line feed only, so U+2028 and U+2029 inside a JSON string stay inside it, and a trailing carriage return is dropped
- AND every extension dialog is answered as cancelled, every tool result is collected, and the session statistics are read after agent_settled
- BUT a process that closes its output before settling raises PiRpcError, and a run past its deadline is killed and raises PiRpcTimeout

### scenario.harness.pi-worker-launch — Launch a Pi worker and admit its single result

- GIVEN a consistent worker launch with a workspace, grants, tools, a system prompt, a message, a result schema and a Pi model
- WHEN PiWorkerRuntime runs it
- THEN Pi starts in RPC mode with ambient discovery disabled, the host-rendered system prompt as the complete system prompt and submit_result advertised with exactly the launch's result schema
- AND the returned value is the details of the single successful submit_result call, with usage from Pi's session statistics
- AND a run_checks call is answered by the host's check callback
- BUT a run without a submission fails with invalid_completion, a run past its deadline fails with limit_exhausted, and an inconsistent launch is refused before any process starts

### scenario.harness.pi-worker-gate — Refuse tool calls outside the worker's grant

- GIVEN a running Pi worker with read and write grants and a tool list
- WHEN its model reads, searches or writes a path outside the grants, or calls a tool it was not granted
- THEN the Concorde worker extension refuses the call with an error result naming the policy and the file is neither read nor changed
- AND calls inside the grants execute normally
- AND a bash command runs with the provider credential variables unset

### scenario.harness.worker-sandbox — Confine the worker process to its grant

- GIVEN a launch with a workspace, write entries including a pending file and a pending directory, and a run directory
- WHEN the runtime derives the mount plan and starts the Pi process inside it
- THEN the process can write exactly the write entries, the pending placeholders and its run directory, while the rest of the workspace and the host filesystem are read-only
- AND the developer's masked secret locations read as empty or absent, other worktrees of the repository are absent while its shared Git directory remains readable, the host's temporary directory is invisible, and the process starts in the workspace with a private HOME and PID namespace
- AND a pending placeholder the worker left empty is removed after the run, while written placeholders stay
- AND a write entry that is a symlink or leaves the workspace is refused before any process starts

### scenario.harness.worker-sandbox-unavailable — An unenforceable boundary refuses the launch

- GIVEN a host without a trusted bubblewrap installation, or a platform other than Linux
- WHEN a worker launch is requested
- THEN the runtime refuses it as `worker sandbox unavailable` before any Pi process starts
- AND no worker ever runs unconfined

### scenario.harness.pi-worker-delegation — Terminal workers reject delegation

- GIVEN a terminal worker with its bounded file/tool grants
- WHEN launched without depth variables or with incomplete, malformed or exhausted legacy depth values
- THEN launch proceeds without consuming or changing outer task-host grants
- AND the Pi catalog contains only the declared non-delegating tools and no ambient Skills, instructions, extensions or child catalogs
- AND requests for subagent tools, recursive Operation tools, child definitions and child selections fail rather than launching another worker
- AND result submission and correction, cancellation, timeouts, file scopes and runtime freshness retain their existing behavior

## Operation admission and Graph execution

### scenario.harness.execute-operation — Successful operation execution

- GIVEN an installed Pi tool names one registered public Operation
- AND stdin carries a well-formed `concorde-operation-invocation@3` envelope in `execute` mode
- WHEN the host admits the request
- THEN it selects the operation's declared execution Graph and obtains every Agent invocation it needs, bound to current instructions, context and compiled authority, from the invocation host
- AND it returns a `concorde-operation-result@3` with status `succeeded` and the operation's own typed output

See [single boundary](requirements.md#req.harness.single-boundary) and [distinct outcomes](requirements.md#req.harness.distinct-outcomes).

### scenario.harness.execute-blocked-launch — Stale build or unenforceable permission blocks launch

- GIVEN the recorded build manifest no longer matches its sources, or the compiled policy for the bound Agent cannot be enforced by the Pi worker extension gate
- WHEN the host would otherwise launch an Agent for an admitted request
- THEN it blocks the request with `stale_build` or the applicable permission error before any process starts
- AND any existing candidate is preserved unchanged

### scenario.harness.describe-policy — Preview an operation's grants without executing it

- GIVEN a request with `mode: describe-policy`
- WHEN the host processes it
- THEN it returns status `described`, naming the bound Agent, Harness, `agent_binding_digest`, `instructions_digest` and effective loop timeout for each previewed stage
- AND no Agent is launched and no project file changes

### scenario.harness.invocation-worktree-binding — An invocation binds to the worktree at its working directory

- GIVEN a public Pi tool submits an invocation through the entry script from some working directory
- WHEN the host admits the request
- THEN it binds the project root to exactly that directory, without searching parent directories
- AND it reads the registry, every Spec collection and the listed implementation files from that worktree alone, while lifecycle status and durable run evidence come only from the Git-identified primary authority
- AND a working directory at a Git worktree root yields workspace kind `primary` or `change`, and a directory outside any Git repository yields kind `unversioned`
- AND a working directory inside a Git worktree that is not its root is refused with `workspace_mismatch` and no Agent is launched
- BUT the worktree in which the developer's agent session started, the worktree whose Pi entry supplied the catalog and every other linked worktree contribute no project registry, Spec document or implementation file to the invocation; primary lifecycle records remain separate host metadata

See [project root is the entry process's working directory](requirements.md#req.harness.project-root-is-working-directory).

### scenario.harness.workspace-inventory — The inventory joins primary lifecycle state to live worktree identity

- GIVEN the primary worktree and one or more live linked worktrees, some managed by the `.concorde/status/<change_id>.json` and some not
- WHEN an operation invoked in the primary worktree resolves its `workspace` metadata
- THEN `active_worktrees` lists every live linked worktree from Git's worktree inventory with its path, branch, head and lock status
- AND a managed worktree contributes only the change_id, target, task summary, phase, status and outcome recorded in the `.concorde/status/<change_id>.json`, and an unmanaged worktree is reported with status `unmanaged`
- AND authoritative task records persist only in primary `.concorde/status/`, while unmanaged inventory is derived from Git
- BUT no linked worktree's registry, Spec document or implementation file is read, so a candidate's draft Spec edits stay invisible to the primary until they are delivered
- AND an operation invoked in a linked worktree instead sees kind `change` with its own candidate identity and status

### scenario.harness.worktree-relay — Mutating request in the primary worktree runs in a host-created candidate

- GIVEN a mutating operation request in an ordinary consumer project is admitted while the current session's worktree is the primary worktree
- WHEN the host would otherwise start development work there
- THEN it creates a candidate worktree from the committed HEAD, records its change in primary status and runs the same request through the selected candidate launcher, with the candidate's change_id when the request type records one
- AND the invocation returns the candidate launcher's complete result envelope, whose workspace names the candidate, and forwards its policy and usage diagnostics
- AND it does not copy uncommitted primary changes into the candidate, records all durable progress and run evidence only in primary without changing primary source or index, and never moves the originating session
- AND a later request from the primary worktree that names the recorded change_id runs in that candidate again, while a change_id no live candidate records is refused with missing_change
- AND a consumer candidate receives a complete verified local installation from the explicitly invoking package before relay and runs only that local runtime; source candidates instead require their own pre-existing current private build and local environment without ambient installation or rebuilding during relay
- BUT source-primary mutations are refused with fresh_session_required even when a change_id names a candidate; source maintenance instead needs an assigned candidate, a fresh Concorde-catalog-free writer and a separate sibling tester

### scenario.harness.graph-specs — Every Graph Spec equals its compiled Graph

- GIVEN the Graph catalog compiles every executable Graph with inert nodes
- WHEN the Graph Spec check reads every Mermaid flowchart bound with `%% graph: <name>` in the registered Spec documents
- THEN each bound diagram's node identifiers are exactly the compiled nodes including start and end, its edges are exactly the compiled edges, each edge leaving a node with several successors carries its routing condition and each edge leaving a node with one successor carries none, and every executing node's label states its in and out state
- AND each bound diagram's section, in an implementation-role document, states its **State.**, **Nodes.** and **Edges.** parts once each and in that order before the diagram, where State and Edges are nonempty and a code fence's `#` lines do not end the section
- AND its Nodes table between the Nodes and Edges parts lists exactly the compiled nodes other than start and end, each once and in backticks, with the same in and out state as the node's diagram label
- AND the section's heading carries an explicit `{#anchor}` that a module-role document of the same owning Module links to, resolving relative link paths
- AND every compiled Graph has exactly one bound diagram and every bound name is a compiled Graph
- BUT a passing check proves only that the Spec and the executed topology agree, not that the routing is right

### scenario.harness.graph-api-only — Every Graph is built with the Graph API

- GIVEN the Graph catalog compiles every executable Graph with inert nodes
- WHEN the Graph Spec check inspects each compiled Graph and parses every Python file under `src/` and `scripts/` without executing it
- THEN each compiled Graph is a compiled `StateGraph` of LangGraph's Graph API
- AND no file imports LangGraph's Functional API, `langgraph.func` or its `entrypoint` and `task` decorators
- AND a Graph of any other kind, an import of the Functional API and a file that cannot be parsed are each an error finding naming the Graph or the file and line

### scenario.harness.graph-execution — Execute the inspected Graph

- GIVEN an admitted operation request through a local or Studio entry
- WHEN the host executes the request
- THEN the same compiled Graph definitions select its operation branch, Agent stages and feedback transitions
- AND selected assessment, planning, scoped review and Issue verification advance through bounded Graph transitions without automatic authoring or child development
- AND failed admission or a stopping outcome prevents dependent nodes from running
- AND existing task identity, context isolation, review requirements and delivery authorization remain enforced
- AND a change to the Graph that schedules scoped reviews invalidates their recorded input identity

### scenario.harness.graph-bounds — Preserve domain limits across Graph composition

- GIVEN a Graph whose admitted work requires more than LangGraph's default scheduling limit
- WHEN the host executes its bounded batch or Issue-verification transitions
- THEN the configured scheduling allowance permits the admitted sequence to reach its domain completion or limit outcome
- AND exhausting a declared domain limit does not silently restart the Graph or widen its authority

### scenario.harness.operation-state — One executable identity and State boundary

- GIVEN a registered deterministic, model-backed or composed Operation
- WHEN its node is embedded in a LangGraph with a larger parent State
- THEN only declared input channels reach its implementation and only declared output updates leave it
- AND trusted hosts and launchers remain in Runtime context rather than State
- AND a model invocation still validates phase, artifacts, output fields and effective authority
- AND its composition dependencies use the same Operation inventory

### scenario.harness.operation-result-state — Host graph failures remain explicit

- GIVEN a host-backed Operation invoked through its State interface
- WHEN admission or execution returns a blocked or failed operation envelope
- THEN the result channel preserves that envelope and its errors without inventing successful output
- AND its external Pi adapter preserves the existing versioned wire contract

### scenario.harness.primary-status — Stable primary coordination and run records

- GIVEN a primary repository and an assigned candidate with a stable task identity
- WHEN candidate work records progress and execution evidence
- THEN only primary status and runs contain durable records, with candidate provenance
- AND branch rename and candidate deletion do not erase task identity or terminal outcomes
- AND a missing source cannot be recreated as an unversioned persistence authority; a late report uses its previously bound primary archive or fails safely
- AND simultaneous registrations of one explicit change_id in different candidates yield at most one success and never overwrite the winning record
- AND removing and recreating the same path, branch and commit creates a different worktree incarnation, so neither reads nor live inventory inherit the old task
- AND a stale status or target snapshot is rejected without erasing newer blockers, validation or independent progress; a caller rereads before updating
- AND target snapshots, including unsaved new targets, keep their construction-time change and incarnation ownership; missing or mismatched ownership is refused even when target IDs and revisions coincide, while branch rename and current no-op saves remain valid
- AND ordinary-Git merge recording refuses a present replacement source or a different task in the same incarnation before using its HEAD or cleanliness, but can retry from already recorded candidate-commit evidence when the original source is absent

### scenario.harness.status-migration — Explicit safe migration and recovery

- GIVEN legacy worktree, delivery or candidate-run data
- WHEN explicit migration is previewed, accepted, interrupted or retried
- THEN preview changes nothing, collisions preserve both inputs, retries finish identical writes and history remains archived
- AND old readiness is not represented as fresh validation
- AND a merging receipt without verified publication remains blocked with no delivered outcome, with or without local schema-2 state
- AND accepted receipt states merging, cleanup_pending and delivered establish delivery only when Git verifies the recorded publication; unknown states remain blocked
- AND cleanup records actual absence separately from publication, preserves explicit retention for present sources and otherwise stays pending, while an unknown receipt state keeps cleanup unknown
- AND preview generates no incarnation token; accepted local-state migration binds the current worktree incarnation explicitly and preserves the original source bytes
- AND same-ID local state and receipt with contradictory source path, recorded branch or bound task intent fail with migration_conflict before any token, journal or import target creation or source removal
- AND compatible historical source labels can survive a live branch rename and interrupted retry without losing original bytes; disagreeing legacy labels require explicit repair rather than identity inferred from the current checkout

### scenario.harness.local-installation — Complete independent candidate execution

- GIVEN a consumer primary whose installed Framework and runtime are ignored by Git
- WHEN the host creates a candidate for an admitted Operation
- THEN the supported installer supplies its complete local Pi entry/catalog, Framework, dependencies, interpreter and receipt before local execution
- AND later relay verifies/reuses its package identity without reprovisioning or rewriting receipt/marker bytes
- AND its local Pi session tool can invoke Operations directly, including programmer and read-only review under unchanged grants and other-worktree masks
- AND durable status/runs stay primary-owned with candidate-local runtime provenance, while source-private candidates receive no ambient installation

### scenario.harness.local-installation-failure — Installation failure retains recoverable work

- GIVEN a missing, stale, conflicting or failed candidate installation, or an installed entry from another project
- WHEN relay or installed local admission attempts execution
- THEN it fails clearly before a worker without primary/global fallback or widened sandbox authority
- AND a newly created candidate survives failed bootstrap with primary blocked installation status and its original owner/task intent
- AND explicit supported installer recovery followed by retry reuses the same change, while conflicting owned bytes remain protected

### scenario.harness.diagnostic-spans — Bounded timing does not change execution

- GIVEN nested or concurrent runtime work, standalone installation diagnostics or a failing telemetry sink
- WHEN common spans observe success, error, cancellation or incomplete work
- THEN records retain monotonic duration, wall timestamp, span/parent/process identity and available host identities without raw prompts, source, tool output, environment values or arbitrary argv
- AND missing counts remain unknown, bounded overflow is explicit and telemetry failure cannot change successful mutation or cause a retry
- AND analysis uses per-process interval unions and distinguishes summed nested work from elapsed wall time
- AND durable Operation traces use existing primary authority while standalone diagnostics create no execution authority

### scenario.harness.outer-observation — Observe direct sessions without Operation authority

- GIVEN a main, maintenance-worker or tester session with explicit passive observation and native Pi events
- WHEN the session resumes, makes model requests, calls tools, waits for a supervisor or compacts
- THEN native custom entries record measured intervals and observed capacity/current usage/cache/reserve/compaction with unknown fields preserved
- AND no Operation, child, tool, prompt change, settings change or network telemetry is introduced by observation
- AND native lineage and bounded main-supplied handoff/test reasons remain diagnostic facts rather than delegation or primary persistence grants
- AND request roundtrip and outside-tools intervals are not claimed as server thinking time
