# Design Reference: Concorde

This reference explains how the project-level boundaries map to repository sources. `module.md`, module-owned
contracts, and the maintained level view remain authoritative for responsibility and organization.

## Implementation Notes

### Installed interaction surface

Concorde has no standalone end-user application. Spec Kit materializes Markdown command definitions
as coding-agent skills or slash commands. During feature work the maintainer invokes one of those
skills and the coding agent follows its instructions.

The skill sources come from two packages:

- `presets/concorde/commands/` and `templates/` compose Concorde guidance into the normal Spec
  Kit phases: clarify, specify, plan, tasks, implement, analyze, checklist, task-to-issues, and
  converge. The same preset adds `speckit.fast-loop` as a separate additive command for an eligible
  established small change; it is not a tenth normal Spec Kit phase.
- `extensions/concorde/commands/` defines the Concorde-specific init, context, validate,
  implementation-acceptance, and read-only ask skills. The extension also carries Feature 005's
  canonical reflection-triage bodies, Claude/Codex wrappers, queue helper, and projector as support
  assets rather than another command surface.

Installed copies under `.agents/skills/`, `.claude/`, `.codex/`, or another integration directory are
materializations. The preset and extension directories are the maintained package sources. Fast-loop
and reflection triage are distributed and self-hosted through those same public component mechanisms.
Generated triage paths are owned only through `.specify/concorde-agent-assets.json` digest records;
shared `.concorde/reflections/` state remains maintainer-owned.

### Script boundary

Only four Concorde-specific skills cross into the deterministic runtime: `init`, `context`,
`validate`, and `impl.accept`. The read-only `ask` skill and the mutating `fast-loop` skill are
followed by the coding agent and have no runtime subcommand. Normal phase skills call `workspace.py`
only to resolve the selected nested workspace and derive phase paths. Fast-loop calls the same
root-scoped adapter first for its selected anchor and then explicitly for every discovered affected
feature; each call still resolves one canonical root before semantic eligibility review.

The script boundary is implemented by:

- `extensions/concorde/scripts/bash/concorde.sh` and
  `extensions/concorde/scripts/powershell/concorde.ps1` — portable launchers;
- `extensions/concorde/scripts/python/concorde.py` — Python entry adapter;
- `extensions/concorde/scripts/python/workspace.py` — selected-workspace adapter;
- `extensions/concorde/scripts/python/reflections_queue.py` — installed triage queue and plan helper;
- `extensions/concorde/runtime/concorde/` — deterministic initialization, context, validation,
  reflection, readiness, implementation-acceptance, and agent-projection logic.

The installed `agent-assets` runtime operation is invoked by Distribution and self-hosting after Spec
Kit component work; it is not an additional maintainer-facing skill or component lifecycle. It renders
only the active integration requested by the caller, verifies receipt-scoped path ownership, and
preserves shared state and inactive integrations.

Scripts return structured results. Command instructions interpret those results and present them to
the maintainer. A script never becomes a second conversational interface. Semantic affected-feature
discovery remains with the agent; Protocol v8 and the workspace runtime remain unchanged.

### Workspace file model

The workflow uses files as durable documentation or scoped memory:

| Lifetime | Files | Authority |
|---|---|---|
| Durable architecture | `module.md`, module `design.md`, `architecture/contracts/**`, `architecture/diagrams/**` | Maintained project architecture |
| Durable feature intent | `abstract.md`, feature `design.md` | Accepted user intent and design |
| Durable accepted realization | feature `implementation.md` | Last explicitly accepted implementation |
| Durable project memory | specification-root `reflections.md` | Cross-feature problems and follow-up state |
| Temporal attempt memory | `attempt/plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/**`, `checklists/**` | Current delivery attempt only |
| Selection state | `.specify/feature.json` | Current feature pointer owned by Spec Kit |
| Installed agent projection | `.agents/skills/reflections-triage/**`, `.claude/agents/**`, `.codex/agents/**`, `.specify/concorde-agent-assets.json` | Generated active/inactive integration surfaces owned by matching receipt digests |
| Shared triage state | `.concorde/reflections/config.json`, `plans/`, `worktrees/`, project reflection log | Maintainer-owned state; never projection-owned |
| Generated documentation | `generated/**`, docsite build output | Disposable read model; never source authority |

