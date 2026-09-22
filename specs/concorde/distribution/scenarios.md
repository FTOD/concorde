# Distribution scenarios

These precise specifications belong directly to the [Distribution Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term                                                      | Meaning / definition                         |
| --------------------------------------------------------- | -------------------------------------------- |
| [Pi integration](../module.md#terminology)                | Defined in Concorde Framework.               |
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

Throughout these scenarios, public operation/Operation is the compatibility catalog/launcher term
from [Operations](../operations/module.md#terminology), not a StateGraph backend claim. Exact
scenario IDs, transport fields and historical retirement names remain unchanged. Current
capability kinds and canonical role ownership follow [Agents](../agents/roles.md) and the
[typed catalog contract](contracts.md#typed-executable-catalog-compatibility).

## Installation service

### scenario.distribution.install-preview — Preview reports current owned output integrity without writing

- GIVEN a Pi installation target directory
- WHEN the installer runs without `--apply`
- THEN it returns a read-only preview of owned Framework, Pi extension and root-guidance changes, with a notice explaining manual retirement of external CLI-owned Skills
- AND repeating the preview reports current owned output integrity without writing anything

### scenario.distribution.install-apply — Applying an accepted current proposal installs owned outputs

- GIVEN a reviewed installation or update proposal that is still current
- WHEN the installer runs with `--apply`
- THEN it writes the accepted receipt-owned Framework, Pi extension and root-guidance changes without invoking a Skills CLI
- AND it deploys the Protocol bundle under `.concorde/protocol/` as receipt-owned output, refreshed on every install and update, without touching the project's Protocol binding
- AND it preserves project Specs, configuration, reflection history and unrelated user files
- AND a `node_modules` directory below the package's `pi/` directory is neither deployed nor inspected

Framework code, internal worker instructions, rule assets, templates and supporting tools are
deployed under `.concorde/framework/`; the managed runtime is provisioned separately. No public
Skill product is deployed. The installer copies no Skill into `.agents/skills/` or `.claude/skills/`
and never invokes `npx skills`. The Protocol bundle is deployed at `.concorde/protocol/`, independent
of the Framework layout, without accepting its binding for the project. `pi/node_modules` is
neither inspected nor copied; the managed runtime provisions TypeBox from its own lock with npm.
The Pi shim imports the deployed extension, and `AGENTS.md` directs the reader to the Protocol.
Concorde-owned defaults such as `.concorde/issues/.gitignore` are seeded only when absent,
excluded from the receipt, and never overwritten. Initialization remains separate.

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
survive reinstall, update and retirement of legacy client entries. Root symlinks (including dangling ones),
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
entry removal happens when upgrading a legacy Claude installation to Pi, with the same rule
for the file the entry leaves behind.

### scenario.distribution.install-retired-clients — Pi-only upgrade preserves legacy ownership

- GIVEN a legacy schema-1 multi-client installation receipt
- WHEN the Pi-only installer applies an upgrade
- THEN it installs the Pi shim and AGENTS.md entry and removes only unchanged receipt-owned retired files and the exact owned CLAUDE.md block
- AND edited owned content, unsafe links or changed preview inputs block before writing
- AND surrounding text, modes, unrelated files, external CLI-owned Skills and skills-lock.json are preserved
- AND a failure restores retired owned bytes, modes and the previous receipt, permitting a fresh-plan retry
- AND old receipts without root entries can add Pi guidance without adopting arbitrary preexisting marked content

Both text and JSON installer results report that external CLI-owned Skills require explicit manual
removal of the developer's own retired Concorde entries, never wholesale directory or lock deletion.
The installer performs no CLI delegation, including during migration. Empty retired directories
may remain; ownership of a file does not grant ownership of neighboring directory contents.

### scenario.distribution.template-ownership — Templates ship only with their owners

- GIVEN a current package and a fresh target or a legacy receipt naming root template outputs
- WHEN installation previews and applies the current package
- THEN fresh Framework output has no root templates directory, Module and Scenario starters remain under protocol/templates, and plan/task starters ship in their owning Agent packages
- AND upgrade removes only unchanged receipt-owned obsolete template files, leaving unowned neighboring material untouched and possibly leaving empty legacy directories
- AND modified owned files, symlinks or changes after preview block before writing, while a failed apply restores retired bytes, modes and the prior receipt
- AND repeated installation is idempotent and the relocated starters add no worker context, tools or prompt injection

### scenario.distribution.install-pi-session — Installing places the Pi session extension only

- GIVEN a target project
- WHEN installation is applied without client-selection flags
- THEN it installs `.pi/extensions/concorde-session.ts` as a receipt-owned output importing the deployed framework extension and naming its launcher and managed runtime interpreter
- AND it installs the AGENTS.md Protocol entry that Pi reads as a context file
- AND no standalone Skills, Skills CLI locks, Codex projections or Claude projections are installed
- BUT the retired `--integration` flag is rejected for every value, including pi, before target mutation

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

The distributable manifest is `concorde.json` schema_version 5, Concorde 8.0.0, Architecture
Profile 15, Workspace Protocol 16 and Delivery Proposal 10. Schema 5 removes the top-level
`templates` inventory field and package root; the retired field is rejected even when empty.
Module and Scenario starters belong only to `protocol/templates/module.md` and
`protocol/templates/scenario.md`. Plan and task starters belong to
`agents/planner/plan-template.md` and `agents/task_author/tasks-template.md`, carried by
ordinary Agent packaging without runtime injection. Earlier package schemas require an
explicit package update and are rejected rather than reinterpreted. The Pi-only `client: "pi"`
layout remains; `integrations`, `skill_namespace`, Skills CLI selection and the `skills` package
root remain unsupported. Receipt schema 2, runtime/wire and project Protocol versions are unchanged.

Installation receipt schema 2 records `client: "pi"`, not client selections or Skills CLI delegation.
Schema 1 receipts are explicitly accepted for migration because their exact output-digest and
bounded root-block records retain identical meanings; only their obsolete client/delegation
metadata is discarded on successful upgrade. Unsupported receipt versions fail closed. Cleanup
of root guidance alone preserves the rest of the existing receipt. Eleven public capability adapters and seven domain roles remain; the separate outer tester is
also distributed, while maintenance-worker and source coordinator support are source-only.
Removing a client does not remove a model provider.

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

### scenario.distribution.prompt-references — Resolve only explicit whole-line path references

- GIVEN prompt sources with column-one `@path.md` references and optional quoted key=value bindings
- WHEN the resolver renders a worker, Protocol adapter or Operation guidance root
- THEN nested references preserve binding behavior and source provenance without changing intended rendered instruction bytes
- AND invalid or missing targets, unsafe paths, malformed parameters, audience/layer violations, cycles and diamonds fail without a partial successful result
- AND retired column-one `@include path.md` directives fail explicitly, including in nested sources
- BUT ordinary literal Markdown mentions, emails, decorators, inline references and indented lines remain unchanged

### scenario.distribution.build-render — Build renders deterministic Pi projections from authored sources

- GIVEN current Operation guidance, worker instruction, operation and Protocol sources
- WHEN build runs without a client selector
- THEN it renders seven canonical native Agent bodies and their byte-identical compatibility paths, one Pi catalog containing exactly eleven public descriptions, guidance and versioned schemas, Studio configuration, Protocol assets and runtime schemas
- AND repeated renders are byte-identical and perform no network or process I/O
- BUT retired integration arguments and Skill publishing commands are rejected, not reinterpreted

### scenario.distribution.build-checkout-skills-user-invoked — The source Pi entry stays private and waits for explicit requests

- GIVEN a source-checkout build without a framework prefix
- WHEN build renders the Pi entry
- THEN its only client projection is `generated/session/pi/concorde-session.ts`, outside ambient discovery
- AND its catalog requires an explicit developer request before an Operation runs
- AND consumer installation separately renders the same catalog under `.pi/extensions/` with the installed framework and runtime paths

### scenario.distribution.private-selection — Private fresh session selection

- GIVEN an assigned candidate with a fresh build and explicitly named absolute Pi entry/runtime paths
- WHEN a fresh test child's inputs are selected
- THEN selection returns only the exact candidate-built Pi entry and embedded catalog bytes, transitive source/build digest and runtime identity
- AND missing, modified, aliased or out-of-candidate paths fail without ambient fallback
- AND maintenance selection admits no Concorde entry/catalog and every selection requests fresh non-forked context with inherited/discovered catalogs disabled
- AND saved selections are admitted only in ignored candidate scratch and reverified before Pi registration, tool calls and runtime use
- AND legacy API/schema, unknown fields, changed catalog or implementation, source links and foreign runtime paths fail closed
- AND a Studio redirect or a redirect into another linked source worktree is refused, while explicitly scoped external disposable consumer data is allowed
- BUT returning selection metadata or bytes does not prove extension loading, tool use or model execution

### scenario.distribution.build-pi-session — Build embeds ordinary Operation guidance in the Pi shim

- GIVEN `prompts/operation-guidance/<name>.md`, their shared includes and exported request schemas
- WHEN build renders the Pi shim
- THEN it imports the tracked session extension and embeds every public Operation's exact name, description, resolved guidance and request schema with its version
- AND guidance contains no unresolved package token or standalone stdin envelope mechanics
- AND the source catalog names its own launcher and `.venv` and marks explicit-request-only, while an installed catalog names the prefixed extension/launcher and managed runtime interpreter
- AND build checking, package validation and byte-exact goldens detect catalog or source drift without independent Skill assets

### scenario.distribution.build-write — write_build records source and output digests in the manifest

- GIVEN a completed render
- WHEN write_build runs
- THEN it writes the rendered outputs plus `generated/build-manifest.json` recording every recorded source path's sha256
- AND it removes retired outputs within its declared owned subtrees (`generated/agents`, `generated/protocol` and `generated/docs`) and manifest-owned retired private or ambient projections under the retirement contract below, preserving other generators' assets

### scenario.distribution.build-check — check_build reports staleness without writing

- GIVEN the currently committed generated outputs
- WHEN check_build runs
- THEN it compares a pure in-memory render and reports every stale or drifted output
- AND it writes nothing to the worktree

### scenario.distribution.build-retired-skills — Retired output requires exact ownership before removal

- GIVEN old private Codex/Claude projections or ambient projections remain from a previous source build
- WHEN check_build or write_build runs
- THEN checking reports their presence without writing and rebuilding retires only exact-byte old manifest-owned regular outputs after whole-plan preflight
- AND unowned or modified retired files, symlinked files or ancestors, extra retired directory content and unknown files in owned generated subtrees block before any output write or deletion
- AND neighboring external CLI-owned Skills, unknown ambient names and skills-lock.json remain untouched
- AND retired golden fixtures are removed only from the explicit historical fixture inventory, with extra files and symlinks rejected

The historical projection roots are `generated/session/codex`, `generated/session/claude`,
`.agents/skills` and `.claude/skills`; only the eleven public names and the explicitly retired
`concorde-reflections-triage`, `concorde-review`, `concorde-main`, `concorde-dev-loop` and
`concorde-specify-loop` are inspected there. The old ambient Pi shim is also an exact retirement
candidate. Name membership is not proof of file ownership: every removed file needs its old
manifest digest. Unknown contents are never erased by prefix or recursive cleanup. Empty output
ancestors can be pruned after their last verified file is removed. Repeated builds are idempotent.
`write_build` has no alternate destination or installed-layout option; the installer consumes the
pure renderer and performs its own receipt-owned writes. The tracked `skills/` product is removed
in source maintenance, not a directory a normal build or installer may adopt wholesale.

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
- THEN it verifies freshness first and returns a frozen `ModelInstructions` with the worker's name, description, source path, rendered body, non-null effect declaration and complete `WorkerBinding`
- AND its record has no Skill discriminator or optional unbound-instruction form, while the binding retains every source, instruction, profile, manifest, timeout and digest field
- AND an unknown Agent or an invalid binding fails closed with a typed BuildError (`stale_build`, `unknown_agent`, or `invalid_agent_binding`)
- BUT a public Operation catalog name alone is not a worker identity and cannot load worker instructions

`validate_package(root)` runs the complete prompt, operation-module, Agent, contract,
Spec-alignment and build-output checks behind `python -m concorde validate` and `build --check`.
`recompute_protocol_manifest`/`python -m concorde protocol-manifest` report, accept (`--write`), or
bind (`--bind-project`) the tracked `protocol/manifest.json` digest to the current build; accepting
a changed Protocol export is developer-only, and a consumer separately accepts the installed
manifest version/digest in its own project configuration. Domain Agent responsibility files are bound
separately by their canonical role profiles. Protocol adapters and the Framework execution profile are bound by
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
- AND the single registered `concorde.operations` metadata array must contain the same boolean `deterministic` for every operation alongside its `id`, `public`, `context_selection` and `public_name`
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
- THEN it takes the Ctrl-C path: a running worker's Pi process is killed and its outcome is cancelled, a finite Host invocation interrupted outside a worker launch ends with the `execution_cancelled` error and the change's recorded status, and the result envelope is printed before exit
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
- AND it runs every public Operation's launcher runtime check with the managed runtime's own interpreter and rejects a check that reports another environment as its prefix, so the verified inventory describes the runtime rather than the installer's interpreter
- AND an unchanged verified runtime may be reused, though even `unchanged` rechecks health and may refresh the marker

### scenario.distribution.runtime-provision-failure — Failed acquisition or verification does not replace a valid runtime

- GIVEN a provisioning attempt that fails acquisition or verification
- WHEN provision_runtime returns that failure
- THEN it must not replace a previously valid runtime or mark partial state usable
- AND a create destination that appears after planning is rejected rather than adopted
- AND the returned result carries no successful runtime metadata, so a caller cannot infer recovery from its absence

### scenario.distribution.launcher-managed-runtime — The installed launcher re-executes itself inside the managed runtime

- GIVEN an installed project whose framework lives at `.concorde/framework` and whose verified managed runtime, with the installer's owner marker, lives at `.concorde/.venv`
- WHEN `.concorde/framework/scripts/run-operation.py` is started with any other interpreter, including an ambient `python3`, even one that cannot import LangGraph
- THEN it re-executes itself with the managed runtime's interpreter before reading its invocation, so the Operation runs with the locked dependencies and the runtime check reports that runtime as its prefix
- AND a launcher already running inside that runtime, such as the one the Pi session tool starts, is not re-executed
- AND the source checkout, which matches neither layout, keeps the interpreter that started it
- AND an unavailable selected Graph backend returns a blocked `missing_runtime` envelope, while direct Host-tool dispatch does not impose that Graph check
- AND missing or unverified installed runtimes still fail local installation admission without an ambient fallback

### scenario.distribution.install-local-worktree — Full local installs from source or installed providers

- GIVEN an explicitly admitted source package or receipt-verified installed package and a normal Git-created consumer worktree whose ignored runtime and receipt are absent
- WHEN the host explicitly bootstraps that worktree through the supported installation service or its deployed installer
- THEN it installs the complete local Framework, Pi entry with embedded catalog, independently provisioned dependencies, managed interpreter and receipt of the exact admitted package identity
- AND all runtime checks use that local interpreter and the installation remains verifiable without the provider's virtual environment
- AND current verified local state is reused without reinstalling, acquiring dependencies or rewriting marker/receipt bytes
- AND no candidate-local durable status/runs are created and no Operation or model is called

### scenario.distribution.install-preserve-project — Preserve inherited project assets without adopting them

- GIVEN a target with committed inherited Protocol and canonical AGENTS guidance but no local installation receipt, or arbitrary existing project-owned root instructions
- WHEN installation selects explicit preserve-project mode
- THEN existing complete Protocol, root instruction bytes and modes, config, registry, Specs and accepted binding remain unchanged and unowned content is not adopted
- AND wholly absent admissible Protocol and absent AGENTS may be seeded as owned outputs, and repeated application retains that ownership and is idempotent
- AND prior local receipt-owned project entries must still match their recorded ownership and retain it
- AND partial, aliased or invalid Protocol bundles stop without mixing versions, while a complete incompatible preserved bundle is not automatically accepted for execution
- BUT the default installer still rejects an unowned marked root block

### scenario.distribution.install-local-failure — Failed local installation never supplies an execution fallback

- GIVEN missing or conflicting local installation state, changed admitted provider bytes, a concurrent installer or a failed acquisition/verification step
- WHEN local verification or explicitly authorized bootstrap is requested
- THEN missing/stale state fails clearly without implicit bootstrap, conflicting ownership is preserved, and no primary/global runtime replaces the local installation
- AND failed creation rolls back owned files and receipt while preserving unrelated project bytes and permits a fresh-plan retry after the cause is corrected
- AND source/target aliases and active source-checkout targets are refused, and a concurrent supported installer cannot mutate the same installation
- AND every failed verification returns no successful local execution observation


### scenario.distribution.test-timing — Test reasons and measured input identity

- GIVEN legacy or explicitly scoped test-runner arguments and optional prior evidence
- WHEN the runner discovers and executes its selected units
- THEN it records reason, scope, phase, attempt/prior identity and whitelisted input/test/runtime/lock/environment fingerprints
- AND unchanged declared inputs are recognizable without treating a same-tree commit as invalidation
- AND discovery, queue, execution and total elapsed durations remain separate, setup remains unknown unless observed, and expensive fixture runtime spans remain nested diagnostics
- AND legacy callers use manual reason and unspecified scope/phase without new required flags
- AND parallel unit sums are not reported as elapsed wall time or server thinking time
