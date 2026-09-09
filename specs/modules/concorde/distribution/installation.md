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

The canonical Module and Implementation templates, Feature fragment and mandatory Spec document
format are authored under `protocol/` and distributed with the independent standard. The three
Spec entries under `templates/` link to those sources. Plan, task and reflection starters remain
Framework workflow assets; they are not additional Protocol Spec kinds.

The Framework identifies its supported project configuration as Profile 9. Initialization writes
`.concorde/config.json` with `profile_version: 9`, the `registry` path, an accepted Protocol
`version` and manifest `digest` under `protocol`, and the typed `capability_configuration` for
integration and enforcement. Its registry uses JSON schema version 2. Profile 9 and registry
schema 2 are Framework compatibility and storage versions; Spec Protocol 2.1.0 identifies the
independent specification standard. Installation and initialization preserve these separate roles.

## feature.distribution.install

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

The distributable manifest is concorde.json schema 3, Concorde 4.0.0, Architecture Profile 9,
Workspace Protocol 14 and Delivery Proposal 10. It contains exactly 8 roles and 13
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
definitions, configures integration/enforcement, and writes an explicit Module stub with missing
business requirements stated honestly. The stub declares document identity, target membership and
main visibility. Configuration changes use concorde-configure with a typed
configuration. Profile 7 is not agent-compatible and has no migration capability.

Install/update cannot silently rewrite a consumer's Protocol binding. A package with changed Protocol
assets requires the consumer's explicit binding decision before execution. Templates and
prompts enforce the same architectural principles for all consumer projects.

## feature.distribution.build

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
python3 scripts/worktree-guard.py --explain
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
byte-identical. The host refuses ordinary capability execution on a stale build (error code `stale_build`),
verified against `generated/build-manifest.json` before every top-level invocation except a
lifecycle capability; editing a prompt without rebuilding therefore fails closed rather than serving
stale instructions.

### Worktree guard

The source checkout refuses native worktree creation in developer agent sessions, because its
project-local Skills are worktree-owned build output: a session that loaded them in one worktree
and then created or entered another would act on the second worktree with the first worktree's
instructions. Worktrees for changes come only from the Concorde host, which creates the candidate
worktree from the committed base, builds it, and returns a P10 handoff for a fresh session there.

`scripts/worktree-guard.py` is the hook command. It reads one Claude Code or Codex hook payload
from stdin and decides: a `WorktreeCreate` event is always refused, so `claude --worktree`,
subagents with `isolation: "worktree"` and background-session worktrees never materialise; a
`PreToolUse` event is refused for the `EnterWorktree` tool, for `Agent`/`Task` calls whose
`isolation` is `worktree`, and for shell tools whose command text contains `git … worktree add`,
`git … worktree move` (global git options such as `-C` and `--git-dir=` included) or a `claude`
launch with `--worktree`/`-w`. Other events, tools and commands pass silently; `git worktree list`,
removing a worktree, and starting a session in an existing host-created worktree are allowed. A
refusal writes a `permissionDecision: deny` object with its reason to stdout, the reason to stderr,
and exits 2, which both runtimes treat as a block and report to the model. Unreadable input exits
1, a visible non-blocking hook error rather than a refusal of every tool call. `--check "<command>"`
decides one command text and `--explain` prints the policy for people.

The checked-in integration files register the guard per worktree, so a session opened in any
worktree of this repository is guarded from its first tool call. `.claude/settings.json` denies
`EnterWorktree`, `Agent(isolation:worktree)` and the `git worktree add`, `git worktree move` and
`claude --worktree` command prefixes outright, and runs the guard from `PreToolUse` (matching
`EnterWorktree`, `Agent`, `Task`, `Bash` and `PowerShell`) and from `WorktreeCreate`; Claude Code
applies deny rules and hooks to native subagents as well. `.codex/rules/worktree.rules` forbids the
`git worktree add` and `git worktree move` prefixes without prompting, and `.codex/hooks.json` runs
the guard from `PreToolUse` for shell commands; Codex loads both only for a trusted project and runs
the hook only after it was reviewed once with `/hooks`, so the execpolicy rule is the layer that
holds before that review. These files are the checkout's agent-integration configuration, next to
`AGENTS.md`; the registry binds no file under `.claude/` or `.codex/` to an Implementation Spec.

The guard protects the developer's session and its native subagents; it is a guardrail, not a
sandbox. It inspects the command text an agent submits, so a command that computes
`git worktree add` at runtime, or input sent to an already running shell, is outside its reach; and
because the whole text is inspected, a file that must mention these commands is written with the
editor tool rather than a shell here-document. Concorde's own workers are unaffected: Claude workers
start with `--restricted`, which ignores project settings, and Codex workers start with
`--ignore-user-config`, which leaves the project `.codex/` layer untrusted. The guard is repository
policy for developing Concorde; the installer ships neither the script nor the integration files,
and consumer projects receive no hook.

An agent that needs a change worktree requests it through a Concorde capability. The host builds
the worktrees it creates for candidate changes; any other freshly created worktree has no Concorde
Skills until it is built. The policy forbids direct edits to `generated/`,
`.claude/skills/concorde-*` or `.agents/skills/concorde-*`: maintain `prompts/`, `skills/` or
`capabilities/` sources, rebuild in their own worktree, then require `build --check` to pass. A
project-local Skill cannot govern maintenance of its own prompts, Skills, capabilities, or generated
surface. A maintenance session that has not loaded that Skill body may update sources and rebuild;
a session that has loaded it must reopen before editing. Discovery metadata alone does not load a
Skill body.

Pull-request CI requires `build --check`, the package validator, and the worktree-guard tests to
pass. Behavioral coverage must show exact staleness detection without writes, both integrations
rendered together, byte-identical repeated builds, the guard's refusals and allowances for the
documented events and commands with their exit codes and outputs, and that the checked-in Claude
Code and Codex files register the guard. A fresh clone must carry the guard and those files.
Building within one worktree must leave the other's generated bytes unchanged.

## Main routing view

Select `module.distribution` for manifest inventory, canonical Skill/role rendering and the build's
agent surface ownership. Select `module.distribution` for managed Python or viewer provisioning. Select
`module.harness` when the requested behavior is project initialization or Protocol
binding rather than installation ownership. These IDs are sufficient to route Module work without
expanding the Module targets.

## Viewer installation and launch ownership

Installation distributes scripts/run-viewer.py and provisions its pinned official viewer runtime.
The launch interface and graph admission behavior are owned by module.views and documented in
[Understand Anything viewer](../views/viewer.md). Native package acquisition and recovery remain
on module.distribution; starting the viewer is a separate developer action.