An agent may read durable files for bounded context and write the files explicitly assigned to the
current phase. Attempt files may be replaced during convergence. Durable intent changes through the
relevant specification workflow. The first accepted realization is written through explicit,
digest-bound implementation acceptance. An explicitly requested eligible fast-loop may later
reconcile a bounded set of affected existing features and related contract/architecture detail after
proportional evidence passes; maintained architecture edits remain pending exact maintainer review.

### Interaction matrix

| Skill family | Reads | Writes | Script use |
|---|---|---|---|
| Clarify / specify | Existing durable architecture and feature intent | Durable feature intent | Selected-workspace routing as needed |
| Plan / tasks | Durable intent and bounded architecture | `attempt/` planning and task files | Workspace routing; context/validation when instructed |
| Implement / analyze / converge | Durable intent plus current `attempt/` | Product code, task state, attempt evidence, reflections | Workspace routing; context/validation when instructed |
| `fast-loop` | One selected anchor plus every explicitly resolved affected feature; bounded module/contract/code/test/doc evidence; worktree state | Eligible code/tests, every affected feature document, related contract/architecture/module-reference/user docs, genuine reflections; architecture edits require exact review | Repeated root-scoped workspace routing only |
| `reflections-triage` | Project reflection log, shared config, validated plans, assigned worktree state | Parent-persisted plans; implementer commits only in assigned worktrees; maintainer-owned merge/status | Installed queue helper and platform-native child roles |
| `concorde.context` / `validate` | Maintained architecture and feature files | None | Deterministic runtime operation |
| `concorde.init` | Project/config state | Proposal only, then approved root files | Deterministic runtime operation |
| `concorde.impl.accept` | Completed attempt and durable targets | Approved durable realization and attempt cleanup | Atomic deterministic operation |
| `concorde.ask` | Smallest relevant installed guidance and project sources | None | No runtime operation; agent answers with citations |
| Distribution / self-host | Installed extension, component/projection plans, receipts | Spec Kit-owned components plus digest-owned native projections | Public Spec Kit lifecycle followed by installed `agent-assets` preview/sync/verify |

### Skill and workspace-file data flow

The maintained [skill-to-file data flow](architecture/diagrams/skill-workspace-file-flow.json)
separates the architecture-related workspace (`.concorde/config.json`, module sources, contracts,
and level views) from the selected feature workspace (durable feature files, temporal `attempt/`
memory, code, reflections, and accepted realization). It shows normal single-root phases and the
fast-loop exception that resolves an anchor plus bounded affected roots. Its delivered
<a href="/architecture/concorde-skill-workspace-file-flow.html">interactive view</a> keeps the main
lifecycle paths sparse; the embedded matrices name the exact per-skill exceptions and write sets.

### Supporting adapters

Distribution packages the maintained preset and extension, publishes their catalogs, and delegates
component and command materialization to Spec Kit. It treats the nine normal commands as complete
instruction modifications and fast-loop as an additive surface: removal can reveal lower normal
winners, while solely owned fast-loop disappears (R-030).

Spec Kit 0.16.4 has no arbitrary custom-agent projection primitive. After successful bundle work,
Distribution invokes only the `agent-assets` operation from the installed extension. Preview uses a
disposable installed candidate; apply synchronizes and verifies one native triage skill and two roles;
update/removal act only on paths whose current digest matches the projection receipt. Direct installer
rendering was rejected because it would fork Feature 005's canonical semantics (R-044).

Self-hosting uses the same projector and receipt rules. Integration records are independent, so a
Claude refresh preserves Codex outputs and vice versa; shared config, plans, worktrees, logs,
permission settings, unrelated assets, and modified projections remain untouched. This replaces the
prior backup-and-restore workaround recorded by R-042 without changing the module boundary.

