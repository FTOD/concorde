# Agent calls

The exact preparation, acceptance, evidence and hook interfaces of one Agent call, and the
requirements and scenarios they serve. The [entry](module.md) explains why the path is shaped this
way. The JSON exchanged between workflow scripts, Host-step commands and the Host is the
[Host-step protocol](interfaces.md#contract.execution.host-step).

## Requirements

### req.execution.proposal-not-completion — A proposal is not a result

An Agent call's proposal SHALL NOT be accepted as a result before the acceptance step has verified
the run's native records and rechecked the current inputs.

Submission and staging never change task state. The acceptance step (`accept` for a single call,
a workflow hook's step through the driver's `accept` or `admit` service for a Workflow slot) reads
pi-subagents' records of the run itself, as defined in [Native evidence](#native-evidence).

### req.execution.single-proposal — One proposal per call

A result gate SHALL hold at most one proposal per call, never replacing one it has stored or
refused.

A submission that pi-subagents rejects against the output schema never reaches the Host, so the
Agent may correct it within the same run and deadline.

### req.execution.settling-not-completion — Ending a run is not completing it

An Agent call that ends without exactly one valid submitted proposal SHALL NOT be treated as
completed.

### req.execution.single-acceptance — One acceptance per call

The driver SHALL apply an Agent hook's acceptance at most once per Agent call.

The exclusive terminal reservation described under [Result gate](#result-gate) makes a repeated,
concurrent or retried `accept` fail instead of recording again.

### req.execution.no-retry — No automatic retry

No execution failure SHALL cause an automatic retry of an Agent call or a Workflow.

A failed or uncertain acceptance is final for its call; a further attempt is a new request that
passes admission again.

### req.execution.preflight-shape — Launch only the prepared shape

An Agent call SHALL be refused before its model starts unless launch preflight resolves exactly the
prepared Agent definition file, a fresh context without inherited project context, global context
or Skills, no nested subagents, and no tool outside that file's tool list.

The tool list is the one the [Agent binding](../context/module.md#concept.context.agent-binding)
derived from the Agent definition, plus `report_issue` and pi-subagents' `structured_output`. It
bounds which tools exist, not which files those tools reach.

### req.execution.no-provider-imports — Providers are reached through hooks

The native driver SHALL reach provider behaviour only through the hook entry points named in Agent
definitions and capability declarations.

No module bound by Agent execution imports a provider package; the entry point is resolved at run
time from its `module:attribute` string.

### req.execution.producer-pinned — Read only the reviewed native producer

The Host SHALL read native evidence only from a pi-subagents installation whose package identity and
selected source digests equal the pinned native runtime contract.

### req.execution.model-selection — Each Agent runs on its own selection

Every Agent call SHALL be launched with the model, thinking level and time limit resolved for that
Agent from the project configuration.

## Call preparation

The driver prepares each call in a directory it creates outside every worktree, or in the slot
directory a workflow hook issued. It contains:

| Item | Content |
| --- | --- |
| `descriptor.json` | The call's bound inputs: operation, phase, Agent, ticket, project and package roots, the Python interpreter, the stored invocation envelope and configuration, the frozen snapshot, the stage plan's review input, the result type, the digest of every delivered file, of the registry, of the instructions and of the change status, the admitted pi-subagents binding, the parent session identities and the launch call without its gate |
| `descriptor.digest` | The digest of `descriptor.json`; every Host step receives both and refuses a mismatch |
| `context/` | The capsule Task context assembled, including `context.json` |
| `context/.pi/agents/<agent>.md` | The Agent definition file pi-subagents discovers |
| `context/.pi/settings.json` | `{"subagents": {"projectRootResolution": "nearest"}}`, so discovery stays inside the capsule |
| `capture.ts` | A one-line extension that loads the child extension bound to this descriptor |

**Agent definition file.** Its front matter sets `name` to `concorde-` plus the hyphenated Agent
name; `tools` to the Agent binding's tools plus `report_issue`; `extensions` to the capture
extension; `allowNestedSubagents: false`; `maxSubagentDepth: 1`; `acceptanceRole` (`writer` when
the definition's effects write implementation, otherwise `read-only`); `inheritProjectContext`,
`inheritGlobalContext` and `inheritSkills` all `false`; `defaultContext: "fresh"`; `async: false`;
`timeoutMs` from the model selection; `systemPromptMode: "replace"`; and, when selected, `model`
and `thinking`. Its body is the stage plan's instruction override, or else the Agent's rendered
instructions. The digests of this file, the capture extension and the settings file are bound in
the descriptor before launch.

**Call.** The returned `call` has exactly `agent`, `task` (naming the ticket), `cwd` (the capsule),
`agentScope: "project"`, `context: "fresh"`, `async: false`, `mission: false`, `artifacts: true`,
`artifactDir: "session"`, `intercomBridge: {"mode": "off"}`, `agentContract: {"version": 1}`,
`outputSchema` and `gate: {"command": ...}`. The output schema is self-contained: an object with
exactly `invocation_id` (constant, the issued ticket) and `result` (the Agent's result type with
its data schema embedded). The gate command runs the Host step `stage` with this descriptor, unless
a workflow hook supplied the slot's gate command.

**Prerequisites.** Preparation refuses without a selected pi-subagents package root
(`CONCORDE_NATIVE_SUBAGENTS_ROOT` in the Pi session), with `missing_runtime`.

**Describe-policy.** In `describe-policy` mode preparation returns `state: "described"` and a
`policy` object with `enforcement: "prompt-level"`, the Agent, the read list (`context.json`, the
snapshot's documents and, when the definition reads references, the external entries), the intended
write roots (the Module's `ImplementationScope` roots when the definition writes implementation,
otherwise none), the tools and `delegation: false`. No directory is created and no Agent runs.

## Launch preflight

`nativePreflight(root, call)` calls pi-subagents' public `resolveSubagentLaunchContract` and throws
unless the resolved contract has:

- an Agent of source `project` whose file is exactly `<cwd>/.pi/agents/<agent>.md`;
- ambient extensions disabled and no fan-out authorization;
- an effective tool allowlist inside the `tools` listed in that Agent definition file plus
  `structured_output`;
- context `fresh`, no inherited project or global context, no inherited or resolved Skills and no
  active intercom bridge.

For a single call the native call extension runs it after `check`; for a Workflow the provider's
Host-step helper runs it for each issued slot before the script launches that slot, and records the
resolved contract as `preflight.json` in the slot directory. A failed preflight is reported with
layer `native-preflight` and category `host-refusal`, keeping pi-subagents' reasons as causes.

## Result gate

The result gate is a set of driver actions over files in the call's directory, run by the Host-step
command `--native-context <action> <descriptor> <digest>`. Each action takes the command lock,
checks the descriptor digest, re-admits the stored invocation (so a changed configuration or
runtime selection is refused), refuses a call whose `invalid` marker or terminal record exists
(except `invalidate` and `observe-error`), and rechecks that the snapshot, configuration,
instructions, registry, change status, delivered capsule files and definition assets are unchanged
and that the Agent hook's `recheck` passes.

| Action | Behaviour |
| --- | --- |
| `check` | Run before launch; returns `state: "prepared"` |
| `submit` | Refuses more than 1 MiB; creates `proposal.json` exclusively in canonical JSON; validates it; on any failure records the cause, creates `invalid` and fails; otherwise returns `state: "proposed"`, `accepted: false` |
| `invalidate` | Records the reason when given and creates `invalid`; any later action except `observe-error` fails with the recorded cause |
| `observe-error` | Records a schema rejection the Agent may still correct, once per event; does not invalidate |
| `report` | Forwards one Issue report to Issues bound to this call and returns the receipt; keeps the receipts in `reports.json` |
| `checks` | Only when the Agent binding lists `run_checks`: runs the Module's configured checks and returns each check result with the last 20,000 bytes of its log |
| `stage` | Revalidates the proposal and prints the staging control document |
| `accept` | Revalidates the proposal, re-admits the pi-subagents installation, verifies the single run, requires the reported gate command to equal the issued one, reserves `terminal.json` exclusively, calls the Agent hook's `accept`, archives the descriptor, proposal, native metadata and correlation as `native-context.json` in the primary worktree's run directory, and records the terminal outcome |
| `admit` | For a Workflow slot: the same checks as `accept` up to the gate comparison, then returns the proposal and native metadata with `state: "admitted"`, without reservation or acceptance |

**Validating a proposal.** The proposal is exactly `{invocation_id, result}` with the issued ticket;
its stored bytes equal their canonical form and are at most 1 MiB; `result` satisfies the Agent's
result type and only the output fields its definition may populate; every Issue it cites was
received by this call's reporter; and the Agent hook's `validate` passes, which checks the stage
identity and the provider's own predicate. A missing proposal fails with category `no-submission`;
an invalidated call fails with its recorded causes.

**Failed run.** When the reported run row was interrupted, stopped, timed out or exited nonzero,
`accept` fails with outcome `cancelled`, `limit_exhausted` or `failed`, keeping the native row and
the recorded slot failures as causes.

**Reservation.** `terminal.json` is created exclusively with `{"state": "finalizing"}` before the
hook's acceptance runs and rewritten with the accepted outcome after it, so a second `accept`
refuses with `invalid_completion`. After an uncertain failure the call needs a new request.

## Native evidence {#native-evidence}

**Producer admission.** `admit_native_runtime(root)` accepts only an absolute, symlink-free
pi-subagents package root whose `package.json` names `pi-subagents` 0.69.0 and whose files listed in
`pi/native-runtime-contract.json` have exactly the recorded digests. The admitted binding has format
`pi-subagents-0.69.0-versionless-v1`. Every record read below must carry no `schema_version` or
`lifecycleArtifactVersion` field.

**Records.** Each record is read from an absolute, symlink-free path as one JSON object of at most
16 MiB; a missing, oversized or unreadable record fails with `stale_evidence`, never with partial
success.

**Single call.** The native call extension correlates the `subagent` tool call and its result in
the live session; the driver then requires: not an error, the same session, mode `single`, exactly
one result row for the expected Agent with exit code 0 and none of `error`, `detached`,
`interrupted`, `stopped`, `terminalOutcome`, `timedOut`, `metadataSaveError`, `outputSaveError` or
`transcriptError`; the row's launch contract digest equal to the one preflight produced; the
structured output file pi-subagents saved equal in digest to the captured proposal; metadata with
the same run, Agent and launch digest, exit code 0 and no error, transcript error or process
signal; an acceptance status `verified` with exactly one gate run whose command is the issued gate,
status `passed`, exit code 0, no structured output, and whose standard output is a valid staging
control document for this proposal.

**Workflow coverage.** Given the Workflow's async directory, run identity, session identity, ticket
and the issued slots, the driver reads `status.json` and requires mode `workflow`, the same run and
session, state `running` or `complete`, and no stop, timeout, error or terminal outcome. Every step
with a `workflowKey` and every child-terminal emission carrying the ticket must cover exactly the
issued keys, once each. For each slot: the step's parent run is the Workflow, its Agent matches, its
status is `completed` with no error, stop or timeout, and its run identity equals the emission's;
the emission's invocation identity and proposal digest match; the metadata file the emission names
has the same run and Agent, exit code 0 and no error; and its single gate satisfies the rules for a
single call. The Workflow may still be running when this check passes, because pi-subagents writes
its receipt only after the final Host step.

## Hooks {#hooks}

Hooks are resolved from `module:attribute` entry-point strings: an Agent hook from the Agent
definition's `hook`, a workflow hook from the capability declaration's native entry. The resolved
attribute must provide the methods below; anything else refuses preparation with
`invalid_agent_binding`.

```python
@dataclass(frozen=True)
class StagePlan:
    stage_inputs: tuple[dict, ...] = ()   # typed stage inputs admitted for this call
    review_input: dict | None = None      # typed review input written beside the snapshot
    instructions: str | None = None       # replaces the rendered instructions for this call
    stop: dict | None = None              # a result envelope that ends preparation; no Agent runs
    stop_accepted: bool = False           # whether that stop is itself an accepted outcome
    bind_admitted_snapshot: bool = False  # later steps recheck the snapshot frozen at preparation

class AgentHook(Protocol):
    def prepare(self, run: Invocation, admitted: tuple[dict, ...] | None) -> StagePlan: ...
    def recheck(self, run: Invocation, descriptor: dict) -> None: ...
    def validate(self, run: Invocation, snapshot: ContextSnapshot, plan: StagePlan, data: dict) -> None: ...
    def accept(self, run: Invocation, snapshot: ContextSnapshot, plan: StagePlan, data: dict) -> dict: ...
```

The driver calls `prepare` once with `admitted=None` at preparation, and again in later steps with
the stage inputs recorded in the descriptor, so the hook rebuilds the same plan; a rebuilt plan whose
stage inputs or review input differ from the recorded ones is `stale_context`. `recheck` raises for
provider inputs the snapshot does not cover, such as a selected Issue's revision. `validate` raises
`SpecError` for an invalid proposal. `accept` runs once, after reservation, and returns the result
envelope the call reports; a proposal whose outcome is a blocker is passed to `accept` like any
other.

```python
@dataclass(frozen=True)
class WorkflowPlan:
    script: str                           # package-relative workflow script
    host: str                             # package-relative Host-step helper
    steps: tuple[str, ...]                # the Host-step names the script may run
    expansion: dict                       # JSON substituted into the script
    helpers: tuple[str, ...] = ()         # package-relative modules inlined before the script
    stop: dict | None = None              # a result envelope that ends preparation; no Workflow runs
    stop_accepted: bool = False

class WorkflowHook(Protocol):
    def prepare(self, run: Invocation, driver: WorkflowDriver) -> WorkflowPlan: ...
    def step(self, run: Invocation, driver: WorkflowDriver, name: str) -> dict: ...
    def on_failure(self, run: Invocation, driver: WorkflowDriver, native_state: str) -> dict | None: ...

class WorkflowDriver(Protocol):
    def issue_slot(self, key: str, agent: str, task: dict, *, stage_inputs: tuple[dict, ...] = ()) -> dict: ...
    def check(self, key: str) -> None: ...
    def coverage(self, keys: Sequence[str]) -> None: ...
    def admit(self, key: str) -> dict: ...
    def accept(self, key: str) -> dict: ...
    def receipt(self, value: dict) -> None: ...
    def stopped(self) -> bool: ...
```

`issue_slot` prepares one Agent call exactly as a single call, through that Agent's hook, in a slot
directory under the Workflow's directory, and returns its `call`; a key can be issued once. `check`
runs the slot's `check` action. `coverage` performs [Workflow coverage](#native-evidence) for the
given keys. `admit` returns a slot's independently verified proposal without acceptance; `accept`
applies the slot Agent's hook acceptance once. `receipt` writes the Workflow's result receipt,
which ends it. A step name must be one of the plan's `steps`; the driver refuses a step after the
Workflow was stopped or finished. `on_failure` is called once when the result step first observes a
failed or stopped Workflow without a receipt, and returns the receipt to record, if any.

## Model selection

The project configuration's `operation_configuration.data` may contain `model`, `thinking`,
`timeout_seconds` and `workers`, a map from Agent key (for example `code_reviewer`) to an object
with any of the same three fields. `worker_selection(configuration, agent)` returns a
`WorkerSelection(model, thinking, timeout_seconds)` taking each field from the Agent's entry, else
the default. `validate_worker_selections` rejects, with a typed `invalid_field` error at the JSON
pointer of the entry, a key naming no Agent, a `timeout_seconds` that is not positive and a `model`
without a `provider/` part. Thinking levels are `off`, `minimal`, `low`, `medium`, `high`, `xhigh`
and `max`.

## Scenarios

### Preparation

#### scenario.execution.prepare-call — Prepare a single Agent call

- GIVEN an admitted request whose provider asks the Host's native service to run one Agent, and a selected pi-subagents root
- WHEN the driver prepares the call
- THEN it resolves the Agent's hook from its definition and asks it for the stage plan
- AND Task context freezes the snapshot and assembles the capsule with the plan's stage inputs
- AND the driver writes the Agent definition file, the capture extension and a descriptor binding every input digest
- AND it returns `state: "prepared"`, `accepted: false` and the exact call with its gate command
- BUT no model has run and nothing is accepted

#### scenario.execution.hook-stop — A stage plan's stop ends preparation

- GIVEN an Agent hook whose stage plan carries a stop response
- WHEN the driver prepares the call
- THEN it returns that response with `state: "not-run"` and `accepted` equal to the plan's `stop_accepted`
- BUT it creates no capsule and no call

#### scenario.execution.unresolved-hook — An unresolvable hook refuses preparation

- GIVEN an Agent definition whose hook entry point does not import or lacks the hook methods
- WHEN the driver prepares a call of that Agent
- THEN preparation fails with `invalid_agent_binding`
- BUT no capsule or call directory is left behind

#### scenario.execution.describe-call — Describe a call without launching it

- GIVEN a request in `describe-policy` mode for a capability that runs one Agent
- WHEN the driver prepares it
- THEN it returns `state: "described"` with the read list, the intended write roots, the tools and `delegation: false`
- BUT it creates no capsule, issues no ticket and launches nothing

#### scenario.execution.missing-runtime — Preparation needs a selected native runtime

- GIVEN a request that would run an Agent and no selected pi-subagents package root
- WHEN the driver prepares it
- THEN preparation fails with `missing_runtime`
- BUT no call is returned

### Launch

#### scenario.execution.preflight-refusal — A launch outside the prepared shape never starts

- GIVEN a prepared Agent call
- WHEN launch preflight resolves a different Agent file, an inherited project or global context, a Skill, a nested subagent permission or a tool outside the Agent definition file's list
- THEN the Host refuses the launch before the model starts
- AND the refusal is reported in the `native-preflight` layer of the causal feedback record, keeping pi-subagents' own reasons as its causes

#### scenario.execution.foreign-call — Only the prepared call launches

- GIVEN a prepared single Agent call in the Pi session
- WHEN the user session calls `subagent` with a different call object, or with the prepared one a second time
- THEN the native call extension blocks the tool call before `check` or preflight run
- BUT the prepared call stays usable until it is launched or replaced

### Submission and staging

#### scenario.execution.stage-proposal — A submission becomes a staged proposal

- GIVEN a launched Agent call
- WHEN the Agent submits one valid result with `structured_output` and its run ends
- THEN the result gate stores exactly one canonical proposal after the hook's validation
- AND the gate command prints one staging control document with `state: "staged"` and `accepted: false`
- BUT neither submission nor staging changes any task state

#### scenario.execution.schema-rejection — A schema rejection can be corrected

- GIVEN a launched Agent call
- WHEN pi-subagents rejects a `structured_output` call against the output schema
- THEN the rejection is recorded once through `observe-error` with category `schema-rejection`
- AND the call is not invalidated, so a corrected submission in the same run can still be stored

#### scenario.execution.reject-proposal — An invalid proposal is never accepted

- GIVEN a launched Agent call
- WHEN it submits a proposal that is not an object, exceeds 1 MiB, names another ticket, fails its result type, cites an Issue this call did not receive, or fails the hook's validation, or submits a second proposal
- THEN the result gate records the cause and invalidates the call
- AND the Agent receives a failed tool result naming the refusal
- BUT no later `stage` or `accept` of that call succeeds

#### scenario.execution.no-submission — A run without a proposal is not completed

- GIVEN a launched Agent call whose run ends without a stored proposal
- WHEN its gate or its acceptance runs
- THEN it fails as an invalid completion with category `no-submission`, keeping any recorded schema rejections as causes

### Acceptance

#### scenario.execution.accept-call — Accept a verified single call

- GIVEN a staged single Agent call whose run succeeded and whose inputs are unchanged
- WHEN the native call extension runs `accept` with the correlated native result fields
- THEN the driver verifies the native records, the launch digest and the passed gate bound to this proposal
- AND it reserves the terminal record and calls the Agent hook's acceptance once
- AND it archives the descriptor, proposal and native records in the primary worktree's run directory
- AND the tool result reports `accepted: true` with the hook's result envelope

#### scenario.execution.failed-run — A failed run is not rescued by its gate

- GIVEN an Agent call whose run was interrupted, stopped, timed out or exited nonzero, even though its gate passed
- WHEN `accept` runs
- THEN it fails with outcome `cancelled`, `limit_exhausted` or `failed` and keeps the native row as a cause
- AND the call is invalidated
- BUT files a programmer already changed stay in the candidate

#### scenario.execution.stale-call — Changed inputs make a call stale

- GIVEN a staged Agent call
- WHEN any delivered file, snapshot source, configuration, instruction, registry, change status or provider input recheck differs from preparation before `accept`
- THEN acceptance fails with `stale_context` and invalidates the call
- BUT nothing is recorded as accepted

#### scenario.execution.repeat-accept — A repeated acceptance never records twice

- GIVEN an Agent call whose terminal record already exists
- WHEN `accept` runs again, concurrently or after an uncertain failure
- THEN it fails with `invalid_completion`
- BUT the Agent hook's acceptance is not called a second time

#### scenario.execution.cancelled-call — Cancellation revokes acceptance

- GIVEN a prepared or launched Agent call that has not been accepted
- WHEN the session shuts down, the call is replaced, or its acceptance fails
- THEN the call is invalidated and no later step accepts it
- BUT no automatic retry starts

#### scenario.execution.report-issue — An Agent files an Issue through the call

- GIVEN a launched Agent call
- WHEN the Agent calls `report_issue` with a report
- THEN the driver forwards it to Issues bound to this call's ticket, Agent, phase and Module and returns the receipt
- AND the receipt may be cited by this call's proposal
- BUT the receipt is not the call's result and survives a later failure of the call

### Workflow evidence

#### scenario.execution.workflow-coverage — Every issued slot is covered once

- GIVEN a Workflow bound to its run, session and ticket, with the slots the Host issued
- WHEN a workflow hook asks the driver for coverage of those slots
- THEN the driver finds exactly one completed, successful child per issued key with matching run, Agent and proposal identities and a passed gate bound to that proposal
- AND the check passes while the Workflow is still running, without a receipt pi-subagents writes only at its end

#### scenario.execution.workflow-coverage-gap — A missing or failed child blocks a Workflow

- GIVEN a Workflow with issued slots
- WHEN a child is missing or duplicated, failed with a passing gate, emitted a success flag without a completed step, or lost its metadata or status write
- THEN coverage fails with `stale_evidence` or `invalid_completion`
- BUT no slot of that Workflow is admitted or accepted

#### scenario.execution.foreign-producer — An unpinned producer is refused

- GIVEN a pi-subagents installation whose version or selected source digests differ from the pinned contract, or a record carrying a version field
- WHEN the driver would read native evidence
- THEN it refuses with `unsupported_version` or `stale_evidence`
- BUT it never reinterprets the records under a guessed layout

### Model selection

#### scenario.execution.model-selection — Launch each Agent on its configured selection

- GIVEN a project configuration with a default model, thinking level and time limit and per-Agent overrides
- WHEN the driver prepares an Agent call
- THEN each value comes from the Agent's entry, else the default, and a missing time limit falls back to the Agent definition's own
- AND the selection reaches Pi as the model, the thinking level and the deadline of the launch
- BUT an unset model or thinking level keeps Pi's own default

#### scenario.execution.model-selection-reject — Reject a selection no Agent can run

- GIVEN a configuration whose `workers` map names an unknown Agent, or that holds a nonpositive time limit, a model without a provider or an unknown thinking level
- WHEN the configuration is validated
- THEN it is rejected with a typed `invalid_field` error at the pointer of the offending entry
