# Build

`build(project_root, integration="all", *, framework_prefix="")` renders Agent instructions,
integration-specific Skill files (Codex `.agents/skills` and Claude `.claude/skills`),
`generated/langgraph.json`, the rule assets (`generated/protocol/principles.md`, its kind
definition, and `generated/protocol/schemas.json`) deterministically from
`operations/`, `protocol/`, `prompts/`, `skills/` and the operation contracts. The principles asset
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
| [Public operation](../development/module.md#terminology) | Defined in Development operation host. |
| [Internal operation](../development/module.md#terminology) | Defined in Development operation host. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Worktree](../module.md#terminology) | Defined in Concorde Framework. |
| [Protocol binding](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Document role](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Worker profile](../harness/module.md#terminology) | Defined in Harness. |

The build no longer emits the docsite-only `generated/docs/instructions.json` or
`generated/docs/wire.json`; normal owned-output cleanup retires old copies. This does not remove
runtime Agent instructions, exported schema APIs or `generated/protocol/schemas.json`.

## Rendering and freshness

Distribution owns a Skill's authored source under `skills/`, shared invocation instructions under
`prompts/workflow-host/`, and rendered integration-specific installation. Each public Skill maps to
one public Operation; non-public operations have no Skill. The external runtime reads
the Skill and submits the declared typed request through `scripts/run-operation.py`; the [Development Module](../development/module.md)
admits and executes that request. That entry path is project-relative, so a rendered Skill
carries no worktree identity: it binds to the worktree in which the developer's runtime executes
it, and Development derives the project root from that working directory. Building or installing
a Skill does not execute its Operation or add it to a Concorde Agent's Harness. Operation behavior remains with its providing Module.

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