Auto-Docs validates maintained sources, renders declared diagrams, and projects `specs/`, `docs/`,
and the root README into a generated site. These adapters consume the workflow architecture; they do
not sit between a skill, script, and workspace file during normal feature work.

### Type-qualified distribution identity

The maintained preset and extension both use the ID `concorde` and remain distinct through the
Spec Kit component key `(kind, id)`: `preset:concorde` and `extension:concorde`. Their source and
installed trees, catalogs, registries, lifecycle verbs, and ownership records are type-specific.
The bundle continues to pin one of each. Release transport uses
`concorde-preset-<version>.zip` and `concorde-extension-<version>.zip` so two same-ID components
cannot collide in one release directory; archive filenames do not redefine manifest identity.

The identity cutover retains no alias or dual registration. This is safe because no supported
public release requires in-place migration; development installations are rematerialized through
the public Spec Kit lifecycle. User-facing documentation says Concorde modifies the existing Spec
Kit commands. The manifest's `strategy: replace` remains only the complete-layer composition
mechanism needed to run workspace routing before legacy path assumptions.

## Design Rationale

The former organization mixed packaging boundaries, host integration, file semantics, and runtime
behavior. In particular, the name “Scripts” hid the concrete fact that the implementation
is a Python script runtime operating on files. The revised organization uses observable nouns and
keeps each dependency directional:

`Maintainer → Skills → Scripts → Workspace Files`, with a direct `Skills → Workspace Files` path for
agent-authored phases. Distribution feeds Skills and Scripts; Auto-Docs consumes Workspace Files.

Fast-loop follows the direct Skills → Workspace Files path because arbitrary code and documentation
authoring belongs to the coding agent. Scripts contribute canonical anchor and affected-root facts
one root at a time; semantic impact discovery stays with the agent. Risk is determined by stable
module responsibilities/dependencies, project-level user compatibility/migration policy,
affected-authority completeness, and worktree safety rather than line count, feature count, or a
second mutation engine.

Reflection triage follows the same separation. Agent-followed roles own investigation and bounded
implementation judgment, while the queue helper and projector own only deterministic validation,
ordering, rendering, and digest reconciliation. Keeping canonical bodies in the extension makes the
built archive the shared source for consumers and self-hosting. Requiring Distribution to invoke that
installed operation preserves Spec Kit's component authority while filling its one missing projection
primitive.

Using one shared component ID keeps the public name aligned with the product while the component
type carries the distinction Spec Kit already requires. Type-qualified archive filenames solve the
separate transport collision without leaking packaging mechanics back into component identity.
The repository-wide cutover required explicitly approved terminology-only reconciliation across
historical and adjacent durable references; R-034 and R-035 preserve that migration lesson without
changing the modules' responsibilities or dependency direction.

This split also makes testing clearer: command-surface tests belong to Skills, runtime and launcher
tests belong to Scripts, workspace-layout and acceptance tests belong to Workspace Files, release and
projection-transaction tests belong to Distribution, and site tests belong to Auto-Docs.

## Alternatives Considered

- **Keep “Scripts” and improve its prose** — rejected because the name still suggests an
  abstract domain kernel while the actual boundary is executable scripts over project files.
- **Combine Skills and Scripts** — rejected because users interact with skill instructions while
  scripts are subordinate implementation mechanisms with structured, non-conversational results.
- **Treat files as implementation details** — rejected because durable versus temporal file lifetime
  is the workflow's central state model and must be reviewable as architecture.
- **Fold Distribution and Auto-Docs into the three-part spine** — rejected because installation
  and publication cross project boundaries and have distinct failure and ownership rules.
- **Implement fast-loop as a runtime operation** — rejected because deterministic scripts cannot
  author arbitrary project code and documentation without duplicating the coding agent.
- **Add persistent multi-feature selection or all-project feature payloads** — rejected because normal
  Spec Kit phases deliberately use one selected root and semantic impact cannot be inferred safely
  from an unbounded registry response.
