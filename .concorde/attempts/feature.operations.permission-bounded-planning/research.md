# Research: Permission-Bounded Planning Operations

## Decision 1 — Separate the control plane from enforcement

- **Decision**: Treat the trusted Operation Python/runtime as the control plane. It resolves
  Workspace Protocol 13, chooses the next public capability, compiles a concrete policy, and hands
  one immutable launch specification to a host executor. Codex/Claude/outer OS isolation enforces
  the policy; LangGraph never claims enforcement.
- **Rationale**: The current graph has no production agent launcher and calls an injected executor
  once per stage. The requested trust boundary is impossible to prove from prompt text or graph
  topology alone.
- **Alternatives considered**: Prompt-only file lists were rejected as non-enforcing. Making
  LangGraph implement a filesystem sandbox was rejected because it is a scheduler, not the process
  boundary.

## Decision 2 — Make leaf effects machine-readable and Operation bindings narrowing-only

- **Decision**: Extend canonical leaf Skill metadata with an integration-neutral `effects` mapping
  over validated workspace role tokens (`reads`, `writes`, `network`, and credential posture).
  Operation source binds every direct leaf occurrence to an agent/integration configuration and may
  only remove rights. Validation rejects any widening.
- **Rationale**: Current mutation boundaries exist only in Skill prose, so a deterministic validator
  cannot prove that a stage policy is safe. Keeping the declaration with the leaf preserves the
  complete-Skill authority model.
- **Alternatives considered**: A central registry was rejected because it duplicates leaf authority.
  One profile per stage was rejected because the current `tasks` and reflection stages bundle leaves
  with different effects.

## Decision 3 — Preserve Operation abstraction through acyclic nesting

- **Decision**: Operation metadata and Python literals declare ordered `capabilities`, not only
  `skills`. A direct capability may be a leaf Skill or another manifested Operation. Nested
  Operations remain opaque to the parent; runtime and validation reject self-reference and indirect
  cycles with an exact cycle path.
- **Rationale**: Promoting `concorde-plan` while flattening its new internal leaves into every caller
  would violate the requested hierarchy. The standard loop should know only the public planner
  contract.
- **Alternatives considered**: Flattening was rejected as an abstraction leak. Importing arbitrary
  nested Python during static validation was rejected; static validation reads literal topology,
  while execution dispatches the trusted paired entry point.

## Decision 4 — Keep planning internals out of user surfaces

- **Decision**: Replace public leaf `concorde-plan` with public Operation `concorde-plan`, backed by
  internal leaves `concorde-plan-context` and `concorde-plan-author`. Add `exposure: internal` Skill
  metadata; internal leaves remain packaged/loadable by Operations but are not projected as
  user-invocable Codex/Claude skills.
- **Rationale**: The implementation pieces are not public workflow choices. Hiding them preserves
  the stable public name and the module abstraction.
- **Alternatives considered**: Projecting both leaves was rejected because it exposes internals and
  leaves three competing planning entry points.

## Decision 5 — Resolve planning dependencies from required interfaces only

- **Decision**: The trusted planning-context resolver includes the selected feature, its providing
  architecture/owned locators, and the direct feature file owning each `interfaces.required` ID.
  Every provider inclusion carries the interface ID as a reason. Other related features remain
  summaries.
- **Rationale**: Current `related_features` metadata is an untyped ID list; relationship meaning is
  prose and cannot drive a security boundary deterministically. Interface ownership is already
  indexed and unique.
- **Alternatives considered**: Inferring dependency meaning from prose or names was rejected.
  Expanding the ontology with typed feature edges is a future feature, not a prerequisite for this
  enforceable first version.

## Decision 6 — Resolve concrete paths before starting an agent

- **Decision**: Add a trusted permission-context resolver that maps leaf role tokens to real,
  project-relative non-symlink paths. It derives providing-module owned implementation locators from
  architecture entities, required-interface provider feature files from the interface index,
  selected attempt/control paths from Protocol 13, and implementation writes from validated task
  paths. The launch specification contains only concrete paths and a digest.
- **Rationale**: Current Protocol 13 `executable_context` is repository-wide root hints and is too
  broad for a security boundary. The existing repository loader may remain a trusted control-plane
  implementation detail as long as untrusted agents receive only bounded context and native path
  policy.
