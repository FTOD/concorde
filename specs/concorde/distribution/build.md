# Build

`build(project_root, integration="all", *, framework_prefix="")` renders Agent instructions,
this checkout's integration-specific Skill projections under private `generated/session/codex` and `generated/session/claude`, `generated/langgraph.json`, the rule assets (`generated/protocol/principles.md`,
its kind definition, and `generated/protocol/schemas.json`) deterministically from
`operations/`, `protocol/`, `prompts/` (the Skill sources are `prompts/skills/<name>.md`) and the
operation contracts. The tracked published Skills under `skills/` come from the same sources
through the separate `skills --write` step, explained below. The principles asset
bundles the Protocol principles, Spec management (including Spec and Context) and Required format
chapters with the separate Framework execution profile. The kind asset contains the Module chapter
and its canonical templates. Framework configuration, phase authority and Mermaid authoring
conventions belong to the execution profile, not the independent standard.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Operation](../module.md#terminology) | Defined in Concorde Framework. |
| [Public operation](../operations/module.md#terminology) | Defined in Operations. |
| [Internal operation](../operations/module.md#terminology) | Defined in Operations. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Worktree](../module.md#terminology) | Defined in Concorde Framework. |
| [Protocol binding](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Document role](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Worker profile](../harness/module.md#terminology) | Defined in Harness. |

The build no longer emits the docsite-only `generated/docs/instructions.json` or
`generated/docs/wire.json`; normal owned-output cleanup retires old copies. This does not remove
runtime Agent instructions, exported schema APIs or `generated/protocol/schemas.json`.

## Rendering and freshness

Distribution owns a Skill's authored source under `prompts/skills/`, shared invocation
instructions under `prompts/workflow-host/`, the published Skills under `skills/` and this
checkout's rendered integration-specific projections. Each public Skill maps to one public
Operation; non-public operations have no Skill. The external runtime reads the Skill and submits
the declared typed request through `scripts/run-operation.py`; the
[Harness admission](../harness/admission.md) admits and executes that request. That entry path
is project-relative, so a rendered Skill carries no worktree identity: it binds to the worktree in
which the developer's runtime executes it, and Harness admission derives the project root from that
working directory. Building or installing a Skill does not execute its Operation or add it to a
Concorde Agent's Harness. Operation behavior remains with its providing Module.

The checkout's own projections are untracked private build output under `generated/session/`,
never registered in ambient discovery. The published Skills are different: they are
what the Agent Skills CLI (`npx skills add`) installs, from this repository or from the framework
copy an installer deployed, and that CLI copies a repository's `skills/` verbatim. So `skills/`
holds one client-neutral rendering per public Operation, bound to an installed framework's launcher
`.concorde/framework/scripts/run-operation.py` and carrying only the standard front matter, and it
is tracked. Like the tracked Protocol copy, it changes only through an explicit step,
`python3 scripts/concorde.py skills --write`, committed together with the source it renders;
`skills --check`, `build --check` and package validation report a stale, missing or retired
published Skill, and `build` itself never writes there. A build with a framework prefix, the build
an installer runs for a project, renders no Skill projection at all for the same reason. See the
[publish contract](scenarios.md#scenario.distribution.skills-publish).

For the Pi coding agent the build renders no Skills but one private shim, `generated/session/pi/concorde-session.ts`,
from the same Skill sources: it imports the tracked Pi session extension and embeds every public
Operation's description, guidance and request schema. The guidance leaves out the two includes
that describe the stdin envelope, because the extension's `concorde` tool builds that envelope and
runs the same launcher itself. The shim is rendered, checked and rewritten like a Skill projection
and is bound to no worktree either: it locates the project through its own path.

Retiring a public Skill also retires its generated entry, so a developer's runtime does not keep
advertising a removed operation. The build remembers explicitly retired names even after they
leave the current manifest; freshness checking reports their remaining directories and rebuilding
removes their projections. Unknown Skills are preserved, including ones with a Concorde-like name.
Cleanup stops before writing if a retired directory contains extra files or unsafe links, rather
than guessing whether those files belong to the developer. See the
[retirement contract](scenarios.md#scenario.distribution.build-retired-skills).

### Protocol and runtime support are separate

The package supports Protocol 10.0.0 with source_profile 15 and document metadata schema 2. Its tracked manifest binds the exact
generated rule and versioned schema bytes; project configuration binds the exact manifest bytes.
Context payloads and worker wrappers retain their independently versioned wire agreements; the
Protocol document-role migration does not change those envelopes. Build freshness establishes projection integrity;
structural validation, configured checks and review evidence remain separate. Updates to exported
schemas require a rebuild and explicit manifest rebinding in the same worktree. Consumer package
updates preserve the existing binding until explicitly accepted.

## Design

### Projection identity

Agent builds publish twelve independent worker projections and no separate common one. Each
rendered `generated/agents/<name>.md` concatenates the shared common worker rules
(`prompts/workers/common.md`) and that worker's own role Spec source; the manifest records both
sources, together with the bytes of each of that worker's declared child definitions. Package
validation compares the unified `concorde.operations` metadata with every executable declaration:
exposure, context selection, determinism, USES, State and optional workspace/tools/children.

Agent instruction file membership must equal the declared worker inventory. Agent Python bindings,
role Spec bodies, child definitions and available operation/wire sources are recorded build
inputs; changing them makes verify_fresh reject the old build even when the shared common
instruction body is unchanged.

## Precise specifications

The Distribution Module owns the exact obligations and interface details in [contracts](contracts.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.

## Fresh source-maintenance selection

Source maintenance starts a new Skill-free writer in a candidate, never a fork carrying old Skill
bodies. The main session remains outside that authoring context. After the writer checks, commits
and stops, the main starts a separate fresh sibling tester in the same candidate. Both disable
inherited/discovered Concorde catalogs; the tester receives only explicit private candidate paths.
Failed tests return to maintenance followed by another fresh tester. Neither child delegates tasks.

`select-session --mode test --runtime <absolute-candidate-launcher> --skill <absolute-private-SKILL.md>`
checks candidate sources, manifest and exact selected output bytes. Maintenance mode accepts no
Skills. Missing, unreadable, symlinked, stale or outside paths block selection without fallback.
The returned bodies and provenance are launch inputs, not execution receipts. The external harness
must enforce fresh context, discovery disablement and its actual depth/permission ceiling.

Selection may be saved with `--output <absolute-candidate/.concorde/work/selection.json>`.
The explicitly configured `CONCORDE_SESSION_SELECTION` names that file at launcher entry; the
launcher re-verifies the selected paths, bodies and provenance before executing and records the
selection in primary run evidence without claiming the external model loaded it. Maintenance
selection is not permission to invoke public graphs while authoring their governing Skills.

Private selection refuses a Studio redirect because it cannot attest that remote runtime as the
selected candidate; it never falls back to the server's catalog or code.
