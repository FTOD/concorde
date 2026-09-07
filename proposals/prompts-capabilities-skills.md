# Prompts, capabilities and skills: one source of truth for agent instructions

Status: approved design for a coordinated Protocol cutover. This document is the working record
for branch `refactor/prompts-capabilities-skills`. It is deleted after adoption, like the previous
Profile 8 proposal; the durable rules land in the Protocol principles and Concorde's own Specs.

Base: main `ed4deb5` (Protocol 1.0.0, Architecture Profile 8, invocation schema 2, 14 Operations of
which 8 are public wrappers).

## 1. Decisions this design records

The maintainer decided, in order:

1. Textual agent instructions live in Markdown snippets ("prompts") that may include one another
   through one explicit reference syntax. The reference graph must be a DAG. Atomicity is not
   required; snippets are shared text, not indivisible rules.
2. "Capability" replaces "Operation" as the executable unit. A capability is one Python module;
   its file name is its identity. It declares, as importable data, the agents it launches and their
   permissions, the capabilities it uses and its typed request/response. No separate descriptor
   files.
3. `skills/` at the repository root lists the user-facing entries only. Everything the user can
   invoke is a skill; everything else is reachable only in-process. Internal capabilities have no
   Skill, no executable entry and no `exposure` flag: existence of a skill *is* public exposure.
4. The two development loops merge into one `dev-loop` capability with `specify` and `run_reviews`
   flags. `fast-loop` disappears as a skill and as a capability.
5. Rendering (reference check, resolution, substitution) happens only at build time. The host and
   the agent runtimes read rendered files. Rendered files are not tracked by Git, except the small
   Protocol manifest that consumers pin. The docsite publishes the rendered versions.
6. Spec documents never use the include mechanism. Spec text is shared through registry-declared
   Shared Specs; instruction text is shared through includes. The exact wire schemas stop being a
   Spec document: the Spec keeps promise-level contracts, code owns exact JSON Schema, and a
   deterministic check keeps both aligned (option C).
7. The rename Operation → capability is done once, including wire type identities, the Protocol
   text, Spec documents and tests. The invocation schema moves from version 2 to version 3.
8. Registry ownership of prompts, capabilities and skill sources follows the capability each text
   serves, not the artifact type.

## 2. Terminology

| Term | Meaning | Lives in | Identity |
| --- | --- | --- | --- |
| prompt | A Markdown snippet with YAML front matter; may `@include` other prompts | `prompts/<owner>/…​.md` | repository-relative path |
| role | One launchable agent identity: a root prompt plus `effects` (reads, writes, network, credentials); receives one fresh process and one compiled policy per launch | `src/concorde/host/roles.py` as `Role` objects | Python constant name; external name is the lower-case role name |
| capability | The executable unit the host runs: a Python module declaring `CLASS`, `ROLES`, `USES`, `REQUEST`, `RESPONSE` and implementing `run` | `capabilities/<name>.py` | module file name |
| skill | A user-facing entry rendered as a Claude Code / Codex SKILL.md that invokes exactly one public capability | source `skills/<concorde-name>/SKILL.md`; rendered into `.claude/skills/` and `.agents/skills/` | `concorde-<name>` |
| build | Deterministic rendering of prompts, skills, roles, Protocol assets, `langgraph.json` and the build manifest | `python -m concorde build` | `generated/build-manifest.json` |
| projection | A rendered, untracked output of the build | `generated/`, `.claude/skills/concorde-*`, `.agents/skills/concorde-*` | build manifest entry |

Old → new: Operation → capability; public Operation → skill + global/lifecycle capability; internal
stage Operation → stage capability; internal leaf Skill → role; `operations/<x>/SKILL.md` body →
skill source plus prompts; `skills/<role>/SKILL.md` → role prompt plus `Role.effects`;
`agent-assets/` → deleted; `sync-agent-surfaces apply/check` → build plus freshness check.

Naming rule: a capability module name uses underscores (`dev_loop.py`). Every external identifier
is `concorde-` plus the hyphenated module name: skill `concorde-dev-loop`, request type
`concorde-dev-loop-request@1`, response type `concorde-dev-loop-response@1`, Studio graph
`concorde-dev-loop`. One function derives all of them; nothing else spells them.

## 3. Repository layout after the cutover

