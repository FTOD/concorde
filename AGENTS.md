# Developing Concorde

This is a source checkout, not a consumer installation. Read the canonical
`.concorde/protocol/principles.md` and the affected complete Specs before changing sources.
Specs and paired metadata under `specs/` use English.

## Self-maintenance

The main session coordinates from its initial worktree. For source maintenance it creates a
candidate from a committed base and launches one fresh, Concorde-catalog-free maintenance child there.
Disable inherited and discovered Concorde catalogs; never fork previously loaded Concorde instructions.
The child owns all authoring and deterministic checks, never delegates tasks, never moves
worktrees, and stops writing before testing. Only one writer owns a worktree at a time.

The main session then launches a separate fresh sibling test child in that candidate, explicitly
supplied only the exact candidate-built private Pi entry, embedded catalog and runtime provenance. A test child
never rewrites the Pi integration governing it. Failures return to maintenance, then another fresh tester.
Neither child creates grandchildren; Operation workers are terminal nodes scheduled by the Graph/host, with their own file/tool grants. Selection metadata is not evidence of extension loading, tool use or model execution.

Build does not install this checkout's Pi integration in ambient `.agents`, `.claude` or `.pi` discovery.
Private artifacts live in `generated/session/`. Use `select-session` with absolute Pi entry and
runtime paths to verify private selection; a missing or stale candidate artifact is a blocker,
never permission to fall back to a primary/global integration. Consumer installation is separate.

Maintenance can finish through ordinary Git after verification; Concorde delivery is not required.
Only the main session may integrate, and only with explicit merge authorization. Keep candidate
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
Supply `CONCORDE_SESSION_SELECTION` and only the returned exact `-e` entry to the fresh Pi host,
with the returned discovery-disable flags and a separate host-owned configuration directory.
Keep the actual task/file/tool grant; selection creates no authority and does not launch a session.
The source entry requires the candidate Python environment rather than an ambient interpreter.
