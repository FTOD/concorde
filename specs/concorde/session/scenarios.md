# Pi session scenarios

The concrete situations [Pi session](module.md) promises to handle. Module-wide obligations are
stated once in the [requirements](requirements.md); exact fields and limits are in the
[interfaces](interfaces.md). Scenarios about the coordinator instructions and TODO notes are
instruction contracts: checking the rendered instructions shows what a session is told, not that a
live model always complies.

## The concorde tool

### scenario.session.prompt — A session learns the tool and the capabilities

- GIVEN a Pi session that loaded a session entry
- WHEN a turn starts
- THEN the entry appends a Concorde section to the system prompt naming the `concorde` tool and every catalog capability with its description
- AND the tool's `operation` parameter admits exactly the catalog's capabilities, its `action` is `run`, `describe` or `result`, and its optional `mode` is `execute` or `describe-policy`

See [req.session.public-only](requirements.md#req.session.public-only).

### scenario.session.explicit-request-only — The source entry runs capabilities only on request

- GIVEN a session that loaded the private entry of Concorde's source checkout with a valid selection
- WHEN a turn starts
- THEN the appended section also states that a capability runs only when the developer asks for it by name

### scenario.session.describe — Describing a capability runs nothing

- GIVEN a Pi session that loaded a session entry
- WHEN the model calls `concorde` with action `describe`
- THEN the tool returns the capability's description, guidance and request schema from the catalog
- BUT it starts no process

### scenario.session.run-host — Running a Host capability goes through the launcher

- GIVEN a Pi session that loaded a session entry
- WHEN the model calls `concorde` with action `run`, a capability whose catalog path is the launcher, and the request data as `input`
- THEN the tool wraps `input` in a version 3 capability request, starts the launcher in the project root with the request on standard input, and returns the printed result envelope

See [req.session.unchanged-input](requirements.md#req.session.unchanged-input).

### scenario.session.run-refused — A blocked or failed run is a tool error

- GIVEN a `run` through the launcher
- WHEN the launcher prints an envelope with status `blocked` or `failed`, exits non-zero or prints output that is not an envelope
- THEN the tool returns a tool error carrying the envelope, when there is one, and a causal feedback record
- BUT it never returns the run as a success

See [req.session.failure-is-error](requirements.md#req.session.failure-is-error).

### scenario.session.run-invalid — An unknown capability or a missing input is refused locally

- GIVEN a Pi session that loaded a session entry
- WHEN the model calls `run` for a capability the catalog does not list, or without `input`
- THEN the tool refuses the call with an error naming the problem
- BUT it starts no launcher

### scenario.session.large-result — A large result is saved whole

- GIVEN a capability whose result text is larger than the tool's reply limit
- WHEN the tool returns it
- THEN the reply holds the text cut at the limit and names a private temporary file holding the whole text

### scenario.session.cancel — Aborting the turn cancels the run

- GIVEN a `run` in progress through the launcher
- WHEN the developer aborts the turn
- THEN the tool sends the launcher SIGTERM and reports the cancellation as a tool error carrying whatever the launcher printed
- AND a launcher that has not exited within the grace period is killed together with its process group

### scenario.session.native-prepare — A model-backed capability is prepared, not run

- GIVEN a Pi session that loaded a session entry
- WHEN the model calls `run` for a capability whose catalog kind is `agent-entry` or `workflow`, or for a `native_actions` action of a Host capability
- THEN the tool passes the capability request to the launcher's native preparation step and returns the prepared Agent call or workflow state unchanged
- BUT it starts no Agent itself and presents no Agent output as accepted

### scenario.session.result-poll — Polling a workflow reports its Host state

- GIVEN a workflow prepared through the `concorde` tool
- WHEN the model calls `concorde` with action `result` for that capability
- THEN the tool returns the workflow's current state as reconciled by the Host

## Selection

### scenario.session.select — Selecting a candidate's exact build

- GIVEN a candidate with a fresh build and absolute, unaliased paths to its private session entry and launcher
- WHEN `select-session --mode test` runs
- THEN the record names the build manifest digest, the launcher and session extension digests, the complete entry text, the exact embedded catalog and the Pi flags of a fresh session without discovered resources
- AND with `--output` below the candidate's `.concorde/work/` the record is saved there

See [req.session.private-selection](requirements.md#req.session.private-selection).

### scenario.session.select-refused — A stale or foreign input yields no selection

- GIVEN a missing, modified, aliased or out-of-candidate entry or launcher, a symbolic link among the candidate's sources, or a build that is not fresh
- WHEN `select-session` runs
- THEN it fails with a build error and returns no record
- BUT it does not substitute the primary checkout's or an installed build

See [req.session.no-selection-fallback](requirements.md#req.session.no-selection-fallback).

### scenario.session.select-verify — Reverifying an unchanged selection

- GIVEN a saved selection and an unchanged candidate
- WHEN `select-session --verify` runs
- THEN it returns the same record

### scenario.session.select-verify-changed — A changed candidate invalidates its selection

- GIVEN a saved selection and a candidate whose build, entry, catalog or launcher changed since
- WHEN `select-session --verify` runs
- THEN it fails with `stale_build`

### scenario.session.entry-requires-selection — The private entry needs a selection

- GIVEN the private entry of a source checkout
- WHEN a Pi session loads it without a selection transport, with two transports naming different paths, or without the candidate's own interpreter
- THEN loading fails and no tool is registered

See [req.session.selection-reverified](requirements.md#req.session.selection-reverified).

### scenario.session.selection-changed — A selection that changes mid-session refuses further calls

- GIVEN a session that loaded the private entry with a verified selection
- WHEN the selection transport or the selected bytes change and the model calls the `concorde` tool
- THEN the call fails and asks for a fresh session
- AND no launcher starts

### scenario.session.selection-no-evidence — A selection is not execution evidence

- GIVEN a saved selection
- WHEN it is read
- THEN its execution evidence field is null
- AND nothing in it claims that Pi loaded the entry, that a tool ran or that a model executed

See [req.session.selection-not-evidence](requirements.md#req.session.selection-not-evidence).

## Task subagents

### scenario.session.task-subagents — The source checkout projects both Task subagents

- GIVEN a source build and pi-subagents available to the user session
- WHEN the user session resolves the project agents `maintenance-worker` and `tester`
- THEN both exist, each with fresh context, a replaced system prompt, no inherited context or Skills, an explicit extension list and no `subagent` tool
- AND the tester's extension list holds the tester command extension and the source session entry

See [req.session.single-definition](requirements.md#req.session.single-definition) and
[req.session.no-delegation](requirements.md#req.session.no-delegation).

### scenario.session.consumer-tester — A consumer installation projects only the tester

- GIVEN a consumer installation
- WHEN its user session resolves the project agents
- THEN only the generic tester exists, with the installed session entry in its extension list
- AND no maintenance worker, coordinator instructions or brief lifecycle extension is present

See [req.session.source-only](requirements.md#req.session.source-only).

### scenario.session.projection-conflict — A changed projection is never overwritten

- GIVEN a projection path holding a locally modified projection or a file the build did not write
- WHEN the build or an installation would write that path
- THEN it stops without writing, naming the path

### scenario.session.tester-independent — The tester reports failures without repairing them

- GIVEN a stopped candidate and a selected targeted or full testing scope with a reason
- WHEN the user session launches a fresh tester with that candidate's selection
- THEN the tester runs commands only through `test_command` and keeps governing files read-only
- AND it reports the tested revision, scope, commands, failures, skips and residual risks, distinguishing scripted fixtures from live model runs
- BUT it never repairs sources, never falls back to other assets and never launches another agent

See [req.session.tester-commands-only](requirements.md#req.session.tester-commands-only).

### scenario.session.tester-command — A tester command runs in the read-only boundary

- GIVEN a tester with a valid selection
- WHEN it calls `test_command` with a command that exits zero and report names
- THEN the command runs in the read-only check boundary with fresh scratch
- AND the tool returns the exit status, the tail of each output stream and a complete evidence export summary that names its export manifest, which lists each requested report among the exported artifacts

### scenario.session.tester-command-failed — A failed or unexported command fails the tool call

- GIVEN a tester command that exits non-zero, times out, is cancelled or whose evidence export is incomplete
- WHEN the bridge returns its response
- THEN the tool call fails with the whole response

See [req.session.tester-failure-visible](requirements.md#req.session.tester-failure-visible).

### scenario.session.tester-selection-changed — A changed tester selection stops commands

- GIVEN a tester launched with a selection
- WHEN the selection transport changes or the selection no longer verifies and the tester calls `test_command`
- THEN no command runs and the call fails

### scenario.session.maintenance-guard — The maintenance worker cannot delegate or call capabilities

- GIVEN a maintenance worker in a Concorde source checkout
- WHEN it calls the `subagent` or the `concorde` tool
- THEN the call is blocked

### scenario.session.maintenance-outside-source — The maintenance worker stops outside Concorde

- GIVEN a maintenance worker whose working directory is not a Concorde source checkout
- WHEN it calls any tool
- THEN the call is blocked

See [req.session.maintenance-source-only](requirements.md#req.session.maintenance-source-only).

## Source user session coordination

### scenario.session.coordinator-ownership — Register, bind and release children

- GIVEN the source user session and a candidate created from a committed base
- WHEN it follows its coordinator instructions to start maintenance and later hand the candidate over
- THEN it registers the candidate in the primary status store and verifies the record before launching the maintenance worker
- AND it binds the actual launched child run, not a workflow container, and rereads the record
- AND before a tester or resumed maintenance worker takes over, it verifies the child stopped, releases exactly that child and then binds the next one

### scenario.session.coordinator-register-repeat — Registering a candidate again reuses its record

- GIVEN a candidate already registered in the primary status store
- WHEN the source user session registers it again
- THEN the existing change identity is returned with its goal and mode unchanged

### scenario.session.coordinator-ownership-failure — A failed register, bind or release stops dependent work

- GIVEN the source user session following its coordinator instructions
- WHEN a registration, bind or release fails or cannot be verified by rereading the record
- THEN it stops dependent work and reports the failure
- BUT it claims no ownership or handoff and clears no other coordinator's owner

### scenario.session.stage-continuity — The user session owns stages and integration

- GIVEN authorized source maintenance with independent work packages
- WHEN the source user session follows its coordinator instructions
- THEN it owns the decomposition, file and contract ownership, workflow steps and component, integration and testing gates, without calling Concorde's planner
- AND it keeps the same maintenance worker through an unfinished stage and its feedback, and may start a fresh one for a completed stage with changed goals after a durable handoff
- BUT separate component candidates imply no combined success, merge or cleanup

See [req.session.frozen-continuation](requirements.md#req.session.frozen-continuation).

### scenario.session.coordinator-only — Coordinator instructions reach only the source user session

- GIVEN a source build
- WHEN the source user session and each Task subagent start
- THEN the coordinator instructions are appended to the source user session's system prompt
- BUT no Task subagent, fresh or resumed, and no Agent receives them

See [req.session.coordinator-user-session-only](requirements.md#req.session.coordinator-user-session-only).

## Task brief

### scenario.session.brief-lifecycle — The current task brief survives compaction once

- GIVEN a source user session or maintenance worker with the brief lifecycle extension and a recorded current task brief
- WHEN Pi completes a compaction of that session
- THEN the extension injects the current brief once into the next model request
- AND an obsolete brief is never injected

See [req.session.brief-once](requirements.md#req.session.brief-once).

### scenario.session.brief-without-compaction — No compaction, no injection

- GIVEN a session with the brief lifecycle extension and a recorded brief
- WHEN a checkpoint is written, a message asks to compact, or a compaction fails
- THEN no brief is injected

### scenario.session.brief-invalid — An invalid brief clears the stored brief

- GIVEN a maintenance worker progress message carrying a malformed task brief
- WHEN the extension reads it
- THEN the stored brief is cleared and the error is recorded
- BUT the progress message is delivered unchanged

## TODO notes

### scenario.session.todo-collection — Collect a settled change as a note

- GIVEN a source user session discussion whose change has a settled goal, scope and expected behaviour
- WHEN the developer asks for or approves recording it
- THEN the user session writes one Markdown note under `.concorde/todos/`, or updates the existing note for the same change
- AND the note keeps the context, decisions, alternatives, boundaries, examples and source Issue references
- AND the user session rereads the saved note before reporting success
- BUT recording changes no implementation or Spec and starts no maintenance

### scenario.session.todo-unsettled — Ask before recording an unsettled request

- GIVEN an explicit TODO request whose goal, scope or expected behaviour is unsettled
- WHEN the source user session decides how to respond
- THEN it asks whether to keep clarifying or save an Issue, and waits for the answer
- BUT it saves neither an immature note nor an Issue on its own

### scenario.session.todo-promotion — Move a mature Issue into a note

- GIVEN the developer confirms moving a mature Issue into a TODO note
- WHEN the source user session performs the transfer
- THEN it reads the whole Issue and its associated records, writes the note with all relevant background and source references, and rereads it
- AND only after that verification succeeds does it delete the Issue, without asking again

### scenario.session.todo-promotion-failure — A failed transfer keeps the Issue

- GIVEN a transfer of an Issue into a TODO note
- WHEN writing or verifying the note fails, or deleting the Issue fails
- THEN the Issue is kept
- AND after a failed deletion the verified note is kept too, and the partial transfer is reported so that a retry updates the same note

## Installed-output handoff

### scenario.session.installed-output-handoff — A tester tests an installation of the selected source

- GIVEN a tester with an active source selection and an empty target inside its command scratch
- WHEN a tester command runs the installed-output handoff
- THEN the selected source is installed into the target and verified with the installed copy's own interpreter
- AND the provenance record names the source selection and build and the installed entry, catalog, launcher, build, receipt and runtime
- AND the source selection is still active and unchanged afterwards

### scenario.session.installed-output-refused — The handoff refuses anything outside tester scratch

- GIVEN a target outside the command's scratch or not empty, a missing or different active selection, or a source that changed during the installation
- WHEN the installed-output handoff runs
- THEN it fails and issues no provenance record
