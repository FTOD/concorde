# Concorde Source-Checkout Agent Policy

This policy applies only while developing the Concorde repository itself. Project-local
`concorde-*` Skills are worktree-owned instructions: an agent session must not carry them from the
worktree where the session started into another linked worktree.

In a fresh clone, run `python3 scripts/concorde.py build` once before this path resolves. Read and
follow `generated/protocol/principles.md` as the canonical Concorde Spec Protocol and Framework rule bundle, including P10 for
all session handoffs below. This file adds only source-checkout worktree and maintenance boundaries.

## Spec language

Concorde's own Specs under `specs/` MUST use English, including diagram labels, descriptions,
relationship text and viewer locale. This is a Concorde project convention, not a requirement of
the Concorde Spec Protocol; it does not prescribe the language of consumer projects or conversations.

## Worktree ownership

A session works in the worktree that supplied its Skills and never creates, moves or enters
another worktree itself. Worktrees for changes are created only by the Concorde host: invoke a
Concorde capability (for example `concorde-dev-loop`), let the host prepare the candidate worktree
from the committed base, and continue there in a fresh session under P10. That successor session
starts with the target worktree as its initial working directory, fresh context and that worktree's
own Skills; changing cwd or spawning a native subagent that inherits this conversation or its Skill
bodies does not satisfy the handoff. Never switch the current worktree in place to another branch
or revision to avoid a handoff; a new target revision belongs in a host-created linked worktree
with its own agent session.

This checkout enforces the rule in the agent runtimes, so it does not depend on an agent
remembering it. Claude Code reads `.claude/settings.json`, which denies the `EnterWorktree` tool,
subagents with `isolation: "worktree"`, and shell commands that run `git worktree add`,
`git worktree move` or `claude --worktree`; its `PreToolUse` and `WorktreeCreate` hooks run
`scripts/worktree-guard.py`, which also refuses the forms a permission rule cannot express and
aborts every native worktree creation, `claude --worktree` at startup included. Codex reads
`.codex/rules/worktree.rules`, which forbids `git worktree add` and `git worktree move`, and
`.codex/hooks.json`, which runs the same guard before each shell command; Codex loads both only for
a trusted project and runs the hook only after you reviewed it once with `/hooks`. Both runtimes
apply these rules to native subagents as well. The guard inspects the whole command text, so write
a file that must mention these commands with the editor tool rather than a shell here-document.
`python3 scripts/worktree-guard.py --explain` prints the policy; `--check "<command>"` decides one
command.

The guard protects developer sessions of this checkout; it is not a sandbox, and it is not
installed into consumer projects. Concorde's own workers run with project settings ignored and
never create worktrees themselves. A refusal is a policy result, not a defect to work around: do
not compute the command at runtime or reach the same effect through another tool.

## Delivery between participating worktrees

For user-authorized delivery, the agent's initial worktree may be either the selected source
worktree or the primary worktree. A third-worktree session cannot initiate that delivery. The
session keeps its own worktree's Skills as usual. The deterministic host may inspect the
participants and verify integration without moving the session or loading the other participant's
Skills. These bounded delivery actions are an exception to the cross-worktree handoff above;
unrelated development and Skill projection maintenance remain bound to the original worktree.

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

Run `python3 scripts/concorde.py build` after changing `prompts/`, `skills/`, `capabilities/` or
wire contracts (`src/concorde/spec/contracts.py`, `contract_shapes.py`, or a
module under the top-level `capabilities/` package). This always operates on the worktree
containing the sources; never point one worktree's build at another worktree's outputs. Run
`python3 scripts/concorde.py build --check` to verify the outputs are current without writing.

Outputs under `generated/`, `.claude/skills/concorde-*` and `.agents/skills/concorde-*` are
untracked build output, not authoring sources: never directly create, edit, delete, or rename
them. Make the change in `prompts/`, `skills/` or `capabilities/` and rebuild. The host refuses to
run any capability on a stale build (error code `stale_build`), verified against
`generated/build-manifest.json`. A freshly created worktree must be built once before an agent can
load Concorde Skills; the host builds the worktrees it creates for candidate changes, and any other
fresh worktree has no Concorde Skills until it is built.

Do not invoke a project-local `concorde-*` Skill to govern a task that changes its own `prompts/`,
`skills/`, `capabilities/`, or generated Skill surface. If such a Skill body is already loaded as
instructions, stop before the first edit and initiate a fresh maintenance session in this same
worktree under P10, automatically by default, without loading the affected Skill bodies. Use the
manual fallback above only when necessary. Skill discovery metadata alone is not a loaded Skill body.
A maintenance agent that has not invoked a project-local Skill may update sources, run the build,
run `build --check`, and test normally.
