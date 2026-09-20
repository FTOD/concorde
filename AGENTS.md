# Developing Concorde

This is a source checkout, not a consumer installation. Read the canonical
`.concorde/protocol/principles.md` and the affected complete Specs before changing sources.
Specs and paired metadata under `specs/` use English.

## Self-maintenance

The main session coordinates from its initial worktree. For source maintenance it creates a
candidate from a committed base and launches one fresh, Skill-free maintenance child there.
Disable inherited and discovered Concorde catalogs; never fork previously loaded Skill bodies.
The child owns all authoring and deterministic checks, never delegates tasks, never moves
worktrees, and stops writing before testing. Only one writer owns a worktree at a time.

The main session then launches a separate fresh sibling test child in that candidate, explicitly
supplied only exact candidate-built private Skills and candidate runtime provenance. A test child
never rewrites the Skills governing it. Failures return to maintenance, then another fresh tester.
Neither child creates grandchildren; Operation workers are terminal nodes scheduled by the Graph/host, with their own file/tool grants. Skill metadata is not evidence of loading or executing a Skill.

Build does not install this checkout's Skills in ambient `.agents`, `.claude` or `.pi` discovery.
Private artifacts live in `generated/session/`. Use `select-session` with absolute Skill and
runtime paths to verify private selection; a missing or stale candidate artifact is a blocker,
never permission to fall back to a primary/global Skill. Consumer installation is separate.

Maintenance can finish through ordinary Git after verification; Concorde delivery is not required.
Only the main session may integrate, and only with explicit merge authorization. Keep candidate
and terminal status until separately authorized cleanup. Never edit another worktree's source or
index. The primary coordinator owns durable `.concorde/status/` and `.concorde/runs/` persistence.
Task-authorized edits to `.concorde` are not intrinsically forbidden, but must preserve scope,
truthful evidence, ownership and concurrency safety; bounded workers retain their actual grants.

## Source and verification

Author `prompts/`, `operations/`, `protocol/`, `src/`, `pi/` and Specs, not rendered outputs.
Run `python3 scripts/concorde.py build` in this worktree after instruction, runtime or contract
changes. Published `skills/` are tracked generated output: update only with `skills --write`.
After Protocol changes use `protocol-manifest --write --bind-project` to refresh the tracked copy.
Never build into another worktree. Initialize vendored references with
`python3 scripts/development/init-references.py` when needed.

Format changed sources explicitly before verification and confirm a second pass is a no-op.
Use the configured/runtime-selected formatter, retaining each file's indentation. Inspect the
final diff, run `build --check`, `skills --check`, `python3 scripts/concorde.py validate` and relevant
Python/TypeScript tests. Deterministic checks are not model-based Skill tests. Commit verified
steps, inspect staged diffs before committing and status afterwards, including deferred formatter
writes. Do not invoke public Concorde graphs while authoring their own governing Skills.
