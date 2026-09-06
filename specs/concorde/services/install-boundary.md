```concorde-document
{
  "id": "document.installation.boundary",
  "targets": ["service.installation"],
  "main_visible": true
}
```

# Installation service

## feature.installation.install

The public deterministic installer accepts `--target PATH`, `--integration codex|claude`, and
optional `--checkout PATH`. The default is a read-only preview; `--apply` applies the reviewed
installation/update. Repeating the preview reports current owned output integrity. It owns
.concorde/framework, .concorde/install.json and receipt-recorded integration outputs; it preserves
project Specs, configuration, reflection history and unrelated user files.
It seeds project-owned Reflection defaults and
`.concorde/topology-proposals/.gitignore` only when absent; project defaults are excluded from the
installation receipt and never overwritten on update.

The distributable manifest is concorde.json schema 3, Concorde 4.0.0, Architecture Profile 8,
Workspace Protocol 14 and Delivery Proposal 10. It contains exactly 7 internal Skills and 22 paired
public Operations, explicit package roots including protocol, and 9 templates. Codex .agents/skills
and Claude .claude/skills expose the same 22 wrappers; canonical internal roles stay private.
Every wrapper sends typed invocation@2 to its paired executable and does not inspect project context.

Owned content is hashed in the installation receipt. A local modification conflicts unless an
explicit supported ownership transition authorizes replacement. Staging/provisioning/verification
must finish before installation is accepted; failure restores replaced outputs and receipts. The
locked managed Python runtime runs actual Operations; viewer provisioning is separate and versioned.
Check verifies receipt hashes and required runtime identity without changing project behavior.

Initialization is a distinct typed concorde-init Operation: propose returns a complete file proposal;
apply validates exact before-digests and target state. It pins the packaged global principles and kind
definitions, configures integration/enforcement, and writes an explicit Domain stub with missing
business requirements stated honestly. The stub declares document identity, target membership and
main visibility. Configuration changes use concorde-configure with a typed
configuration. Profile 7 is not agent-compatible; concorde-migrate requires authored Profile 8 registry
and Markdown replacements with concorde-document declarations, rejects active attempts and rolls back invalid application.

Install/update cannot silently rewrite a consumer's Protocol binding. A package with changed Protocol
assets requires the consumer's explicit migration/binding decision before execution. Templates and
prompts enforce the same architectural principles for all consumer projects.

## feature.installation.self-distribute

Concorde's source checkout projects its canonical public paired Operations and internal reflection
agents into that same worktree's Codex and Claude surfaces. Canonical internal Skills remain private.
It does not install a duplicate `.concorde/framework` into the repository. The inputs are the root
`concorde.json`, canonical `skills/`, `operations/`, `agent-assets/`, and the integration renderers;
generated files never become authoring sources. Repository agent policy stays in `AGENTS.md`, with
`CLAUDE.md` directing Claude to it; the projector does not inject checkout policy into Skill bodies.

From the worktree being maintained, the deterministic entry points are:

```bash
python3 scripts/development/sync-agent-surfaces.py status --project-root . --format json
python3 scripts/development/sync-agent-surfaces.py check --project-root . --format json
python3 scripts/development/sync-agent-surfaces.py apply --project-root . --format json
python3 scripts/development/sync-agent-surfaces.py verify-worktree --project-root . \
  --loaded-skill-path /absolute/runtime/path/to/.agents/skills/concorde-context/SKILL.md
```

Every mode must execute the script belonging to the worktree named by `--project-root`; a checker/root
mismatch fails before mutation. `status`, `check`, and `apply` return capability-surface schema 2 with
`schema_version`, `tool`, `status`, `outputs`, and sorted `actions`. Each action has a relative `path`,
an `action`, and a `sha256` digest. Actions classify `current`, `create`, `update`, `replace-symlink`,
`conflict`, and `unexpected`. The desired output count is twice the manifested public Operation count
plus four specialist-agent projections. Public wrappers retain Operation provenance and checkout
runtime paths; both integrations derive from the same canonical sources.

`status` is read-only and reports drift without a failing exit code. `check` is also read-only and
returns nonzero for any drift. `apply` refreshes only desired generated outputs as regular files,
including replacing legacy generated symlinks. A non-file target conflict prevents apply; an
unexpected Concorde-owned projection remains untouched and prevents both check and apply from
reporting current. Invalid canonical sources, missing pairs, and output collisions fail without a
false current result. Unrelated assets and canonical source bytes remain unchanged. Repeating apply
against current inputs is idempotent, and the following check must report current.

`verify-worktree` takes an absolute project-local Skill path exactly as advertised by the agent
runtime. It accepts regular `.agents/skills/concorde-*/SKILL.md` or
`.claude/skills/concorde-*/SKILL.md` files, derives the owning Git root and integration, and requires
the active worktree's generated surfaces to be current. A successful schema-1 result identifies
`tool`, `status`, `project_root`, `loaded_worktree`, `integration`, `capability`, `surface_match`,
and `worktree_head`. Unsafe or missing paths, stale active projections, or different loaded/active
roots return nonzero. Different roots are rejected even when their generated bytes match. The
failure names both worktrees and asks the user to open a new agent in the target worktree; updating
the loaded/primary checkout is not a substitute.

Repository policy requires this verification before project work and after changing worktrees, for
each distinct owning worktree represented by project Skill paths retained in the conversation.
An agent that creates a requested linked worktree reports its path and branch and hands work to a
new agent opened there. The policy forbids direct edits to generated capability and reflection-agent
files: maintain canonical sources, run apply in their own worktree, then require check to pass.
A project-local Skill cannot govern maintenance of its own surface. A maintenance session that has
not loaded that Skill body may update sources and projections; a session that has loaded it must
reopen before editing. Discovery metadata alone does not load a Skill body.

Pull-request CI requires the worktree-local check and source projection/worktree-affinity tests.
Behavioral coverage must show exact drift detection without writes, both integrations refreshed
together, non-file conflicts and unexpected projections preserved, and a second check becoming
current after a valid apply. With two linked worktrees, verification must reject a Skill loaded from
the other root both before and after their canonical sources diverge. Applying within one worktree
must leave the other's generated bytes unchanged, while verification with its own current Skill
path succeeds.

## Main routing view

Select `module.package-assets` for manifest inventory, canonical Skill/Operation rendering and agent
surface ownership. Select `module.managed-runtime` for managed Python or viewer provisioning. Select
`service.spec-context` when the requested behavior is project initialization, migration or Protocol
binding rather than installation ownership. These IDs are sufficient to route Module work without
expanding the Module targets.
