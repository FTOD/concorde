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
  implementation-acceptance, and read-only ask skills.

Installed copies under `.agents/skills/`, `.claude/`, or another integration directory are
materializations. The preset and extension directories are the maintained package sources. Fast-loop
is distributed and self-hosted through those same public component mechanisms.

### Script boundary

Only four Concorde-specific skills cross into the deterministic runtime: `init`, `context`,
`validate`, and `impl.accept`. The read-only `ask` skill and the mutating `fast-loop` skill are
followed by the coding agent and have no runtime subcommand. Normal phase skills call `workspace.py`
only to resolve the selected nested workspace and derive phase paths; fast-loop calls the same adapter
with a root-scoped phase to resolve an existing durable feature before semantic eligibility review.

The script boundary is implemented by:

- `extensions/concorde/scripts/bash/concorde.sh` and
  `extensions/concorde/scripts/powershell/concorde.ps1` — portable launchers;
- `extensions/concorde/scripts/python/concorde.py` — Python entry adapter;
- `extensions/concorde/scripts/python/workspace.py` — selected-workspace adapter;
- `extensions/concorde/runtime/concorde/` — deterministic initialization, context, validation,
  reflection, readiness, and implementation-acceptance logic.

Scripts return structured results. Command instructions interpret those results and present them to
the maintainer. A script never becomes a second conversational interface.

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
| Generated projection | `generated/**`, docsite build output | Disposable read model; never source authority |

An agent may read durable files for bounded context and write the files explicitly assigned to the
current phase. Attempt files may be replaced during convergence. Durable intent changes through the
relevant specification workflow. The first accepted realization is written through explicit,
digest-bound implementation acceptance; an explicitly requested eligible fast-loop may later
reconcile the selected feature's established durable intent and realization directly after
proportional evidence passes.

### Interaction matrix

| Skill family | Reads | Writes | Script use |
|---|---|---|---|
| Clarify / specify | Existing durable architecture and feature intent | Durable feature intent | Selected-workspace routing as needed |
| Plan / tasks | Durable intent and bounded architecture | `attempt/` planning and task files | Workspace routing; context/validation when instructed |
| Implement / analyze / converge | Durable intent plus current `attempt/` | Product code, task state, attempt evidence, reflections | Workspace routing; context/validation when instructed |
| `fast-loop` | One selected established feature, bounded architecture, relevant code/tests/docs, worktree state | Eligible code/tests, affected selected feature documents, related non-architectural guides, genuine reflections | Root-scoped workspace routing only |
| `concorde.context` / `validate` | Maintained architecture and feature files | None | Deterministic runtime operation |
| `concorde.init` | Project/config state | Proposal only, then approved root files | Deterministic runtime operation |
| `concorde.impl.accept` | Completed attempt and durable targets | Approved durable realization and attempt cleanup | Atomic deterministic operation |
| `concorde.ask` | Smallest relevant installed guidance and project sources | None | No runtime operation; agent answers with citations |

### Skill and workspace-file data flow

The maintained [skill-to-file data flow](architecture/diagrams/skill-workspace-file-flow.json)
separates the architecture-related workspace (`.concorde/config.json`, module sources, contracts,
and level views) from the selected feature workspace (durable feature files, temporal `attempt/`
memory, code, reflections, and accepted realization). It shows which related Spec Kit and Concorde
skills consume or produce each side. Its delivered
<a href="/architecture/concorde-skill-workspace-file-flow.html">interactive view</a> keeps the main
lifecycle paths sparse; the embedded matrices name the exact per-skill exceptions and write sets.

### Supporting adapters

Distribution packages the maintained preset and extension, publishes their catalogs, and delegates
materialization to Spec Kit. It treats the nine normal commands as complete instruction
modifications and fast-loop as an additive surface: removal can reveal lower normal winners, while
solely owned fast-loop disappears (R-030). Auto-Docs validates maintained sources, renders declared diagrams,
and projects `specs/`, `docs/`, and the root README into a generated site. These adapters consume the
three-part workflow architecture; they do not sit between a skill, script, and workspace file during
normal feature work.

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
authoring belongs to the coding agent. Scripts contribute only canonical selection facts. This keeps
the risk decision semantic—feature ownership, architecture, contracts, compatibility, and worktree
safety—instead of encoding an unreliable line-count threshold or a second mutation engine.

Using one shared component ID keeps the public name aligned with the product while the component
type carries the distinction Spec Kit already requires. Type-qualified archive filenames solve the
separate transport collision without leaking packaging mechanics back into component identity.
The repository-wide cutover required explicitly approved terminology-only reconciliation across
historical and adjacent durable references; R-034 and R-035 preserve that migration lesson without
changing the modules' responsibilities or dependency direction.

This split also makes testing clearer: command-surface tests belong to Skills, runtime and launcher
tests belong to Scripts, workspace-layout and acceptance tests belong to Workspace Files, release
tests belong to Distribution, and site tests belong to Auto-Docs.

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
- **Alias fast-loop to `speckit.implement`** — rejected because implementation requires an active
  attempt and would silently reintroduce the planning, tasks, and acceptance ceremony this path omits.
- **Define smallness by changed-line count** — rejected because ownership and architectural risk, not
  diff size, determine whether direct authoring is safe.

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
