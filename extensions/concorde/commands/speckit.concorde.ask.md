---
description: "Answer a grounded, read-only question about the Concorde workflow or framework"
---

# Ask About Concorde

Treat `$ARGUMENTS` as the maintainer's natural-language question. If it is empty, ask the maintainer
to provide one question and stop. This is a read-only explanatory procedure followed by the coding
agent; it is not a Concorde Python runtime operation.

## Resolve the question

1. Classify the question as general framework guidance, project-specific guidance, or a mixture.
2. If materially different answers depend on an unnamed module, feature, lifecycle stage, command,
   or intended behavior, ask one focused clarification question. Do not guess.
3. If the request is general programming work rather than a question about Concorde, state that it is
   outside this surface and recommend the appropriate normal Spec Kit phase without invoking it.

## Select authoritative sources

Read the smallest relevant set in this order:

1. Installed extension sources under `.specify/extensions/concorde/`, especially `extension.yml`,
   `README.md`, and the matching command definitions under `commands/`.
2. Installed preset sources under `.specify/presets/concorde-core/`, especially `preset.yml`,
   `README.md`, command definitions, and templates governing the named lifecycle stage.
3. For project-specific questions only, the project constitution and the smallest bounded set of
   maintained `specs/` sources needed to answer: the current module's `module.md`, one-level
   `architecture.json`, relevant contracts, and the named feature's durable `spec.md` and `design.md`.
   For a sub-feature question, include its parent durable spec/design as aggregate context and only
   concise sibling summaries; do not read sibling bodies or parent/sibling attempts merely because
   they exist. Distinguish two-level feature containment from adjacent-module `refines` links.
4. Use `.concorde/config.json` and `.specify/feature.json` only to locate configured or selected
   sources. They are control state, not behavioral authority.
5. Use generated pages only to locate canonical sources when necessary. Prefer maintained sources in
   citations and never treat a generated read model as stronger authority than its source.

Do not assume a Concorde authoring checkout exists. Do not read unrelated deeper modules or feature
bodies merely because they are present. If an identifier cannot be resolved uniquely, report that
uncertainty or ask for clarification.

## Compose the answer

Return standard Markdown containing:

- a direct answer understandable without opening any source;
- the relevant lifecycle stage or command when useful, clearly presented as a recommendation rather
  than an action already performed;
- a `Basis` section that distinguishes **Framework rule**, **Project observation**, **Agent
  inference**, and **Uncertainty** wherever those categories affect confidence; and
- a `Sources` section with project-relative citation paths for every installed-guidance or maintained
  project fact used.

When installed guidance, maintained project sources, or versions conflict, cite each relevant source,
describe the disagreement, and do not silently normalize it. Do not present model memory as Concorde
authority. If the available sources do not support an answer, say so explicitly.

## Non-mutation invariants

The question surface is strictly read-only. Do not write or edit maintained sources, project control
state, temporal implementation artifacts, generated outputs, code, tests, or installed packages. Do
not change feature selection, regenerate documentation, run implementation, invoke another Concorde
lifecycle operation, or execute a recommended command. Answer, clarify, or state the supported
boundary and then stop.
