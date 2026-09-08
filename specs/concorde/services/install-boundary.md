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
Installation places rendered Skill entries in the selected project's `.agents/skills/` or
`.claude/skills/` directory. Framework code, role instructions, rule assets, templates and supporting
tools are deployed under `.concorde/framework/`; the managed runtime is provisioned separately.
Skill definitions and generated instruction assets remain Framework-owned, while their installed
entries are used through the project's model integration.

It also installs the selected root rule entry: `AGENTS.md` explicitly directs Codex to read
`.concorde/framework/generated/protocol/principles.md`; `CLAUDE.md` uses Claude's native relative `@` import.
Only the selected integration's entry is installed. It loads the rule bundle containing the
Concorde Spec Protocol and Framework execution profile, including P10 handoffs, without duplicating
the handoff rules. Internal controlled contexts retain their separate injection
and disabled ambient instruction discovery.

Root entries are shared files with block ownership, not whole-file ownership. Receipt outputs with
role `protocol-guidance` hash only the exact bounded block (including its separator), not user text.
New entries precede user text; upgrades retain an existing block's position. Bytes outside the block
and existing modes survive reinstall, update and integration changes. Root symlinks (including dangling
ones), directories, malformed/duplicate/misordered markers, unowned blocks and modified owned blocks
are conflicts. A stale shared-file preview fails before writes. Runtime/setup failure rolls back
root bytes, modes and the receipt with the other installation outputs.

`--remove-protocol-guidance` previews only removal of receipt-owned root entries; adding `--apply`
performs that cleanup without provisioning or removing the runtime/framework. Empty root files remain,
other receipt records remain, and repeating cleanup is unchanged. This is the root-entry cleanup
step for uninstall, not a full-package removal command. An integration switch uses the same block
ownership checks to remove the previous integration's entry. Old receipts without root entries can
upgrade by adding them without adopting arbitrary preexisting marked content.
It seeds project-owned Reflection defaults and
`.concorde/topology-proposals/.gitignore` only when absent; project defaults are excluded from the
installation receipt and never overwritten on update.

The distributable manifest is concorde.json schema 3, Concorde 4.0.0, Architecture Profile 8,
Workspace Protocol 14 and Delivery Proposal 10. It contains exactly 9 roles and 13
capabilities, of which 7 are Skills (global or lifecycle) and 6 are stages reachable
only through a composing capability, explicit package roots including prompts/capabilities/protocol, and 7
templates. Codex .agents/skills and Claude .claude/skills expose the same 7 Skills;
canonical roles and stage capabilities stay private.
Every Skill sends a typed invocation@3 to `scripts/run-capability.py` and does not inspect project context.

Owned content is hashed in the installation receipt. A local modification conflicts unless an
explicit supported ownership transition authorizes replacement. Staging/provisioning/verification
must finish before installation is accepted; failure restores replaced outputs and receipts. The
locked managed Python runtime runs actual capabilities; viewer provisioning is separate and versioned.
Check verifies receipt hashes and required runtime identity without changing project behavior.

Initialization is a distinct typed concorde-init capability: propose returns a complete file proposal;
apply validates exact before-digests and target state. It pins the packaged global principles and kind
definitions, configures integration/enforcement, and writes an explicit Domain stub with missing
business requirements stated honestly. The stub declares document identity, target membership and
main visibility. Configuration changes use concorde-configure with a typed
configuration. Profile 7 is not agent-compatible and has no migration capability.

Install/update cannot silently rewrite a consumer's Protocol binding. A package with changed Protocol
assets requires the consumer's explicit binding decision before execution. Templates and
prompts enforce the same architectural principles for all consumer projects.

## feature.installation.self-distribute

Concorde's source checkout builds its own canonical Skill and role surfaces into that same
worktree's Codex and Claude surfaces. It does not install a duplicate `.concorde/framework` into the
repository. The inputs are the root `concorde.json`, canonical `prompts/`, `skills/`,
`capabilities/`, and the contract modules under `src/concorde/host`; rendered files under
`generated/`, `.claude/skills/concorde-*` and `.agents/skills/concorde-*` are untracked build output
and never become authoring sources. Repository agent policy stays in `AGENTS.md`, with `CLAUDE.md`
directing Claude to it; the build does not inject checkout policy into Skill bodies.

From the worktree being maintained, the deterministic entry points are:

