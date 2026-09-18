# Distribution scenarios

These precise specifications belong directly to the [Distribution Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker profile](../harness/module.md#terminology) | Defined in Harness. |
| [Operation](../module.md#terminology) | Defined in Concorde Framework. |
| [Public operation](../development/module.md#terminology) | Defined in Development operation host. |
| [Internal operation](../development/module.md#terminology) | Defined in Development operation host. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Worktree](../module.md#terminology) | Defined in Concorde Framework. |
| [Candidate](../module.md#terminology) | Defined in Concorde Framework. |
| [Installation](installation.md#terminology) | Defined in Installing and updating Concorde. |
| [Update](installation.md#terminology) | Defined in Installing and updating Concorde. |
| [Installation receipt](installation.md#terminology) | Defined in Installing and updating Concorde. |
| [Initialization](../spec/initialize.md#terminology) | Defined in Project initialization. |
| [Protocol binding](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |

## Installation service

### scenario.distribution.install-preview — Preview reports current owned output integrity without writing

- GIVEN a supported integration and a target directory
- WHEN the installer runs without `--apply`
- THEN it returns a read-only preview of owned Framework, Skill and root-guidance changes
- AND repeating the preview reports current owned output integrity without writing anything

### scenario.distribution.install-apply — Applying an accepted current proposal installs owned outputs

- GIVEN a reviewed installation or update proposal that is still current
- WHEN the installer runs with `--apply`
- THEN it writes the accepted receipt-owned Framework, Skill and root-guidance changes
- AND it deploys the Protocol bundle under `.concorde/protocol/` as receipt-owned output, refreshed on every install and update, without touching the project's Protocol binding
- AND it preserves project Specs, configuration, reflection history and unrelated user files
- AND a `node_modules` directory below the package's `viewer/` or `pi/` directory is neither deployed nor inspected

Installation places rendered Skill entries in the selected project's `.agents/skills/` or
`.claude/skills/` directory. Framework code, role instructions, rule assets, templates and
supporting tools are deployed under `.concorde/framework/`; the managed runtime is provisioned
separately. The Protocol bundle the project binds and grants to agents, the tracked manifest and
its rendered assets, is deployed at `.concorde/protocol/`, a stable project path independent of
the Framework layout. A `node_modules` directory below the package's `viewer/` or `pi/` directory, left by
a local install in a source checkout, is neither deployed nor inspected, because the managed runtime
provisions the viewer and the Pi worker extensions from their own `package.json` and lock; every other
entry below `viewer/` and `pi/` is deployed like the rest of the package. It also installs the selected root rule entry: `AGENTS.md` explicitly directs Codex to
read `.concorde/protocol/principles.md`; `CLAUDE.md` uses Claude's native relative `@` import of
the same file. Only the selected integration's entry is installed. It seeds the Concorde-owned
defaults a project starts from, `.concorde/issues/.gitignore` and
`.concorde/topology-proposals/.gitignore`, only when absent; these defaults are
excluded from the installation receipt and never overwritten on update. Everything that exists only
because Concorde is installed is the installer's output; initialization creates only what the
user's project generates through Concorde, its configuration, registry and Module stub.

### scenario.distribution.install-conflict-rejected — Conflicting or stale ownership blocks acceptance

- GIVEN a locally modified owned block, an unowned root entry, a symlinked or malformed root file, or a stale preview
- WHEN `--apply` is requested
- THEN the installer rejects the change before writing
- AND any already-replaced owned state is restored

Root rule ownership and installation's failure rollback are Module-wide requirements; see
[req.distribution.root-block-ownership](requirements.md#req.distribution.root-block-ownership) and
[req.distribution.rollback-on-failure](requirements.md#req.distribution.rollback-on-failure).

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

### scenario.distribution.configure-apply — Configuration changes an initialized project's Pi worker selection atomically

- GIVEN an initialized project and an explicit supported configuration value
- WHEN concorde-configure is applied
- THEN the new configuration is written atomically
- AND unsupported values, an uninitialized project or a failed write leave the previous configuration in place

### scenario.distribution.accept-protocol — Accepting an upgraded installed Protocol is explicit

- GIVEN an initialized project whose Protocol binding no longer matches the Protocol copy the installer placed under `.concorde/protocol/`
- WHEN concorde-configure is applied without `accept_protocol`
- THEN it fails with protocol_mismatch and leaves the binding unchanged
- BUT when it is applied with `accept_protocol: true`, it rebinds the configuration to the installed copy's manifest and admits the repository, rolling the write back if admission fails

Owned content is hashed in the installation receipt. A local modification conflicts unless an
explicit supported ownership transition authorizes replacement. Staging, provisioning and
verification must finish before installation is accepted; failure restores replaced outputs and
receipts. The locked managed Python runtime runs actual operations; viewer provisioning is
separate and versioned. Check verifies receipt hashes and required runtime identity without
changing project behavior.

The distributable manifest is `concorde.json` schema_version 3, Concorde 8.0.0, Architecture
Profile 15, Workspace Protocol 16 and Delivery Proposal 10. The single inventory has 26
Operations: 9 public Skill entries and 17 private nodes, including 12 model-backed nodes with
Pi worker profiles. It declares package roots including `prompts`/`operations`/`protocol`, with
no separate `agents` authoring root, and 4 templates. Codex `.agents/skills` and Claude
`.claude/skills` expose the same 9 Skills; non-public Operations remain private. Every Skill sends a typed `invocation@3` to
`scripts/run-operation.py` and does not inspect project context.

Project initialization and Protocol-binding decisions are a distinct typed `concorde-init`
operation owned by the [Spec Module](../spec/module.md), not by this Module.

### scenario.distribution.worktree-guard-refuses — The guard refuses native worktree creation in a developer session

- GIVEN a Claude Code or Codex hook payload for a `WorktreeCreate` event, an `EnterWorktree` tool call, a worktree-isolated Agent/Task call, or a shell command whose text contains a worktree-add/move or `claude --worktree` form
- WHEN the worktree guard decides that payload
- THEN it writes a `permissionDecision: deny` object with its reason to stdout and the reason to stderr, and exits 2
- AND `git worktree list`, removing a worktree and starting a session in an existing host-created worktree are allowed unchanged

The guard's decision procedure and its checkout-only scope are Module-wide requirements; see
[req.distribution.guard-inspects-text](requirements.md#req.distribution.guard-inspects-text) and
[req.distribution.guard-checkout-only](requirements.md#req.distribution.guard-checkout-only).

The source checkout refuses native worktree creation in developer agent sessions because its
project-local Skills are worktree-owned build output: a session that loaded them in one worktree
and then created or entered another would act on the second worktree with the first worktree's
instructions. A developer session therefore makes its change in the worktree it started in, as
direct developer-authorized maintenance; a further worktree exists only when the developer
explicitly asks for a Concorde graph, whose host creates the candidate worktree from the committed
base, builds it, and returns a P10 handoff for a fresh session there.

Unreadable hook input exits 1, a visible non-blocking hook error rather than a refusal of every
tool call. `--check "<command>"` decides one command text and `--explain` prints the policy for
people. `.claude/settings.json` denies `EnterWorktree`, `Agent(isolation:worktree)` and the
`git worktree add`, `git worktree move` and `claude --worktree` command prefixes outright, and runs
the guard from `PreToolUse` and `WorktreeCreate`; `.codex/rules/worktree.rules` and
`.codex/hooks.json` provide the matching Codex layer, loaded only for a trusted project. The guard
inspects the command text an agent submits, so a command that computes `git worktree add` at
runtime, or input sent to an already running shell, is outside its reach. Concorde's own workers
are unaffected: each Pi worker process starts with sessions, project settings and discovered
extensions disabled and its own configuration directory holding only what the host placed there,
so it never reads this checkout's `.claude/` or `.codex/` layer and never creates a worktree itself.

### scenario.distribution.check-docsite-external — Type-check preparation uses disposable external files

- GIVEN a source checkout with a configured docsite type check
- WHEN the maintenance type-check command runs
- THEN it prepares a disposable external docsite copy and derives the sidebar from the actual project registry
- AND dependency installation and generated sidebar files are confined to that copy
- AND installed project dependencies may be reused read-only only when their dependency marker matches package and lock bytes
- AND the command returns the type compiler's exit status and removes the temporary copy

`scripts/development/check-docsite-types.py` uses the temporary directory selected by the host's
environment. Configured invocation supplies external scratch through TMPDIR. Existing matching
dependencies are linked for reads; otherwise `npm ci --ignore-scripts` installs into the temporary
copy. It never updates a dependency marker or `.generated` files in the actual checkout. Checks
that need persistent source or dependency changes must prepare them in the implementation phase.

## Build

### scenario.distribution.build-render — Build renders deterministic projections from authored sources

- GIVEN the current `prompts/`, `skills/`, `operations/` and Protocol chapter sources
- WHEN build runs for a selected integration
- THEN it renders Agent instructions, Skill files, the Studio graph configuration, Protocol assets and runtime schemas deterministically
- AND repeated renders of unchanged inputs are byte-identical and perform no network or process I/O

### scenario.distribution.build-checkout-skills-user-invoked — The source checkout's Skills wait for the developer's explicit request

- GIVEN a build without a framework prefix, whose Skill launcher is the checkout's own `scripts/run-operation.py`
- WHEN build renders the Claude Skill projections
- THEN every rendered `SKILL.md` declares `user-invocable: true` and `disable-model-invocation: true`, so Claude Code offers the Skill to the developer's own `/concorde-<name>` invocation and never lists it for the model
- AND a build with a framework prefix, the installed consumer projection, declares `disable-model-invocation: false`
- BUT Codex projections carry no invocation fields in either case

A build without a framework prefix projects the Skills into the Concorde source checkout itself.
Developing that checkout is direct developer-authorized maintenance by default, and one of
Concorde's own graphs runs there only when the developer explicitly asks for it, by its slash
command or by naming it in prose; in the latter case the developer's session reads the rendered
Skill file under `.claude/skills/<name>/` and submits the typed request it describes. Hiding the
Skill from the model keeps that choice with the developer. An installed consumer project receives
the same Skills through a framework prefix and keeps model-initiated invocation, because there the
Skills are the intended everyday entry points. Codex has no equivalent front-matter switch; the
checkout's root instructions state the rule for that runtime.

### scenario.distribution.build-write — write_build records source and output digests in the manifest

- GIVEN a completed render
- WHEN write_build runs
- THEN it writes the rendered outputs plus `generated/build-manifest.json` recording every recorded source path's sha256
- AND it removes retired outputs within its declared owned subtrees (`generated/agents`, `generated/protocol` and `generated/docs`) and explicitly retired Skill projections under the retirement contract below, preserving other generators' assets

### scenario.distribution.build-check — check_build reports staleness without writing

- GIVEN the currently committed generated outputs
- WHEN check_build runs
- THEN it renders into a temporary directory and reports every stale or drifted output
- AND it writes nothing to the worktree

### scenario.distribution.build-retired-skills — Retired Skill projections do not survive rebuilding

- GIVEN an explicitly retired Skill directory remains after its name leaves the current Skill inventory or build manifest
- WHEN check_build or write_build runs for the selected integration
- THEN check_build reports the retired directory without modifying it
- AND write_build removes only its regular `SKILL.md` and empty directory at the selected Skill destination
- AND unknown Skill directories, including names beginning with `concorde-`, and unselected integrations remain untouched
- BUT a retired path that is not a directory, a symlink in its integration ancestors or contents, or any extra directory content causes write_build to fail before deleting or writing outputs

The explicit retirement inventory currently contains `concorde-reflections-triage`; new retirements
extend that inventory rather than authorizing deletion by prefix. An already empty retired directory
is removed too. When `integration_root` is supplied, retirement uses that destination, not the
source package's Skill directories. All retirement candidates are preflighted before any output
mutation. A symlinked integration ancestor is also refused by check_build without traversing it.
Repeated rebuilding is idempotent. Build fixture membership equals the current worker and Skill
projection inventory; obsolete fixture files are not an alternative supported inventory.

### scenario.distribution.build-stale-blocks-execution — A stale build fails closed

- GIVEN a recorded source has changed since the last build
- WHEN a top-level model-backed operation is invoked in execute or describe-policy mode
- THEN verify_fresh raises a `stale_build` BuildError and the invocation does not proceed with stale instructions

The deterministic operations `concorde-init`, `concorde-configure`,
`concorde-validate` and `concorde-deliver` are exempt from this entry check: they launch no Agents
and consume no generated Agent instructions. Loading an Agent still verifies freshness
independently. This exception does not waive Protocol, input, permission or evidence checks.

### scenario.distribution.load-agent — load_model_instructions returns one Agent's current admitted binding

- GIVEN a named Agent and a fresh build
- WHEN load_model_instructions is called
- THEN it verifies freshness first and returns the Agent's rendered body, effect declaration and complete `WorkerBinding`
- AND an unknown Agent or an invalid binding fails closed with a typed BuildError (`stale_build`, `unknown_agent`, or `invalid_agent_binding`)

`validate_package(root)` runs the complete prompt, operation-module, Agent, contract,
Spec-alignment and build-output checks behind `python -m concorde validate` and `build --check`.
`recompute_protocol_manifest`/`python -m concorde protocol-manifest` report, accept (`--write`), or
bind (`--bind-project`) the tracked `protocol/manifest.json` digest to the current build; accepting
a changed Protocol export is developer-only, and a consumer separately accepts the installed
manifest version/digest in its own project configuration. Agent responsibility files are bound
separately by their Operation execution profiles. Protocol adapters and the Framework execution profile are bound by
Protocol assets; the independent standard under `protocol/` is an external normative input, not a
Module-bound Spec. Protocol adapters alone may include its plain Markdown chapters, which require
no audience front matter. The build records included chapter bytes in source identities so edits
invalidate runtime outputs. Modules refer to their own entity file listings rather than owning file
prefixes themselves.

### scenario.distribution.operation-determinism — Operation metadata accounts for model calls

- GIVEN operation modules declaring public exposure, context selection, Agents, host routing and acyclic `USES` composition
- WHEN package validation checks their metadata
- THEN each module must declare a boolean `DETERMINISTIC`, rejecting missing values, strings and integers
- AND the flag must be true exactly when neither its model profile, host routing nor any transitive USES operation can call a model
- AND an operation declaring no Agent context selection must have no model-call path
- AND the single registered `concorde-operations` block must contain the same boolean `deterministic` for every operation alongside its `id`, `public`, `context_selection` and `skill`
- BUT a path that skips model execution does not make a model-backed operation deterministic

Validation checks declared model-call paths, not arbitrary Python or subprocess behavior. It
reports invalid metadata with `CONCORDE-OPERATION-CONSTANTS-001`, inconsistent determinism
with `CONCORDE-OPERATION-DETERMINISTIC-001`, and Spec metadata drift with
`CONCORDE-SPEC-OPERATIONS-001`. Unknown or cyclic composition remains a composition error;
validation cannot certify its determinism.

## Managed runtime

### scenario.distribution.runtime-plan — Planning compares existing state without changing it

- GIVEN a target directory, the loaded runtime specification and its current receipt
- WHEN plan_runtime runs
- THEN it returns one action of create, unchanged, rebuild or conflict with the compared path, role and digest
- AND planning performs no file replacement or package acquisition, though it may run local offline health probes

### scenario.distribution.runtime-provision — Provisioning stages and verifies the reviewed action

- GIVEN a current reviewed plan_runtime action that is not conflict
- WHEN provision_runtime runs
- THEN it stages the locked Python interpreter, the official viewer and the pinned Pi worker extensions, verifies their identity, and records the resulting receipt
- AND an unchanged verified runtime may be reused, though even `unchanged` rechecks health and may refresh the marker

### scenario.distribution.runtime-provision-failure — Failed acquisition or verification does not replace a valid runtime

- GIVEN a provisioning attempt that fails acquisition or verification
- WHEN provision_runtime returns that failure
- THEN it must not replace a previously valid runtime or mark partial state usable
- AND a create destination that appears after planning is rejected rather than adopted
- AND the returned result carries no successful runtime metadata, so a caller cannot infer recovery from its absence
