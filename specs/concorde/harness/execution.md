# Agent execution

### Configured deterministic checks

This host-only service runs configured commands without a model invocation. It is independent of
worker model selection and of the worker tool gate. Checks can read project files; their own
temporary files, caches and reports belong in fresh host-managed space outside the project.
Creating, modifying, moving or deleting a project file is denied at the attempted system call,
including a write followed by restoration. Project-local lifecycle and log paths are read-only too.

```python
execute_check(project_root: Path, argv: Sequence[str], *, timeout: float,
              environment: Mapping[str, str]) -> CheckResult
CheckResult(stdout: bytes, stderr: bytes, returncode: int, timed_out: bool = False)
CheckBackend.run(project: Path, argv: Sequence[str], scratch: Path,
                 environment: Mapping[str, str], timeout: float) -> CheckResult
```

The backend interface is trusted host code, never a registry field or a task-supplied executable.
Only Linux's BubblewrapBackend is currently supported. It requires a root-owned system bubblewrap,
user/mount/PID/IPC namespace support and kernel pidfds exposed by Python or libc. System file owners
unmapped by a parent check namespace are admitted only on its already read-only system mounts.
Missing binaries, unsupported
platforms, denied namespace setup, unsafe project locations and unavailable external temporary
storage raise `CheckSandboxError(RuntimeError)`. That exception retains byte `stdout`/`stderr`
diagnostics for the host. No failure retries through ordinary subprocess or weaker permissions.
An empty command, non-directory project or nonpositive/nonfinite timeout is also rejected.

Every call creates independent scratch storage even when ambient TMPDIR points into the project.
`TMPDIR`, `TMP`, `TEMP`, `XDG_CACHE_HOME` and `npm_config_cache` point into that storage;
`CONCORDE_CHECK_TMPDIR` names its root and `CONCORDE_CHECK_REPORT_DIR` its reports directory.
`PYTHONDONTWRITEBYTECODE=1` avoids routine Python cache attempts but is not the write boundary.
Hardcoded project cache/report paths must migrate; tools that modify sources belong in implementation.
Scratch and reports are ephemeral and disappear after the check. No report import into the project
is implicit. Standard output/error remain separate byte streams for outside-host persistence.

The result preserves command exit status using bubblewrap's shell encoding, including `128+signal`
for signal termination. A timeout, including sandbox setup time, returns `timed_out=True` and
`returncode=-1` with captured partial output. Host cancellation propagates after cleanup. A missing
trusted successful-exec status is an isolation/launch error, not an ordinary check failure. A
successful sandbox exit establishes execution under this boundary, not test adequacy or semantic
completeness. The calling host remains responsible for digest and candidate freshness checks;
`CHECK_POLICY="project-read-only-v1"` identifies this execution guarantee for evidence invalidation.

#### scenario.harness.check-read-only — Project mutation is denied during execution

- GIVEN a configured command with project read access
- WHEN it or a descendant attempts creation, modification, deletion, rename or modification followed by restoration
- THEN the operating system rejects the operation before project bytes or directory entries change
- AND alternative pathnames, inherited descriptors and nested namespace remounts cannot grant project writes

#### scenario.harness.check-scratch — Each check can read inputs and write disposable output

- GIVEN an admitted command and an available external temporary directory
- WHEN the host executes the check
- THEN project reads and writes to the issued temporary and cache/report directories succeed
- AND repeated calls receive separate scratch directories that are removed after execution
- AND an ambient project-local temporary path cannot become a writable project mount

#### scenario.harness.check-result — Output and exit status are returned only to the host

- GIVEN a check that writes standard output and standard error and exits with a specified code
- WHEN its isolated execution finishes
- THEN the executor returns both byte streams and that exit code without exposing a project log descriptor
- AND large output on both pipes is drained without blocking command completion

#### scenario.harness.check-unavailable — Unsupported enforcement prevents execution

- GIVEN an unsupported OS, missing sandbox backend or a real sandbox setup failure
- WHEN the host requests a configured check
- THEN execution fails closed with CheckSandboxError and host-only diagnostics
- AND no ordinary subprocess fallback runs the configured command

#### scenario.harness.check-lifetime — Descendants cannot outlive their check

- GIVEN a check that spawns detached descendants
- WHEN the initial command completes or its deadline expires
- THEN the host terminates every descendant before returning and removes scratch afterward
- AND a timeout preserves partial output with timeout status instead of successful evidence

### Required Agent and Harness boundary

