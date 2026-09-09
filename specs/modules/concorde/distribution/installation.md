```concorde-document
{
  "id": "document.distribution.installation",
  "targets": [
    "module.distribution"
  ],
  "main_visible": true
}
```
# Installation service

## Configuration compatibility

The canonical Module template and Scenario fragment and the mandatory Spec document format are
authored under `protocol/` and distributed with the independent standard. The `templates/` entry
links to those sources. Plan, task and reflection starters remain Framework workflow assets; they
are not additional Protocol Spec kinds.

The Framework identifies its supported project configuration as Profile 10. Initialization writes
`.concorde/config.json` with `profile_version: 10`, the `registry` path, an accepted Protocol
`version` and manifest `digest` under `protocol`, and the typed `capability_configuration` for
integration and enforcement. Its registry uses JSON schema version 3. Profile 10 and registry
schema 3 are Framework compatibility and storage versions; Spec Protocol 3.0.0 identifies the
independent specification standard. Installation and initialization preserve these separate roles.

## Installing and updating a target project

### scenario.distribution.install-preview — Preview reports current owned output integrity without writing

- GIVEN a supported integration and a target directory
- WHEN the installer runs without `--apply`
- THEN it returns a read-only preview of owned Framework, Skill and root-guidance changes
- AND repeating the preview reports current owned output integrity without writing anything

### scenario.distribution.install-apply — Applying an accepted current proposal installs owned outputs

- GIVEN a reviewed installation or update proposal that is still current
- WHEN the installer runs with `--apply`
- THEN it writes the accepted receipt-owned Framework, Skill and root-guidance changes
- AND it preserves project Specs, configuration, reflection history and unrelated user files

Installation places rendered Skill entries in the selected project's `.agents/skills/` or
`.claude/skills/` directory. Framework code, role instructions, rule assets, templates and
supporting tools are deployed under `.concorde/framework/`; the managed runtime is provisioned
separately. It also installs the selected root rule entry: `AGENTS.md` explicitly directs Codex to
read `.concorde/framework/generated/protocol/principles.md`; `CLAUDE.md` uses Claude's native
relative `@` import. Only the selected integration's entry is installed. It seeds project-owned
Reflection defaults and `.concorde/topology-proposals/.gitignore` only when absent; project
defaults are excluded from the installation receipt and never overwritten on update.

### scenario.distribution.install-conflict-rejected — Conflicting or stale ownership blocks acceptance

- GIVEN a locally modified owned block, an unowned root entry, a symlinked or malformed root file, or a stale preview
- WHEN `--apply` is requested
- THEN the installer rejects the change before writing
- AND any already-replaced owned state is restored

- req.distribution.root-block-ownership: A root rule entry SHALL be owned only within its exact bounded block, including its separator, and SHALL NOT hash or replace surrounding user text.
- req.distribution.rollback-on-failure: A runtime or setup failure during installation SHALL roll back root bytes, modes and the receipt together with the other installation outputs.

Root entries are shared files with block ownership, not whole-file ownership. New entries precede
user text; upgrades retain an existing block's position. Bytes outside the block and existing modes
survive reinstall, update and integration changes. Root symlinks (including dangling ones),
directories, malformed/duplicate/misordered markers, unowned blocks and modified owned blocks are
conflicts.

### scenario.distribution.install-remove-guidance — Root-guidance cleanup removes only receipt-owned entries

- GIVEN an installed receipt with owned root entries
- WHEN `--remove-protocol-guidance --apply` is requested
- THEN only the receipt-owned root entries are removed
- AND the runtime, Framework and other receipt records are left in place
- AND repeating the cleanup leaves the result unchanged

This is the root-entry cleanup step for uninstall, not a full-package removal command.

### scenario.distribution.install-switch-integration — Switching integration replaces only the previous entry

- GIVEN an existing installation for one supported integration
- WHEN installation is applied for a different integration
- THEN the previous integration's owned root entry is removed under the same ownership checks
- AND the new integration's entry is installed
- AND old receipts without root entries can upgrade by adding them without adopting arbitrary preexisting marked content

## Configuring an initialized project