```
prompts/
  protocol/            Protocol text: principles and kind definitions (closed include subgraph)
  workflow-host/       invocation boundary, worktree handoff, gap reporting, loop and review rules,
                       coordinator, planner, task-author, implementation-worker, reviewer prompts,
                       worker preambles that the executor prepends to every launch
  spec-context/        spec-author, reader, context-assessor prompts
  reflections/         reflection investigation and implementation prompts
  installation/        ambient text for init and configure skills
skills/
  concorde-main/SKILL.md          concorde-dev-loop/  concorde-reflections-triage/
  concorde-init/  concorde-configure/  concorde-validate/  concorde-deliver/
capabilities/
  __init__.py          CAPABILITIES = (...) explicit inventory
  main.py dev_loop.py reflections_triage.py           global
  init.py configure.py validate.py deliver.py          lifecycle
  specify.py review.py context_solve.py plan.py tasks.py implement.py   stage
src/concorde/host/     the runtime formerly under src/concorde/capabilities/: resolver, build,
                       validator, roles, contracts, execution, permissions, worktrees, delivery
protocol/manifest.json tracked: Protocol version and digests of the rendered assets
generated/             untracked build output (see section 8)
.claude/skills/concorde-*  .agents/skills/concorde-*   untracked rendered skills
```

`templates/`, `docsite/`, `specs/`, `.concorde/` keep their roles. `operations/`, `agent-assets/`,
`.codex/`, `.claude/agents/`, `scripts/development/sync-agent-surfaces.py`,
`scripts/render-capability-surfaces.py`, `scripts/sync-protocol-assets.py` and the tracked copies
of every projection are deleted.

## 4. Prompts

### 4.1 File format

```markdown
---
audience: worker | ambient | shared
---
Body text. It may contain include directives and variables.
```

`audience` is required. `worker` text is read by a fresh host-launched agent; `ambient` text is
read by the user's own Claude Code / Codex session through a Skill; `shared` text is valid for
both. The Protocol prompts under `prompts/protocol/` are always `shared`.

### 4.2 Include directive

```
@include prompts/workflow-host/worktree-handoff.md
@include prompts/workflow-host/invoke.md capability=concorde-main request=concorde-main-request
```

Rules:

- The directive occupies a whole line, starts at column one, names a repository-relative path and
  may carry `key=value` parameters. Nothing else on the line. Markdown links, code spans and prose
  mentions are never references; a capability or skill name in prose is plain text.
- Parameters bind `{KEY}` variables inside the included file for that inclusion only. A variable
  with no binding fails the build. Variables use the existing single-brace form; `{OPERATION}`,
  `{SCRIPT}` and `{FRAMEWORK}` are replaced by build-supplied values.
- The build rejects: any cycle; the same file reached twice inside one root (diamonds are reported
  with both paths and must be restructured); a directive whose target is missing; an unresolved
  directive or variable in any output; an include whose target has an incompatible audience
  (`ambient` roots may include only `ambient`/`shared`; `worker` roots only `worker`/`shared`);
  any include of a skill source or a Spec document; any include from outside `prompts/protocol/`
  into a Protocol root or from a Protocol root into anything outside `prompts/protocol/`; a prompt
  that no root reaches (dead text).
- Roots are: every skill source, every role root prompt, every worker preamble the executor
  loads, and the Protocol assembly files. Reachability is computed from these.
- Optional lint, on by default: a token matching `concorde-[a-z-]+` in any prompt or skill source
  must equal an existing skill name, capability external name or exported type identity. This is
  a check on plain words, not a reference syntax.

### 4.3 What is not a prompt

Runtime data is never templated into prompt text. The workspace receipt, the configuration
snapshot, the runtime input JSON, the completion schema and the invocation identity continue to
be appended by the executor as separate typed sections. Prompts are static text with static
parameters.

Spec documents under `specs/` keep their current form: Markdown plus the `concorde-document`,
`concorde-participants` and `concorde-contract` blocks. They are read literally by the context
service and published by the docsite from the Git tree.

## 5. Roles

`src/concorde/host/roles.py` defines the nine roles as frozen `Role` objects:

```python
COORDINATOR = Role(name="coordinator", prompt="prompts/workflow-host/coordinator.md",
                   effects=Effects(reads=("discovery-context",), writes=(), network=False,
                                   credentials="none"))
```