The local companion contract **Agents and Harnesses** defines A1–A5 for this Module. Execution MUST
receive a resolved worker binding, its frozen context, its compiled policy and its model selection,
and run exactly that worker. The worker executor's preflight reverifies the carried `AgentBinding`,
the instructions, the admitted context and the policy against the current build and the worker's
contract before starting any process, so the launch below executes only a complete, checked worker
profile.

### Worker execution

`WorkerExecutor` runs one host-built `WorkerInvocation` as one Pi worker and returns a
`WorkerOutcome`, or raises `CapabilityExecutionError`. The local companion contract **Agent runtime
value and collaborator contracts** defines these records, the invocation builder and the preflight;
the [Pi worker runtime](#pi-worker-runtime) below defines the process.

#### Workspace kinds

A worker profile declares `workspace: capsule` or `workspace: project`; the registered workers and
their kinds are listed in [Agents and Harnesses](agents-and-harnesses.md).

- A **capsule** is a host-created temporary directory outside the project root, created for one
  invocation immediately before launch and removed after the host has verified it. It contains
  `context.json`, holding the frozen snapshot bytes, beside byte-identical copies of every Spec
  document and Protocol file that index lists, at their project-relative paths, plus the copied
  external references a worker with the `references` effect receives. It is the Pi process's
  working directory, and the tool gate's read grant is that directory, so the project root, the
  candidate worktree, other worktrees and the developer's home directory are outside the grant.
  The discovery, Spec, assessment, planning and task workers use this kind.
- A **project** workspace is the candidate worktree itself and the Pi process's working directory.
  The snapshot is written below `.concorde/runs/<invocation>/<uuid>/context.json` inside that
  worktree; the grant covers it, the Spec documents and the installed Protocol copy under
  `.concorde/protocol/` it indexes, at their project paths, and the selected Module's
  implementation: its listed entries with write authority for the programmer, its enumerated files
  read-only for the code reviewer and the investigator.

In both kinds the host rereads the snapshot file after the worker settles and rejects a result whose
file bytes, registry digest, document digests or initialized configuration changed during execution
with `stale_context` or `configuration_mismatch`.

#### Input and result

A worker's system prompt is the invocation's instructions: the common worker rules, the worker's
role Spec and the Protocol rule bundle, in that order. Its only message is the canonical typed
context: task context inline, Spec context as the index of granted files. Its output contract is its
`submit_result` tool, whose parameters are the self-contained JSON Schema of the contract's result
type. The executor wraps the single submitted value as that type, checks it against the contract and
returns it; the host then checks its context identity and gap provenance before accepting stage
completion. Independently, each admitted worker may use `report_issue` to persist an observation
through a host-issued, scope-bound callback before submitting its final result. Report admission
is separate from completion; accepted reports survive an invalid or interrupted final result.
The [Issue reporting boundary](../reflections/issues.md#worker-reporting-service) defines report
shape and authority. A worker in a project workspace also receives the host check service behind
`run_checks`.

#### Common limits

The Pi process itself is outside the gate: it runs as the developer's user with the developer's Pi
credentials and talks to its model provider. The gate bounds what the model's tools can reach, not
the process, and a shell command run by a worker granted `bash` is not confined by it. The
credential paths the compiler always denies (`.env`, `.aws`, `.ssh` and the other listed entries)
are project-relative entries; home-directory secrets are outside the grant because the grant is
default-deny. Running the whole Pi process inside an operating-system sandbox that mounts only the
granted paths is the planned stronger boundary.

### Pi worker runtime

A Pi worker is one Pi coding agent process run in RPC mode for one bounded task. Pi calls the
worker's model through its own providers and executes its built-in tools; LangGraph stays the
orchestration around it. `PiWorkerRuntime` launches one `WorkerLaunch` and returns a
`WorkerResult` or raises `WorkerExecutionError`:

```python
WorkerLaunch(worker: str, workspace: str, system_prompt: str, message: str,
             result_schema: Mapping[str, Any], tools: tuple[str, ...],
             read_paths: tuple[str, ...] = (), write_paths: tuple[str, ...] = (),
             children: tuple[ChildAgent, ...] = (), child_tools: tuple[str, ...] = (),
             model: str | None = None, thinking: str | None = None, timeout_seconds: float = 1800,
             report_schema: Mapping[str, Any] | None = None)
ChildAgent(name: str, definition: str)
PiWorkerRuntime(package_root: Path, pi_executable: str | None = None,
                environment: Mapping[str, str] | None = None, credentials_dir: Path | None = None,
                popen=subprocess.Popen)
PiWorkerRuntime.__call__(launch: WorkerLaunch, *, checks: Callable[[], Any] | None = None,
                         report_issue: Callable[[dict], Any] | None = None) -> WorkerResult
WorkerResult(value: dict[str, Any], run: PiRun, usage: dict[str, Any])
WorkerExecutionError(message: str, outcome: "failed"|"cancelled"|"limit_exhausted"|"invalid_completion",
                     run: PiRun | None = None)
run_prompt(argv, *, cwd: str, env: Mapping[str, str], message: str, timeout: float, popen=subprocess.Popen) -> PiRun
```

Paths in a launch are relative to its absolute workspace, which is the process's working
directory. `model` is Pi's `provider/id` and `thinking` one of Pi's levels (`off` through `max`).
The tools are Pi's built-ins (`read`, `grep`, `find`, `ls`, `edit`, `write`, `bash`) and the
Concorde tools: `submit_result`, which every worker has; `run_checks`, which requires the host
check service; `report_issue`, which requires both its host callback and report schema; and
`subagent`, which a worker has exactly when it declares children. Edit and write require a write
grant, and child tools are built-ins or `run_checks`, never `report_issue`. An inconsistent launch
is refused before any process starts. The executor accepts an optional host reporter with a
`schema` property and callable report handler, forwards it only to the admitted runtime, and does
not convert reporting authority into any file write grant. The common Development host supplies
this service for actual worker launches, including capsule workers, but not policy previews.

The private Unix socket dispatches only explicitly granted `run_checks` and `report_issue` calls.
Requests must be complete newline-terminated JSON frames of at most 128 KiB, received within ten
seconds. Reporting parameters are validated by the bound host callback, which returns only a
receipt. A rejected callback returns an error that the extension throws as a failed tool result,
not a successful receipt. Reporting never returns `terminate`; the worker can continue reporting
or working. Accepted persistence is retained if cancellation disconnects the client before the
acknowledgement arrives.

### Usage accounting

Pi reports what a run consumed in its session statistics, which the runtime reads after the worker
settles: input, cached input, output and total tokens, cost and assistant turns. The executor
records them as an `ExecutionUsage` record on the `WorkerOutcome`: the configured `model` and
`thinking` level, `input_tokens`, `cached_input_tokens`, `output_tokens`, `total_tokens`,
`cost_usd`, `turns`, host-measured `wall_seconds`, and the `prompt_bytes` and `context_bytes` the host
handed the process. A figure Pi did not report is `None`, never zero.

The host records one line per launch through `record_usage` in `.concorde/runs/<root invocation
id>/usage.jsonl`, labelled with `capability`, `stage`, `target_id`, `agent`, `change_id`, the
launching host's `invocation_id` and `depth`, the launch's own `launch_invocation_id`, `context_id`
and `model`, and the usage record. The root invocation id is the top-level capability invocation's
identity, inherited by every nested capability invocation (`CapabilityHost.root_invocation_id`), so
one Flow run keeps one file. The same record reaches the host observer as an `agent_usage` event.
`read_usage` and `summarize_usage` aggregate the lines per step (capability, stage and target),
stage, target, worker and run; the `concorde usage` Tool and the executable boundary's stderr summary
use them. Usage is diagnostic evidence about cost: it gates nothing, and a failure to persist it
never fails the launch. See [usage accounting](module.md#scenario.harness.usage-accounting).

### Outcomes

A worker's deadline is its selected `timeout_seconds`, else its profile's timeout as bound in its
`AgentBinding`. `CapabilityExecutionError.outcome` distinguishes four cases so a caller need not
parse message text: `failed` for a refused preflight, a process that exits or breaks the RPC
protocol before settling, or any other launch failure; `cancelled` for a host interrupt, with the
process already killed; `limit_exhausted` for a run past its deadline, likewise killed; and
`invalid_completion` for a run with no, several or an invalid submitted result. A contract
rejection keeps its class in `code` (`permission_denied` for disallowed authored fields). None of
these outcomes triggers an automatic retry, with the same or any wider permissions. Authorized
implementation edits made before a failure can remain in the candidate; the executor does not
promise rollback.

### Representative use

The wire collaborator provides `json_schema(type_id: str) -> dict` for a self-contained typed result
schema and `validate_typed(value: Any, expected: str | None = None, field: str = "") -> dict` for
strict type, version, property and uniqueness validation. Unknown types or versions, unsafe paths,
invalid fields and mismatched expected types raise `TypedDataError(ValueError)` with `code` and
`field`; the executor treats them as invalid completion, not successful output. These calls perform
no project mutation or remote schema resolution.

```python
executor = WorkerExecutor()
# invocation is already built by the trusted host with build_worker_invocation.
try:
    outcome = executor(invocation, checks=checks)
except CapabilityExecutionError as failure:
    reason = failure.outcome          # stop the transition; failure.usage may carry what was spent
else:
    assert outcome.invocation_digest == invocation.digest
    result = outcome.value["data"]    # the validated typed result
```

Consumers bind the outcome to the invocation and binding digests and consume the typed result
rather than raw process output. A runtime double can test these boundary mechanics but cannot
establish that a model detected a semantic gap or behavior defect.

## Design

### Check isolation mechanism

Linux recursively maps the host filesystem read-only so another pathname, hard link or external
dependency directory cannot supply a writable alias. It replaces `/proc` with the sandbox's PID
view and `/dev` with minimal private devices, drops capabilities, disconnects the terminal and
gives only the new scratch directory a writable host mount. Shared memory uses scratch as well.
Project roots at `/` or below `/proc`, `/dev` or `/sys` are unsupported. Additional user namespaces
remain available for nested checks; inherited read-only mounts cannot be remounted writable there.
The bootstrap binary uses a fixed system search and minimal loader environment; the supplied
check environment travels through an anonymous options descriptor rather than the public process
command line and is installed for sandbox execution. This service defines no finer read,
network or credential policy and does not mediate effects requested from external services.

The host closes inherited descriptors, supplies null stdin and captures output through pipes,
never by passing an open project log to the process. Bubblewrap's host-only metadata descriptors
are closed before command execution. A launch gate keeps the command stopped until the host pins
namespace PID 1 with a pidfd. On timeout, cancellation, failure and normal completion, the host
terminates the namespace and waits for cleanup before removing scratch. This includes descendants
that double-fork, create sessions or reset parent-death signals. Both output pipes drain while the
initial command runs, and a background process holding them open cannot prevent cleanup.

### Worker launch and enforcement

#### What the host itself enforces

- **Fresh process, closed inputs.** Every launch is a new Pi process with sessions, context files,
  skills, prompt templates, themes and discovered extensions disabled. No predecessor transcript,
  conversation or session state is passed.
- **Environment allowlist.** The process environment is rebuilt from `SAFE_ENVIRONMENT` in
  `harness.py` (`HOME`, `PATH`, `LANG`, `LC_ALL`, `LC_CTYPE`, `LOGNAME`, `USER`, `TMPDIR`, `TMP`,
  `TEMP` and their Windows equivalents), the provider credential variables Pi documents and Pi's
  own control variables. Every other variable of the calling shell is absent.
- **Binding equality.** Preflight rejects an invocation whose binding, instructions, Protocol files,
  context or policy differ from what the current build and the worker's contract admit.
- **Tool gate.** The Concorde worker extension refuses every tool call outside the compiled grant in
  the worker and in each child ([tool gate](#tool-gate)).
- **Result admission.** Only one submitted result that satisfies the result type and the contract
  completes the invocation; a settled process alone is not completion.

#### Launch

Each launch gets a private run directory that is removed afterwards. Its `agent/` directory is
Pi's configuration directory for the process (`PI_CODING_AGENT_DIR`): Concorde's own settings
(project trust never, install telemetry off, pi-subagents builtin agents disabled), the developer's
Pi credentials (`auth.json` and custom-provider `models.json`, copied from the developer's Pi
directory), the declared child definitions under `agents/` and the pi-subagents configuration
under `extensions/subagent/config.json`. Beside it lie `policy.json`, which the Concorde worker
extension enforces, `system-prompt.md`, which it installs as the worker's complete system prompt,
`tmp/`, the process's temporary directory, and, for a worker with `run_checks` or `report_issue`,
the host tool service's socket. The developer's own Pi settings, sessions, agents, extensions and skills are
never read. When Pi refreshes an OAuth credential during the run, the host writes the refreshed
`auth.json` back to the developer's Pi directory, but only while that file still holds the bytes the
run was issued, so a concurrent refresh is never overwritten.

The process runs `pi --mode rpc --no-session --no-context-files --no-skills --no-prompt-templates
--no-themes --no-extensions -e pi/extensions/concorde-worker.ts [-e pi-subagents] --no-approve
--offline --tools <tools> [--model <model>] [--thinking <level>]`, with pi-subagents loaded only
for a worker with children. Its environment is the host allowlist, the provider credential
variables Pi documents, `PI_OFFLINE`, `PI_SKIP_VERSION_CHECK`, `PI_TELEMETRY=0`, the run
directory's `TMPDIR` and the policy location. The host sends one `prompt` command carrying the
worker's message, reads records split on line feed only until `agent_settled`, answers every
extension dialog as cancelled, reads the session statistics and closes the process.

The result is the `details` of the worker's single successful `submit_result` call. That tool's
parameters are the launch's result schema, so the model sees its output contract as a tool, and it
ends the run. No submission or a second one is `invalid_completion`; a missed deadline kills the
process and is `limit_exhausted`; a host interrupt is `cancelled`; a process that exits or breaks
the protocol before settling is `failed`. None of them retries. The caller validates the value
against its own typed contract. Usage comes from Pi's session statistics: input, cached input and
output tokens, cost, assistant turns and the host-measured wall time.

#### Tool gate

The Concorde worker extension gates every tool call before it executes: a tool outside the
granted list is refused; `read`, `grep`, `find` and `ls` must target a path whose canonical form,
symlinks resolved, lies under a read or write grant, and a search without a path targets the
workspace itself; `edit` and `write` must target a path under a write grant; each `bash` command
first unsets the provider credential variables. A refused call returns an error result naming the
policy, and the model continues. The gate runs inside the Pi process, so it is a policy boundary,
not an operating-system sandbox: a shell command is not confined by it. Running the whole Pi
process inside an operating-system sandbox that mounts only the granted paths is the planned
stronger boundary.

#### One-level delegation

A worker with children loads pi-subagents, pinned in `pi/package.json`: a source checkout installs it
with `npm ci --prefix pi`, and in an installed project the installer provisions the same lock into the
managed runtime under `.concorde/.venv/share/concorde/pi`, where the runtime finds it beside the
installed framework. Its configuration allows one level of delegation, runs children in the foreground in
fresh contexts, and disables pi-subagents' background runs, missions, schedules and inter-session
channels. On session start the Concorde extension registers two things with pi-subagents for the
worker's session: a capability ceiling naming exactly the declared children and the child tools,
and itself as a required child extension, so every child session loads the same gate. In a child
session the gate uses the child tool list, refuses `subagent` and `submit_result`, and does not
replace the child's system prompt. A child is a lightweight pi-subagents Markdown definition: what
it does inside the worker is not a Concorde contract, and only the worker's submitted result
leaves the process.

#### Host check service

For a worker granted `run_checks`, the host serves one Unix socket in the run directory. The tool
sends `{"tool": "run_checks"}` and returns the host's JSON reply, or an `error` field when the host
callback fails; the host runs the configured checks under its own read-only executor.

#### scenario.harness.pi-rpc-client — Read one Pi RPC run to settlement

- GIVEN a process speaking Pi's RPC protocol
- WHEN the host runs one prompt through run_prompt
- THEN records are split on line feed only, so U+2028 and U+2029 inside a JSON string stay inside it, and a trailing carriage return is dropped
- AND every extension dialog is answered as cancelled, every tool result is collected, and the session statistics are read after agent_settled
- BUT a process that closes its output before settling raises PiRpcError, and a run past its deadline is killed and raises PiRpcTimeout

#### scenario.harness.pi-worker-launch — Launch a Pi worker and admit its single result

- GIVEN a consistent worker launch with a workspace, grants, tools, a system prompt, a message, a result schema and a Pi model
- WHEN PiWorkerRuntime runs it
- THEN Pi starts in RPC mode with ambient discovery disabled, the host-rendered system prompt as the complete system prompt and submit_result advertised with exactly the launch's result schema
- AND the returned value is the details of the single successful submit_result call, with usage from Pi's session statistics
- AND a run_checks call is answered by the host's check callback
- BUT a run without a submission fails with invalid_completion, a run past its deadline fails with limit_exhausted, and an inconsistent launch is refused before any process starts

#### scenario.harness.pi-worker-gate — Refuse tool calls outside the worker's grant

- GIVEN a running Pi worker with read and write grants and a tool list
- WHEN its model reads, searches or writes a path outside the grants, or calls a tool it was not granted
- THEN the Concorde worker extension refuses the call with an error result naming the policy and the file is neither read nor changed
- AND calls inside the grants execute normally
- AND a bash command runs with the provider credential variables unset

#### scenario.harness.pi-worker-delegation — Delegate one level to declared children under the same gate

- GIVEN a Pi worker that declares a child agent and child tools
- WHEN its model delegates a task to that child
- THEN pi-subagents runs the child as a foreground session that loads the Concorde worker extension and has exactly the child tools
- AND the gate refuses the child's calls outside the worker's grants, and the child cannot delegate or submit a result
- AND delegation to an agent the worker did not declare is refused
- BUT only the worker's own submitted result leaves the process
