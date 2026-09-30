# Decision log: spec-quality-protocol

Goal: State in the Spec Protocol how a good Spec is evaluated (Module quality and architecture quality between Modules, non-deterministic), and add a review-architecture task type that reads every Module's Specs but no code contents

## Brief (main agent, 2026-10-01)

This task is the first of four that rebuild Concorde's reviews; the later ones (`panel-architects`,
`module-code-review`) build on what it specifies. Keep to the Modules bound here.

### The developer's decisions this task carries out

1. **The Spec Protocol states how a good Spec is evaluated.** Today the evaluation system lives only
   in the framework prompt `prompts/workers/spec-review/checklist.md` (six dimensions:
   readability, obligations, design, views, terminology, context; blocking vs advisory). The
   Protocol has the writing guidance (`protocol/module.md`, "Writing guidance") and the
   "semantic sufficiency" claim (`protocol/principles.md#conformance`) but no evaluation system.
   The developer wants the Protocol to state it, explicitly accepting that it is non-deterministic
   (a judgment, never a structural check). Add it as part of the Spec writing guidelines
   (`protocol/writing.md` lists the parts), covering:
   - **Module quality**: what the current checklist judges (reader-first order, one decidable
     obligation per requirement, testable scenarios, design explained by the problems it prevents,
     faithful views, terminology), stated as criteria of the Protocol rather than as a worker's
     instructions.
   - **Architecture quality between Modules**, judged from the whole project's Specs: Modules drawn
     around responsibilities and axes of change (build on "Choosing Module boundaries"), cohesion,
     decoupling and narrow behaviour-defined interfaces, clear boundaries with one owner for every
     concept and promise, no overlapping responsibilities and no unowned gaps, explicit and sensible
     dependency direction with no undeclared dependency, failure containment between Modules
     (each knows how to react when a collaborator fails), consistent abstraction levels and
     consistent promises across Modules about the same thing. Mutual `uses` between Modules are
     acceptable (an earlier decision of the developer): a cycle alone is not a defect.
   - What makes a problem **blocking** vs **advisory** in Protocol terms: blocking when a reader or
     a task bound to the Module could not rely on the Spec as written.
   The tiers of Issues (who may fix a problem) are **not** Protocol matter: they belong to the
   framework and are specified by the `project-issues` task. Do not put them in the Protocol.
2. **A new Protocol task type, `review-architecture`**, for the architects the `panel-architects`
   task adds to `spec_panel`: it reads the Specs of every Module of the project (the whole Spec
   side, read only) and the names but not the contents of code; it writes nothing. The developer
   chose "whole project's Specs, no code contents" over adding code contents or a host-rendered
   registry digest. Specify it in `protocol/boundaries.md` (task type table, its row and its
   explanation, which likely needs a new boundary set or a rule for "every Module's Specs"), bump
   the Protocol version, compute its grant in Spec core, and make the Harness give its workers the
   same read-only tools as `review-spec` on both backends. Update the glossary's
   `concept.task-type` ("seven Protocol task types") and any other term this changes.

### Left to the task session

Naming, the chapter's structure and exactly how the new set is declared, as long as every level
stays computable from declarations (Protocol axiom A7). Do not change `prompts/workers/spec-review/`
or `src/concorde/spec_review/`: those belong to `panel-architects`. Escalate to the main agent,
together, anything that changes what another Module promises beyond the new task type.

### Verification and delivery

After Protocol changes run `python3 scripts/concorde.py build` and
`python3 scripts/concorde.py protocol-manifest --write --bind-project`; run `spec-validation` and
the relevant tests, then `task-validation` and `delivery`, and report to the main agent.

## Task session decisions (2026-10-01)

- **Chapter.** The evaluation system is a new Protocol chapter `protocol/evaluation.md`
  ("Evaluating a Spec"), the third part of the Spec writing guidelines (`writing.md`, README,
  `prompts/protocol/kinds/module.md` bundle). It states: evaluation is a judgment, not
  deterministic, never a structural check, evidence of semantic sufficiency only, bound to the
  Specs read; two levels (Module quality from `SpecContext`, architecture quality from every
  Module's Specs); severity blocking/advisory defined by whether a reader or a task bound to the
  Module could rely on the Spec as written, and explicitly no further grading (tiers stay out).
  Module quality keeps the checklist's six dimensions (readability, obligations, design, views,
  terminology, context) as criteria. Architecture quality has six dimensions: responsibilities,
  ownership, interfaces, dependencies, failure containment, consistency; mutual `uses` stated as
  acceptable. `principles.md#conformance` now points semantic sufficiency at the chapter.