- **Keep contracts, diagrams, and cross-feature behavior categorically ineligible** — rejected because
  they can be bounded implementation detail when module responsibilities and dependency direction
  remain stable; exact architecture review preserves governance (R-041).
- **Alias fast-loop to `speckit.implement`** — rejected because implementation requires an active
  attempt and would silently reintroduce the planning, tasks, and acceptance ceremony this path omits.
- **Define smallness by changed-line or feature-root count** — rejected because affected-authority
  completeness and architectural risk determine whether direct authoring is safe.
- **Render native reflection agents inside the installer** — rejected because it would duplicate
  Feature 005's canonical behavior and could disagree with the installed extension archive.
- **Wait for a native Spec Kit custom-agent manifest field** — rejected for 0.5.0 because Spec Kit
  0.16.4 lacks that primitive and the bounded installed operation preserves its lifecycle authority.
- **Treat matching filenames as projection ownership** — rejected because update/removal could
  overwrite customized or unrelated agent assets; current digest plus receipt is required.
- **Keep a suffix on the preset ID** — rejected because the suffix carried no behavioral,
  ownership, or lifecycle distinction that Spec Kit's component type did not already express.
- **Use `concorde` as both the component ID and both archive filenames** — rejected because two
  different archives cannot occupy the same release path; transport filenames must include type.
- **Retain the former preset as a compatibility alias** — rejected because no supported public
  migration requires it, duplicate command layers would be ambiguous, and the maintainer required
  a single project-wide identity.

## Decision Log

- Replaced the host-centric module split with Skills, Scripts, and Workspace Files.
- Retained Distribution and Auto-Docs as supporting adapters.
- Defined installed skills as the only feature-work interaction surface.
- Made durable, temporal, selection, and generated file lifetimes explicit at the root.
- Assigned deterministic operations and workspace routing to Scripts rather than to an abstract core.
- 2026-08-30: Added `speckit.fast-loop` as an additive agent-followed preset surface with root-scoped workspace routing and no mutation runtime.
- 2026-08-30: Relaxed fast-loop from one-feature/non-contract scope to an anchor plus bounded affected
  features, kept module responsibility/dependency and project-level user policy as the hard boundary,
  and required exact review of architecture edits (R-041).
- 2026-08-30: Kept Protocol v8 and Python scripts unchanged; fast-loop repeats explicit single-root
  resolution and leaves semantic impact discovery with the agent.
- 2026-08-30: Recorded the cross-integration self-host materialization workaround pending an
  inactive-surface preservation fix (R-042).
- 2026-08-30: Kept additive fast-loop removal distinct from lower-layer restoration for the nine normal command modifications (R-030).
- 2026-08-30: Retained follow-up to clarify selected-sub-feature task-path wording (R-027) and to derive release capability counts from manifests rather than duplicated literals (R-032).
- 2026-08-30: Unified the preset and extension IDs as type-qualified `preset:concorde` and
  `extension:concorde`; retained `concorde-bundle` as the bundle identity.
- 2026-08-30: Chose type-qualified preset/extension archive filenames to avoid a transport
  collision while preserving the shared component ID.
- 2026-08-30: Rejected a compatibility alias and recorded the explicitly approved coordinated
  durable-reference migration (R-034, R-035).
- 2026-08-30: Refreshed repository-evidence pins and type-stable diagram sources exposed by the
  identity/path migration (R-037, R-038).
- 2026-08-30: Packaged Feature 005's canonical triage bodies, wrappers, default config, and queue
  helper in `extension:concorde@0.5.0`; no platform-specific behavior fork was introduced.
- 2026-08-30: Added one post-bundle `agent-assets` transaction sourced only from the installed
  extension, with disposable installed preview and digest-receipt update/removal ownership (R-044).
- 2026-08-30: Reused that transaction for self-hosting and replaced the inactive-integration
  backup/restore workaround with independent integration receipt preservation (R-042).
