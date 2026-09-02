# Concorde extension

The extension registers five integration-neutral commands around Architecture Source Profile 7 and
Feature Workspace Protocol 12:

- `speckit.concorde.init` proposes, then explicitly applies, a root module with one
  `architecture.md`; it never guesses product modules.
- `speckit.concorde.context` returns exactly one bounded module or design-only feature context.
- `speckit.concorde.validate` deterministically checks module hierarchy, typed entities, directed
  relationships/interactions, flat features, embedded interfaces, Architecture Zoom references,
  attempts, diagrams, reflections, and path safety.
- `speckit.concorde.deliver` produces Delivery Proposal 8, revalidates a completed attempt, and
  atomically removes only that temporal directory. Durable design/architecture and code/tests are
  retained byte-identically.
- `speckit.concorde.ask` answers from cited installed guidance and bounded project sources without
  mutation.

Features are created and selected through normal Spec Kit mechanisms. Each feature is one direct
`<module>/features/<NNN-name>.md` file; stable related-feature IDs express composition or
dependency. `.specify/feature.json` remains the only selection record.

Protocol 12 resolves:

- selected feature identity, `feature_path`, and providing module;
- the providing module's `architecture.md`, bounded module ancestry, and bounded related-feature
  summaries;
- stable-ID-derived `.concorde/attempts/<feature-id>/` paths/state plus
  `.concorde/reflections/log.md` process state; and
- deterministic source/test discovery context.

It does not synthesize an implementation summary or expand another feature/attempt. Source code is
implementation authority, tests/checks are evidence, and generated pages/diagrams are projections.
Target projects need Python 3.11+ for runtime-backed surfaces and no third-party Python dependency.

## Reflection triage agent assets

The extension also carries the canonical `reflection-triage/v3` orchestrator, model-neutral
investigator/implementer roles, safe default configuration, Claude/Codex wrappers, and deterministic
queue helper. The helper allocates never-reused IDs atomically and removes an open entry only after
its `small` `fast-loop` plan is validated, merged, marked `merged`, and proven in current history.
Other routes and efforts retain maintainer disposition. These surfaces support reflection
maintenance and are not a sixth command.

`concorde agent-assets preview|sync|verify|remove --integration <claude|codex>` reconciles native
project surfaces. Claude receives one skill and two role documents; Codex receives one skill and two
agent TOML files. Generated files contain no mandatory model or checkout path.

Shared maintainer state lives under `.concorde/reflections/`: `log.md` is tracked authority,
`config.json` configures triage, and plans/worktrees remain disposable. The installer receipt at
`.specify/concorde-agent-assets.json` hashes only generated projections. Update/removal touches a
listed path only while its digest matches the receipt; modified, legacy, inactive-integration,
unrelated, and policy-protected files are preserved and reported.

Investigators are read-only and return evidence-backed plans. Implementers receive one explicit
worktree and file ownership. The parent owns plan persistence and merge, never edits reflection
Status/Note, and invokes deterministic merged-small removal only after validation.
