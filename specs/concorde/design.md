# Design Reference: Concorde

This reference explains how the project-level boundaries map to repository sources. `module.md`, module-owned
contracts, and the maintained level view remain authoritative for responsibility and organization.

## Implementation Notes

### Installed interaction surface

Concorde has no standalone end-user application. Spec Kit materializes Markdown command definitions
as coding-agent skills or slash commands. During feature work the maintainer invokes one of those
skills and the coding agent follows its instructions.

The skill sources come from two packages:

- `presets/concorde-core/commands/` and `templates/` compose Concorde guidance into the normal Spec
  Kit phases: clarify, specify, plan, tasks, implement, analyze, checklist, task-to-issues, and
  converge.
- `extensions/concorde/commands/` defines the Concorde-specific init, context, validate,
  implementation-acceptance, and read-only ask skills.

Installed copies under `.agents/skills/`, `.claude/`, or another integration directory are
materializations. The preset and extension directories are the maintained package sources.

### Script boundary

Only four Concorde-specific skills cross into the deterministic runtime: `init`, `context`,
`validate`, and `impl.accept`. The read-only `ask` skill is followed by the coding agent and has no
runtime subcommand. Normal phase skills call `workspace.py` only to resolve the selected nested
workspace and derive phase paths.

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
current phase. Attempt files may be replaced during convergence. Durable intent changes only through
the relevant specification workflow, and accepted realization changes only through explicit,
digest-bound implementation acceptance.

### Interaction matrix

| Skill family | Reads | Writes | Script use |
|---|---|---|---|
| Clarify / specify | Existing durable architecture and feature intent | Durable feature intent | Selected-workspace routing as needed |
| Plan / tasks | Durable intent and bounded architecture | `attempt/` planning and task files | Workspace routing; context/validation when instructed |
| Implement / analyze / converge | Durable intent plus current `attempt/` | Product code, task state, attempt evidence, reflections | Workspace routing; context/validation when instructed |
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
materialization to Spec Kit. Auto-Docs validates maintained sources, renders declared diagrams,
and projects `specs/`, `docs/`, and the root README into a generated site. These adapters consume the
three-part workflow architecture; they do not sit between a skill, script, and workspace file during
normal feature work.

## Design Rationale

The former organization mixed packaging boundaries, host integration, file semantics, and runtime
behavior. In particular, the name “Scripts” hid the concrete fact that the implementation
is a Python script runtime operating on files. The revised organization uses observable nouns and
keeps each dependency directional:

`Maintainer → Skills → Scripts → Workspace Files`, with a direct `Skills → Workspace Files` path for
agent-authored phases. Distribution feeds Skills and Scripts; Auto-Docs consumes Workspace Files.

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

## Decision Log

- Replaced the host-centric module split with Skills, Scripts, and Workspace Files.
- Retained Distribution and Auto-Docs as supporting adapters.
- Defined installed skills as the only feature-work interaction surface.
- Made durable, temporal, selection, and generated file lifetimes explicit at the root.
- Assigned deterministic operations and workspace routing to Scripts rather than to an abstract core.