Roles: coordinator, reader, spec_author, context_assessor, planner, task_author,
implementation_worker, spec_reviewer, code_reviewer. Their `effects` are exactly the values now in
`skills/<role>/SKILL.md` front matter. The policy compiler consumes `Role.effects`; nothing about
authority is read from Markdown. A role's rendered instructions are `generated/roles/<name>.md`;
the host reads that file, verifies build freshness, and places the bytes in the snapshot's
`instructions` field, so `context_id` continues to cover the exact instruction bytes.

The instruction strings currently embedded in `operation_executor.py` (`_prompt`: review,
topology author, main coordinator and agent-stage preambles) become `worker` prompts under
`prompts/workflow-host/preambles/`. The executor keeps assembling preamble + role instructions +
typed runtime sections in the same order as today.

## 6. Capabilities

### 6.1 Module contract

```python
"""capabilities/plan.py"""
from concorde.host import roles, contracts

CLASS = "stage"                                     # "global" | "lifecycle" | "stage"
ROLES = (roles.CONTEXT_ASSESSOR, roles.PLANNER)    # agents this module launches itself
USES = ()                                          # capabilities invoked in-process, by module name
REQUEST = contracts.task_request(target_required=True)
RESPONSE = contracts.stage_response()

def run(host, configuration, request):             # returns the typed response
    ...
```

- `NAME` is derived from the file name; a module may not override it.
- `CLASS` decides main routing: only `global` capabilities run the coordinator to select a target;
  `lifecycle` capabilities have no agent cognition; `stage` capabilities require `target_id`.
- `ROLES` lists only roles launched by this module. `describe-policy` and the package validator
  compute a capability's full grant by walking `USES`. A stage never widens a parent's grant.
- `REQUEST`/`RESPONSE` are JSON Schema dicts built with the existing `wire_shapes` helpers.
  `contracts.exported_types()` is the union over the inventory plus the internal data types.
- `run` may delegate to shared host machinery. Moving logic out of the former
  `scoped_operations.py` into modules is allowed incrementally; the constants are mandatory from
  the first commit that introduces the module.
- `capabilities/__init__.py` lists the inventory explicitly. A module not listed, or a listed name
  without a module, fails validation. Import cycles among capability modules are validation errors;
  the `USES` graph must be acyclic.

### 6.2 Inventory

| Capability | Class | Roles launched | Uses |
| --- | --- | --- | --- |
| main | global | coordinator, reader, spec_author | — |
| dev_loop | global | coordinator | specify, review, plan, tasks, implement, validate |
| reflections_triage | global | implementation_worker | dev_loop |
| init, configure, validate, deliver | lifecycle | — | — |
| specify | stage | spec_author | — |
| review | stage | spec_reviewer, code_reviewer | — |
| context_solve | stage | context_assessor | — |
| plan | stage | context_assessor, planner | — |
| tasks | stage | task_author | — |
| implement | stage | implementation_worker | — |

`dev_loop` request: the task fields plus `specify: boolean` (default `true`) and
`run_reviews: boolean` (default `true`). `specify=false` is the former fast loop. A review
requirement recorded for a change cannot be disabled by a later `run_reviews=false` on the same
change; every skip is recorded as today. `reflections_triage` composes `dev_loop` with
`specify=true`.

### 6.3 Executable boundary

Only skills have an executable boundary. `scripts/run-capability.py <skill-name>` reads one
`concorde-capability-invocation@3` on stdin and refuses any name that is not a skill. Stage
capabilities have no `operation.py`, no launcher and no error code for direct invocation; there is
nothing to invoke. `describe-policy` remains available for every skill and reports the merged grant
of the capability tree beneath it.

## 7. Skills

Source `skills/concorde-main/SKILL.md`:

```markdown
---
name: concorde-main
description: "Global entry: answer questions, route work, and design or apply system topology from main-visible Domain and Service Specs."
capability: main
---
@include prompts/workflow-host/invoke.md capability=concorde-main request=concorde-main-request
@include prompts/workflow-host/main-actions.md
@include prompts/workflow-host/report-as-returned.md
```

