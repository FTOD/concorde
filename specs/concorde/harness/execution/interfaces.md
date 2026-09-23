# Agent execution interfaces

The exact records, limits and rules behind the [entry](module.md). The obligations they serve are
in [requirements](requirements.md); situations are in [scenarios](scenarios.md).

## Agent call preparation

A provider's Host service prepares each Agent call in a directory owned by that call, outside any
worktree. The shared services below expect it to contain:

| Item | Content |
| --- | --- |
| `descriptor.json` | The call's bound inputs: operation, phase, Agent, invocation ticket, project and package roots, frozen context snapshot, digests of every delivered file, of the registry, of the Agent instructions and of the candidate, the admitted pi-subagents binding and the parent session identity |
| `descriptor.digest` | The digest of `descriptor.json`; every Host step receives both and refuses a mismatch |
| `.pi/agents/<agent>.md` | The Agent definition pi-subagents discovers, described below |
| `capture.ts` | A one-line extension that loads `pi/extensions/concorde-native-child.ts` bound to this descriptor |
| `.pi/settings.json` | `{"subagents": {"projectRootResolution": "nearest"}}`, so discovery stays inside the directory |

The Agent definition's front matter sets `tools` to the Agent's tools plus `report_issue` (without
`bash` in the code-review phase), `extensions` to the capture extension, `allowNestedSubagents:
false`, `maxSubagentDepth: 1`, `acceptanceRole` (`writer` for implementation, otherwise
`read-only`), `inheritProjectContext: false`, `inheritGlobalContext: false`, `inheritSkills:
false`, `defaultContext: "fresh"`, `async: false`, `timeoutMs` from the model selection,
`systemPromptMode: "replace"` and, when selected, `model` and `thinking`. Its body is the Agent's
rendered instructions. The digests of the Agent file, the capture extension and the settings file
are bound in the descriptor before launch.

The returned `call` selects project-scope Agent discovery, the call directory as its working
directory, one `outputSchema` whose `invocation_id` is fixed to the issued ticket, and one plain
gate command that runs the Host step `stage`.

## Native preflight

`nativePreflight(root, call)` in `pi/native-preflight.ts` calls pi-subagents'
`resolveSubagentLaunchContract` and throws unless the resolved contract has:

- an Agent of source `project` whose file is exactly `<cwd>/.pi/agents/<agent>.md`;
- ambient extensions disabled and no fan-out authorization;
- an effective tool allowlist inside `read`, `grep`, `find`, `ls`, `report_issue` and
  `structured_output`, plus `edit`, `write`, `bash` and `run_checks` for `concorde-programmer` and
  `run_checks` for `concorde-code-reviewer`;
- context `fresh`, no inherited project or global context, no inherited or resolved Skills and no
  active intercom bridge.

A failed preflight is reported with layer `native-preflight` and category `host-refusal`.

## Host step transport

`nativeCommand(binding, action, value)` in `pi/extensions/concorde-native-child.ts` runs the bound
command (`<python> scripts/run-operation.py --native-context`) with `action`, the descriptor path
and its digest as arguments, the call's project root as working directory and `value` as JSON on
standard input. It resolves with the one JSON document printed on standard output.

| Limit or outcome | Rule |
| --- | --- |
| Deadline | 30 seconds; for `checks`, the time the provider computed from the configured check limits |
| Output bound | 2 MiB each on standard output and standard error; more kills the command |
| Failure categories | `timeout`, `cancelled`, `observation` (output bound), `host-refusal` (a rejected response with errors), `native-exit`, `transport` |
| Rejection | a response with `state: "rejected"` or a nonzero exit is a failure, never a result |

The capture extension registers `report_issue` (Host action `report`) and, when the Agent has
`run_checks`, that tool (Host action `checks`). A rejected report is a failed tool call.

## Proposal capture

`observeNativeProposal` in `pi/native-proposal.ts` listens to Pi's `tool_result` and
`tool_execution_end` events for `structured_output`:

- the first successful call's `input.value` must be a JSON object and is sent to Host action
  `submit`; a Host refusal sends `invalidate` and returns a failed tool result;
- any later successful call is refused as a duplicate and invalidates the call;
- a call pi-subagents rejected against the output schema is reported to Host action
  `observe-error` with category `schema-rejection`, does not invalidate the call, and can be
  corrected; the notification is cached so a repeated event is not persisted twice.

## Result gate

The result gate of one Agent call is a set of Host actions over files in the call's directory. They
are run by the shared native Host step driver (`scripts/run-operation.py --native-context <action>
<descriptor> <digest>`); each action first re-admits the original request and checks the
descriptor digest, so a changed descriptor, configuration or runtime selection is refused.

