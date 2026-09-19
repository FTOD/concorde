# Concorde Source-Checkout Agent Policy

This policy applies only while developing the Concorde repository itself. Project-local
`concorde-*` Skills are worktree-owned instructions: an agent session must not carry them from the
worktree where the session started into another linked worktree.

In a fresh clone, run `python3 scripts/concorde.py build` once so the Concorde Skills exist, then
`python3 scripts/development/init-references.py` to check out the vendored external references
under `reference/` (media-free partial clones of the submodules `.gitmodules` records). Read and
follow `.concorde/protocol/principles.md`, the tracked Protocol copy that
`python3 scripts/concorde.py protocol-manifest --write --bind-project` refreshes after a Protocol
change, as the canonical Concorde Spec Protocol and Framework rule bundle, including P10 for
candidate worktrees. This file adds only source-checkout worktree and maintenance boundaries.

## Direct maintenance is the default

Developing this checkout is direct developer-authorized maintenance in the current worktree: read
the Specs and the code, make the change, run the build and the deterministic checks below, and land
each verified step as its own commit. Concorde's own graphs run on this checkout only when the user
explicitly asks for one, by invoking its slash command or by naming the graph in the request; that
covers the global Skills (`concorde-main`, `concorde-dev-loop`, `concorde-specify-loop`,
`concorde-spec-review`, `concorde-code-review`, `concorde-issues`) and the lifecycle Skills (`concorde-init`,
`concorde-configure`, `concorde-validate`, `concorde-deliver`) alike. Never select one because a
task looks like a development change, and verify direct maintenance with
`python3 scripts/concorde.py validate` and the test commands rather than with `concorde-validate`.
The build renders this checkout's Claude Skills with `disable-model-invocation: true`, so they stay
hidden from the model until the user types `/concorde-<name>`; when the user names a graph in prose
instead, read its rendered file under `.claude/skills/<name>/SKILL.md` and submit the typed request
it describes through `scripts/run-operation.py`. An explicitly requested graph keeps every rule of
this policy, including the worktree rules below.

## Format before committing

Format changed source files **before verification, staging and committing**. In Pi, pi-lens can
queue formatting and safe autofixes until `agent_end`, after the agent has already run its commit
command and final status check. Its smart-default formatter can run even without a repository
formatter config; a clean status before the final response does not prove no deferred write remains.
In the observed TypeScript case, pi-lens selected Biome and reformatted tests after the commit.

- Run the configured formatter explicitly on the changed files before the final checks. When an
  active runtime selects a formatter automatically, use that same formatter and effective options,
  including each file's existing indentation; do not substitute an arbitrary formatter or reformat
  the whole repository. pi-lens records `formatter_selected` and `deferred_format_file` events in
  `~/.pi-lens/latency.log` when diagnosing unexpected changes.
- Re-read the resulting diff, run the relevant checks on the final bytes, and confirm a second
  formatter pass is a no-op before staging. Repeat this sequence after any further source edit.
  `git diff --check` detects whitespace errors, not formatter compliance.
- Inspect the staged diff before committing and `git status --short` afterwards. If a deferred
  formatter still changes files, inspect and verify those changes rather than discarding them or
  assuming they are unrelated; include them in the authorized change before declaring it complete.

## Spec language

Concorde's own Specs under `specs/` MUST use English, including diagram labels, descriptions,
relationship text and viewer locale. This is a Concorde project convention, not a requirement of
the Concorde Spec Protocol; it does not prescribe the language of consumer projects or conversations.

## Worktree ownership

A session works in the worktree whose build supplied its projections, and direct maintenance
needs no other worktree: the change is made, verified and committed here. When the user
explicitly asks for a Concorde graph that changes the project (for example `concorde-dev-loop`)
from the primary worktree, the host creates the candidate worktree from the committed base and
runs the graph there with the candidate's own code; this session stays here and receives the
candidate's result, whose workspace names the candidate's path, branch and change_id. Continue
the same change from here with that change_id, or open a separate session inside the candidate.
Never switch this worktree in place to another branch or revision to work on a candidate.