```bash
python3 scripts/concorde.py build --format json
python3 scripts/concorde.py build --check --format json
python3 scripts/concorde.py verify-worktree --project-root . \
  --loaded-skill-path /absolute/runtime/path/to/.claude/skills/concorde-main/SKILL.md
```

Every invocation operates on the worktree containing the sources named by `--project-root`; it never
points one worktree's build at another worktree's outputs. `build` renders every role, Skill and
Studio-graph projection deterministically from `prompts/`, `skills/` and `capabilities/`, writes them
under `generated/`, `.claude/skills/*` and `.agents/skills/*`, and records their exact source digests
in `generated/build-manifest.json`. `build --check` renders into a temporary directory and reports
every stale or drifted output without writing anything; a current result requires the recorded
outputs and the tracked `protocol/manifest.json` digests to match a fresh render exactly.

`build` and `build --check` are idempotent and byte-identical across repeated runs, and never perform
network or process I/O. Rebuilding after an unrelated source change leaves unrelated outputs
byte-identical. The host refuses to run any capability on a stale build (error code `stale_build`),
verified against `generated/build-manifest.json` before every top-level invocation except a
lifecycle capability; editing a prompt without rebuilding therefore fails closed rather than serving
stale instructions.

`verify-worktree` takes an absolute project-local Skill path exactly as advertised by the agent
runtime. It accepts regular `.agents/skills/concorde-*/SKILL.md` or
`.claude/skills/concorde-*/SKILL.md` files, derives the owning Git root and integration, and requires
the active worktree both to own that loaded Skill and to have a fresh build. A successful schema-1
result identifies `tool`, `status`, `project_root`, `loaded_worktree`, `integration`, `capability`,
`surface_match`, and `worktree_head`. An unsafe or missing path, a stale active build, or different
loaded/active worktree roots return nonzero. Different roots are rejected even when their generated
bytes currently match. The failure names both worktrees and directs the outer agent to initiate a
P10 handoff to the target worktree, automatically by default; updating the loaded/primary checkout
is not a substitute. If automatic startup is unavailable or cannot establish the required isolation,
the outer agent asks the user to open the session manually with the complete prompt. Its existing
diagnostic channel includes a P10 handoff draft with the target path/branch and explicit unknown task/progress
fields for the outer session to complete. A stale build in the same worktree instead asks a
maintenance session to rebuild; it does not allow a session with the affected Skill body already
loaded to edit that Skill. The verifier does not read task, patch or conversation artifacts to invent
a continuation or launch the successor session itself.

Repository policy requires this verification before project work and after changing worktrees, for
each distinct owning worktree represented by project Skill paths retained in the conversation.
An agent that creates a requested linked worktree hands work to a new agent opened there under
Framework execution profile P10, with the known path and branch. A freshly created worktree, including one the host
creates for a candidate change, must be built once before an agent can load Concorde Skills; the
policy forbids direct edits to `generated/`, `.claude/skills/concorde-*` or `.agents/skills/concorde-*`:
maintain `prompts/`, `skills/` or `capabilities/` sources, rebuild in their own worktree, then require
`build --check` to pass. A project-local Skill cannot govern maintenance of its own prompts, Skills,
capabilities, or generated surface. A maintenance session that has not loaded that Skill body may
update sources and rebuild; a session that has loaded it must reopen before editing. Discovery
metadata alone does not load a Skill body.

Pull-request CI requires `build --check`, the package validator, and the worktree-affinity tests to
pass. Behavioral coverage must show exact staleness detection without writes, both integrations
rendered together, and byte-identical repeated builds. With two linked worktrees, verification must
reject a Skill loaded from the other root both before and after their canonical sources diverge.
Building within one worktree must leave the other's generated bytes unchanged, while verification
with its own current Skill path succeeds after that worktree rebuilds.

## Main routing view

Select `module.package-assets` for manifest inventory, canonical Skill/role rendering and the build's
agent surface ownership. Select `module.managed-runtime` for managed Python or viewer provisioning. Select
`service.spec-context` when the requested behavior is project initialization or Protocol
binding rather than installation ownership. These IDs are sufficient to route Module work without
expanding the Module targets.

## Viewer installation and launch ownership

Installation distributes scripts/run-viewer.py and provisions its pinned official viewer runtime.
The launch interface and graph admission behavior are owned by service.viewer and documented in
[Understand Anything viewer](viewer-boundary.md). Native package acquisition and recovery remain
on module.managed-runtime; starting the viewer is a separate developer action.
