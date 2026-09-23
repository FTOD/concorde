# Developing Concorde

This is a source checkout, not a consumer installation. Read the canonical
`.concorde/protocol/principles.md` and the affected complete Specs before changing sources.
Specs and paired metadata under `specs/` use English. The rules below restate, for this checkout,
what the [Pi session](specs/concorde/session/module.md) Spec defines for the source user session,
its coordinator instructions and its Task subagents; the Spec wins where they differ.

## Self-maintenance

The source user session may discuss and, with user consent, collect mature lightweight TODO notes
without starting maintenance. This recordkeeping exception changes only TODO notes and authorized
Issue records, never implementation or Specs, and grants no child authoring authority. The
coordinator instructions (`prompts/user-session/source/coordinator.md`) define maturity,
persistence and safe Issue promotion.

The user session owns high-level work packages, dependencies, file and contract ownership and
integration and testing gates; these are not Concorde `plan`/`tasks` artifacts. Within its task
authority it may directly change prompts, tools, workflows and coordination mechanisms in a tree it
exclusively owns; new assets never change an active sibling's frozen launch grant. For candidate
implementation it creates a candidate from a committed base, registers it in the primary
`.concorde/status/` before launch, launches one fresh maintenance worker there with inherited and
discovered Concorde catalogs disabled, and binds that child's actual run ID. It verifies the child
stopped before releasing exactly that owner (same child and phase) and handing the candidate to a
tester or resuming the same worker. Run records and pi-subagents mission records are not status
registration, and children never keep a replacement ledger. The coordinator instructions give the
exact `status` commands.

The maintenance worker owns all authoring and deterministic checks in its candidate, never
delegates, never moves worktrees and stops writing before testing. Only one writer owns a worktree
at a time. Reuse the same worker across ordinary milestones and feedback; a completed stage with
changed goals may use a fresh worker after a durable handoff and an exact stop, release and bind.
Independent components may use several candidates in parallel, combined and verified by the user
session.

The user session chooses independent testing as none, targeted or full, with an explicit scope and
reason. When selected, it launches a separate fresh `tester` in that candidate, supplied only the
exact candidate-built private session entry, its embedded catalog and runtime provenance. A tester
never rewrites the Pi integration governing it; failures return to maintenance and then to another
fresh tester. Task subagents never start other Task subagents; the Agents inside a capability are
terminal and keep their own file and tool grants. A session selection is launch provenance, never
evidence of extension loading, tool use or model execution.

The build never installs this checkout's session entry or catalog into ambient discovery. It keeps
the checked project files `.pi/agents/maintenance-worker.md`, `.pi/agents/tester.md`, the
source-user-session-only `.pi/extensions/concorde-coordinator.ts`, the passive observer
`.pi/extensions/concorde-observe.ts` and the task-brief lifecycle extension
`.pi/extensions/concorde-brief-lifecycle.ts` current. Their sources are `prompts/task-subagent/`,
`prompts/user-session/` and `pi/`; never hand-edit the projections. Only the user session loads the
coordinator: children's explicit extension lists and disabled discovery exclude it. The installer
ships only the generic tester, not maintenance or coordinator rules. Tester commands run in Check
execution's read-only boundary with external scratch, not with unrestricted bash, write or edit.
Private artifacts live in `generated/session/`; a missing or stale candidate artifact blocks, and
never permits falling back to a primary or global integration.

Maintenance can finish through ordinary Git after verification; Concorde delivery is not required.
Only the user session integrates, and only with explicit merge authorization. Keep candidates and
terminal status until separately authorized cleanup. Never edit another worktree's sources or
index. The primary owns durable `.concorde/status/` and `.concorde/runs/`. Task-authorized edits to
`.concorde` are allowed when they preserve scope, truthful evidence, ownership and concurrency
safety.

## Source and verification

Author `prompts/`, `operations/`, `agents/`, `protocol/`, `src/`, `pi/` and Specs, never rendered
output under `generated/`. Run `python3 scripts/concorde.py build` in this worktree after changing
instructions, runtime code or contracts, and never build into another worktree. After Protocol
changes run `protocol-manifest --write --bind-project`. Initialize vendored references with
`python3 scripts/development/init-references.py` when needed. Control flow is a pi workflow run by
pi-subagents or a LangGraph Graph written with the Graph API only (never `langgraph.func`); each has
its step table or Graph Spec in its owner's Spec.

Unchanged complete Specs already read in valid same-session context need not be reread; new
ownership seams and fresh readers still need complete paired context. The lifecycle extension
reinjects the current concise task brief once after an observed compaction; checkpoints and
`/compact` messages alone are not compaction. Supervisor updates report stage, objective,
artifacts, check failures, blocker, next action and evidence. A resource handoff request reports
observed capacity, current input and cache, reserve and compaction status, or an actual error;
missing metrics stay unknown, and cumulative tokens alone do not prove exhaustion.

Use format, static and targeted checks for local edits, affected integration tests for coherent
changes and one full Python suite on the final stable input. A stage handoff needs no full suite.
Repeat evidence only after a relevant input or environment change or a concrete failure, and record
why. Self-tests are never independent.

Format changed sources explicitly (`uvx ruff format` for Python, Prettier for TypeScript and
JavaScript) and confirm a second pass changes nothing. Inspect the final diff and run
`build --check`, `validate`, `check-package`, the Graph Spec check
(`scripts/development/check-graph-specs.py --catalog concorde.operations.graph_catalog:catalog`)
and the relevant Python and TypeScript tests. Deterministic checks are not model-based integration
tests. Commit verified steps, inspecting staged diffs before committing and the status afterwards.
Do not invoke public Concorde capabilities while changing their own governing integration.

To select a candidate's build for a tester, run in that candidate
`.venv/bin/python scripts/concorde.py select-session --mode test --pi-entry
"$PWD/generated/session/pi/concorde-session.ts" --runtime "$PWD/scripts/run-operation.py" --output
"$PWD/.concorde/work/pi-selection.json"` and reverify with `select-session --verify
<absolute-selection-path>` before launch. Launch the project `tester` through pi-subagents with
`context: fresh`, `skill: false`, `async: true` and `extensionBindings:
{"concorde/1":{"selection":"<absolute saved selection>"}}`; this per-launch binding needs no global
environment or settings change. A standalone fresh Pi host instead receives
`CONCORDE_SESSION_SELECTION`, only the returned exact `-e` entry, the returned discovery-disable
flags and its own configuration directory. The private entry verifies the selection before
registering and before every tool call, and needs the candidate's own Python environment. A
selection grants nothing and starts no session.
