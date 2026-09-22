# Pi session integration

This topic explains how a developer's Pi session reaches Concorde: the session entry and its
`concorde` tool, the Task subagent files the build writes for Pi to discover, how a fresh test
session is pinned to one candidate's exact build, and how a tester's commands run. None of these
pieces grants anything by itself; the Host and the Harness make every decision.

## Terminology

| Term | Definition |
| --- | --- |
| [Developer](../vocabulary.md#concept.concorde.developer) | |
| [User session](../vocabulary.md#concept.concorde.user-session) | |
| [Capability](../vocabulary.md#concept.concorde.capability) | |
| [Host](../vocabulary.md#concept.concorde.host) | |
| [Task subagent](../vocabulary.md#concept.concorde.task-subagent) | |
| [Worker](../vocabulary.md#concept.concorde.worker) | |
| [Agent](../agents/module.md#concept.agents.agent) | |
| [Workflow](../harness/execution/module.md#concept.execution.workflow) | |
| [Candidate](../harness/worktrees/module.md#concept.worktrees.candidate) | |

Session entry, capability catalog, launcher and session selection are defined in the
[Distribution entry](module.md#terminology).

## The two session entries

The build renders the same catalog into two entries that differ only in where they live and what
they run:

| | Source checkout | Consumer project |
| --- | --- | --- |
| Entry | `generated/session/pi/concorde-session.ts` | `.pi/extensions/concorde-session.ts` |
| Discovered by Pi | no; loaded explicitly with `-e` and a session selection | yes, as a project extension |
| Launcher | `scripts/run-operation.py` | `.concorde/framework/scripts/run-operation.py` |
| Interpreters tried | `.venv/bin/python`, `.venv/Scripts/python.exe` | `.concorde/.venv/bin/python`, `.concorde/.venv/Scripts/python.exe` |
| Explicit request only | yes | no |

When the entry loads it refuses to run inside a terminal worker (a process with
`CONCORDE_WORKER_POLICY` set), refuses any catalog other than schema 2, and, for the source entry,
refuses to load without a session selection. The consumer entry falls back to `python3` when none of
its interpreters exists; admission then refuses the run because the local installation is
incomplete. The source entry has no such fallback.

## The concorde tool

Before each turn the entry appends a Concorde section to the system prompt. It names the `concorde`
tool, says that public capabilities run only through it, explains how results and native calls are
read, lists every capability with its description, and in the source checkout adds that a capability
runs only when the developer asks for it by name.

The tool takes `operation` (one of the catalog's names), `action` and, for `run`, `input` and an
optional `mode` of `execute` (the default) or `describe-policy`, which previews the context and
permissions without running an Agent.

| Kind in the catalog | Capabilities | What `run` does |
| --- | --- | --- |
| `host` | `concorde-init`, `concorde-configure`, `concorde-validate`, `concorde-deliver` | Runs the launcher with the invocation on standard input and returns its result |
| `agent-entry` | `concorde-context-solve`, `concorde-tasks`, `concorde-implement` | Prepares one exact native Agent call for the user session to start |
| `workflow` | `concorde-plan`, `concorde-spec-review`, `concorde-code-review`, `concorde-issues` | Prepares a named asynchronous native workflow; `result` polls it |

`concorde-issues` runs through the launcher like a Host capability for every action except
`solve`. For a launcher run, the tool wraps `input` in a `concorde-operation-invocation` envelope of
version 3 whose `input` is the typed `<capability>-request` at the catalog's request version, starts
the launcher in its own process group in the project root, and returns the result with a one-line
usage summary taken from the launcher's diagnostics. A non-zero exit, unreadable output or a
`blocked` or `failed` status becomes a tool error that carries the envelope. For native paths the
tool asks the launcher's `--native-context prepare` entry to prepare the call; the returned call is
started by the user session through the pi-subagents `subagent` tool, and Agent execution accepts or
rejects the Agent's proposal afterwards. A native structured output or a passing gate is never
itself success.

`describe`, an unknown capability and a `run` without `input` never start the launcher. Results larger
than 48 KiB are cut at that size and saved whole to a private temporary file whose path the text
names. Aborting the turn sends the launcher SIGTERM; the launcher cancels its work and prints its
result, and if it has not exited after five seconds the whole process group is killed.

## Task subagent files

Pi discovers project agents in `.pi/agents/` and project extensions in `.pi/extensions/`. The build
writes these from canonical sources, so that the user session can delegate to real Task subagents
and load its own coordination instructions:

| File | Written for | Content |
| --- | --- | --- |
| `.pi/agents/tester.md` | source and consumer | The tester definition from `prompts/task-subagent/tester.md` |
| `.pi/agents/maintenance-worker.md` | source only | The maintenance-worker definition from its source-only prompt |
| `.pi/extensions/concorde-coordinator.ts` | source only | Appends the coordinator prompt `prompts/user-session/source/coordinator.md` to the user session's system prompt |
| `.pi/extensions/concorde-brief-lifecycle.ts` | source only | Re-exports the user session's brief lifecycle from `pi/extensions/concorde-brief-lifecycle.ts` |
| `.pi/extensions/concorde-observe.ts` | source and consumer | Re-exports the passive observer from `pi/extensions/concorde-observe.ts` |

Each agent definition takes its tools, extensions and acceptance role from the Task subagent
profiles in Agents and fixes the isolation settings: the prompt replaces Pi's default prompt, no
project context, global context or Skills are inherited, context starts fresh, the `subagent` tool
is excluded, and the run is asynchronous. The tester's extension list includes the session entry of
its layout, so a tester can call capabilities of exactly the build it tests.

The coordinator extension is loaded only by the source user session. Task subagents do not receive
it, because their definitions disable ambient extensions and list their own explicitly, and a
consumer installation never ships it. What the coordinator, tester and maintenance worker do is
defined by Agents; the build only renders and registers them.

## Session selection

A tester of a candidate must load that candidate's build and nothing else. The user session first
creates a selection in the candidate:

```sh
.venv/bin/python scripts/concorde.py select-session --mode test \
  --pi-entry "$PWD/generated/session/pi/concorde-session.ts" \
  --runtime "$PWD/scripts/run-operation.py" \
  --output "$PWD/.concorde/work/pi-selection.json"
```

Selection accepts only absolute paths inside the candidate with no symbolic link anywhere on them,
and only the candidate's own private entry and launcher. It refuses a candidate whose sources
contain a symbolic link, whose build is not fresh, or whose outputs differ from a fresh render. The
record it returns names the build manifest digest, the launcher and session extension digests, the
complete entry bytes and the exact catalog embedded in them, and the Pi flags the host must use:
`--no-session --no-context-files --no-skills --no-prompt-templates --no-themes --no-extensions` plus
`-e` with the entry. Mode `maintenance` takes no entry at all, because a maintenance writer works
without any Concorde catalog.

A selection is saved only under the candidate's `.concorde/work/` scratch. `select-session --verify
<path>` recomputes the whole record from the current candidate and fails unless it is identical. The
host passes the saved path to a fresh Pi process in `CONCORDE_SESSION_SELECTION`, or for a native
pi-subagents launch as the extension binding `{"concorde/1": {"selection": "<path>"}}`. The private
entry verifies the selection with the candidate's own `.venv` interpreter before it registers the
tool and again before every call, compares the recorded entry, catalog and launcher with its own,
refuses a selection that changed during the session, and refuses a redirect to LangGraph Studio. The
launcher reverifies the selection before it runs anything.

A selection proves which bytes a session was told to load. It is not evidence that Pi loaded them,
that a tool was called or that a model ran.

## The tester bridge

The tester Task subagent has no shell. Its `test_command` tool, provided by the tester extension
that Check execution owns, runs `python -m concorde.distribution.tester_check` with the candidate's
or the installed Framework's interpreter and sends it a request on standard input:
`{"command": "...", "timeout": 120, "reports": ["junit.xml"]}`.

The bridge refuses a command longer than 32768 characters, a timeout outside 1 to 3600 seconds or
any other field. It prints a ready line, runs the command with `/bin/bash -c` through Check
execution's executor in the read-only sandbox with a private temporary directory, and prints one
response with the exit code, time-out and cancellation flags, the last 20000 bytes of each output
stream with their full sizes, and a summary of the exported evidence. SIGTERM or SIGINT requests
cancellation at the executor's next check instead of interrupting evidence export. A failed command
is a normal response, not a bridge failure.