Concorde's own workers run with project settings ignored and never create worktrees themselves.

## Delivery between participating worktrees

For user-authorized delivery, the agent's initial worktree may be either the selected source
worktree or the primary worktree. A third-worktree session cannot initiate that delivery. The
session keeps its own worktree's Skills as usual. The deterministic host may inspect the
participants and verify integration without moving the session or loading the other participant's
Skills. Delivery is a bounded action on both participants; unrelated development and Skill
projection maintenance remain bound to the original worktree.

Default delivery creates an independent `concorde/delivered/<change_id>` branch in the shared Git
repository and removes the source worktree after verification. It never advances the primary
worktree's checked-out branch or changes its index or project files. Retain the source only when
explicitly requested; an active source session must end after removal and use P10 for later work.
No delivery request grants permission to discard unrelated local edits.

Only an explicit user request to merge into the primary branch authorizes a separate
`merge_primary:true` delivery request from the primary worktree's owning session. At most one agent
may own writes in the primary worktree at a time, including maintenance and conflict resolution;
other agents must develop in their own linked worktrees. The host serializes shared lifecycle
metadata and final primary merges with the repository lock, verifies the latest integration and
preserves local edits. A generic request to deliver does not authorize the final primary merge.

## Building this worktree

Run `python3 scripts/concorde.py build` after changing `prompts/` (including the Skill sources
`prompts/skills/<name>.md`), `operations/` or wire contracts (`src/concorde/spec/contracts.py`,
`contract_shapes.py`, or a module under the top-level `operations/` package). This always
operates on the worktree containing the sources; never point one worktree's build at another
worktree's outputs. Run `python3 scripts/concorde.py build --check` to verify the outputs are
current without writing.

Outputs under `generated/`, `.claude/skills/concorde-*`, `.agents/skills/concorde-*` and the Pi
session shim `.pi/extensions/concorde-session.ts` are untracked build output, not authoring
sources: never directly create, edit, delete, or rename them. The published Skills under
`skills/` are tracked rendered output with the same rule: never edit them by hand; after changing
a Skill source, run `python3 scripts/concorde.py skills --write` and commit `skills/` together
with the source (`build --check` and `skills --check` report a stale copy). Make the change in
`prompts/`, `operations/` or `pi/extensions/` and rebuild. The host refuses to
execute or describe a top-level non-lifecycle operation on a stale build (error code
`stale_build`), verified against `generated/build-manifest.json`. Deterministic lifecycle
operations (`concorde-init`, `concorde-configure`, `concorde-validate`, `concorde-deliver`) are
exempt from that entry check; loading an Agent independently verifies freshness. This exception
does not waive Protocol, input, permission or evidence checks. A freshly created worktree must be
built once before an agent can load Concorde Skills; the host builds the worktrees it creates for
candidate changes, and any other fresh worktree has no Concorde Skills until it is built.

A project-local `concorde-*` Skill never governs a task that changes its own `prompts/`,
`skills/`, `operations/`, or rendered Skill surface, even when the user asked for a graph: such a
change is direct maintenance. If such a Skill body is already loaded as instructions, stop before
the first edit and initiate a fresh maintenance session in this same worktree under P10,
automatically by default, without loading the affected Skill bodies. Use the manual fallback above
only when necessary. Skill discovery metadata alone is not a loaded Skill body. A maintenance agent
that has not invoked a project-local Skill may update sources, run the build, run `build --check`,
and test normally.

## Developer-authorized direct maintenance exception

For explicitly authorized maintenance of the Concorde source checkout,
the agent may directly edit tracked project configuration and registry files,
including `.concorde/config.json` and `.concorde/specs.json`.

When the developer explicitly requests a manual merge into main, the agent
may use ordinary Git integration after reviewing the complete change and
running the required deterministic checks. Concorde Operations are not
required for this direct-maintenance path.

This exception takes precedence over the Host-only delivery rules for this
path. It does not authorize fabricating readiness or review evidence,
manually rewriting lifecycle records, discarding unrelated local changes,
or concurrent writers in the same worktree.