The build adds the integration front matter (`argument-hint`, `compatibility`, `metadata`,
`user-invocable`, `disable-model-invocation` for Claude; the Codex equivalent), replaces
`{OPERATION}` with the launcher path for the target environment, appends the "Input TypedValue
schema" section rendered from the capability's `REQUEST`, and writes the standard
`<integration-root>/<skill>/SKILL.md` structure. A skill source may include only `ambient` or
`shared` prompts. The seven skills: concorde-main, concorde-dev-loop, concorde-reflections-triage,
concorde-init, concorde-configure, concorde-validate, concorde-deliver. The validator requires
`capability` to name a `global` or `lifecycle` capability and requires every such capability to
have exactly one skill.

## 8. Build

`python -m concorde build [--project-root .] [--integration claude|codex|all] [--check]`

Outputs, all untracked:

```
generated/build-manifest.json     sources {path: sha256}, outputs {path: sha256, sources: [...]}
generated/roles/<role>.md         rendered role instructions
generated/preambles/<name>.md     rendered executor preambles
generated/protocol/principles.md  rendered Protocol text
generated/protocol/kinds/*.md
generated/protocol/schemas.json   exported JSON Schemas from contracts
generated/langgraph.json          Studio graph list derived from skills
generated/docs/…                  rendered skill bodies and schemas for the docsite
.claude/skills/concorde-*/SKILL.md
.agents/skills/concorde-*/SKILL.md
```

Rules:

- Deterministic: authored include order, LF newlines, trailing newline, `json.dumps(sort_keys=True,
  indent=2)`, no timestamps. Building twice yields identical bytes; a test asserts it.
- `--check` builds into a temporary directory, compares against the manifest on disk and the
  tracked `protocol/manifest.json`, and exits non-zero on any difference. CI runs it.
- Freshness is enforced at run time: before the host launches any role or renders a policy, it
  recomputes the source digests recorded in `generated/build-manifest.json` and fails closed with
  `stale_build` if they differ or the manifest is missing. Outputs are never rebuilt implicitly by
  a capability run.
- `protocol/manifest.json` stays tracked. The build recomputes the asset digests from the rendered
  Protocol files; `--check` fails if the tracked manifest differs, so a Protocol change is visible
  in review even though the rendered assets are not. `.concorde/config.json` keeps pinning the
  manifest digest; `--bind-project` remains the explicit maintainer acceptance.
- Installation is a build targeted at the consumer: `install-concorde.py` copies the package roots
  (`prompts`, `capabilities`, `skills`, `src`, `scripts`, `protocol`, `templates`, `docsite`,
  `viewer`) into `.concorde/framework/`, runs the build with the framework prefix, and records
  every output in the receipt. Consumers never run the build themselves.
- The host builds when it creates a candidate worktree, so a handoff opens on a ready checkout.
  A human-created worktree runs `python -m concorde build` once; `CLAUDE.md` and `AGENTS.md`
  say so. `verify-worktree` keeps its meaning: the runtime-advertised SKILL.md path (now
  untracked) must belong to the worktree being worked on.
- `concorde.json` keeps only hand-authored package metadata (name, version, viewer, package roots,
  install paths). The skill, capability and role inventories are derived and are no longer listed.

## 9. Wire and Protocol changes

Wire:

| Before | After |
| --- | --- |
| `concorde-operation-invocation@2` with `operation_id` | `concorde-capability-invocation@3` with `capability_id` |
| `concorde-operation-result@2` with `operation_id` | `concorde-capability-result@3` with `capability_id` |
| `concorde-operation-configuration@1`; `.concorde/config.json` key `operation_configuration` | `concorde-capability-configuration@1`; key `capability_configuration` |
| response field `completed_operations` | `completed_capabilities` |
| `concorde-standard-dev-loop-*`, `concorde-fast-loop-*` | `concorde-dev-loop-*` |
| error codes `unknown_operation`, `internal_operation` | `unknown_capability`; the internal code is removed |

Existing consumer projects edit the configuration key by hand; there is no migration tool.

Protocol text (rendered from `prompts/protocol/`): every occurrence of "Operation" in P5, P7, P8,
P9 and P10 becomes "capability" or "skill" according to its meaning; the P7 classes paragraph is
restated as: global, lifecycle and stage capabilities; only skills have an executable boundary;
stage capabilities are never projected and have no direct invocation; context selection happens
only inside global capabilities. The kind definitions are checked for the same word. Version stays
1.0.0 with new digests, following the precedent of every earlier Protocol refactor.

## 10. Self-Spec and registry changes

Documents:

