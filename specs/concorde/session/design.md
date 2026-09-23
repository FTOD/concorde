# Pi session design notes

Extended explanations behind the [Pi session](module.md) entry: a worked example, the selection
flow in detail, what is enforced and what is only instructed, and the Module's incidental choices
and open questions. Exact fields and limits are in the [interfaces](interfaces.md).

## A worked example

The user session first calls `concorde` with `{"operation": "concorde-validate", "action":
"describe"}`, reads the guidance and schema, and then calls `{"operation": "concorde-validate",
"action": "run", "input": {"change_id": "..."}}`. The tool wraps `input` unchanged in a capability
request, starts the launcher in the project root with the request on its standard input, and returns
the printed result envelope. A `run` may take long and blocks the turn.

For `concorde-context-solve`, `concorde-tasks` and `concorde-implement`, `run` returns one exact Agent
call prepared by the Host, which the user session passes unchanged to the pi-subagents `subagent`
tool. For `concorde-plan`, the two review capabilities and the `solve` action of `concorde-issues`,
`run` prepares a named workflow and `result` reports its state as the Host reconciled it. A `run`
with `mode: "describe-policy"` asks the Host to describe the context and permissions an execute run
would use, without starting an Agent. Calling `describe` repeatedly is free; repeating `run` is a new
request, and the Host decides whether it resumes or refuses. A very large result is cut in the reply
and saved whole to a private temporary file whose path the reply names.

## Why the tool is thin

Every check that matters, the typed request, the configuration, the worktree, the permissions and
the acceptance of a result, belongs to the Host, because the model can call the tool with anything.
The catalog carries each capability's path, including which actions of a mixed capability are
workflows, so the tool never needs its own list of provider capabilities, and the installed entry
and the private entry come from one build.

## Selecting a candidate in detail

```sh
.venv/bin/python scripts/concorde.py select-session --mode test \
  --pi-entry "$PWD/generated/session/pi/concorde-session.ts" \
  --runtime "$PWD/scripts/run-operation.py" \
  --output "$PWD/.concorde/work/pi-selection.json"
```

Selection accepts only absolute, unaliased paths inside the candidate and only the candidate's own
private entry and launcher, refuses a stale build, and records the Pi flags a fresh session must
use. `select-session --verify <path>` recomputes the record and fails unless nothing changed. The
user session launches the tester through pi-subagents with fresh context and the extension binding
`{"concorde/1": {"selection": "<absolute path>"}}`, or a standalone Pi process with
`CONCORDE_SESSION_SELECTION`. Verification happens at load, before every tool call and in the
launcher, because each step could otherwise run with bytes that changed after the previous check.
A missing or stale candidate artifact blocks the test; nothing falls back to the primary checkout's
build or an installed copy. The record carries no evidence field that could be filled in: what a
session actually did is observed elsewhere.

## What is enforced

| Rule | How it holds |
| --- | --- |
| The tester runs commands only through `test_command` | Enforced by the tester's tool guard, which blocks every other tool |
| A tester command cannot change project files | Enforced by Check execution's read-only boundary; the command still reads anything the user can read, shares the network and receives the environment |
| The maintenance worker works only in a Concorde source checkout and never calls `subagent` or `concorde` | Enforced by the maintenance guard on every tool call |
| The maintenance worker writes only in its own candidate | Not enforced; it has `bash`, `edit` and `write`, and the rule is an instruction |
| One writer per candidate, register before launch, bind and release | The status commands refuse conflicting ownership; the sequence itself is an instruction to the source user session |
| A running child keeps its launch instructions | Holds because Pi loads a child's instructions and extensions once at launch |
| TODO notes change no implementation or Spec | Not enforced; an instruction to the source user session |
| A worker cannot call capabilities | Agents are launched without the session entry, and the tester's and maintenance worker's guards block the `concorde` tool; a worker with a shell can still start the launcher directly, which is not enforced |

Several scenarios of this Module are instruction contracts: a check of the rendered instructions
shows what a session is told, not that a live model always complies.

## Incidental choices and transitional paths

The selection service, the Task subagent projector and the tester bridge currently live under
`src/concorde/distribution/`; they belong to Pi session and may move to `src/concorde/session/`.

The environment variable `CONCORDE_NATIVE_PROJECT_ROOT` is a test fixture override: when set, the
native preparation steps run against that directory as the project root. The private entry accepts
it only when it was loaded with a verified selection, so it cannot redirect an ordinary session;
consumer entries refuse it.

## Open questions

- The tester's definition lists the session entry of its layout among its extensions, so the
  selection is verified when it starts, but its tool guard blocks the `concorde` tool. Whether a
  tester should be able to call capabilities of the build it tests is undecided.
