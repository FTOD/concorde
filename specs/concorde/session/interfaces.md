# Pi session interfaces

The exact files, records, tool parameters and limits of [Pi session](module.md). The entry explains
why they exist; the [requirements](requirements.md) and [scenarios](scenarios.md) state what is
promised about them.

## Session entries

| | Source checkout | Consumer project |
| --- | --- | --- |
| Entry path | `generated/session/pi/concorde-session.ts` | `.pi/extensions/concorde-session.ts` |
| Discovered by Pi | no; loaded only with `-e` and a session selection | yes, as a project extension |
| Launcher | `scripts/run-operation.py` | `.concorde/framework/scripts/run-operation.py` |
| Interpreters tried, in order | `.venv/bin/python`, `.venv/Scripts/python.exe` | `.concorde/.venv/bin/python`, `.concorde/.venv/Scripts/python.exe` |
| Fallback when none exists | none; loading fails | `python3` (`python` on Windows); admission then refuses the run because the local installation is incomplete |
| `explicit_request_only` | `true` | `false` |

An entry imports `concordeSession` from the tracked extension `pi/extensions/concorde-session.ts`
(installed under `.concorde/framework/`), embeds `const CATALOG: SessionCatalog = {...};` and
exports `concordeSession(<project root>, CATALOG, <entry path>)` as its default. Loading refuses
when `CONCORDE_WORKER_POLICY` is set, when the catalog's `schema_version` is not the one below, and
for an explicit-request-only catalog when no selection transport is present.

## Capability catalog

```concorde-contract
{
  "id": "contract.session.catalog",
  "version": 1,
  "schema": {
    "type": "object",
    "properties": {
      "schema_version": {"const": 3},
      "launcher": {"type": "string", "minLength": 1},
      "interpreters": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "explicit_request_only": {"type": "boolean"},
      "operations": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "name": {"type": "string", "minLength": 1},
            "kind": {"enum": ["host", "agent-entry", "workflow"]},
            "native_actions": {"type": "array", "items": {"type": "string", "minLength": 1}},
            "description": {"type": "string", "minLength": 1},
            "guidance": {"type": "string"},
            "request_version": {"type": "integer"},
            "request_schema": {"type": "object"}
          },
          "required": ["name", "kind", "native_actions", "description", "guidance", "request_version", "request_schema"],
          "additionalProperties": false
        }
      }
    },
    "required": ["schema_version", "launcher", "interpreters", "explicit_request_only", "operations"],
    "additionalProperties": false
  },
  "semantics": "The capability catalog embedded in one session entry. launcher is the project-relative launcher path and interpreters the project-relative interpreters tried in order. explicit_request_only is true only for the private entry of a Concorde source checkout. operations lists every public capability once, in catalog order. kind host means run starts the launcher with the capability request; agent-entry means run prepares one exact native Agent call; workflow means run prepares a named asynchronous native workflow that result polls. native_actions lists the values of input.action for which a host capability's run is prepared as a workflow instead, and is empty otherwise. guidance is the fully resolved capability guidance text; request_schema is the self-contained JSON Schema of the data of the typed request <name>-request at request_version. Any other schema_version is refused when the entry loads.",
  "example": {
    "schema_version": 3,
    "launcher": "scripts/run-operation.py",
    "interpreters": [".venv/bin/python", ".venv/Scripts/python.exe"],
    "explicit_request_only": true,
    "operations": [
      {
        "name": "concorde-issues",
        "kind": "host",
        "native_actions": ["solve"],
        "description": "List, show, report, reopen or solve recorded Issues.",
        "guidance": "# concorde-issues\n\nUse this capability to ...\n",
        "request_version": 1,
        "request_schema": {"type": "object"}
      }
    ]
  }
}
```

<a id="participation-catalog"></a>

**Participation.** Pi session defines the catalog and requires it: the session extension reads
nothing else to decide which capabilities exist and which path each takes. Distribution provides it:
its build renders one catalog into every session entry from the Operation catalog, the capability
guidance and the registered request schemas.

## Capability guidance

