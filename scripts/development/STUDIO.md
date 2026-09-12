# LangGraph Studio for Concorde

Studio can start every Concorde Skill and inspect capabilities submitted by the existing
CLI or Skill launcher. Both paths execute the same `CapabilityHost`, typed request validation,
configuration binding, native agent permission checks and worktree lifecycle as local CLI runs.
Studio is an optional development interface; ordinary CLI and Skill calls need no Agent Server.

## Start a server in this source worktree

Use Python 3.11 or newer and run these commands from the intended Concorde checkout. When working
through an agent, follow its `AGENTS.md` worktree ownership policy: the session stays in the
worktree that supplied its Skills and never creates another worktree itself.

```bash
uv sync --locked --group studio
python3 scripts/concorde.py build
uv run --locked --group studio langgraph dev --config generated/langgraph.json --host 127.0.0.1 --port 2024 --n-jobs-per-worker 1 --no-browser
```

Open <https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024> and select an assistant.
`generated/langgraph.json` (build output; run the build before starting Studio) registers all eight
Flows, one per Skill, derived from `skills/`. The five stage capabilities run through their
composing Skill and remain visible in stage/process events; stage capabilities have no
executable entry, and Studio does not restore one. API health
is available at <http://127.0.0.1:2024/ok> and API documentation at <http://127.0.0.1:2024/docs>.
The `concorde-review` assistant accepts `task` and `review_mode: "spec"` or `"code"`, plus optional
target/focus routing hints. It runs a standalone read-only review without creating a development change.
The local dev API works without model credentials for deterministic capabilities and policy previews.
The hosted Studio UI requires a LangSmith account; follow the official
[Studio setup](https://docs.langchain.com/oss/python/langgraph/studio) for its authentication setup.
Actual agent execution still requires the project's configured Codex or Claude runtime and credentials.

`generated/langgraph.json` disables LangSmith tracing by default. Local thread/checkpoint files are
stored in ignored `.langgraph_api/`. The dev server is intended for local use. Keep it on loopback
and use one job per worker for this filesystem workspace; do not submit concurrent mutations from
additional servers or local CLIs against the same worktree.

The entry module binds project and package roots to **the checkout containing that module**,
independently of request input. Start a separate server on a different port for another worktree.
Starting this config from another directory does not retarget it. This source-checkout launcher is
not installed into consumer projects; see the consumer setup below.

## Start and debug a capability in Studio

Select `concorde-main`, create a new thread, and enter this complete input in Graph mode:

```json
{
  "invocation": {
    "type_id": "concorde-capability-invocation",
    "schema_version": 3,
    "capability_id": "concorde-main",
    "mode": "describe-policy",
    "configuration": null,
    "input": {
      "type_id": "concorde-main-request",
      "schema_version": 1,
      "data": {"task": "Explain Concorde's workflow host", "target_id": "module.development"}
    }
  }
}
```

This previews the admitted policies without starting an agent. Switch `mode` to `execute` to run it.
For another capability, select its assistant and change both `capability_id` and the inner request
`type_id`; use that capability's existing request data contract. Null configuration loads the
project's initialized settings. A supplied configuration must match those settings. The invocation
has the same six fields and 1 MiB size limit as CLI stdin. Optional `expected_workspace` alongside
`invocation` asserts exact absolute `project_root` and `package_root` identities; it never selects them.

The public Flow has a `validate_invocation` node followed by the named capability subflow. Expand
that subflow to inspect admission, workspace/configuration binding and the capability's real dispatch
branches. Query/discovery, topology, planning, development and reflection Flows are composed below it;
`get_graph(xray=True)` exposes the same definitions. Use Studio interrupt-before on the public capability
node to inspect the invocation before executing it. Replay rechecks the envelope and workspace assertion.
Internal host Flows deliberately disable checkpoints: host objects live in per-run runtime context,
while node updates and public checkpoints contain JSON. Internal nodes are inspectable, but internal
checkpoint resume is not supported; pause or replay at the public capability boundary. Inspect `result`, `policies` and
`events` in the final state. `result` is the unchanged `concorde-capability-result` schema 3 envelope.
Input or workspace rejection clears previous output and returns a blocked result without execution.
Always submit a complete invocation for a new run; LangGraph merges partial input into thread state.
Use a new thread for an independent request. Hosts, permission descriptions and event lists are fresh
for each invocation, including repeated complete invocations on the same thread.

For Python breakpoints, the CLI supports a debugger port:

```bash
uv run --locked --group studio --with debugpy langgraph dev --config generated/langgraph.json --host 127.0.0.1 --port 2024 --n-jobs-per-worker 1 --debug-port 5678 --wait-for-client --no-reload --no-browser
```

Attach your Python debugger to localhost:5678. See the official
[CLI reference](https://docs.langchain.com/langsmith/cli) for debug and server options. Replaying a
capability checkpoint executes the capability again: filesystem writes, external checks and agent
processes are not rolled back by LangGraph. Inspect the existing worktree state before replaying a
mutation. A paused/interrupted Agent Server run is not an authorization to bypass Concorde checks.

## Monitor CLI and Skill calls

Start the server above. In the shell or agent environment that launches capabilities, set:

```bash
export CONCORDE_STUDIO_URL=http://127.0.0.1:2024
```

Keep using the same JSON invocation on stdin, without the Studio `invocation` wrapper:

```bash
python3 scripts/run-capability.py concorde-main <<'JSON'
{"type_id":"concorde-capability-invocation","schema_version":3,"capability_id":"concorde-main","mode":"describe-policy","configuration":null,"input":{"type_id":"concorde-main-request","schema_version":1,"data":{"task":"Explain Concorde's workflow host","target_id":"module.workflows"}}}
JSON
```

Skills already use this same launcher, so no Skill prompt or request-format change is needed. Set
the variable in the environment inherited by the Skill's command runner (or on that command) before invoking it.
This monitors newly submitted calls by forwarding execution to the server. It does not attach to
already-running processes or import historical runs.

Each call creates a Studio thread and prints its thread ID, server URL and run ID to **stderr**.
Open that thread in Studio while the command waits. Policy descriptions remain on stderr. **stdout
contains exactly the original JSON capability result**, with exit code 0 for `succeeded`/`described`
and 3 for `blocked`/`failed`. Unset `CONCORDE_STUDIO_URL` to use ordinary local execution.

The client sends both caller roots; a server belonging to another project, package checkout or
linked worktree returns `workspace_mismatch` before running any capability. Only loopback HTTP URLs
are accepted; redirects and environment HTTP proxies are disabled. Environment variables do not
grant primary-worktree or outer-sandbox authorization. Server-side agent subprocesses retain the
original environment allowlist and native enforcement; they do not inherit this transport switch.

## Events, results and failures

Custom stream events are emitted live and retained as JSON in final `events`:

| Event | Meaning |
| --- | --- |
| `capability_started`, `capability_finished` | Top-level and nested host capability invocation, with invocation ID, depth and final status |
| `stage_started`, `stage_finished`, `stage_failed` | Development-loop stage, including deterministic validation, review skips and readiness; carries `trigger` (`deterministic` or `ai-review` on these events; the persisted `.concorde/worktree.json` graph record also distinguishes `ai-assessment` and `human`) and `iteration`, the repair-loop cycle number for that stage |
| `agent_started`, `agent_finished`, `agent_failed` | Agent executor handoff with capability, stage, role and invocation ID; the same launch's `agent`, `harness` and `agent_binding_digest` identity is available in the run's persisted `policies` (policy descriptions) |

Use API streaming with `stream_mode: ["custom", "updates"]` to receive these events while a run is
active. Studio can inspect persisted `events` and `policies` on completion. Agent events describe
process handoffs, not token-level traces, internal tool calls or proof that a completion passed
admission. The final capability result reports completion/admission failures. Ordinary host graph
nodes encapsulate their stages; loop events do not create independently replayable phase
checkpoints. Abrupt server/process termination may leave only the events already streamed.

A successful Agent Server run can contain a Concorde `blocked` or `failed` result: inspect
`result.status`, `result.errors` and, when present, `result.output.data.outcome`. Malformed envelopes,
configuration mismatch, unsupported permissions and cross-worktree requests retain structured
Concorde error results. Server infrastructure failures/interruption instead produce
`studio_run_failed`; network and HTTP failures produce `studio_transport_failed` on the CLI.

The client never retries run creation and never falls back to local execution. If it loses the
connection or is interrupted, the server-side run may still be active. Inspect the printed thread
before submitting again. An interrupted Studio run can be inspected/resumed from Studio, but the
original CLI exits with code 3; resuming it does not retroactively deliver a new CLI result.

Worktree handoff, change ownership, delivery authorization and native completion receipts continue
to apply. A `concorde-deliver` server session may belong to either the selected source or destination
worktree; unrelated third-worktree and nested delivery remain rejected. Default delivery creates
`concorde/delivered/<change_id>` and removes the source unless `keep_worktree:true` is explicitly
requested. End the source session after removal. Only an explicitly user-authorized separate
`merge_primary:true` request from the sole primary writer updates the primary branch, under the
repository lock and with current integration checks. The Studio client still checks
its caller against the server's bound workspace; third-worktree forwarding cannot impersonate a
participating session. A primary-worktree mutation can prepare a worktree and return a handoff; it
cannot continue development there through this server. Run each server with its own checkout's authority.

## Consumer project setup

The runtime adapter and standard-library client are included with Concorde's Python sources, but
the optional server dependencies and source-development config are not part of the managed consumer
runtime. To use Studio in an installed consumer project, install `langgraph-cli[inmem]` in a separate
server environment and author a project-local entry module such as `studio.py`:

```python
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parent
PACKAGE = PROJECT / ".concorde/framework"
sys.path.insert(0, str(PACKAGE / "src"))
from concorde.spec.contracts import SKILL_NAMES
from concorde.harness.studio import build_studio_flow

for capability in SKILL_NAMES:
    globals()[capability.replace("-", "_")] = build_studio_flow(capability, PROJECT, PACKAGE)
```

Register those variables in that project's `langgraph.json` (for example,
`"concorde-main": "./studio.py:concorde_main"`) and start the server from that project with the
same loopback/single-job options. Its CLI must run from the same project root with the colocated
`.concorde/framework` package. Server roots are trusted startup code, never user input. An updated
installed framework is required; a source server cannot substitute for a consumer server.

## Verification

From the source checkout:

```bash
uv sync --locked --group studio
PYTHONPATH=src .venv/bin/python -m unittest tests.concorde.harness.test_studio tests.concorde.harness.test_studio_client
CONCORDE_TEST_STUDIO=1 PYTHONPATH=src .venv/bin/python -m unittest tests.concorde.harness.test_studio_server
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests/concorde -t . -p 'test_*.py'
```

The opt-in integration suite starts a real Agent Server on an available local port, exercises all
eight assistants, stage admission, direct execution, SSE events, CLI/Skill-launcher forwarding, JSON/exit compatibility
and rejection paths, then stops the server. It uses temporary consumer projects and deterministic
model process responses through the real executor/admission pipeline; it does not require online
model calls or mutate this checkout's primary-worktree registry.