- **Alternatives considered**: Letting the agent resolve its own permissions was rejected because it
  requires ambient read access before confinement.

## Decision 7 — Render Codex permission profiles, not legacy sandbox flags

- **Decision**: For supported Codex CLI versions, render a unique digest-named permission profile
  with `:minimal = "read"`, exact `:workspace_roots` rules, `network.enabled = false`, approval policy
  `never`, strict config parsing, ephemeral execution, and user-config isolation. Never pass
  `--sandbox` together with `default_permissions`. Unsupported clients require a declared outer
  sandbox with the same effective path set or fail closed.
- **Rationale**: Official OpenAI documentation states that permission profiles and legacy
  `sandbox_mode` do not compose; profiles provide path-level `read`/`write`/`deny` rules and more
  specific entries override broader ones.
- **Sources**: https://learn.chatgpt.com/docs/permissions and
  https://learn.chatgpt.com/docs/config-file/config-reference
- **Alternatives considered**: `workspace-write` was rejected because it grants the whole workspace.
  Mutating user `$CODEX_HOME` profiles was rejected; native `-c key=value` overlays keep the launch
  self-contained.

## Decision 8 — Use Claude rules and strict OS sandbox together

- **Decision**: Run Claude non-interactively in restricted/`dontAsk` mode with an inline `--settings`
  document. Render exact Read/Edit/Write rules and enable the Bash sandbox with
  `failIfUnavailable: true`, `allowUnsandboxedCommands: false`, filesystem allow/deny rules, network
  disabled by default, and credential scrubbing. Unsupported platforms require an outer sandbox or
  fail closed.
- **Rationale**: Claude permission rules govern built-in tools, while its sandbox enforces Bash and
  child-process access at OS level. Official guidance says deny precedes ask/allow and the default
  fallback is unsandboxed unless `failIfUnavailable` is set.
- **Sources**: https://code.claude.com/docs/en/permissions,
  https://code.claude.com/docs/en/sandboxing, and
  https://code.claude.com/docs/en/cli-usage
- **Alternatives considered**: Permission mode alone was rejected because it controls prompting, not
  subprocess filesystem reach. `bypassPermissions` was rejected outside an independently verified
  outer sandbox.

## Decision 9 — Add an injectable real process executor

- **Decision**: Provide a host executor that can launch `codex exec` or `claude -p` from an immutable
  launch specification, with an injectable subprocess runner for tests. Return structured output,
  policy/config digests, process status, and enforcement receipt. The existing credential-free CLI
  remains able to describe topology/policies without launching a model.
- **Rationale**: Configuration rendering alone would not satisfy the requested execution boundary;
  an explicit host handoff and receipt make the enforcement claim testable without network calls.
- **Alternatives considered**: Hard-wiring credentials or running live models in tests was rejected.

## Decision 10 — Make reflection routing conditional before per-leaf execution

- **Decision**: Preserve public `concorde-plan` in reflection routing but stop treating every route
  alternative as an unconditional linear invocation. `status` is read-only and terminates after the
  queue Tool; `investigate` runs investigators; only a validated chosen route invokes fast-loop or
  nested plan; only ready fast-loop plans reach isolated implementers.
- **Rationale**: The current demo always visits all four stages and bundles `fast-loop` with `plan`.
  Moving to one launch per leaf would otherwise execute mutually exclusive routes.
- **Alternatives considered**: Referencing `concorde-plan-author` directly was rejected as an
  abstraction violation.

## Decision 11 — Treat the capability migration as Concorde 2.1.0

- **Decision**: Keep Package Manifest schema 2 and Profile 7/Protocol 13, bump the package to 2.1.0,
  and update the constitution to 7.1.0. The framework contains 17 leaves (15 public, 2 internal) and
  three Operations, while supported integrations still expose 18 public `concorde-*` skills.
- **Rationale**: The public `concorde-plan` name and observable purpose remain stable, while nesting,
  internal exposure, and permission enforcement are additive framework semantics. No compatibility
  reader or alias remains.
- **Alternatives considered**: A Package Manifest schema bump was rejected because its separate
  skill/operation inventories remain sufficient. Retaining 2.0.0 was rejected because installed
  capability kind and enforcement behavior materially change.
