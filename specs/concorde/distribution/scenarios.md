# Distribution scenarios

These precise specifications belong directly to the [Distribution Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term                                                      | Meaning / definition                         |
| --------------------------------------------------------- | -------------------------------------------- |
| [Skill](../module.md#terminology)                         | Defined in Concorde Framework.               |
| [Worker](../module.md#terminology)                        | Defined in Concorde Framework.               |
| [Worker profile](../harness/module.md#terminology)        | Defined in Harness.                          |
| [Operation](../module.md#terminology)                     | Defined in Concorde Framework.               |
| [Public operation](../operations/module.md#terminology)   | Defined in Operations.                       |
| [Internal operation](../operations/module.md#terminology) | Defined in Operations.                       |
| [Host](../module.md#terminology)                          | Defined in Concorde Framework.               |
| [Worktree](../module.md#terminology)                      | Defined in Concorde Framework.               |
| [Candidate](../module.md#terminology)                     | Defined in Concorde Framework.               |
| [Installation](installation.md#terminology)               | Defined in Installing and updating Concorde. |
| [Update](installation.md#terminology)                     | Defined in Installing and updating Concorde. |
| [Installation receipt](installation.md#terminology)       | Defined in Installing and updating Concorde. |
| [Initialization](../spec/initialize.md#terminology)       | Defined in Project initialization.           |
| [Protocol binding](../spec/values.md#terminology)         | Defined in Identities and versions.          |
| [Spec](../module.md#terminology)                          | Defined in Concorde Framework.               |

## Installation service

### scenario.distribution.install-preview — Preview reports current owned output integrity without writing

- GIVEN one or more supported integrations and a target directory
- WHEN the installer runs without `--apply`
- THEN it returns a read-only preview of owned Framework and root-guidance changes and names the Skill placement it will delegate to the Agent Skills CLI
- AND repeating the preview reports current owned output integrity without writing anything

### scenario.distribution.install-apply — Applying an accepted current proposal installs owned outputs

- GIVEN a reviewed installation or update proposal that is still current
- WHEN the installer runs with `--apply`
- THEN it writes the accepted receipt-owned Framework and root-guidance changes and then has the pinned Agent Skills CLI place the published Skills for the selected Skill clients
- AND it deploys the Protocol bundle under `.concorde/protocol/` as receipt-owned output, refreshed on every install and update, without touching the project's Protocol binding
- AND it preserves project Specs, configuration, reflection history and unrelated user files
- AND a `node_modules` directory below the package's `pi/` directory is neither deployed nor inspected

Framework code, role instructions, rule assets, templates, the published Skills and supporting
tools are deployed under `.concorde/framework/`; the managed runtime is provisioned separately.
The installer copies no Skill into `.agents/skills/` or `.claude/skills/` itself: after the owned
outputs are in place it runs the Agent Skills CLI pinned by the package manifest against the
deployed framework copy, as [install-skills-cli](#scenario.distribution.install-skills-cli)
specifies. The Protocol bundle the project binds and grants to agents, the tracked manifest and
its rendered assets, is deployed at `.concorde/protocol/`, a stable project path independent of
the Framework layout. A `node_modules` directory below the package's `pi/` directory, left by
a local install in a source checkout, is neither deployed nor inspected, because the managed runtime
provisions the Pi worker extensions from their own `package.json` and lock; every other
entry below `pi/` is deployed like the rest of the package. It also installs each selected client's
root rule entry: `AGENTS.md` explicitly directs Codex and Pi to read
`.concorde/protocol/principles.md`; `CLAUDE.md` uses Claude's native relative `@` import of the
same file. It seeds the Concorde-owned defaults a project starts from,
`.concorde/issues/.gitignore`, only when absent;
these defaults are excluded from the installation receipt and never overwritten on update.
Everything that exists only because Concorde is installed is the installer's output or its
delegation to the Skills CLI; initialization creates only what the user's project generates
through Concorde, its configuration, registry and Module stub.

### scenario.distribution.install-skills-cli — The Agent Skills CLI places the published Skills

- GIVEN a selection that includes a Skill client, Claude Code or Codex, and an applied plan whose framework copy is in place
- WHEN the installer places the Skills
- THEN it runs the Agent Skills CLI version pinned in the package manifest (`install.skills_cli`) with the deployed framework copy `./.concorde/framework` as the source and the selected clients as agents, so the CLI installs the framework's published `skills/` into `.agents/skills/` or `.claude/skills/` in its own layout and records the in-project source in its `skills-lock.json`
- AND the receipt records the delegation, the pinned CLI, the source and the agents, but owns none of the placed Skill files or the CLI's lock file
- AND a Skill file an earlier installer still owns is removed first, together with the directories it leaves empty, so the CLI finds no foreign directory in its way
- AND a CLI failure fails the installation and rolls back the owned outputs like any other failure; the Skills the CLI may have placed are not receipt state
- BUT a selection of only Pi delegates nothing, because Pi receives the session extension shim

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
conflicts. The one whole-file act the installer performs is removing a root file it created itself
when its entry's removal leaves that file empty; the receipt records that creation, and a file the
developer created is never removed.

### scenario.distribution.install-remove-guidance — Root-guidance cleanup removes only receipt-owned entries

- GIVEN an installed receipt with owned root entries
- WHEN `--remove-protocol-guidance --apply` is requested
- THEN only the receipt-owned root entries are removed
- AND a root file the installer itself created for its entry, which the receipt records, is removed with the entry when nothing else remains in it, while a file the developer created stays even when the removal leaves it empty
- AND the runtime, Framework and other receipt records are left in place
- AND repeating the cleanup leaves the result unchanged

This is the root-entry cleanup step for uninstall, not a full-package removal command. The same
entry removal happens when a later selection leaves a client out
([install-multiple-clients](#scenario.distribution.install-multiple-clients)), with the same rule
for the file the entry leaves behind.

### scenario.distribution.install-multiple-clients — One project may carry several clients

- GIVEN an existing installation for one or more clients
- WHEN installation is applied with a selection of clients, repeating `--integration` for several
- THEN every selected client's root entry is installed and the receipt records exactly that selection
- AND the root entry of a client selected earlier but left out now is removed under the same ownership checks, while the Skills the Agent Skills CLI placed for it stay until the developer removes them with that CLI, because the installer owns no placed Skill
- AND old receipts without root entries can upgrade by adding them without adopting arbitrary preexisting marked content

### scenario.distribution.install-pi-session — Installing for Pi places the session extension shim instead of Skills

- GIVEN the `pi` integration is selected
- WHEN installation is applied
- THEN it installs `.pi/extensions/concorde-session.ts` as a receipt-owned output that imports the extension deployed below `.concorde/framework/pi/extensions/` and names the framework launcher and the managed runtime's interpreter
- AND it delegates no Skill placement for Pi, and installs the `AGENTS.md` root entry that Pi reads as a context file
- AND selecting Pi beside a Skill client adds the shim without touching that client's Skills

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
receipts. The locked managed Python runtime runs actual operations. Check verifies receipt hashes
and required runtime identity without changing project behavior.

The distributable manifest is `concorde.json` schema_version 3, Concorde 8.0.0, Architecture
Profile 15, Workspace Protocol 16 and Delivery Proposal 10. The single inventory has 18
Operations: 11 public Skill entries and seven private model-backed nodes with
Pi worker profiles. It declares package roots including `prompts`/`operations`/`protocol`, with
no separate `agents` authoring root, and 4 templates. Codex `.agents/skills` and Claude
`.claude/skills` expose the same 11 Skills; non-public Operations remain private. Every Skill sends a typed `concorde-operation-invocation@3` to
`scripts/run-operation.py` and does not inspect project context.

Project initialization and Protocol-binding decisions are a distinct typed `concorde-init`
operation owned by the [Spec Module](../spec/module.md), not by this Module.

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

- GIVEN the current `prompts/` (including the Skill sources `prompts/skills/`), `operations/` and Protocol chapter sources
- WHEN build runs for a selected integration
- THEN it renders Agent instructions, the checkout's Skill projections, the Studio graph configuration, Protocol assets and runtime schemas deterministically
- AND repeated renders of unchanged inputs are byte-identical and perform no network or process I/O

### scenario.distribution.build-checkout-skills-user-invoked — The source checkout's Skills wait for the developer's explicit request

- GIVEN a source-checkout build without a framework prefix
- WHEN build renders client projections
- THEN all source Skills and the Pi shim live under `generated/session/<client>/`, outside ambient discovery
- AND byte-identical old manifest-owned ambient projections are retired only after complete preflight, while modified or unowned projections block retirement
- AND installed consumers still receive published Skills through the Agent Skills CLI and the Pi shim under `.pi/extensions/`

### scenario.distribution.private-selection — Private fresh session selection

- GIVEN an assigned candidate with a fresh build and explicitly named absolute Skill/runtime paths
- WHEN a fresh test child's inputs are selected
- THEN selection returns only the exact candidate-built Skill bodies, build digest and runtime identity
- AND missing, modified, aliased or out-of-candidate paths fail without ambient fallback
- AND maintenance selection admits no Skills and every selection requests fresh non-forked context with inherited/discovered catalogs disabled
- BUT returning selection metadata or bodies does not prove a model loaded or executed them

### scenario.distribution.skills-publish — The tracked published Skills are rendered by an explicit step

- GIVEN the Skill sources `prompts/skills/<name>.md` of the public Operations and the exported request schemas
- WHEN `skills --write` runs
- THEN it renders into the tracked `skills/<name>/SKILL.md` one client-neutral Skill per public Operation: the standard front matter (`name`, `description`, `compatibility`, `metadata` naming the source, the operation and the installed framework's launcher `.concorde/framework/scripts/run-operation.py`) and no client-specific invocation field, the resolved guidance with `{OPERATION}` bound to that launcher, and the request schema
- AND `skills --check`, `build --check` and package validation report every published Skill that is missing or differs from a fresh render, and every `skills/<dir>/SKILL.md` no public Operation publishes any more, without writing
- AND explicitly retired published Skill directories are removed only after preflighting all retired and destination paths, preserving unknown directories and rejecting symlinks or extra retired content before any output write
- AND `build` never writes under `skills/`: the published Skills are tracked content the Agent Skills CLI installs from this repository or from a deployed framework copy, so they change only through this explicit step and are committed with their sources

### scenario.distribution.build-pi-session — Build renders the Pi session extension shim from the Skill sources

- GIVEN the current Skill sources, their includes and the exported request schemas
- WHEN build renders the `pi` integration
- THEN it renders exactly one private source projection, `generated/session/pi/concorde-session.ts` (or `.pi/extensions/concorde-session.ts` for an installed consumer), which imports the tracked `pi/extensions/concorde-session.ts` and embeds the catalog: every public Operation's name, description, guidance and request schema with its version, the project-relative launcher and the interpreters to try
- AND the guidance is the Skill text without the stdin envelope includes, which the tool supplies itself, and contains no unresolved package token
- AND without a framework prefix the catalog marks explicit-request-only and names the checkout's own launcher and `.venv`; with a framework prefix it imports the extension below that prefix and names the managed runtime's interpreter
- AND repeated renders are byte-identical and the shim is checked and rewritten like the Skill projections

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

The explicit retirement inventory currently contains `concorde-reflections-triage`, `concorde-review`, `concorde-main`,
`concorde-dev-loop` and `concorde-specify-loop`; new retirements
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

- GIVEN operation modules declaring public exposure, context selection, workers and acyclic `USES` composition
- WHEN package validation checks their metadata
- THEN each module must declare a boolean `DETERMINISTIC`, rejecting missing values, strings and integers
- AND the flag must be true exactly when neither its model profile nor any transitive USES operation can call a model
- AND an operation declaring no Agent context selection must have no model-call path
- AND the single registered `concorde-operations` block must contain the same boolean `deterministic` for every operation alongside its `id`, `public`, `context_selection` and `skill`
- BUT a path that skips model execution does not make a model-backed operation deterministic

Validation checks declared model-call paths, not arbitrary Python or subprocess behavior. It
reports invalid metadata with `CONCORDE-OPERATION-CONSTANTS-001`, inconsistent determinism
with `CONCORDE-OPERATION-DETERMINISTIC-001`, and Spec metadata drift with
`CONCORDE-SPEC-OPERATIONS-001`. Unknown or cyclic composition remains a composition error;
validation cannot certify its determinism.

## Pi session projection

### scenario.distribution.pi-session-prompt — A Pi session learns the concorde tool and the public Operations

- GIVEN a Pi session that loaded the rendered shim
- WHEN the session starts a turn
- THEN the extension appends a Concorde section to the system prompt naming the `concorde` tool and every public Operation with its description, and in the source checkout the rule to run an Operation only on the developer's explicit request
- AND the tool's `operation` parameter admits exactly the public Operations, with actions `describe` and `run` and an optional `mode` of `execute` or `describe-policy`

### scenario.distribution.pi-session-describe — Describing an Operation runs nothing

- GIVEN a Pi session that loaded the rendered shim
- WHEN the model calls `concorde` with action `describe`
- THEN the tool returns the Operation's description, guidance and request schema from the catalog without starting the launcher

### scenario.distribution.pi-session-run — Running an Operation submits the typed envelope through the launcher

- GIVEN a Pi session that loaded the rendered shim
- WHEN the model calls `concorde` with action `run` and the request data as `input`
- THEN the tool wraps the input in a `concorde-operation-invocation@3` envelope with the Operation's request type and version, runs the launcher in the project root with the envelope on stdin, and returns the launcher's result envelope with its usage summary
- AND a result the launcher reports as blocked or failed is returned as a tool error carrying that envelope
- AND a missing `input` or an unknown Operation is refused without starting the launcher
- AND a result above 48 KiB is saved to a file the returned text names

### scenario.distribution.pi-session-cancel — Aborting the turn cancels the running Operation

- GIVEN a `run` in progress through the `concorde` tool
- WHEN the developer aborts the turn
- THEN the extension sends the launcher SIGTERM and reports the cancellation as a tool error carrying whatever result the launcher printed
- AND a launcher that has not exited within the grace period is killed together with its process group

### scenario.distribution.launcher-terminated — SIGTERM cancels the launcher like Ctrl-C

- GIVEN a running `scripts/run-operation.py`
- WHEN the process receives SIGTERM
- THEN it takes the Ctrl-C path: a running worker's Pi process is killed and its outcome is cancelled, a Graph interrupted outside a worker launch ends with the `execution_cancelled` error and the change's recorded status, and the result envelope is printed before exit
- AND SIGTERM while the launcher is still waiting for its invocation prints the pre-host failure envelope with `execution_cancelled`

## Managed runtime

### scenario.distribution.runtime-plan — Planning compares existing state without changing it

- GIVEN a target directory, the loaded runtime specification and its current receipt
- WHEN plan_runtime runs
- THEN it returns one action of create, unchanged, rebuild or conflict with the compared path, role and digest
- AND planning performs no file replacement or package acquisition, though it may run local offline health probes

### scenario.distribution.runtime-provision — Provisioning stages and verifies the reviewed action

- GIVEN a current reviewed plan_runtime action that is not conflict
- WHEN provision_runtime runs
- THEN it stages the locked Python interpreter and the pinned Pi worker extensions, verifies their identity, and records the resulting receipt
- AND it runs every public Skill's launcher runtime check with the managed runtime's own interpreter and rejects a check that reports another environment as its prefix, so the verified inventory describes the runtime rather than the installer's interpreter
- AND an unchanged verified runtime may be reused, though even `unchanged` rechecks health and may refresh the marker

### scenario.distribution.runtime-provision-failure — Failed acquisition or verification does not replace a valid runtime

- GIVEN a provisioning attempt that fails acquisition or verification
- WHEN provision_runtime returns that failure
- THEN it must not replace a previously valid runtime or mark partial state usable
- AND a create destination that appears after planning is rejected rather than adopted
- AND the returned result carries no successful runtime metadata, so a caller cannot infer recovery from its absence

### scenario.distribution.launcher-managed-runtime — The installed launcher re-executes itself inside the managed runtime

- GIVEN an installed project whose framework lives at `.concorde/framework` and whose verified managed runtime, with the installer's owner marker, lives at `.concorde/.venv`
- WHEN `.concorde/framework/scripts/run-operation.py` is started with any other interpreter, such as the `python3` a Skill names, even one that cannot import LangGraph
- THEN it re-executes itself with the managed runtime's interpreter before reading its invocation, so the Operation runs with the locked dependencies and the runtime check reports that runtime as its prefix
- AND a launcher already running inside that runtime, such as the one the Pi session tool starts, is not re-executed
- AND the source checkout, which matches neither layout, keeps the interpreter that started it
- AND when no verified managed runtime exists and the starting interpreter cannot import LangGraph, the launcher prints a blocked envelope with `missing_runtime` naming that interpreter instead of failing inside the host
