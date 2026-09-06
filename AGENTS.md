# Concorde Source-Checkout Agent Policy

This policy applies only while developing the Concorde repository itself. Project-local
`concorde-*` Skills are worktree-owned instructions: an agent session must not carry them from the
worktree where the session started into another linked worktree.

## Worktree affinity

Before project work, identify one absolute project-local `concorde-*` `SKILL.md` path advertised by
the agent runtime. Run the following command from the worktree that the task would read or change,
passing that exact advertised path rather than reconstructing it from the current directory:

```bash
python3 scripts/development/sync-agent-surfaces.py verify-worktree \
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

## Maintaining this worktree's Skill projections

`scripts/development/sync-agent-surfaces.py` always operates on the worktree containing that script.
After changing canonical `skills/`, Operations' `SKILL.md` files, capability projection code, or
reflection agent assets, run `apply` in that same worktree and then require `check` to pass. This is
required in primary and linked worktrees alike; never point one worktree's script at another
worktree.

Never directly create, edit, delete, or rename `.agents/skills/concorde-*` or
`.claude/skills/concorde-*`. They are generated projections, not authoring sources. Make the change
in the owning canonical `skills/` or `operations/*/SKILL.md` file and let this worktree's `apply`
write both integrations. The same generated-only rule applies to `.codex/agents/reflection_*` and
`.claude/agents/reflection-*`; their sources live under `agent-assets/reflections/`.

Do not invoke a project-local `concorde-*` Skill to govern a task that changes its own canonical or
generated Skill surface. If such a Skill body is already loaded as instructions, stop before the
first edit and ask the user to reopen a maintenance agent in this same worktree. Skill discovery
metadata alone is not a loaded Skill body. A maintenance agent that has not invoked a project-local
Skill may update canonical sources, run `apply`, run `check`, and test normally.
