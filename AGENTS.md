# Developing Concorde

This is a source checkout, not a consumer installation. Read the canonical
`.concorde/protocol/principles.md` and the affected complete Specs before changing sources.
Specs and paired metadata under `specs/` use English.

## Self-maintenance

The source user session may discuss and, with user consent, collect mature lightweight TODO notes without
starting maintenance. This user-session-only recordkeeping exception changes only TODOs and authorized
issue records, never implementation or Specs; it grants no child authoring authority. The canonical
source user session coordinator prompt below defines maturity, persistence and safe issue promotion.

The user session owns high-level work packages, dependencies, file/contract ownership, native workflow
steps and component/integration/testing gates, not product Concorde plan/tasks. Within task authority
the user session may directly author/repair profiles, prompts, tools, workflows and coordination mechanisms in
its own exclusively owned tree. New assets never change an active sibling's frozen launch grant.
For candidate implementation it creates a
candidate from a committed base, registers it in primary `.concorde/status/` before launch, then
launches one fresh, Concorde-catalog-free maintenance child there and binds its actual child run ID.
The user session verifies the child stopped before releasing its exact ownership and handing off to a tester
or resuming the same author. Primary runs evidence and pi-subagents mission records are not status
registration; children never maintain a replacement ledger. See the canonical source user session
coordinator prompt under `prompts/user-session/source/coordinator.md` for the supported host CLI lifecycle.
Disable inherited and discovered Concorde catalogs; never fork previously loaded Concorde instructions.
The child owns all authoring and deterministic checks, never delegates tasks, never moves
worktrees, and stops writing before testing. Only one writer owns a worktree at a time.

Reuse the stage author across ordinary milestones and feedback. A completed stage with changed
goals/context may use a fresh author after a durable handoff and exact stop/release/bind. Independent
components may use multiple worktrees in parallel, with user-session-controlled combination and verification.
The user session chooses independent testing as none, targeted or full with an explicit scope and reason.
When selected, the user session launches a separate fresh sibling named tester in that candidate, explicitly
supplied only the exact candidate-built private Pi entry, embedded catalog and runtime provenance. A test child
never rewrites the Pi integration governing it. Failures return to maintenance, then another fresh tester.
Neither child creates grandchildren; Operation workers are terminal nodes scheduled by the Graph/host, with their own file/tool grants. Selection metadata is not evidence of extension loading, tool use or model execution.

Build does not install this checkout's Operation entry/catalog in ambient discovery.
It does maintain checked source project `.pi/agents/maintenance-worker.md`, `.pi/agents/tester.md`,
a source-user-session-only `.pi/extensions/concorde-coordinator.ts` and a separate passive observer entry plus an explicit source-only brief lifecycle extension. Canonical sources are `prompts/task-subagent/`,
`prompts/user-session/` and `pi/`; do not hand-edit projections. The user session's pi-subagents support is a prerequisite, never a
terminal-worker dependency. Coordinator delivery uses Pi extension discovery, not APPEND_SYSTEM:
Pi discovers that append independently of context-file inheritance. The user session alone loads the coordinator;
child explicit extension lists and terminal discovery disablement exclude it. The installer ships only generic tester instructions, not source
maintenance/coordinator rules. Strict tool profiles omit delegation; tester commands use the
OS read-only check boundary and external scratch rather than unrestricted bash/write/edit.
Private artifacts live in `generated/session/`. Use `select-session` with absolute Pi entry and
runtime paths to verify private selection; a missing or stale candidate artifact is a blocker,
never permission to fall back to a primary/global integration. Consumer installation is separate.

Maintenance can finish through ordinary Git after verification; Concorde delivery is not required.
Only the user session may integrate, and only with explicit merge authorization. Keep candidate
and terminal status until separately authorized cleanup. Never edit another worktree's source or
index. The primary coordinator owns durable `.concorde/status/` and `.concorde/runs/` persistence.
Task-authorized edits to `.concorde` are not intrinsically forbidden, but must preserve scope,
truthful evidence, ownership and concurrency safety; bounded workers retain their actual grants.

## Source and verification

Author `prompts/`, `operations/`, `protocol/`, `src/`, `pi/` and Specs, not rendered outputs.
Run `python3 scripts/concorde.py build` in this worktree after instruction, runtime or contract
changes. Build/package checks cover Pi entry, embedded catalog and guidance freshness; there is
no standalone Skill publishing or `skills` command.
After Protocol changes use `protocol-manifest --write --bind-project` to refresh the tracked copy.
Never build into another worktree. Initialize vendored references with
`python3 scripts/development/init-references.py` when needed.

Already fully read unchanged complete Specs in valid same-session context need not be reread;
new ownership seams and fresh readers still require complete paired context. Use compact external
checkpoints and actual supported compaction. The explicit lifecycle extension reinjects only the
current concise task brief once after observed success; checkpoints and `/compact` messages alone
are not compaction. Native supervisor updates report stage/objective/artifacts/check failures/blocker/
next action/evidence, distinct from host activity, context and compaction observations. Resource handoff requests report observed capacity, current input/cache,
reserve and compaction status or an actual error; missing metrics stay unknown. Cumulative tokens,
document KB and lack of a compact tool do not prove exhaustion; the user session verifies the need.

Use format/static/targeted checks for local edits, affected integration for coherent changes and
one full Python suite at final stable input. Stage handoff alone needs no full suite; a same-tree
commit needs only HEAD/bootstrap checks. Repeat corresponding evidence only after relevant input
or environment change or concrete failure, recording the reason. Self-tests are never independent.

Format changed sources explicitly before verification and confirm a second pass is a no-op.
Use the configured/runtime-selected formatter, retaining each file's indentation. Inspect the
final diff, run `build --check`, `python3 scripts/concorde.py validate` and relevant
Python/TypeScript tests. Deterministic checks are not model-based integration tests. Commit verified
steps, inspect staged diffs before committing and status afterwards, including deferred formatter
writes. Do not invoke public Concorde graphs while authoring their own governing integration.

For example, use `.venv/bin/python scripts/concorde.py select-session --mode test
--pi-entry "$PWD/generated/session/pi/concorde-session.ts" --runtime "$PWD/scripts/run-operation.py"
--output "$PWD/.concorde/work/pi-selection.json"`. `--skill` and schema-1 selections are retired,
not aliases. Reverify with `select-session --verify <absolute-selection-path>` before launch.
For a standalone fresh Pi host, supply `CONCORDE_SESSION_SELECTION` and only the returned exact
`-e` Operation entry, alongside explicitly registered observation/check assets, with the returned
discovery-disable flags and a separate host-owned configuration directory. For supported native
pi-subagents, launch project `tester` with `context: fresh`, `skill: false`, `async: true` and
`extensionBindings: {"concorde/1":{"selection":"<absolute saved selection>"}}`. This per-launch
transport needs no global environment/settings mutation. The exact source entry still verifies
selection before registration, and tester commands reverify it before executing fixtures.
Keep the actual task/file/tool grant; selection creates no authority and does not launch a session.
The source entry requires the candidate Python environment rather than an ambient interpreter.
