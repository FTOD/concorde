# Harness scenarios

These precise specifications belong directly to the [Harness Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Harness

### scenario.harness.flow-inspection — Inspect execution without acquiring authority

- GIVEN the executable Flow factories and host-bound public Studio entries
- WHEN a viewer compiles them and requests their LangGraph nodes and edges
- THEN it sees the actual admission, capability branches and composed Flow transitions without invoking an Agent or resolving project Spec contexts
- AND private stages gain no public entry or additional permissions
- AND the public checkpoint contains only JSON input and output while internal host objects and callbacks remain ephemeral
- AND replay of the public capability revalidates the input and expected workspace before any effects

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
- AND a worker without that effect, such as the spec author, spec reviewer or context assessor, sees the entries but receives no grant
- AND a change to an entry's readable bytes makes every admitted snapshot of the Module stale, while a missing entry fails resolution
- AND a host-created candidate worktree receives the primary worktree's reference checkouts without network access
- BUT no phase receives network access or an installed dependency's sources in place of the declared references, and media and archives below an entry are neither digested nor copied

### scenario.harness.agent-node — Run a worker as a LangGraph node typed by its contract

- GIVEN a canonical worker definition and its task contract
- WHEN the host binds it as an CapabilityNode and executes an invocation through its compiled Flow
- THEN the node's input schema is exactly the top-level fields of the contract's admitted context type and its output schema exactly those of the contract's result type
- AND the node revalidates the admitted context before the launch and the returned data against the result type after it, so the launcher can neither admit an unexpected context nor return an unexpected result
- AND the same factory compiled without a launcher is inspectable inside the Flows that run it and starts no process
- BUT the Pi worker launch, its admission checks and usage recording stay in the host's launcher, outside the graph's public state

### scenario.harness.context-invalid-input — Reject an unsupported phase or a blank task

- GIVEN an unsupported phase value or a blank task string
- WHEN resolve_context is called
- THEN the call raises SpecError with code invalid_phase or invalid_input
- AND no partial or reusable snapshot is returned

### scenario.harness.context-stale-recheck — Reject reuse after an admitted input changed

- GIVEN a previously resolved context snapshot
- AND a document, ownership, reference declaration, inclusion reason, Protocol binding or other admitted byte has since changed
- WHEN recheck_context or recheck_discovery_context is called with that snapshot
- THEN the call raises SpecError with code stale_context
- AND the caller must resolve a fresh snapshot before continuing

See [the changed-input recheck bound](requirements.md#req.harness.context-recheck).

### scenario.harness.context-discovery — Assemble several explicit Module contexts for a discovery worker

- GIVEN a nonempty, duplicate-free ordered tuple of registered Module IDs, a capability, a phase of route, and an action of route, ask or design-topology
- WHEN resolve_discovery_context is called
- THEN the host returns a DiscoveryContext whose documents pool indexes the one-level union for every selected Module, deduplicated with ownership and inclusion reasons, and the router, answerer or topology designer launch grants those documents and the Protocol files read-only in its capsule
- AND a focus hint is admitted only when it names a scenario of the target hint's own Module
- AND the returned topology equals the exact registry only for the design-topology action, and is null for every other action

See [the no-recursive-expansion bound](requirements.md#req.harness.context-discovery-no-recurse).

### scenario.harness.context-gap — Report a missing local dependency promise as a Spec gap

- GIVEN a selected Module whose local dependency metadata entries do not match its registered uses and parent relationships
- WHEN the host compares them before launching the context assessor for that Module
- THEN a missing direct entry yields a Module-owned structured Spec gap, and a malformed, duplicate, unknown or unrelated entry yields a conflicting outcome
- AND planning stops only for the dependent step while independent reasoning continues
- BUT no relationship inventory is injected into the worker snapshot when this comparison stops planning

### scenario.harness.agent-bind — Bind a named worker's Spec, profile and children

- GIVEN a named worker registered in the Capability inventory and a current, fresh build
- WHEN resolve_worker is called for that name
- THEN the host returns a reproducible WorkerBinding covering spec_digest, instructions_digest, profile_digest, build_manifest_digest and timeout_seconds, where the profile digest covers every child definition's bytes
- AND worker_profile resolves that same name, its hyphenated spelling or its concorde- external name to the Capability's model execution profile
- AND resolve_worker verifies the binding against the current build before returning it

See [the profile-within-contract bound](requirements.md#req.harness.profile-within-contract).

### scenario.harness.agent-bind-reject — Reject an unknown worker or a stale or inconsistent build

- GIVEN an unregistered worker name, a stale package build, a profile inconsistent with its contract or workspace, or a child definition that is missing, malformed, names a model or thinking level or lists a tool outside the child tool set
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
- THEN the call raises PermissionPolicyError or CapabilityExecutionError before any worker process starts
- AND no failure retries with a more permissive configuration

See [the no-wider-retry bound](requirements.md#req.harness.permission-no-retry).

### scenario.harness.change-owner — Preserve and validate candidate ownership

- GIVEN host-owned candidate state in the current worktree, possibly created before routing
- WHEN the host reads, restores or binds its owner
- THEN an unbound owner remains distinct from an absent or malformed record, and persisted change, path, branch, owner and intent fields are validated before use
- AND a requested existing change cannot silently create replacement state in another worktree
- AND missing binding task or target returns a structured invalid_input error instead of a field lookup exception
- AND binding preserves the recorded task and constraints, while conflicting bound intent is rejected with incompatible_handoff and its field
- AND only a trusted coordinated child may use a distinct component intent without rewriting the root owner
- AND lifecycle metadata supplies recovery identity but never grants implementation access or waives readiness checks

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
- AND it launches one Pi worker with the profile's tools, the policy's grants, the children with their selected models and the contract's result schema as submit_result's parameters
- AND it returns a WorkerOutcome bound to the invocation and binding digests only for a single submitted result that satisfies the result type and the contract

See [the no-automatic-retry bound](requirements.md#req.harness.execute-no-retry) and [the
settling-is-not-completion bound](requirements.md#req.harness.execute-exit-insufficient).

### scenario.harness.execute-failure — Distinguish failed, cancelled, limit-exhausted and invalid outcomes

- GIVEN a refused preflight or a Pi process that fails before settling, a host interrupt, a run past its timeout, or a run whose submitted result is missing, repeated or outside the contract
- WHEN WorkerExecutor is called
- THEN it raises CapabilityExecutionError with outcome failed, cancelled, limit_exhausted or invalid_completion respectively
- AND a contract rejection keeps its code, permission_denied for disallowed authored fields
- AND the caller stops the affected transition rather than retrying automatically

### scenario.harness.worker-contract — A worker runs only its own task contract

- GIVEN the twelve catalog workers and a selected Module or discovery collection
- WHEN the host binds a worker and the executor admits its launch and its result
- THEN only the common worker rules, that worker's role Spec and the Protocol rule bundle form its system prompt
- AND a mismatched phase or action, context or result type, unadmitted or missing required stage artifacts, implementation contents for a worker without implementation reads and a policy wider than the contract are rejected before a process starts
- AND a result with an outcome or a populated field its contract does not permit is rejected, disallowed authored fields as permission_denied
- AND an author and a reviewer of the same Module have different invocation and context identities with no shared conversation, stage artifacts or write grant

### scenario.harness.usage-accounting — Record what every worker launch consumed, per step

- GIVEN a Pi worker that settled and reported its session statistics
- WHEN the host accepts the WorkerOutcome of a stage, review, discovery or topology-author launch
- THEN the outcome carries an ExecutionUsage record with the reported input, cached and output tokens, cost and turns, the configured model and thinking level, the host-measured wall time and the prompt and context sizes
- AND the host appends one JSON line labelled with the capability, stage, target, worker, change and launch identity to `.concorde/runs/<root invocation>/usage.jsonl`, where the root invocation is the top-level capability invocation of the whole Flow run
- AND the host observer receives the same record as an `agent_usage` event, and the `usage` Tool and the executable boundary summarize those lines per step, stage, target and worker
- BUT a figure Pi did not report is recorded as unknown rather than zero, and a persistence failure never fails the launch

### scenario.harness.worker-selection — Launch each worker and child on its configured model

- GIVEN `.concorde/config.json` capability configuration naming a default `model`, `thinking` and `timeout_seconds` and, under `workers`, entries keyed by a worker such as `programmer` or by a worker child such as `programmer/scout`
- WHEN the host binds any worker invocation
- THEN the worker's model and thinking level come from its worker entry, else the default, and each child's from its child entry, else its worker's entry, else the default
- AND the worker's timeout comes from its worker entry, else the default, else its profile
- AND Pi receives the worker's model as `--model` and its thinking level as `--thinking`, and each child definition receives its own as frontmatter
- AND the selection is part of the invocation digest, and a describe-policy run reports it for every worker it describes
- BUT an absent model or thinking level keeps Pi's own default

See [each worker runs on its own configured selection](requirements.md#req.harness.worker-selection).

### scenario.harness.worker-selection-reject — Reject a selection no worker can run

- GIVEN a capability configuration whose `workers` map has a key naming no worker or worker child, a child entry with a timeout, a nonpositive timeout, a model that is not a Pi `provider/id` or an unknown thinking level
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

### scenario.harness.pi-worker-delegation — Delegate one level to declared children under the same gate

- GIVEN a Pi worker that declares a child agent and child tools
- WHEN its model delegates a task to that child
- THEN pi-subagents runs the child as a foreground session that loads the Concorde worker extension and has exactly the child tools
- AND the gate refuses the child's calls outside the worker's grants, and the child cannot delegate or submit a result
- AND delegation to an agent the worker did not declare is refused
- BUT only the worker's own submitted result leaves the process
