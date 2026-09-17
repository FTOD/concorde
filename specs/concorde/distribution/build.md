# Build

`build(project_root, integration="all", *, framework_prefix="")` renders Agent instructions,
integration-specific Skill files (Codex `.agents/skills` and Claude `.claude/skills`),
`generated/langgraph.json`, the rule assets (`generated/protocol/principles.md`, its kind
definition, and `generated/protocol/schemas.json`) deterministically from
`capabilities/`, `protocol/`, `prompts/`, `skills/` and the capability contracts. The principles asset
bundles the Protocol principles, Spec management (including Spec and Context) and Required format
chapters with the separate Framework execution profile. The kind asset contains the Module chapter
and its canonical templates. Framework configuration, phase authority and Mermaid authoring
conventions belong to the execution profile, not the independent standard.

The build no longer emits the docsite-only `generated/docs/instructions.json` or
`generated/docs/wire.json`; normal owned-output cleanup retires old copies. This does not remove
runtime Agent instructions, exported schema APIs or `generated/protocol/schemas.json`.

### Rendering and freshness

A **Skill** is an instruction artifact for the developer's external agent runtime. Distribution
owns its authored source under `skills/`, shared invocation instructions under
`prompts/workflow-host/`, and rendered integration-specific installation. Each public Skill maps to
one public Capability; non-public capabilities have no Skill. The external runtime reads
the Skill and submits the declared typed request through `scripts/run-capability.py`; Development
admits and executes that request. That entry path is project-relative, so a rendered Skill
carries no worktree identity: it binds to the worktree in which the developer's runtime executes
it, and Development derives the project root from that working directory. Building or installing
a Skill does not execute its Capability or add it to a Concorde Agent's Harness. Capability behavior remains with its providing Module.

### Protocol and runtime support are separate

The package supports Protocol 8.0.0 with source_profile 14 and document metadata schema 2. Its tracked manifest binds the exact
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
validation compares the unified `concorde.capabilities` metadata with every executable declaration:
exposure, context selection, determinism, USES, State and optional workspace/tools/children.

Agent instruction file membership must equal the declared worker inventory. Agent Python bindings,
role Spec bodies, child definitions and available capability/wire sources are recorded build
inputs; changing them makes verify_fresh reject the old build even when the shared common
instruction body is unchanged.

## Precise specifications

The Distribution Module owns the exact obligations and interface details in [contracts](contracts.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