`prompts/operation-guidance/<name>.md` exists for each public capability and is owned by the
capability's provider. It starts with front matter of exactly two keys: `name`, equal to the file's
capability name, and a nonempty `description`. The body may include the session guidance fragments
with whole-line `@prompts/workflow-host/<fragment>.md` references. After the build resolves them the
body may not contain `{SCRIPT}`, `{FRAMEWORK}` or `{OPERATION}`, and three or more consecutive
newlines are reduced to two.

The session guidance fragments are `candidate-worktree.md`, `init-request-and-no-flags.md`,
`invoke-operation-opener.md`, `lifecycle-no-cognition.md`, `target-identity-opener.md` and
`task-request-fields.md` under `prompts/workflow-host/`, each with front matter `audience: ambient`.

## The concorde tool

Parameters: `operation` (one of the catalog's names), `action` (`run`, `describe` or `result`),
`input` (an object, required for `run`) and `mode` (`execute`, the default, or `describe-policy`,
only for `run`). No other parameter is accepted.

| Action | Behaviour |
| --- | --- |
| `describe` | Returns the description, the guidance and the request schema with its version. Starts no process. |
| `run`, launcher path | Builds the capability request below, starts `<interpreter> <launcher> <name>` in the project root in its own process group with the request on standard input, and returns the printed envelope. |
| `run`, native path | Builds the same request and passes it to the launcher's `--native-context prepare` step, which returns the prepared Agent call or workflow state. |
| `result` | Returns the current state of the named workflow; refused for a capability that is neither `workflow` nor has `native_actions`. |

The capability request is `{"type_id": "concorde-operation-invocation", "schema_version": 3,
"operation_id": <name>, "mode": <mode>, "configuration": null, "input": {"type_id":
"<name>-request", "schema_version": <request_version>, "data": <input>}}`.

A launcher run is a tool error when the launcher was cancelled, exited non-zero, printed output
that is not JSON, or printed an envelope whose `status` is `blocked` or `failed`. The error carries
the envelope and a causal feedback record with layer `session-launcher` and category `cancelled`,
`host-refusal` (an envelope was printed) or `transport` (none was). A native result is a tool error
when its `state` is `rejected`, `failed`, `stale` or `cancelled`, its `native_state` is `failed` or
`stopped`, or it carries a `failure`.

Returned text longer than 49,152 bytes (48 KiB) is cut at that size, and the complete text is
written with mode 0600 to a new file under the system temporary directory whose path the reply
names. On abort the tool sends the launcher SIGTERM; after 5 seconds it kills the launcher's whole
process group.

The appended system prompt section starts with `## Concorde`, names the `concorde` tool, states that
public capabilities run only through it, explains how results and prepared native calls are read,
adds for an explicit-request-only catalog that a capability runs only when the developer asks for it
by name, and ends with one line per capability: `- <name>: <description>`.

## Selection transports

| Transport | Form |
| --- | --- |
| `CONCORDE_SESSION_SELECTION` | The absolute path of a saved selection |
| `PI_SUBAGENT_EXTENSION_BINDINGS` | JSON of at most 16,384 bytes whose `concorde/1` member is exactly `{"selection": "<absolute path>"}` |

Both may be present only when they name the same path. The path is captured when the entry loads
and must not change during the session. The launcher it starts receives the path in
`CONCORDE_SESSION_SELECTION`. The entry verifies the selection by running `<candidate interpreter>
scripts/concorde.py --project-root <root> select-session --verify <path>` with a 30-second limit and
comparing the returned candidate, entry path, embedded catalog and launcher with its own.

`CONCORDE_NATIVE_PROJECT_ROOT`, a test fixture override, names the directory the native preparation
steps treat as the project root. An entry refuses to load with it unless the entry is
explicit-request-only and a selection is present.

## Session selection record

`scripts/concorde.py select-session --mode test --pi-entry P --runtime P [--output P]` returns the
record, and saves it when `--output` is given. `--mode` accepts only `test`. `select-session
--verify P` returns the reverified saved record and accepts no other selection option.

```concorde-contract
{
  "id": "contract.session.selection",
  "version": 1,
  "schema": {
    "type": "object",
    "properties": {
      "schema_version": {"const": 2},
      "mode": {"const": "test"},
      "candidate": {"type": "string", "minLength": 1},
      "fresh_context": {"const": true},
      "fork_context": {"const": false},
      "discover_catalogs": {"const": false},
      "inherit_catalogs": {"const": false},
      "task_delegation": {"const": false},
      "build_digest": {"type": "string", "minLength": 1},
      "runtime": {
        "type": "object",
        "properties": {"path": {"type": "string"}, "digest": {"type": "string"}},
        "required": ["path", "digest"],
        "additionalProperties": false
      },
      "implementation": {
        "type": "object",
        "properties": {"path": {"type": "string"}, "digest": {"type": "string"}},
        "required": ["path", "digest"],
        "additionalProperties": false
      },
      "pi_entry": {
        "type": "object",
        "properties": {
          "path": {"type": "string"},
          "digest": {"type": "string"},
          "content": {"type": "string"},
          "catalog": {
            "type": "object",
            "properties": {"content": {"type": "string"}, "digest": {"type": "string"}},
            "required": ["content", "digest"],
            "additionalProperties": false
          }
        },
        "required": ["path", "digest", "content", "catalog"],
        "additionalProperties": false
      },
      "launch": {
        "type": "object",
        "properties": {
          "cwd": {"type": "string"},
          "pi_args": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["cwd", "pi_args"],
        "additionalProperties": false
      },
      "execution_evidence": {"const": null}
    },
    "required": ["schema_version", "mode", "candidate", "fresh_context", "fork_context", "discover_catalogs", "inherit_catalogs", "task_delegation", "build_digest", "runtime", "implementation", "pi_entry", "launch", "execution_evidence"],
    "additionalProperties": false
  },
  "semantics": "The exact launch inputs of one fresh Pi test session in one candidate. candidate is the absolute, unaliased candidate root. build_digest is the SHA-256 of the candidate's build manifest bytes. runtime is the candidate launcher scripts/run-operation.py and implementation the tracked session extension pi/extensions/concorde-session.ts, each with the digest the build manifest records for it. pi_entry is the candidate's private entry generated/session/pi/concorde-session.ts with its digest, its complete text and the exact embedded catalog text with that text's digest. launch.cwd is the candidate root and launch.pi_args is exactly --no-session --no-context-files --no-skills --no-prompt-templates --no-themes --no-extensions -e <entry path>. The record is valid only while a fresh recomputation from the current candidate equals it byte for byte in canonical form. execution_evidence is always null: the record is never evidence that Pi loaded the entry, that a tool ran or that a model executed. Every digest is sha256: followed by 64 lowercase hexadecimal digits.",
  "example": {
    "schema_version": 2,
    "mode": "test",
    "candidate": "/work/concorde-candidate",
    "fresh_context": true,
    "fork_context": false,
    "discover_catalogs": false,
    "inherit_catalogs": false,
    "task_delegation": false,
    "build_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "runtime": {"path": "/work/concorde-candidate/scripts/run-operation.py", "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111"},
    "implementation": {"path": "/work/concorde-candidate/pi/extensions/concorde-session.ts", "digest": "sha256:2222222222222222222222222222222222222222222222222222222222222222"},
    "pi_entry": {
      "path": "/work/concorde-candidate/generated/session/pi/concorde-session.ts",
      "digest": "sha256:3333333333333333333333333333333333333333333333333333333333333333",
      "content": "// generated session entry\n",
      "catalog": {"content": "{\"schema_version\": 3}", "digest": "sha256:4444444444444444444444444444444444444444444444444444444444444444"}
    },
    "launch": {
      "cwd": "/work/concorde-candidate",
      "pi_args": ["--no-session", "--no-context-files", "--no-skills", "--no-prompt-templates", "--no-themes", "--no-extensions", "-e", "/work/concorde-candidate/generated/session/pi/concorde-session.ts"]
    },
    "execution_evidence": null
  }
}
```

<a id="participation-selection"></a>

**Participation.** Pi session provides the selection record to external callers: the user session
or host that launches a fresh tester reads `launch` and passes the saved path through a selection
transport. Pi session keeps the record deterministic for an unchanged candidate and refuses every
record that a fresh recomputation does not reproduce.

Selection refuses, with build error code `stale_build` for stale or changed bytes and
`invalid_build` otherwise: a relative or aliased path, a path outside the candidate, a runtime other
than the candidate launcher, an entry other than the candidate's private entry, a symbolic link
anywhere below `src/concorde`, `agents`, `operations`, `prompts`, `protocol`, `pi` or `scripts`
(ignoring `node_modules` and `__pycache__`), a build manifest that is missing, malformed or records
an unsafe path, a build that is not fresh, outputs that differ from a fresh render, and an entry or
launcher whose bytes differ from what the manifest records. A saved selection must lie strictly
below `<candidate>/.concorde/work/`.

## Task subagent projection

The Task subagent definitions are `TaskSubagentProfile` records `{name, prompt, tools, extensions,
source_only, acceptance_role}` in `agents/task_subagent.py` (the tester) and `agents/source/` (the
maintenance worker). The projector renders `.pi/agents/<name>.md` with this front matter, followed by
a generated-file comment and the resolved prompt:

| Field | tester | maintenance-worker |
| --- | --- | --- |
| `tools` | read, grep, find, ls, test_command | read, grep, find, ls, bash, edit, write |
| `extensions` | `concorde-tester.ts` and the session entry of the layout | `concorde-maintenance.ts`, `concorde-brief-lifecycle.ts` |
| `acceptanceRole` | `read-only` | absent |
| common | `systemPromptMode: replace`, `inheritProjectContext: false`, `inheritGlobalContext: false`, `inheritSkills: false`, `defaultContext: fresh`, `excludeTools: subagent`, `async: true`, `completionGuard: false` | same |
| rendered in the installed layout | yes | no |

The projector also renders, for the source layout only, `.pi/extensions/concorde-coordinator.ts`,
which appends the resolved `prompts/user-session/source/coordinator.md` to the system prompt, and
`.pi/extensions/concorde-brief-lifecycle.ts`, which re-exports the user session variant of the brief
lifecycle; and for both layouts `.pi/extensions/concorde-observe.ts`, which re-exports the passive
observer. Extension paths in a definition are relative to `.pi/agents/`.

Source-only files: `agents/source/`, `prompts/task-subagent/source/`, `prompts/user-session/`,
`pi/extensions/concorde-maintenance.ts`, `pi/extensions/concorde-brief-lifecycle.ts`, and the
rendered `.pi/agents/maintenance-worker.md`, `.pi/extensions/concorde-coordinator.ts` and
`.pi/extensions/concorde-brief-lifecycle.ts`.

The tester's tool guard allows only `read`, `grep`, `find`, `ls`, `test_command`,
`structured_output` and `contact_supervisor`. The maintenance guard blocks every tool call unless
the working directory contains `concorde.json` and `specs/concorde/module.md`, and always blocks
`subagent` and `concorde`.

## Tester command

`test_command` takes `command` (a string of at most 32,768 characters), `timeout` (1 to 3,600
seconds, default 600) and `reports` (at most 16 unique names of 1 to 240 characters, each a file the
command writes below `$CONCORDE_CHECK_REPORT_DIR`). It starts `<interpreter> -m
concorde.distribution.tester_check` in the tester's working directory with `PYTHONPATH` set to the
package's `src`, `PYTHONDONTWRITEBYTECODE=1`, `CONCORDE_TEST_TOOL_CALL_ID` set to the tool call
identity and `CONCORDE_SESSION_SELECTION` when a selection is bound. The interpreter is the source
checkout's `.venv/bin/python` or, installed, `.concorde/.venv/bin/python`; a missing interpreter
fails the call.

The bridge reads `{"command": string, "timeout": number in (0, 3600], "reports"?: [names]}` and
refuses any other key. It reverifies the selection first when one is set. It prints
`{"tester_check_ready": true, "execution_id": "..."}`, runs `/bin/bash -c <command>` through Check
execution's tester command execution with a private `/tmp`, and prints one response:
`returncode`, `timed_out`, `cancelled`, `cancellation_requested`, `error`, `evidence` (the export
summary) and, for each of `stdout` and `stderr`, the last 20,000 bytes, the total byte count
(`<stream>_bytes`) and a `<stream>_truncated` flag. SIGTERM or SIGINT sets a cancellation request
that the execution observes at its next check, so evidence export is never interrupted. The tool
sends SIGTERM on abort only after the ready line, treats more than 1 MiB of bridge output as a
failure, and fails the call unless `returncode` is 0, `cancelled` is false, `error` is null and the
evidence summary reports `complete`.

## Task brief

A brief is an object with exactly the string fields `goal`, `grant`, `stage`, `objective`, `blocker`
(`"none"` when there is none) and `next`, and the array fields `decisions`, `completed`, `checks` and
`evidence`. Every text is nonblank and at most 2,000 characters, every array has at most 16 entries,
and the serialized object is at most 12,000 characters.

The source user session's variant registers the tool `update_task_brief` with parameter `brief`,
which replaces the brief and returns a copy of it. Both variants accept the command `/task-brief
<JSON>`, register `/session-compact` (which waits for idle and runs Pi compaction), and read a
`task-brief` fenced block from a `contact_supervisor` call whose `reason` is `progress_update`.

The extension appends session entries of custom types `concorde.task-brief.v1` (the brief, or
`null` after an invalid one), `concorde.task-brief-injected.v1` (the compaction entry identity an
injection answered), `concorde.task-brief-missing.v1`, `concorde.task-brief-error.v1` and
`concorde.compaction-failed.v1`, and restores its state from them on session start and tree change.
After a `session_compact` event it marks the latest compaction entry pending; at the next `context`
event it appends one hidden custom message holding the current brief, marked as reported memory that
grants nothing, and records the injection. A failed compaction clears the pending mark.

## Coordinator status commands

The coordinator instructions use the primary checkout's `status` command, run in the primary
checkout and never in a child:

| Step | Command |
| --- | --- |
| Register a candidate | `scripts/concorde.py status --register "$candidate" --task "$goal" --mode maintenance` |
| Read all records | `scripts/concorde.py status` |
| Bind a launched child | `scripts/concorde.py status --change-id "$change_id" --child "$child_id" --phase maintenance` (or `--phase test`) |
| Release a stopped child | the bind command with `--release`, using the current owner's phase |
| Record an authorized merge | `scripts/concorde.py status --change-id "$change_id" --manual-merge "$commit" --cleanup pending` |

## TODO notes

One Markdown file per note under `.concorde/todos/` in the source user session's worktree, with no
index file, no metadata companion and no registry entry.

## Installed-output handoff

`tests/concorde/support/install_output_handoff.py` provides `install_selected_fixture(target,
selection)`. It requires `CONCORDE_CHECK_TMPDIR`, a canonical `target` strictly inside that scratch
that is absent or empty, and `CONCORDE_SESSION_SELECTION` equal to `selection`, which must load as a
test selection of the source. It admits the source package, runs the source installer into `target`
with an environment from which `CONCORDE_SESSION_SELECTION`, the `concorde/1` binding,
`CONCORDE_NATIVE_PROJECT_ROOT`, `CONCORDE_WORKER_POLICY`, `PYTHONPATH` and `PYTHONHOME` are removed,
verifies the installation with the installed interpreter, and requires the installed package
identity to equal the admitted one and the selection and source to be unchanged afterwards. It
writes `installed-output-provenance.json` (schema 1, smaller than 8,000 bytes) into the scratch and
returns that record with the separated environment.

## Participation in other Modules' contracts

<a id="participation-admission"></a>

Pi session requires Request admission's [invocation](../harness/admission/contracts.md#contract.admission.invocation)
contract at version 3, [result](../harness/admission/contracts.md#contract.admission.result) contract
at version 4 and [feedback](../harness/admission/contracts.md#contract.admission.feedback) contract at
version 1: the tool builds only requests of that shape, reads only envelopes of that shape and
attaches feedback records of that shape to its tool errors.

<a id="participation-build-manifest"></a>

Pi session requires Distribution's [build manifest](../distribution/interfaces.md#contract.distribution.build-manifest)
contract at version 1: selection judges a candidate's build current exactly as that contract
defines freshness, and takes the recorded digests of the launcher, the session extension and the
private entry from it.
