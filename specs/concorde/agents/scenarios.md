# Agents scenarios

These scenarios cover Agent definitions, their distribution, and the source user session's
coordination of Task subagents. Several of them are instruction contracts: a check of the rendered
instructions shows what an Agent is told, not that a live model always complies.

## Definitions

### scenario.agents.inventory — One definition for every Agent

- GIVEN the source checkout with seven Domain Agents and two Task subagents
- WHEN the build renders Agent instructions and Task subagent definitions and the Host resolves Domain Agent profiles
- THEN every Domain Agent's profile and instructions come from its definition under `agents/<name>/`
- AND the source projection contains both Task subagents
- AND a consumer projection contains the tester but neither the maintenance-worker nor the coordinator instructions
- AND the user session appears in no inventory
- BUT an unknown Agent, a missing definition or a difference between the inventory and its metadata is a validation finding, never a second definition

See [req.agents.single-definition](requirements.md#req.agents.single-definition).

### scenario.agents.domain-tools — Domain Agent tool limits

- GIVEN the seven Domain Agent definitions
- WHEN a capability prepares a native call for one of them
- THEN the prepared agent has its profile's tools plus `report_issue` and no delegation tool
- AND only the programmer has `edit`, `write` or `bash`
- AND a code-reviewer call has no `bash`, although its profile lists it
- AND the prepared agent starts with fresh context and without inherited project or global instructions or Skills

## Task subagents

### scenario.distribution.task-subagents — Task subagents are discoverable, with separate distribution

- GIVEN a source build or a consumer installation, and pi-subagents available to the user session
- WHEN the user session resolves the project agents `maintenance-worker` and `tester`
- THEN the source checkout provides both, each with fresh context and an explicit extension list
- AND a consumer installation provides only the generic tester, without source maintenance or coordinator text
- AND neither Task subagent has the `subagent` tool, and the tester's commands run with governing files read-only and external scratch
- AND the coordinator instructions reach the source user session and no fresh or resumed child
- AND a tester launched with a selection binding loads exactly the selected candidate entry, and without a valid binding loads none
- AND installing or updating a consumer project keeps the user's own Pi system-prompt additions byte for byte
- BUT a missing canonical source, a locally modified projection or a user-owned file at a projection path blocks the build or installation instead of being overwritten

See [req.agents.source-only](requirements.md#req.agents.source-only) and
[req.agents.coordinator-user-session-only](requirements.md#req.agents.coordinator-user-session-only).

### scenario.agents.tester-independent — The tester reports failures without repairing them

- GIVEN a stopped candidate and a selected targeted or full testing scope with a reason
- WHEN the user session launches a fresh tester with the exact candidate Pi entry, catalog and runtime
- THEN the tester runs commands only through `test_command` and keeps governing files read-only
- AND it reports the tested revision, scope, commands, failures, skips and residual risks, and distinguishes scripted fixtures from live model runs
- AND it has selected reports exported by the Host before its scratch is removed, and reports any export failure
- BUT it never repairs sources, never falls back to primary or global assets when the candidate's are missing, and never launches another agent

## Source user session coordination

### scenario.agents.coordinator-ownership — Register, bind and release children

- GIVEN the source user session and a candidate created from a committed base
- WHEN it follows its coordinator instructions to start maintenance and later hand the candidate over
- THEN it registers the candidate in the primary status store and verifies the record before launching the maintenance-worker
- AND it binds the actual launched child run, not a workflow container, and rereads the record
- AND registering the same candidate again returns the existing change identity unchanged
- AND before a tester or resumed maintenance-worker takes over, it verifies the child stopped, releases exactly that child and then binds the next one
- AND a failed registration, bind or release stops dependent work without claiming success or clearing another coordinator's owner
- BUT run evidence, notes and mission records never replace the status record, and a cleanup outcome is accepted only for a recorded integration, never silently ignored

See [req.agents.frozen-continuation](requirements.md#req.agents.frozen-continuation).

### scenario.harness.brief-lifecycle — The current task brief survives compaction once

- GIVEN a source user session or maintenance-worker with the brief-lifecycle extension and a recorded current task brief
- WHEN Pi completes a compaction of that session
- THEN the extension injects the current brief once into the next model request
- AND an obsolete brief is never injected
- BUT a checkpoint or a request to compact, without an observed completed compaction, injects nothing

The extension is built into the source checkout's session only; consumer installations and the
tester do not load it.

### scenario.distribution.stage-continuity — The user session owns stages and integration

- GIVEN authorized source maintenance with independent work packages
- WHEN the source user session follows its coordinator instructions
- THEN it owns the decomposition, file and contract ownership, workflow steps and component, integration and testing gates, without calling Concorde's planner
- AND it may repair profiles, prompts and workflows in its own tree without changing an active sibling's launch grant
- AND it keeps the same maintenance-worker through an unfinished stage and its feedback, and may launch a fresh one for a completed stage with changed goals after a durable handoff
- BUT separate component candidates imply no combined success, automatic merge, cleanup or task delegation by a child

### scenario.distribution.user-session-todo-collection — Collect mature notes in the source user session only

- GIVEN a source user session discussion whose change has a settled goal, scope and expected behaviour
- WHEN the developer asks for or approves recording it
- THEN the user session writes one Markdown note under `.concorde/todos/`, or updates the existing note for the same change
- AND the note keeps the context, decisions, alternatives, boundaries, examples and source Issue references, not just a title
- AND the user session rereads the saved note before reporting success, and a failed write keeps the prior records
- BUT discussion alone records nothing, recording changes no implementation or Spec and starts no maintenance, and these instructions are absent from children and consumer installations

### scenario.distribution.user-session-todo-unsettled — Ask before recording an unsettled request

- GIVEN an explicit TODO request whose goal, scope or expected behaviour is unsettled, or a settled conclusion that needs no action
- WHEN the source user session decides how to respond
- THEN for an unsettled request it asks whether to keep clarifying or save an Issue, and waits for the answer
- AND a conclusion that needs no action produces no note
- BUT it saves neither an immature note nor an Issue automatically, and closing or deleting an Issue needs separate confirmation

### scenario.distribution.user-session-todo-promotion — Keep an Issue's background when promoting it

- GIVEN the developer confirms moving a mature Issue into a TODO note
- WHEN the source user session performs the transfer
- THEN it reads the whole Issue and its associated records, writes the note with all relevant background and source references, and rereads it
- AND only after that verification succeeds does it delete the Issue, without asking again
- AND a failed write or verification keeps the Issue, and a failed deletion keeps both and reports a partial transfer that a retry completes by updating the same note
- BUT a partly resolved multi-part Issue keeps its unresolved content, an unsafe deletion keeps the source and reports the blocker, and the transfer is not an Issue disposition