| Action | Behaviour |
| --- | --- |
| `check` | Run by the session extension before launch; confirms the call is still admissible and returns `state: prepared` |
| `submit` | Refuses more than 1 MiB; creates `proposal.json` exclusively in canonical JSON; validates it (below); on any failure records the cause and creates the marker `invalid`; returns `state: proposed`, `accepted: false` |
| `invalidate` | Records the reason and creates `invalid`; any later `stage` or `accept` fails with the recorded cause |
| `observe-error` | Records a schema rejection the Agent may still correct; does not invalidate |
| `stage` | Revalidates the proposal and prints the staging control document |
| `accept` | Revalidates the proposal, re-admits the pi-subagents installation, verifies the single run (see below), requires the reported gate command to be exactly this call's `stage` command, reserves `terminal.json` exclusively, calls the provider's acceptance for the phase, archives the descriptor, proposal, native metadata and correlation in `.concorde/runs/<invocation>/native-context.json` of the primary worktree, and records the terminal outcome |

**Validating a proposal.** The proposal is exactly `{invocation_id, result}` with the issued ticket;
its stored bytes equal their canonical form and are at most 1 MiB; `result` satisfies the Agent's
result type and the fields its profile may populate; the stage identity matches the frozen context
(review results are checked by Review's own validator); every Issue it cites was admitted by this
call's reporter; and the phase's own predicate holds (a nonempty plan, valid tasks, a valid
implementation result). A missing proposal fails as `no-submission`; an invalidated call fails
with its recorded causes.

**Reservation.** Because `terminal.json` is created exclusively before the provider's acceptance
runs, a repeated or concurrent `accept` cannot apply the acceptance twice; after an uncertain
failure the call needs a new request. One finite command runs at a time per call, under a file
lock in the call directory that is never held across a model run.

**Staging control document.** Canonical JSON with exactly the keys `schema_version` (the integer
`1`), `ticket`, `invocation_id`, `proposal_digest` (`sha256:` and 64 lowercase hex digits),
`state` (`"staged"`) and `accepted` (`false`), at most 8,000 UTF-8 bytes; a larger value is an
error, never truncated. Its reader `staging_control` in `native_result.py` requires one complete
document equal to its canonical form and bound to the expected ticket, identity and digest; mixed
text, duplicate keys or a JSON fragment are refused.

## Native terminal evidence {#native-terminal-evidence}

**Producer admission.** `admit_native_runtime(root)` accepts only an absolute, symlink-free
pi-subagents package root whose `package.json` names `pi-subagents` 0.69.0 and whose files listed
in `pi/native-runtime-contract.json` have exactly the recorded digests. The admitted binding has
format `pi-subagents-0.69.0-versionless-v1` and no artifact version. Every record read below must
carry no `schema_version` or `lifecycleArtifactVersion` field.

**Records.** Each record is read from an absolute, symlink-free path as one JSON object of at most
16 MiB; a missing, oversized or unreadable record fails with `stale_evidence`, never with partial
success.

**Single call** (`verify_native_single`). The Pi extension correlates the `subagent` tool call and
its result from the live session; the verifier then requires: not an error, the same session, mode
`single`, exactly one result row for the expected Agent with exit code 0 and none of `error`,
`detached`, `interrupted`, `stopped`, `terminalOutcome`, `timedOut`, `metadataSaveError`,
`outputSaveError` or `transcriptError`; the row's launch contract digest equal to the one preflight
produced; the structured output file pi-subagents saved equal in digest to the captured proposal;
metadata with the same run, Agent and launch digest, exit code 0 and no error, transcript error or
process signal; an acceptance status `verified` with exactly one gate run whose command is the
issued gate, status `passed`, exit code 0, no structured output, and whose standard output is a
valid staging control document for this proposal.

**Workflow** (`verify_native_children`). Given the Workflow's async directory, run identity,
session identity, ticket and the issued children, it reads `status.json` and requires mode
`workflow`, the same run and session, state `running` or `complete`, and no stop, timeout, error or
terminal outcome. Every step with a `workflowKey` and every emission of kind
`concorde.child-terminal` carrying the ticket must cover exactly the issued keys, once each. For
each child: the step's parent run is the Workflow, its Agent matches, its status is `completed`
with no error, stop or timeout, and its run identity equals the emission's; the emission's
invocation identity and proposal digest match; the metadata file the emission names has the same
run and Agent, exit code 0 and no error; and its single gate satisfies the same rules as for a
single call. The Workflow may still be running when this check passes, because pi-subagents writes
its receipt only after the final Host step.

## Model selection

The project configuration's `operation_configuration.data` may contain `model`, `thinking`,
`timeout_seconds` and `workers`, a map from Agent key (for example `code_reviewer`) to an object
with any of the same three fields. `worker_selection(configuration, agent)` returns a
`WorkerSelection(model, thinking, timeout_seconds)` taking each field from the Agent's entry, else
the default. `validate_worker_selections` rejects, with a typed `invalid_field` error at the JSON
pointer of the entry, a key naming no Agent, a `timeout_seconds` that is not positive and a `model`
without a `provider/` part. Thinking levels are `off`, `minimal`, `low`, `medium`, `high`, `xhigh`
and `max`.

## Diagnostic spans

A span has `schema_version` 1, `trace_id`, `span_id`, nullable `parent_id`, `layer` (`A`, `B` or
`C`), `name`, `process_id`, nullable `session_id` and `task_id`, `started_at` (UTC), process-local
monotonic `start_ns`, nullable `duration_ns`, `status` (`ok`, `error`, `cancelled` or
`incomplete`) and `metadata`, which admits only counts (`input_tokens`, `output_tokens`,
`cache_read_tokens`, `cache_write_tokens`, `prompt_bytes`, `context_bytes`, `items`, `returncode`,
`probe_index`) and invocation labels. A trace keeps at most 20,000 spans and counts the rest as
omitted. For an admitted `execute` run whose `run.json` exists, the trace is written once, with
mode 0600, to `.concorde/runs/<invocation>/timing.json`; otherwise it is marked `not-admitted` or
`unavailable` and only reported to the observer. A standalone process may name an existing
directory in `CONCORDE_DIAGNOSTIC_TIMING_DIR` to receive private span files; that directory grants
nothing. Passive Pi observation writes session entries of type `concorde.timing.v1`.

## Graph Spec check {#graph-spec-check}

`graph_spec_findings(repository, catalog)` in `src/concorde/harness/graph_specs.py`, run by
`scripts/development/check-graph-specs.py`, reports:

| Finding | Condition |
| --- | --- |
| `CONCORDE-GRAPH-001` | A bound name that is not a catalog Graph, a Graph with more than one bound diagram, or a catalog Graph with none |
| `CONCORDE-GRAPH-002` | A bound diagram that cannot be parsed as a flowchart |
| `CONCORDE-GRAPH-003` | A diagram whose nodes or edges differ from the compiled ones; an edge declared twice; an unlabelled edge from a node with several successors or a labelled edge from a node with one; a node label that does not start with the node name or lacks `in:` and `out:` |
| `CONCORDE-GRAPH-004` | A catalog entry that is not a compiled `StateGraph` |
| `CONCORDE-GRAPH-005` | A Python file under `src/`, `scripts/`, `operations/` or `agents/` that imports `langgraph.func`, or cannot be parsed |
| `CONCORDE-GRAPH-006` | A section that is not in an implementation document; a missing, repeated or misordered **State.**, **Nodes.** or **Edges.** part; an empty State or Edges part; a missing `Node \| Executes \| in \| out` table between Nodes and Edges; a table that does not list exactly the compiled nodes other than start and end, once each in backticks, with the same `in` and `out` as the diagram label |
| `CONCORDE-GRAPH-007` | A section heading without an explicit `{#anchor}`, or an anchor that no module document of the same Module links to |

A diagram is bound when a fenced `mermaid` block contains a line `%% graph: <name>`; its section
runs from the nearest heading before it. Fenced code never ends a section. Source files are parsed,
never run; directories named `node_modules`, `__pycache__`, `.venv`, `build` and `dist` and
dot-prefixed entries are skipped.

## Terminal Agent Operation

`OperationNode(name)` resolves `name` to an Agent's worker profile. Its `graph(launcher=None)`
compiles the StateGraph `terminal_agent_operation` with Runtime context type
`OperationRuntimeContext(host=None, configuration=None, launcher=None)` and no checkpointer, and
`invoke(context, launcher)` validates a typed input value and runs it. The node accepts either a
typed result or its bare data from the service. Its exact topology is the
[Graph Spec](graphs.md#terminal-agent-operation).

Each public capability module also exposes a State adapter: `run_host(name, state, runtime)` in
`operation_state.py` wraps the State as the capability's typed request, runs it through admission
with the host and configuration from `OperationRuntimeContext`, and returns `{"result": envelope}`;
it refuses when no host was supplied.
