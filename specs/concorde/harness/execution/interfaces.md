# Host-step protocol and workflow runtime

The JSON protocol between a workflow script or Host-step command and the Host, and the Pi-side
runtime that registers and runs Workflows. The [entry](module.md#concept.execution.workflow)
explains when a Workflow is used; each provider's step table says what its own steps do.

## The protocol {#the-protocol}

A **Host-step command** is `<python> <launcher> --native-context <action> <descriptor> <digest>`,
optionally followed by a slot key, run with the project root as working directory. It reads at most
1 MiB of JSON from standard input (an empty input is `{}`) and prints exactly one JSON object on
standard output. It exits 0 with the response, or 3 with a rejection. Every command first checks
that the descriptor's bytes still have the digest it was given.

```concorde-contract
{
  "id": "contract.execution.host-step",
  "version": 1,
  "schema": {
    "$defs": {
      "digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
      "command": {"type": "array", "minItems": 1, "items": {"type": "string"}},
      "binding": {
        "type": "object",
        "required": ["argv", "root", "descriptor", "digest"],
        "properties": {
          "argv": {"$ref": "#/$defs/command"},
          "root": {"type": "string"},
          "descriptor": {"type": "string"},
          "digest": {"$ref": "#/$defs/digest"}
        },
        "additionalProperties": false
      },
      "workflow": {
        "type": "object",
        "required": ["name", "script", "host", "steps", "helpers", "commands", "expansion"],
        "properties": {
          "name": {"type": "string", "pattern": "^concorde\\.[a-z-]+\\.[A-Za-z0-9:-]+$"},
          "script": {"type": "string"},
          "host": {"type": "string"},
          "steps": {"type": "array", "items": {"type": "string"}, "uniqueItems": true},
          "helpers": {"type": "array", "items": {"type": "string"}},
          "commands": {"type": "object", "additionalProperties": {"$ref": "#/$defs/command"}},
          "expansion": {"type": "object"}
        },
        "additionalProperties": false
      },
      "prepared": {
        "type": "object",
        "required": ["state", "accepted", "descriptor", "digest", "ticket", "binding"],
        "properties": {
          "state": {"const": "prepared"},
          "accepted": {"const": false},
          "descriptor": {"type": "string"},
          "digest": {"$ref": "#/$defs/digest"},
          "ticket": {"type": "string"},
          "binding": {"$ref": "#/$defs/binding"},
          "call": {"type": "object"},
          "workflow": {"$ref": "#/$defs/workflow"},
          "result": {"type": "object"}
        },
        "additionalProperties": false
      },
      "staged": {
        "type": "object",
        "required": ["schema_version", "ticket", "invocation_id", "proposal_digest", "state", "accepted"],
        "properties": {
          "schema_version": {"const": 1},
          "ticket": {"type": "string"},
          "invocation_id": {"type": "string"},
          "proposal_digest": {"$ref": "#/$defs/digest"},
          "state": {"const": "staged"},
          "accepted": {"const": false}
        },
        "additionalProperties": false
      },
      "step": {
        "type": "object",
        "required": ["state"],
        "properties": {"state": {"type": "string"}, "accepted": {"type": "boolean"}}
      },
      "child_terminal": {
        "type": "object",
        "required": ["kind", "ticket", "key", "agent", "runId", "invocation_id", "proposal_digest", "metadata", "result"],
        "properties": {
          "kind": {"const": "concorde.child-terminal"},
          "ticket": {"type": "string"},
          "key": {"type": "string"},
          "agent": {"type": "string"},
          "runId": {"type": "string"},
          "invocation_id": {"type": "string"},
          "proposal_digest": {"$ref": "#/$defs/digest"},
          "metadata": {"type": "string"},
          "result": {"type": "object"}
        },
        "additionalProperties": false
      },
      "failure_emission": {
        "type": "object",
        "required": ["kind", "key", "feedback"],
        "properties": {
          "kind": {"const": "concorde.failure"},
          "key": {"type": "string"},
          "feedback": {"type": "object"}
        },
        "additionalProperties": false
      },
      "workflow_result": {
        "type": "object",
        "required": ["state", "accepted", "native_state", "native_error", "failure", "run_id"],
        "properties": {
          "state": {"enum": ["running", "failed", "stale", "accepted"]},
          "accepted": {"type": "boolean"},
          "output": {"type": "object"},
          "native_state": {"type": ["string", "null"]},
          "native_error": {"type": ["string", "null"]},
          "failure": {"type": ["object", "null"]},
          "run_id": {"type": "string"},
          "error": {"type": "string"}
        },
        "additionalProperties": false
      },
      "stop": {
        "type": "object",
        "required": ["state", "accepted"],
        "properties": {"state": {"const": "cancelled"}, "accepted": {"const": false}},
        "additionalProperties": false
      },
      "rejected": {
        "type": "object",
        "required": ["state", "accepted", "result"],
        "properties": {
          "state": {"const": "rejected"},
          "accepted": {"const": false},
          "result": {"type": "object"}
        },
        "additionalProperties": false
      }
    },
    "anyOf": [
      {"$ref": "#/$defs/prepared"},
      {"$ref": "#/$defs/staged"},
      {"$ref": "#/$defs/step"},
      {"$ref": "#/$defs/child_terminal"},
      {"$ref": "#/$defs/failure_emission"},
      {"$ref": "#/$defs/workflow_result"},
      {"$ref": "#/$defs/stop"},
      {"$ref": "#/$defs/rejected"}
    ]
  },
  "semantics": "One message of the Host-step protocol. `prepared` is the Host's answer to a native `prepare`: the descriptor path and digest that every later Host-step command must present, the ticket, the binding the Pi side uses to run Host-step commands, and either the single `call` or the `workflow` plan whose script, helpers and commands are package-relative paths and argument vectors the registrar uses verbatim. `staged` is printed by a gate command after a run; it is canonical JSON of at most 8,000 UTF-8 bytes, bound to one ticket and one proposal digest, and never an acceptance. `step` is the answer to one named workflow Host step: `state` plus the fields the provider's step table fixes, within the bound that table states. `child_terminal` and `failure_emission` are the records a workflow script emits into pi-subagents' status for each staged child and each stop; the Host reconciles them with pi-subagents' own step records and never trusts them alone. `workflow_result` answers the result step: `running` while pi-subagents runs the Workflow, `accepted` or `failed` once a receipt exists, `stale` when the inputs changed before a failure could be recorded, with the native state and a causal feedback record when the Workflow did not complete. `stop` answers the stop step and makes every later step fail. `rejected` is printed with exit status 3 when the Host refuses a step; its `result` is the result envelope with the errors. No message carries model prose, a transcript or a proposal's content except `workflow_result.output`, which is the accepted result envelope.",
  "example": {
    "schema_version": 1,
    "ticket": "2b1f6c1e-4d0a-4d8e-9a57-1f0c2f1b7e10",
    "invocation_id": "2b1f6c1e-4d0a-4d8e-9a57-1f0c2f1b7e10",
    "proposal_digest": "sha256:9f2c1b7a4e6d8c0f3a5b7d9e1f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0e2b4d6f8a",
    "state": "staged",
    "accepted": false
  }
}
```

### Actions every Workflow may use

| Action | Answer |
| --- | --- |
| `workflow-<step>` | The workflow hook's answer to that step, a `step` message |
| `workflow-result` | A `workflow_result`; calls the hook's `on_failure` once when a failed or stopped Workflow has no receipt yet |
| `workflow-stop` | A `stop`; creates the Workflow's stop marker |
| `stage` (or a provider's slot gate) | A `staged` document for one slot |
| `check`, `admit`, `invalidate`, `observe-error`, `report`, `checks` | As for a single call, see [Result gate](agent-calls.md#result-gate) |

A workflow script bounds and parses every step answer it reads and stops with a `failure_emission`
when an answer is malformed, too large or foreign to its ticket. It records one `child_terminal`
emission for each child it ran, after checking that the child completed, its single gate passed and
the staged document names the child's ticket; it copies only the native result fields the driver
needs (`agent`, `exitCode`, `error`, `detached`, `interrupted`, `stopped`, `terminalOutcome`,
`timedOut`, `metadataSaveError`, `outputSaveError`, `transcriptError`, `launchContractDigest`,
`artifactPaths`, `structuredOutputPath`).

## Transport limits

`nativeCommand(binding, action, value)` runs the bound argument vector with `action`, the descriptor
path and its digest, the binding's root as working directory and `value` as JSON on standard input,
and resolves with the one JSON document printed.

| Limit or outcome | Rule |
| --- | --- |
| Deadline | 30 seconds; for `checks`, the time the driver computed from the configured check limits plus ten seconds |
| Output bound | 2 MiB each on standard output and standard error; more kills the command |
| Failure categories | `timeout`, `cancelled`, `observation` (output bound), `host-refusal` (a rejection with errors), `native-exit`, `transport` |
| Rejection | a `rejected` answer or a nonzero exit is a failure, never a result |

A Workflow's own Host steps are run by pi-subagents with the deadline the script passes to
`runs.host`. A provider's Host-step helper uses the shared helper module to wait up to 15 seconds for
the launch binding, run launch preflight for the slots a step issued, and invoke the Python step
with a 2 MiB output bound; the Host-step error adapter keeps a failed helper's causal feedback in
the Workflow directory before pi-subagents clips its output.

## Workflow registrar

The native call extension receives a `prepared` answer. For a single call it keeps the call pending
and intercepts the matching `subagent` call. For a `workflow` plan the registrar:

1. reads the script and each helper from the package root, inlines the shared causal-feedback
   helpers and then each listed helper with its `export` keywords removed, and substitutes the
   expansion JSON for the script's single `__CONCORDE_WORKFLOW__` placeholder;
2. registers a workflow resource named `workflow.name` with pi-subagents for the current session,
   which resolves only for arguments exactly `{"ticket": <ticket>}` and exposes exactly the plan's
   commands as its Host commands;
3. returns the workflow call `{"workflow": name, "args": {"ticket": ticket}, "cwd": <project root>,
   "async": true, "mission": false, "context": "fresh", "intercomBridge": {"mode": "off"}}`;
4. intercepts the first matching `subagent` call, blocks any other or repeated one, and after launch
   writes `workflow-binding.json` with the async directory and run identity exclusively in the
   Workflow directory;
5. answers the `concorde` tool's `result` action with the `workflow-result` step and releases the
   registration once the Workflow is no longer running;
6. on session shutdown or replacement, runs `workflow-stop` and asks pi-subagents to stop a launched,
   unfinished Workflow, or invalidates one that never launched.

The registrar knows no provider: which script runs, which steps exist and what they print all come
from the plan.

## Requirements

### req.execution.host-step-bounded — A Host step is finite and bounded

A Host-step command SHALL be treated as failed when it exceeds its deadline or output bound, exits
nonzero or answers with a rejection.

### req.execution.prepared-launch-once — A prepared call launches once

A prepared Agent call or Workflow SHALL be launched at most once and only with exactly its prepared
call.

### req.execution.registrar-from-plan — Workflows come only from their plan

The workflow registrar SHALL take a Workflow's script, helpers and Host-step commands only from the
prepared workflow plan.

## Scenarios

### scenario.execution.workflow-register — Register a prepared Workflow

- GIVEN a capability whose declaration names a workflow hook, and a request admitted for it
- WHEN the driver prepares it and the registrar receives the workflow plan
- THEN the registrar registers the script built from the plan under the plan's name for the current session
- AND the `concorde` tool returns the workflow call with the issued ticket
- BUT no Agent has run and nothing is accepted

### scenario.execution.workflow-foreign-call — An altered Workflow call is blocked

- GIVEN a registered Workflow
- WHEN the user session calls `subagent` with different arguments, another workflow name or the same call a second time
- THEN the registrar blocks the tool call
- AND the resource refuses to resolve for any arguments other than the issued ticket

### scenario.execution.workflow-launch-failure — A launch without a binding fails

- GIVEN a registered Workflow
- WHEN pi-subagents returns from the launch with an error or without an async directory and run identity
- THEN the tool result is a failure with a `workflow-launch` causal feedback record
- AND a later `result` reports `failed`, not `running`

### scenario.execution.workflow-running — A running Workflow is not a result

- GIVEN a launched Workflow that pi-subagents still runs
- WHEN the user session asks the `concorde` tool for its result
- THEN the answer is `state: "running"`, `accepted: false` with the native run identity

### scenario.execution.workflow-accepted — A finished Workflow reports its receipt

- GIVEN a Workflow whose final Host step wrote an accepted receipt
- WHEN the user session asks for its result
- THEN the answer is `state: "accepted"`, `accepted: true` with the receipt's result envelope
- AND the registration is released

### scenario.execution.workflow-failed — A failed Workflow reports its cause

- GIVEN a Workflow that pi-subagents reports as failed or stopped before a receipt was written
- WHEN the user session asks for its result
- THEN the driver calls the workflow hook's `on_failure` once and records what it returns
- AND the answer is `failed` with the native state and a causal feedback record naming the failed step or child
- BUT nothing is accepted

### scenario.execution.workflow-stop — Stopping ends a Workflow's steps

- GIVEN a launched Workflow that has not finished
- WHEN the session shuts down or a new preparation replaces it
- THEN the registrar runs `workflow-stop` and asks pi-subagents to stop the run
- AND every later workflow step fails with `execution_cancelled`
- BUT a receipt written before the stop stays a separate, accepted fact

### scenario.execution.host-step-failure — A failing Host step is never a result

- GIVEN a Host-step command
- WHEN it passes its deadline, exceeds its output bound, exits nonzero or answers `rejected`
- THEN the caller receives a failure with category `timeout`, `observation`, `native-exit` or `host-refusal`, keeping the Host's errors and bounded diagnostics as causes
- BUT no partial answer is used
