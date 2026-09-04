---
id: module.concorde.capabilities
kind: module
parent: module.concorde
modules: []
features:
  - feature.capabilities.run-deterministic-tools
  - feature.capabilities.provide-capability-surfaces
  - feature.capabilities.permission-bounded-execution
  - feature.capabilities.maintain-agent-surfaces
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-capabilities-system-overview.html
---

# Architecture: Capabilities

## Responsibility

Define how every Concorde capability exists and runs on a coding agent: deterministic Tools behind
portable entry points, exposure/effect-declared leaf Skills, acyclic paired LangGraph Operations,
committed-base linked-worktree preflight for agent mutations, per-leaf permission compilation and
enforced launch, host-attested client bootstrap, typed semantic completion, and identical public
projection into Codex and Claude.

## Boundary

Capabilities owns the three-level capability structure (Tool/Skill/Operation) as a mechanism: portable
launchers and the Tool dispatcher/envelope; the canonical `skills/` and `operations/` source
directories and their metadata grammar (name, exposure, effects, `capabilities:` topology, scripts
tokens); the skill loader/projector; the package capability validator; the shared Operation runtime
(bindings, state, lazy LangGraph); the policy compiler (normalized task policy to Codex permission
profile, Claude strict sandbox, or outer isolation); client-runtime bootstrap attestation; Capability
Completion Envelope 1; the injectable process launcher and receipts; the managed
Operation launcher (`scripts/run-operation.py`); and checkout/installed agent-surface rendering for
Codex and Claude. It also owns the deterministic Git worktree boundary shared by mutating Tool
adapters and actual Operation execution; that helper reads only Git identity/commit metadata and
rejects primary-worktree mutation unless an explicit override is present.

It does not own the content of any individual Skill or Operation (those belong to Understanding,
Lifecycle, and Reflections), Protocol 13 role resolution (`module.concorde.understanding`),
packaging/installation/managed venv (`module.concorde.distribution`), or the agent host itself. Its
runtime attestation trusts only the exact selected external executable; it never owns that file or
admits its package directory as task context.

## Operation Contract Boundary

The root's `entity.concorde.operation` defines the shared concept. This module owns its executable
packaging/launch mechanism and the target `contract.capabilities.operation-data`: separate
configuration and runtime-input JSON, stable type/version resolution, and result admission. It does
not own planning or reflection payload semantics. The existing `entity.capabilities.operation-pair`
is the concrete Manifest 2 specialization with one primary Python file and one associated Skill.