- **New boundary set `ProjectSpecification`** (named after `ProjectImplementation`): both members
  of every document any Module owns and the whole glossary, the same for every Module (the union
  of every `SpecScope`), so every level stays computable from declarations (A7). Registry not
  included (it only mirrors the entries' `module` blocks).
- **`review-architecture` row:** SpecContext read, ImplementationContext names, ImplementationScope
  none, SpecScope none, ExternalContext read, ProjectImplementation **names**, ProjectSpecification
  read. ProjectImplementation at `names` gives "names but not contents of code" for the whole
  project. Bound to the Modules whose place in the architecture is asked about; binding the root
  alone judges the whole project.
- **Context identity** of a `review-architecture` grant also covers the digest of every
  ProjectSpecification file, so a change to any Module's Specs makes its judgment stale
  (`req.spec.context-identity-changes` extended, one SHALL kept).
- **Version 16.1.0** (minor): every 16.0 Spec stays valid; migration section added.
- **Harness tools:** `tool_set` in `src/concorde/harness/settings.py` (Harness-owned) now gives the
  read-only set to every task type whose Protocol row writes nothing (read from `grants.LEVELS`),
  so `review-architecture` gets `review-spec`'s tools on both backends without touching
  `src/concorde/harness/pi_backend.py`, which module.workers binds. Harness binds no tests; the rule
  was checked by calling `tool_set` with both backends' tables.
- **Glossary** updated: `concept.task-type` (eight), `concept.boundary-set` (seven sets),
  `concept.context-identity`, `concept.spec-context`, `concept.implementation-context`.
- **Docs** updated within bound Modules: README.md, docs/README.md, docs/using-concorde.md,
  prompts/development/skill.md.
- **Left for other Modules (not changed, outside this task):** `specs/concorde/execution/workers/launch.md`
  still says "seven Protocol task types" (module.workers); the Spec MCP server's `grant` tool enum in
  `src/concorde/spec_mcp/tools.py` (module.spec-mcp) does not offer `review-architecture`;
  `pi_backend.TOOL_SETS` has no explicit row (not needed, see above).

## Report 1 to the main agent (spec-review quality criteria), 2026-09-30T19:47:41Z

spec-quality-protocol delivered: delivery commit b738f11d on concorde/spec-quality-protocol (work commit a1ad39e1; delivery run r-20260930T194132-delivery-9b925dc7). Verified: build --check, protocol-manifest --write --bind-project, spec-validation 0 findings, full pytest 844 passed / 4 skipped, task-validation ready.

What changed:
- Protocol 16.1.0 (minor; every 16.0 Spec stays valid, migration section added). New chapter protocol/evaluation.md "Evaluating a Spec", the third part of the Spec writing guidelines (writing.md, README, kinds/module bundle; principles#conformance points semantic sufficiency at it). It states evaluation is a judgment, not deterministic, never a structural check; two levels: Module quality (readability, obligations, design, views, terminology, context: the checklist's criteria stated as Protocol criteria) and architecture quality between Modules (responsibilities, ownership, interfaces, dependencies, failure containment, consistency; mutual uses explicitly not a defect); blocking = a reader or a task bound to the Module could not rely on the Spec as written, advisory otherwise; no further grading (Issue tiers stay out of the Protocol).
- New read set ProjectSpecification (both members of every document any Module owns + the whole glossary, same for every Module) and task type review-architecture: SpecContext read, ImplementationContext names, ImplementationScope/SpecScope none, ExternalContext read, ProjectImplementation names, ProjectSpecification read. Its grant's context identity also covers every ProjectSpecification file.
- Spec core computes it (grants.py, boundary sets, errors); Harness: tool_set gives the read-only set to every task type whose Protocol row writes nothing, so review-architecture gets review-spec's tools on both backends without editing module.workers' pi_backend.py.
- Glossary: task-type (eight), boundary-set (seven), context-identity, spec-context, implementation-context. Spec core and Harness Specs, root module.md, README/docs/development skill updated. New scenario scenario.spec.grant-review-architecture with a test.

Decisions I took (all in the decision log): naming (ProjectSpecification, evaluation.md), version 16.1.0 as minor, registry not part of ProjectSpecification, ProjectImplementation at names to give "names but no code contents", a bound Module is judged first but binding the root alone judges the whole project, Harness rule derived from grants.LEVELS instead of a per-backend row.

Open, outside this task's Modules (no decision needed, small follow-ups): specs/concorde/execution/workers/launch.md still says "seven Protocol task types" (module.workers); the Spec MCP server's grant tool enum in src/concorde/spec_mcp/tools.py (module.spec-mcp) does not offer review-architecture; Harness binds no tests, so the tool rule has no Harness-owned test (checked by direct call; workers' tests cover tool_set generally). No escalations.

## Closed: merged, 2026-09-30T19:48:02Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit b738f11d0bac33e03d70eff85f33cee6030ca584 into main and closed it as merged. Nobody answers a report after that.
