# Concorde Source-Checkout Agent Policy

This policy applies only while developing the Concorde repository itself. Project-local
`concorde-*` Skills are worktree-owned instructions: an agent session must not carry them from the
worktree where the session started into another linked worktree.

Read and follow `protocol/principles.md` as the canonical Concorde Protocol, including P10 for
all session handoffs below. This file adds only source-checkout worktree and maintenance boundaries.

## Worktree affinity

Before project work, identify one absolute project-local `concorde-*` `SKILL.md` path advertised by
the agent runtime. Run the following command from the worktree that the task would read or change,
passing that exact advertised path rather than reconstructing it from the current directory:

```bash
python3 scripts/concorde.py verify-worktree \
  --project-root . \
  --loaded-skill-path <absolute-runtime-advertised-SKILL.md-path>
```

Repeat the check for every distinct worktree represented by project-local Concorde Skill paths
retained in the conversation; one representative path per owning worktree is sufficient. Every
check must pass.

If the runtime exposes no absolute project-local Concorde Skill path, worktree affinity cannot be
proven; stop and ask the user to reopen the agent from the intended worktree instead of guessing.

Run it again after any cwd or tool `workdir` change. A result that reports different loaded and
target worktrees ends project work in this conversation. Tell the user which worktree supplied the
loaded Skills and explicitly ask them to open a new agent whose initial working directory is the
target worktree. Do not inspect, plan, test, edit, or invoke a capability in that target worktree
from the old conversation, and never update the loaded Skill worktree as a substitute. Any other
nonzero result also stops work unless it reports same-worktree projection drift and the current
session qualifies for the maintenance recovery below.

An agent may create a requested branch and linked worktree from the authorized committed base, but
must stop after reporting its path and branch. Development in it belongs to a newly opened agent.
Never switch the current worktree in place to another branch or revision to avoid this handoff; a
new target revision belongs in a linked worktree with its own agent session.

## Delivery between participating worktrees

For user-authorized delivery, the agent's initial worktree may be either the selected source
worktree or the destination worktree. A session in a third worktree cannot initiate that delivery.
Verify Skill affinity against the session-owned worktree as usual. Within this bounded delivery,
inspect the other participant, merge its branch into the source to resolve integration conflicts,
run integration checks, and update the destination without moving the session or loading that
participant's Skills. These delivery actions are an exception to the cross-worktree handoff above;
unrelated development and Skill projection maintenance remain bound to the original worktree.
Preserve unrelated destination changes and retain the source worktree when the user requests it
or when it owns the active session. No delivery request grants permission to discard local edits.

## Building this worktree

Run `python3 scripts/concorde.py build` after changing `prompts/`, `skills/`, `capabilities/` or
wire contracts (`src/concorde/capabilities/protocol_contracts.py`, `contract_shapes.py`, or a
module under the top-level `capabilities/` package). This always operates on the worktree
containing the sources; never point one worktree's build at another worktree's outputs. Run
`python3 scripts/concorde.py build --check` to verify the outputs are current without writing.

Outputs under `generated/`, `.claude/skills/concorde-*` and `.agents/skills/concorde-*` are
untracked build output, not authoring sources: never directly create, edit, delete, or rename
them. Make the change in `prompts/`, `skills/` or `capabilities/` and rebuild. The host refuses to
run any capability on a stale build (error code `stale_build`), verified against
`generated/build-manifest.json`. A freshly created worktree — including one this host creates for
a candidate change — must be built once before an agent can load Concorde Skills; `verify-worktree`
fails closed until it is. The same generated-only rule applies to `.codex/agents/reflection_*` and
`.claude/agents/reflection-*`; their sources live under `agent-assets/reflections/` and are
produced by the separate `python3 scripts/concorde.py agent-assets sync` mechanism, not the build.

Do not invoke a project-local `concorde-*` Skill to govern a task that changes its own `prompts/`,
`skills/`, `capabilities/`, or generated Skill surface. If such a Skill body is already loaded as
instructions, stop before the first edit and ask the user to reopen a maintenance agent in this
same worktree. Skill discovery metadata alone is not a loaded Skill body. A maintenance agent that
has not invoked a project-local Skill may update sources, run the build, run `build --check`, and
test normally.