`OperationState.request` and `CapabilityResult.output` are currently strings; prior leaf outputs are
rendered into prompts and nested dispatch serializes child result lists. Capability Completion
Envelope 1 validates execution identity/status/gates but does not type those domain fields. The
target domain envelopes, initialized config snapshot, and typed dispatch remain explicitly pending.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.capabilities.operation-data-contract` | schema | Target common JSON configuration/invocation/result grammar; declared in contract.capabilities.operation-data and not yet wired into the runtime. | `concept:Operation Data Contract 1` |
| `entity.capabilities.posix-launcher` | script | Invokes the colocated Python adapter on POSIX systems. | `scripts/concorde.sh` |
| `entity.capabilities.powershell-launcher` | script | Invokes the same Python adapter on PowerShell systems. | `scripts/concorde.ps1` |
| `entity.capabilities.python-adapter` | program | Adds the colocated package `src` directory to imports and enters the CLI. | `scripts/concorde.py` |
| `entity.capabilities.cli` | program | Dispatches supported Tools and serializes one structured Tool envelope. | `src/concorde/capabilities/cli.py` |
| `entity.capabilities.worktree-gate` | program | Inspects Git top-level, exact `HEAD`, worktree-specific/common Git directories, and rejects agent mutation in the primary worktree unless the maintainer-authorized override is explicit. | `src/concorde/capabilities/worktree.py` |
| `entity.capabilities.tool-result` | type | Structured `tool`, target, status, artifacts, findings, and result payload for one bounded deterministic action. | `src/concorde/model.py#ToolResult` |
| `entity.capabilities.tool-envelope` | function | Serializes one Tool result with a `tool` discriminator. | `src/concorde/diagnostics.py#tool_envelope` |
| `entity.capabilities.skill-sources` | directory | Canonical directories containing exactly one public or internal leaf `SKILL.md` each. | `skills` |
| `entity.capabilities.operation-sources` | directory | Canonical directories containing exactly one Operation Python/Markdown pair each. | `operations` |
| `entity.capabilities.skill-prompt` | document | One complete leaf prompt with public/internal exposure, resolved Tool script paths, and, when composed, exact read/write/network/credential effects; it may invoke Tools but never orchestrates Skills. | `concept:skills/<name>/SKILL.md` |
| `entity.capabilities.operation-pair` | concept | One exact `operation.py` execution authority plus its associated `SKILL.md` invocation and behavioral contract, addressed as one paired capability unit. | `concept:operations/<name>/{operation.py,SKILL.md}` |
| `entity.capabilities.projector` | program | Parses leaf exposure/effects and mixed Operation capabilities, resolves Tool and managed Operation-launcher tokens, filters internal leaves, and renders public Codex/Claude Skill files with owned kind provenance. | `src/concorde/capabilities/skill_assets.py` |
| `entity.capabilities.capability-validator` | program | Validates exact Script/public-internal-Skill/Operation pairs, effects, mixed literal topology/bindings, and direct/indirect cycles without importing Operation Python. | `src/concorde/capabilities/validation.py` |
| `entity.capabilities.operation-runtime` | program | Resolves ordered direct capabilities/bindings, creates the canonical Protocol 13 receipt, builds lazy LangGraphs, attaches each launch request, preserves nested opacity, and accumulates only validated successful capability results. | `src/concorde/capabilities/operation_runtime.py` |
| `entity.capabilities.operation-binding` | type | Ordered unique stages plus exact direct capability occurrences and narrowing agent/effect bindings. | `src/concorde/capabilities/operation_runtime.py#OperationBinding` |
| `entity.capabilities.operation-state` | type | Original request plus append-only successful capability output/completion/receipt triples. | `src/concorde/capabilities/operation_runtime.py#OperationState` |
| `entity.capabilities.policy-compiler` | program | Compiles leaf effects and occurrence bindings into normalized task policies plus Codex profiles or Claude strict-sandbox settings while keeping integration bootstrap separate. | `src/concorde/capabilities/operation_permissions.py` |
| `entity.capabilities.runtime-bootstrap` | type | SHA-256-attested real external client executable, owner/mode/size metadata, and digest-bound read grant used only to bootstrap native enforcement. | `src/concorde/capabilities/operation_permissions.py#RuntimeBootstrapFile` |
| `entity.capabilities.completion-envelope` | type | Capability Completion Envelope 1: exact launch/workspace/bootstrap identity, semantic status, usable output, limitations, and gate evidence. | `src/concorde/capabilities/operation_permissions.py#CapabilityCompletion` |
| `entity.capabilities.process-launcher` | program | Attests/finalizes runtime bootstrap, performs version/enforcement preflight, invokes native structured output, validates semantic completion, and returns a matching receipt or raises without permissive retry. | `src/concorde/capabilities/operation_executor.py#AgentProcessExecutor` |
| `entity.capabilities.operation-launcher` | program | Standard-library bootstrap that selects the source root `.venv` or installed `.concorde/.venv` and executes one exact paired Operation path. | `scripts/run-operation.py` |
| `entity.capabilities.surface-renderer` | program | Renders one integration's complete public leaf/Operation capability surface for install-time projection. | `scripts/render-capability-surfaces.py` |
| `entity.capabilities.checkout-sync` | program | Compares and refreshes this repository's own generated agent capability surfaces from canonical sources. | `scripts/development/sync-agent-surfaces.py` |
| `entity.capabilities.codex-surface` | directory | Fifteen public leaf and three Operation skills projected for Codex; reflection agents project separately under `.codex/agents`. | `.agents/skills` |
| `entity.capabilities.claude-surface` | directory | Fifteen public leaf and three Operation skills projected for Claude; reflection agents project separately under `.claude/agents`. | `.claude/skills` |
| `entity.capabilities.langgraph` | external-system | Graph runtime imported lazily for topology and pinned into the isolated environment by every successful native installation. | `external:langchain-ai/langgraph@1.2.11` |
| `entity.capabilities.tests` | test | Unit, contract, integration, and acceptance evidence for Tool, Skill-projection, and Operation-enforcement semantics. | `tests/concorde/capabilities` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.capabilities.operation-data-contract` | `defines` | `entity.concorde.runtime-input` | Defines the common type/version wrapper; domain fields remain with the providing feature. |
| `entity.capabilities.operation-data-contract` | `defines` | `entity.concorde.operation-result` | Defines target domain-result admission separately from current execution/completion evidence. |
| `entity.concorde.package-manifest` | `declares` | `entity.capabilities.python-adapter` | Binds the Tool dispatcher entry point that every projected Skill invokes. |
| `entity.concorde.package-manifest` | `declares` | `entity.capabilities.operation-launcher` | Binds the managed Operation launcher, Python floor, lock, and venv path in `operation_runtime`. |
| `entity.concorde.package-manifest` | `declares` | `entity.capabilities.skill-sources` | Inventories every leaf Skill exactly once across public and internal exposure. |
| `entity.concorde.package-manifest` | `declares` | `entity.capabilities.operation-sources` | Inventories every Operation pair exactly once. |
| `entity.capabilities.skill-sources` | `contains` | `entity.capabilities.skill-prompt` | Gives each leaf capability one canonical Markdown authority. |
| `entity.capabilities.operation-sources` | `contains` | `entity.capabilities.operation-pair` | Gives each Operation one canonical Python/Markdown authority pair. |
| `entity.capabilities.projector` | `reads_from` | `entity.capabilities.skill-sources` | Loads leaf Skills without composing or rewriting their prompt semantics. |
| `entity.capabilities.projector` | `reads_from` | `entity.capabilities.operation-sources` | Loads each Operation's paired Markdown contract and entry point. |
| `entity.capabilities.projector` | `transforms` | `entity.capabilities.skill-prompt` | Produces one integration-native Codex or Claude Skill file from each public leaf prompt. |
| `entity.capabilities.projector` | `generates` | `entity.capabilities.codex-surface` | Renders the transformed public leaf and Operation prompts as Codex Skills. |
| `entity.capabilities.projector` | `generates` | `entity.capabilities.claude-surface` | Renders the same transformed prompts as Claude Skills. |
| `entity.capabilities.checkout-sync` | `calls` | `entity.capabilities.projector` | Regenerates this repository's own checkout projections for both supported integrations. |
| `entity.capabilities.surface-renderer` | `calls` | `entity.capabilities.projector` | Renders one integration's public capability surface for install-time projection. |
| `entity.capabilities.capability-validator` | `validates` | `entity.capabilities.skill-sources` | Checks exposure, effects, and name/collision rules without importing Skill Python. |
| `entity.capabilities.capability-validator` | `validates` | `entity.capabilities.operation-sources` | Checks mixed literal topology, occurrence bindings, and direct/indirect cycles without importing Operation Python. |
| `entity.capabilities.operation-runtime` | `reads_from` | `entity.capabilities.skill-prompt` | Loads canonical direct capability bodies and declared effects without duplicating them. |
| `entity.capabilities.operation-runtime` | `calls` | `entity.capabilities.policy-compiler` | Produces one normalized/native policy per direct leaf occurrence. |
| `entity.capabilities.operation-runtime` | `calls` | `entity.capabilities.process-launcher` | Hands a digest-bound leaf launch request and Protocol 13 receipt to the real process executor. |
| `entity.capabilities.operation-runtime` | `calls` | `entity.capabilities.langgraph` | Compiles ordered state/nodes/edges only when graph construction is requested. |
| `entity.capabilities.operation-runtime` | `implements` | `entity.capabilities.operation-binding` | Declares exact stage/occurrence/agent/effect bindings the runtime enforces. |
| `entity.capabilities.operation-runtime` | `implements` | `entity.capabilities.operation-state` | Declares the append-only request/result/receipt shape the runtime accumulates. |
| `entity.capabilities.policy-compiler` | `reads_from` | `module.concorde.understanding` | Resolves Protocol 13 roles into concrete project-relative read/write/deny paths before compiling policy. |
| `entity.capabilities.policy-compiler` | `configures` | `entity.concorde.coding-agent` | Renders a Codex permission profile or a Claude strict-sandbox configuration for one leaf launch. |
| `entity.capabilities.process-launcher` | `implements` | `entity.capabilities.runtime-bootstrap` | Resolves, validates, hashes, and rechecks the selected external Codex executable before finalizing its exact read grant. |
| `entity.capabilities.process-launcher` | `implements` | `entity.capabilities.completion-envelope` | Supplies the native schema, parses lifecycle output, validates identity/gates/status, and rejects every failed or malformed completion. |
| `entity.capabilities.process-launcher` | `calls` | `entity.concorde.coding-agent` | Starts a supported CLI only after enforcement/version/bootstrap/digest preflight and accepts only typed success. |
| `entity.capabilities.operation-launcher` | `calls` | `entity.capabilities.operation-runtime` | Enters a paired Operation's graph through the source root `.venv` or installed `.concorde/.venv` without shell activation. |
| `entity.capabilities.posix-launcher` | `calls` | `entity.capabilities.python-adapter` | Forwards Tool arguments without redefining behavior. |
| `entity.capabilities.powershell-launcher` | `calls` | `entity.capabilities.python-adapter` | Provides equivalent Windows entry behavior. |
| `entity.capabilities.python-adapter` | `calls` | `entity.capabilities.cli` | Enters the canonical Tool dispatcher from source or installed layout. |
| `entity.capabilities.cli` | `calls` | `entity.capabilities.worktree-gate` | Rejects mutating init/delivery/docsite/agent-surface actions in a primary or non-Git checkout unless the explicit override is present. |
| `entity.capabilities.operation-pair` | `calls` | `entity.capabilities.worktree-gate` | Requires actual planning, standard-loop, and mutating reflection execution to start in an isolated linked worktree before graph/agent mutation. |
| `module.concorde.understanding` | `calls` | `entity.capabilities.worktree-gate` | Its workspace adapter rejects mutating phases and selection persistence before resolving agent write targets in a primary checkout. |
| `entity.capabilities.cli` | `calls` | `module.concorde.understanding` | Dispatches the `init`, `context`, `explore`, and `validate` Tools. |
| `entity.capabilities.cli` | `calls` | `module.concorde.lifecycle` | Dispatches the cleanup-only `deliver` Tool. |
| `entity.capabilities.cli` | `calls` | `module.concorde.auto-docs` | Dispatches the reviewed `docsite` scaffold Tool. |
| `entity.capabilities.cli` | `calls` | `module.concorde.reflections` | Dispatches the `agent-assets` Tool. |
| `entity.capabilities.cli` | `calls` | `entity.capabilities.tool-envelope` | Serializes every bounded action with Tool terminology. |
| `entity.capabilities.tool-envelope` | `transforms` | `entity.capabilities.tool-result` | Produces the public versioned JSON response. |
| `module.concorde.distribution` | `calls` | `entity.capabilities.projector` | Installs public leaf/Operation Markdown through the same rendering mechanism used at checkout. |
| `module.concorde.distribution` | `calls` | `entity.capabilities.operation-launcher` | Verifies every installed Operation offline through the identical managed bootstrap. |
| `entity.capabilities.projector` | `tested_by` | `entity.capabilities.tests` | Source/projection parity tests prove Codex/Claude output equivalence. |
| `entity.capabilities.capability-validator` | `tested_by` | `entity.capabilities.tests` | Structural fixtures prove exposure/topology/cycle detection without importing Operation Python. |
| `entity.capabilities.operation-runtime` | `tested_by` | `entity.capabilities.tests` | Real LangGraph and sentinel tests prove order, bounded context, and failure stopping. |
| `entity.capabilities.policy-compiler` | `tested_by` | `entity.capabilities.tests` | Contract tests prove Codex/Claude effective-path parity. |
| `entity.capabilities.runtime-bootstrap` | `tested_by` | `entity.capabilities.tests` | Tests reject missing, project-local, untrusted-owner, mutable, stale, and duplicate bootstrap files. |
| `entity.capabilities.completion-envelope` | `tested_by` | `entity.capabilities.tests` | Tests distinguish transport, lifecycle, malformed/stale, explicit-failure, recovered-tool, and semantic-success outcomes. |
| `entity.capabilities.process-launcher` | `tested_by` | `entity.capabilities.tests` | Injected-executor tests record exact finalized argv/settings/receipts without a mandatory live model call. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.capabilities.tool` | A Skill, script, CI job, or maintainer invokes a Tool dispatcher entry point. | Locate the colocated package through a platform launcher or direct Python entry; dispatch the named Tool through the CLI; load the validated project package; validate inputs and safe project-relative paths; execute the bounded action; serialize one canonical Tool envelope. | Deterministic success or failure with stable diagnostics and no conversational side channel. | `contract.capabilities.tools` |
| `interaction.capabilities.launch` | A workflow host launches an installed paired Operation. | Verify worktree authority; enter the managed runtime; resolve Protocol 13 once into a canonical receipt; validate topology/effects/bindings; compile one task policy; attest the exact client bootstrap; finalize the launch; invoke native schema/JSON lifecycle output; validate semantic completion; append only success and stop on every failure. | Ordered successful output/completion/receipt triples, or an explicit workspace/policy/bootstrap/transport/lifecycle/completion failure with no downstream invocation. | `contract.capabilities.permission-bounded-execution`, `contract.capabilities.skill-contract` |
| `interaction.capabilities.project` | An installer or checkout sync projects capabilities to Codex or Claude. | Validate the exact leaf/Operation inventory, exposure, effects, topology, and bindings; omit internal leaves; resolve each Tool and managed-launcher token; render every public leaf and Operation Markdown as one integration-native Skill with source/kind/entry-point provenance; compare against observed output; write only the exact target paths. | Codex or Claude receives the same 15 public leaves plus three Operation skills with no ambient-interpreter dependence, or an explicit conflict/failure diagnostic. | `contract.capabilities.agent-surface`, `contract.capabilities.skill-contract` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.capabilities.run-deterministic-tools` | Skills, Operations, scripts, and automation invoke portable deterministic Concorde Tools through one structured, safe result envelope. |
| `feature.capabilities.provide-capability-surfaces` | Expose every Concorde lifecycle choice as one complete, independently invocable public leaf Skill or Operation with consistent installed semantics. |
| `feature.capabilities.permission-bounded-execution` | Enforce a least-privilege Codex/Claude launch for every direct leaf an Operation composes. |
| `feature.capabilities.maintain-agent-surfaces` | Keep this repository's own checkout agent surfaces byte-current with canonical sources without installing a duplicate framework copy. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- Python standard-library behavior is canonical; shell and PowerShell launchers only locate and
  forward Tool arguments.
- Source and installed packages preserve the same relative `scripts/` plus `src/` layout.
- Every Tool action uses the same repository load and Tool envelope; Operation is reserved for
  LangGraph.
- `skills/<name>/SKILL.md` is the sole prompt authority for a leaf capability; installed files are
  generated projections.
- A leaf Skill may invoke Tools but never embeds a multi-Skill LangGraph or duplicates another Skill's
  prompt body.
- Public leaf and Operation capabilities share one global `concorde-*` installed namespace; internal
  leaves remain packaged/loadable but never project.
- Every Operation body retains its exact paired path, but invocation first enters
  `scripts/run-operation.py` so source checkouts use the root `.venv` and installed projects use
  `.concorde/.venv` without shell activation.
- Direct capability topology is literal, mixed Skill/Operation, order-preserving, and acyclic; a
  parent never flattens a nested Operation's internals.
- Graph construction fails before execution when any direct leaf lacks a non-null launch factory or
  any nested Operation lacks an explicit enforcing dispatcher.
- Leaf effects remain owned by canonical Skill metadata; occurrence bindings and effective
  configuration may narrow but never widen them, and multi-leaf stages receive distinct policies.
- Codex uses a digest-named permission profile without legacy `sandbox_mode`; Claude uses restricted
  `dontAsk` plus strict OS sandbox settings; verified outer isolation is the only fallback when no
  native sandbox is available.
- Integration runtime bootstrap is not task authority. The host resolves only the selected Codex
  executable to a trusted real external file, hashes its bytes/metadata, adds that exact read to the
  finalized native profile, and binds the attestation to launch/config/receipt digests; directories,
  wrappers, project files, mutable or substituted binaries fail closed.
- A host-resolved canonical Protocol 13 receipt satisfies an Operation leaf's workspace gate. The
  leaf receives its exact declared script but never reruns the global resolver from a narrower
  policy; direct Skill invocation still runs the Tool itself.
- Every real agent process returns Capability Completion Envelope 1. Exit zero is transport evidence,
  not semantic success; only identity-bound success with passed gates and no limitations enters
  Operation state. Native lifecycle failure, explicit failure, or invalid completion raises first.
- Codex uses JSONL plus `--output-schema`; Claude uses JSON plus `--json-schema`. Tests inject both
  clients and never require a paid/live model; live execution is optional acceptance evidence.
- Mutating agent entry points fail closed in the primary Git worktree. The
  `--allow-primary-worktree` escape hatch represents an explicit maintainer decision, never an
  inference from a generic change request; primary dirty contents are not inspected or transferred.
- LangGraph remains lazy so base deterministic Tool imports stay dependency-free; a successful
  installation guarantees it inside `.concorde/.venv` and Operation startup stays offline.
- Individual Skills and Operations are owned by the capability module whose use case they realize;
  this module owns only the mechanism by which any of them is declared, validated, enforced, launched,
  and projected. The flat `skills/` and `operations/` directories are a distribution format, not
  module ownership.