- `specs/concorde/services/operation-registry.md` → `capability-registry.md`
  (`document.capability.registry`), shared by `domain.workflow` and `service.workflow-host`.
  It keeps the hand-written behavior table and the class definitions and adds one machine-readable
  block:

  ```concorde-capabilities
  [{"id": "main", "class": "global", "skill": "concorde-main"}, …]
  ```

  Validation requires this block to equal the Python inventory (names, classes, skill names).
- `specs/concorde/services/operation-boundary.md` → `workflow-host-boundary.md`
  (`document.workflow-host.boundary`). Its wire section becomes promise-level: every TypedValue
  name, what it carries, version and unknown-field rules, error codes and their meaning. Every
  identity in `contracts.exported_types()` must appear in this document and every
  `concorde-…-request/response/…` identity in the document must be exported; the validator checks
  both directions. The existing `concorde-contract` blocks (peer contracts between targets) stay.
- `specs/concorde/services/operation-wire.md` is removed from the registry and deleted. Exact
  schemas are code, rendered by the build and published by the docsite.
- `system.md`, `how-work-progresses.md`, `how-projects-adopt-concorde.md`, `install-boundary.md`,
  `context-boundary.md`, `package-assets.md`, `agent-runtime-contracts.md`,
  `registry-contracts.md`, `reflection-boundary.md`, `README.md` and `scripts/development/STUDIO.md`
  are updated for the vocabulary, the build, the untracked projections and the freshness rule.

Registry implementation ownership (`.concorde/specs.json`):

| Target | Adds | Removes |
| --- | --- | --- |
| service.workflow-host | `capabilities/{main,dev_loop,specify,review,context_solve,plan,tasks,implement,validate,deliver}.py`, `prompts/workflow-host`, `src/concorde/host/roles.py`, renamed host modules | `src/concorde/capabilities/…` paths |
| service.spec-context | `prompts/spec-context`, `prompts/protocol`, `protocol/manifest.json` | — |
| service.reflections | `capabilities/reflections_triage.py`, `prompts/reflections`, `src/concorde/reflections/config.default.json` | — |
| service.installation | `capabilities/{init,configure}.py`, `prompts/installation`, `scripts/run-capability.py` | `scripts/run-operation.py`, `scripts/development/sync-agent-surfaces.py` and its tests |
| module.package-assets | `skills`, `src/concorde/host/build.py`, `src/concorde/host/resolver.py`, `src/concorde/host/package_validation.py` | `skills` (old roles), `operations`, `agent-assets`, `render-capability-surfaces.py`, `sync-protocol-assets.py`, `skill_assets.py`, `profile8_validation.py`, `validation.py` |
| module.wire-contracts | `src/concorde/host/contracts.py` | `src/concorde/capabilities/protocol_contracts.py` |

Every `src/concorde/capabilities/<file>` path in the registry is renamed to
`src/concorde/host/<file>`.

## 11. Package validator

One validator, run by `python -m concorde validate` and by `build --check`, replaces
`profile8_validation.py`, the capability parts of `validation.py` and the checks in
`sync-agent-surfaces.py`:

1. Prompt front matter, include DAG, diamonds, missing targets, audience compatibility, layering,
   Protocol closed subgraph, unresolved directives and variables, reachability, name lint.
2. Capability modules: inventory equality, mandatory constants and their types, `CLASS` values,
   `USES` acyclicity, role objects, skill ⇔ public-class equivalence, one skill per public
   capability, no skill for stage capabilities.
3. Contracts: exported type identities are unique; Protocol digests match the tracked manifest.
4. Spec alignment: `concorde-capabilities` block equals the inventory; type identities and the
   boundary document agree in both directions.
5. Build outputs: manifest freshness; rendered files match a rebuild.

Rule identities keep the `CONCORDE-…` form so tests and docs can name them.

## 12. Docsite

