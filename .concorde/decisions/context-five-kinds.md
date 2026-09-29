# Decision log: context-five-kinds

Goal: Developer's decision: a worker's context has five kinds, not four: Spec context (the Protocol's SpecContext of the bound Modules, documents plus terms), external context (the Protocol's ExternalContext: the external dependencies' documentation and source a Module's external references pin), implementation context, capability context and task context. Add concept.external-context to the glossary (owner module.concorde) with its explanation in specs/concorde/core-concepts.md, redefine concept.context as the union of the five, and update every Spec, prompt and user doc that lists the context kinds or says what a worker reads (root Module, Harness, Spec core, Workers, docs/), so none describes external material as part of Spec context. No code change unless something names the kinds.

## Decisions (task session)

- **Definition of external context.** Defined `concept.external-context` as the pinned documentation
  and source of external dependencies that the bound Modules' `external` inclusions select, the
  Protocol's ExternalContext, read only; explained in `core-concepts.md` between Spec context and
  implementation context, saying that only the bound Modules' own inclusions count and that it adds
  no promise. Options: link it to Spec core's per-Module boundary set only; define it at the worker
  level like the other four kinds. Chose the worker level, matching the other kinds' entries.
- **Spec context definition reworded.** It said "the Protocol's SpecContext … without their
  ExternalContext", which implied that the Protocol's SpecContext holds external material; it does
  not (`protocol/context.md`). Reworded to "…SpecContext of those Modules, which holds no external
  material".
- **Implementation context corrected.** Its definition and explanation said a code-reading task
  receives the contents of the bound Modules' files; the Protocol's task-type table grants read on
  ProjectImplementation (the whole project's code and every Module's external material) to
  implement, test, review-code and code-to-spec. Corrected both, in module.concorde's own entry,
  since the five-kinds explanation otherwise misplaced where other Modules' external material
  reaches a code task. Options: leave it (out of the literal goal) or fix it (same entry, same
  Module). Chose to fix.
- **Protocol text left unchanged.** `protocol/context.md` speaks of "four channels" (spec, term,
  implementation, external); those are the Protocol's channels, not the worker's context kinds, and
  already separate external material, so no Protocol change is needed.
- **Workers left unchanged.** Workers' Specs and the brief code neither list the context kinds nor
  describe external material as Spec context; no change was needed there.
- **User guide.** Added the five kinds as a short list to "What workers can and cannot do" in
  `docs/using-concorde.md`, and named the external dependencies' documentation and source in
  `docs/README.md`'s description of the computed context.
- **Harness term link moved.** Replacing "[Spec], implementation and task context" by the linked
  context kinds left the Harness document's first use of "Spec" unlinked (`CHK.term.unlinked`
  warning); linked it at its next use instead.

## Closed: merged, 2026-09-28T18:46:34Z