### scenario.distribution.configure-apply — Configuration changes an initialized project's integration or enforcement setting atomically

- GIVEN an initialized project and an explicit supported configuration value
- WHEN concorde-configure is applied
- THEN the new configuration is written atomically
- AND unsupported values, an uninitialized project or a failed write leave the previous configuration in place

Owned content is hashed in the installation receipt. A local modification conflicts unless an
explicit supported ownership transition authorizes replacement. Staging, provisioning and
verification must finish before installation is accepted; failure restores replaced outputs and
receipts. The locked managed Python runtime runs actual capabilities; viewer provisioning is
separate and versioned. Check verifies receipt hashes and required runtime identity without
changing project behavior.

The distributable manifest is `concorde.json` schema_version 3, Concorde 5.0.0, Architecture
Profile 10, Workspace Protocol 15 and Delivery Proposal 10. It contains exactly 8 roles and 13
capabilities, of which 7 are Skills (global or lifecycle) and 6 are stages reachable only through a
composing capability, explicit package roots including `prompts`/`capabilities`/`protocol`, and 5
templates. Codex `.agents/skills` and Claude `.claude/skills` expose the same 7 Skills; canonical
roles and stage capabilities stay private. Every Skill sends a typed `invocation@3` to
`scripts/run-capability.py` and does not inspect project context.

Project initialization and Protocol-binding decisions are a distinct typed `concorde-init`
capability owned by `module.spec`, not by this Module.

## Worktree guard

### scenario.distribution.worktree-guard-refuses — The guard refuses native worktree creation in a developer session

- GIVEN a Claude Code or Codex hook payload for a `WorktreeCreate` event, an `EnterWorktree` tool call, a worktree-isolated Agent/Task call, or a shell command whose text contains a worktree-add/move or `claude --worktree` form
- WHEN the worktree guard decides that payload
- THEN it writes a `permissionDecision: deny` object with its reason to stdout and the reason to stderr, and exits 2
- AND `git worktree list`, removing a worktree and starting a session in an existing host-created worktree are allowed unchanged

- req.distribution.guard-inspects-text: The worktree guard SHALL decide from the submitted command text, including global git options such as `-C` and `--git-dir=`, and SHALL NOT depend on an agent remembering the policy.
- req.distribution.guard-checkout-only: The worktree guard SHALL protect only developer sessions of this source checkout and SHALL NOT be installed into consumer projects.

The source checkout refuses native worktree creation in developer agent sessions because its
project-local Skills are worktree-owned build output: a session that loaded them in one worktree
and then created or entered another would act on the second worktree with the first worktree's
instructions. Worktrees for changes come only from the Concorde host, which creates the candidate
worktree from the committed base, builds it, and returns a P10 handoff for a fresh session there.

Unreadable hook input exits 1, a visible non-blocking hook error rather than a refusal of every
tool call. `--check "<command>"` decides one command text and `--explain` prints the policy for
people. `.claude/settings.json` denies `EnterWorktree`, `Agent(isolation:worktree)` and the
`git worktree add`, `git worktree move` and `claude --worktree` command prefixes outright, and runs
the guard from `PreToolUse` and `WorktreeCreate`; `.codex/rules/worktree.rules` and
`.codex/hooks.json` provide the matching Codex layer, loaded only for a trusted project. The guard
inspects the command text an agent submits, so a command that computes `git worktree add` at
runtime, or input sent to an already running shell, is outside its reach. Concorde's own workers
are unaffected: Claude workers start with `--restricted`, which ignores project settings, and Codex
workers start with `--ignore-user-config`, which leaves the project `.codex/` layer untrusted.

## Main routing view

Select `module.distribution` for manifest inventory, canonical Skill/role rendering, the build's
agent surface ownership, and managed Python or viewer provisioning. Select `module.spec` when the
requested behavior is project initialization or Protocol binding rather than installation
ownership. Installation distributes `scripts/run-viewer.py` and provisions its pinned official
viewer runtime; the launch interface and graph admission behavior are owned by `module.views` and
documented in [Understand Anything viewer](../views/viewer.md). Native package acquisition and
recovery remain on `module.distribution`; starting the viewer is a separate developer action.