Two generated pages sourced from `generated/`: "Agent instructions" (each skill body and each
role's rendered instructions with the list of contributing prompts from the manifest) and "Wire
contracts" (the rendered schemas). `npm run validate` fails when `generated/build-manifest.json`
is missing or stale, so the site never lags the sources. Both pages are labelled as projections;
per the publication Service they are never agent context authority. The docsite build runs after
the Concorde build in CI.

## 13. Repository policy

`AGENTS.md`: the worktree-affinity section stays; "Maintaining this worktree's Skill projections"
is replaced by "Building this worktree": run `python -m concorde build` after changing `prompts/`,
`skills/`, `capabilities/` or contracts; outputs are untracked and never edited; the host refuses to
run on a stale build. `CLAUDE.md`: `@generated/protocol/principles.md` plus one line telling a
fresh clone to build first. `.gitignore`: `.claude/skills/concorde-*/`, `.agents/`, `.codex/`,
`.claude/agents/`; `generated/` is already ignored. CI: `build --check`, the validator, the
Python suite, the docsite chain.

## 14. Tests

- Golden tests: for the current 8 public SKILL.md files (both integrations) and the 9 role bodies,
  the new build reproduces today's tracked bytes exactly (Stage A, before any content change).
  After the content changes, golden files move to `tests/concorde/fixtures/build/` and compare
  against `generated/`.
- Resolver and validator unit tests for every rule in sections 4 and 11.
- Determinism: build twice, compare.
- Freshness: edit a prompt after building; any skill invocation returns `stale_build`.
- Executable boundary: the launcher accepts the seven skills and refuses every other name;
  invocation schema 3 validation; `capability_id` mismatch handling.
- `dev_loop` flag semantics, including the "cannot disable a recorded review" rule.
- Installer: consumers receive rendered outputs, receipt-owned, and never need to build.
- Spec alignment validators with fixture registries.
- Studio: graphs derived from skills only.
- All tests that exercise the real graph build the package into a temporary root first.

## 15. Staging

Each stage is one commit on the branch and leaves the suite green.

**Stage A — prompts, roles, resolver, build, golden tests.** Add `prompts/`, `roles.py`, the
resolver, `python -m concorde build`, `generated/` outputs and the golden tests proving
byte-identical rendering of today's public SKILL.md files and role bodies. Nothing consumes the
outputs yet; `operations/`, `skills/<role>/`, `agent-assets/` and the tracked projections remain.
Zero behavior change. Executor preambles are extracted here only if the assembled prompt stays
byte-identical for a fixed launch specification; otherwise they move in Stage B.

**Stage B — capabilities, skills, consumers of the build.** Add `capabilities/` modules
(delegating to host machinery), `skills/` sources, the `dev_loop` merge, host loading of
`generated/roles/*` with the freshness check, the launcher, `generated/langgraph.json`, the
package validator, untracked projections, the installer as a build, `AGENTS.md`/`CLAUDE.md`/CI
changes, and deletion of `operations/`, old `skills/<role>/`, `agent-assets/`,
`sync-agent-surfaces.py`, `render-capability-surfaces.py`, `sync-protocol-assets.py`, the
`exposure` flag and the `internal_operation` guard.

**Stage C — rename and Protocol cutover.** Wire schema 3 and every identity in section 9, package
rename to `src/concorde/host/`, Protocol text, Spec document renames and content, registry
ownership, wire document removal, alignment validators, docsite pages, README and STUDIO.md,
`--bind-project`.

**Stage D — verification and cleanup.** Full Python suite, docsite chain, `build --check`,
`validate`, fresh-clone bootstrap test (clone, build, run `describe-policy` through a skill), and
a consumer install test in a temporary project. Delete this proposal in the final commit.

## 16. Acceptance

- `git ls-files` contains no rendered projection: no `.claude/skills/concorde-*`, `.agents/`,
  `.codex/`, `.claude/agents/`, `generated/`, `operations/`, `agent-assets/`, `operation-wire.md`.
- Every shared paragraph exists once under `prompts/`; the golden outputs reproduce today's text
  for unchanged skills and roles.
- The seven skills are the only executable entries; stage capabilities have none.
- A fresh clone works after exactly one build command; a candidate worktree created by the host
  works without any manual step.
- Editing a prompt without rebuilding makes every skill invocation fail with `stale_build`.
- `protocol/manifest.json` is the only tracked derived artifact, and `build --check` proves it
  current.
- The docsite publishes rendered skills, roles and schemas and fails validation on a stale build.
- Python suite, docsite chain, validator and `build --check` are green in CI.

## 17. Out of scope, recorded for follow-up

- Model tiering per role (a `Role.model` hint compiled into launch arguments).
- Exposing stage capabilities as LangGraph subgraphs in Studio.
- The reflection document `phase` vocabulary (`analyze`, `converge`).
- `templates/` (document scaffolds for consumers) stay as they are.
- Removing the merged `refactor/operation-tiers` worktree and branch.
