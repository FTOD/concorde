# Contract: Concorde Workflow Agent Commands

**Contract ID**: `contract.skills.agent-surface`

**Representation**: Spec Kit extension command Markdown 1.0 rendered by the active integration

## Shared Rules

- Canonical names are `speckit.concorde.init`, `speckit.concorde.impl.accept`,
  `speckit.concorde.context`, `speckit.concorde.validate`, and `speckit.concorde.ask`.
- Agent-specific invocation punctuation is presentation only. Codex skills and slash-command outputs
  must preserve the intent, arguments, runtime operation, result schema, and failure behavior below.
- The command body locates the installed extension runtime relative to the project and invokes it
  using the project's selected script flavor. It does not embed an absolute installation path.
- Architecture operation JSON conforms to `architecture-service.schema.json` (Protocol v1);
  selected-workspace resolution and acceptance JSON conforms to `feature-workspace.schema.json`
  (Feature Workspace Protocol v8, acceptance proposal v6). Agent prose may
  summarize either normative result but must not hide findings or claim stronger evidence.
- Context, validation, and acceptance eligibility/proposal checks are read-only. Initialization and
  acceptance apply write only after an explicit accepted proposal is supplied to apply mode.
- The question command is agent-answered and read-only. It does not claim deterministic runtime
  execution and does not invoke another lifecycle operation merely because that operation would help
  answer the question.
- Feature creation and selection are standard Spec Kit behavior, not Concorde commands. A new
  top-level feature or immediate sub-feature is created through `speckit.specify` with
  `SPECIFY_FEATURE_DIRECTORY` set to its canonical root (`<module>/features/NNN-<short-name>` or
  `<parent root>/subfeatures/NNN-<short-name>`); an existing root is selected through the standard
  `.specify/feature.json` `feature_directory` record. Concorde adds no selection command and no
  second selection store. Before every normal phase the extension's workspace adapter resolves and
  validates the selected root (safe path, canonical `abstract.md`/`design.md`/`implementation.md` trio with no
  legacy names, workspace kind, parent context and sibling summaries for a sub-feature,
  durable/temporal paths, the providing module's `module.md` and `design.md` as navigation
  references, and `attempt_state`), and `speckit.concorde.validate` enforces registration,
  canonical path, two-level containment, identity, document pairing, and legacy-name rules
  deterministically. Containment never implies cross-module refinement.
- Module summaries (`module.md`) and feature abstracts (`abstract.md`) are the first project sources any
  command reads; a feature `design.md` is opened when a requirement's exact wording is needed, and a
  module `design.md` or feature `implementation.md` only deliberately — each is cited when used.

## `speckit.concorde.init`

### Intent

Propose, review, and initialize a minimal root Concorde specification hierarchy.

### Inputs

| Argument | Required | Meaning |
|---|---:|---|
| `--project-root <path>` | no | Project root; defaults to current Spec Kit project. |
| `--module-id <id>` | no | Proposed stable root module ID; default is derived deterministically. |
| `--name <text>` | no | Human-readable project/module name. |
| `--proposal <path>` | apply only | Project-relative accepted proposal file. |
| `--apply` | no | Apply the accepted proposal; absent means proposal-only. |

### Behavior

1. With no `--apply`, inspect existing project metadata and emit an `init` response with status
   `proposal` or `unchanged`. Include responsibility, boundary, explicit provided/required contract
   sets, immediate child summaries, every proposed path (configuration, `module.md` summary in the
   Profile 4 shape linking its level view and reference, seeded `design.md` reference, and the
   level view `architecture/diagrams/level-view.json`), the Skills/Scripts/Workspace-Files
   interaction model, and conflicts. A target holding a summary without a reference, or the reverse,
   is a conflict, not a partial success.
2. The agent presents that proposal for maintainer review and does not translate silence into
   acceptance.
3. With `--apply --proposal <path>`, validate the proposal and current target state, stage all files,
   and promote them only when no conflict exists.
4. Re-running against a complete configured package returns `unchanged` with its current root paths,
   children, features, and contracts, even if maintained content differs from the starter template;
   no replacement proposal is emitted and no files are modified.

### Success artifacts

- `.concorde/config.json` (`profile_version: 4`)
- `specs/<root-slug>/module.md`
- `specs/<root-slug>/design.md`
- `specs/<root-slug>/architecture/diagrams/level-view.json`
- any accepted initial contract documents named in the proposal

### Failures

Unsafe paths, malformed proposals, duplicate IDs, changed target state, existing conflicting content,
or incomplete promotion return `conflict`, `invalid`, or `failed` with findings. Existing maintained
content is never silently overwritten.

## `speckit.concorde.impl.accept`

### Intent

Review and compact one completed attempt into selected feature/sub-feature
`implementation.md` (written in full on the first milestone,
completed on later ones) — optionally amend the providing module's `design.md` with the implementation detail and rationale
developed during the attempt, and remove the temporal `attempt/` directory — all as one
atomic operation, only after explicit approval.

### Inputs

| Argument | Required | Meaning |
|---|---:|---|
| `[feature-id-or-root]` | no | Stable feature ID or canonical feature root; defaults to the selected feature. |
| `--propose` | eligibility | Return task/checklist completion status, current paths, digest, and required proposal shape without mutation. |
| `--proposal <path>` | apply only | Project-relative reviewed acceptance proposal (proposal v6) containing candidate feature `implementation.md`, optional module `design.md` amendment, and exact cleanup manifest. |
| `--apply` | no | Apply the unchanged reviewed proposal; absent means eligibility/proposal-only. |

### Agent and runtime responsibilities

1. The installed command first invokes proposal mode. The runtime resolves the selected feature,
   requires a real active `attempt/tasks.md`, parses every Markdown task item and every real
   Markdown file directly under `attempt/checklists/`, and returns ineligible when no task
   exists, a task is unchecked or malformed, or an existing checklist item is unresolved or
   malformed. A missing optional checklist directory represents zero checklist items; symlinked
   checklist paths are unsafe and invalid.
2. An eligible schema-v8 result directly returns `proposal_path`, `task_summary`, and
   `checklist_summary` alongside `workspace` (including `feature_abstract`, `feature_design`,
   `feature_implementation`, `module_summary`, and `module_design`) and a `source_digest` that covers
   current `abstract.md`, feature `implementation.md`, and module `design.md`; the agent never derives or guesses the proposal or
   amendment locations.
3. When eligible, the coding agent reads `abstract.md`, feature `design.md`, current feature `implementation.md`, the
   module summary and current module `design.md`, the complete attempt, relevant
   architecture/contracts, code, and tests. It drafts current feature `implementation.md` covering module
   and feature collaboration, flows, scenario realization, durable decisions, evidence references,
   limitations, and the implementation detail a coder needs, and — when the
   attempt produced implementation detail or rationale worth keeping — a full replacement
   `design.md` for the providing module that adds that material under the reference's stable
   headings without restating summary-owned facts. It does not copy the transient task log or
   redefine module architecture.
4. The agent writes a project-contained proposal at the returned `proposal_path` that names the
   exact feature `implementation.md` path and full candidate content, the optional module `design.md` path
   and full replacement content, the exact `attempt/` removal target, the target feature, and
   the runtime-provided source digest. It presents the candidate realization, the reference
   amendment, and the cleanup manifest to the maintainer. It never proposes a change to `abstract.md`
   or `design.md`.
5. Silence, checked tasks and checklists, passing validation, or prior acceptance do not authorize apply. Only after
   explicit approval does the agent invoke `--apply --proposal <path>`.
6. Apply re-resolves every path, level, parent relationship, task, checklist, symlink, target, and
   digest; accepts only `implementation.path == workspace.feature_implementation`,
   `module_design.path == workspace.module_design` (when present), and `remove ==
   [workspace.attempt_dir]`; stages every file update and the recoverable directory move;
   and commits all outcomes or restores every prior state. Parent, sibling, and child roots, the
   selected `abstract.md` and `design.md`, and every `module.md` remain byte-identical.

### Success artifacts

- `<feature-root>/implementation.md` containing the reviewed accepted realization
- when proposed, `<module>/design.md` equal to the reviewed amendment
- no `<feature-root>/attempt/` directory
- canonical result listing prior/resulting feature implementation digests (`implementation_digest_before/after`),
  prior/resulting module design digests (null when not amended), removed artifacts, and retained
  authorities

### Failures

Missing or incomplete tasks, unresolved or malformed checklist items, an empty/placeholder
candidate realization, a stale digest (including a changed `abstract.md` or module `design.md`), a
proposal targeting `abstract.md`, feature `design.md`, `module.md`, or another level's `design.md`,
unsafe or partial cleanup targets, symlinked paths, changed sources, or an interrupted apply returns
`invalid`, `conflict`, or `failed`. Prior feature `implementation.md`, the
prior module `design.md`, and the complete implementation attempt remain recoverable.

## `speckit.concorde.context`

### Intent

Return exactly one bounded architectural level plus, for a requested feature/sub-feature, one bounded
feature-containment relationship level.

### Inputs

| Argument | Required | Meaning |
|---|---:|---|
| `<module-or-feature-id>` | yes | Stable ID to resolve. A feature/sub-feature resolves through its providing module. |
| `--project-root <path>` | no | Project root; defaults to current Spec Kit project. |
| `--format json` | no | Canonical format; JSON is the default for the Concorde workflow. |

### Result

The `result.context` object contains:

- the requested ID;
- the full current module responsibility, boundary, feature summaries, and provided/required
  contracts, plus the module's `summary` (`module.md`), `design_reference` (`design.md`), and `view`
  paths as navigation references;
- immediate child module summaries, their organization, and concise provided/required contract
  information including ID, role, flow, and counterparty;
- permitted external actors from the current view;
- current-level scenarios and their contract-governed interactions;
- adjacent feature-refinement links; and
- stable references for deliberate navigation to deeper modules or features.

For a requested parent feature it additionally contains authored-order summaries of immediate
sub-features: ID, title, `## Outcome`, evidence status, canonical navigation root, and `abstract.md`
	and `design.md`/`implementation.md` paths. For a requested
sub-feature it contains the parent summary and concise sibling summaries. These containment records
never include another root's specification/design body or any parent/sibling attempt path.

It must not contain lower-module feature bodies, sub-feature bodies outside the requested root,
grandchildren, third feature levels, the body of any `abstract.md`, feature `design.md`, feature
`implementation.md`, or module `design.md`
(module or feature), or deeper implementation details.

### Failures

An unknown or duplicate ID, invalid source profile, cyclic hierarchy, or unreadable current-level view
returns `invalid` with findings. It never guesses a target or modifies a source.

## `speckit.concorde.ask`

### Intent

Answer a maintainer's natural-language question about the Concorde workflow or framework from the
authoritative guidance installed in the project and, when relevant, the smallest bounded set of
maintained project sources.

### Inputs

| Argument | Required | Meaning |
|---|---:|---|
| `<question>` | yes | A question about Concorde concepts, lifecycle stages, command usage, artifact authority, or application of the workflow to the current project. |

### Result

The agent-facing answer contains:

- a direct answer that remains understandable without opening its cited files;
- the relevant lifecycle stage or command when the question is about what to do next;
- project-relative source citations for every installed guidance or maintained project fact used;
- an explicit distinction among general framework rules, project-specific observations, agent
  inference, and unresolved uncertainty; and
- one focused clarification question instead of an answer when the target module, feature, lifecycle
  stage, or intended meaning cannot be safely inferred.

The command reads installed Concorde guidance and only the project sources needed for the question,
starting from module summaries and feature abstracts; it opens a feature `design.md` only when a
	requirement's exact wording is needed, and a module `design.md` or feature `implementation.md` only when the question
asks for implementation detail, rationale, or accepted realization, and cites each one it opens. It does not write files, change active feature selection, regenerate outputs, invoke an implementation
phase, or present model memory as a framework authority.

### Failures

An empty question requests a question from the maintainer. Unknown project identifiers, unavailable
sources, version mismatches, and conflicting authorities remain visible in the response. Unsupported
questions are bounded explicitly rather than answered as though they were Concorde guidance.

## `speckit.concorde.validate`

### Intent

Deterministically validate a whole architecture package or a safely bounded path/ID.

### Inputs

| Argument | Required | Meaning |
|---|---:|---|
| `[path-or-id]` | no | Project-relative source path or stable ID; defaults to configured package root. |
| `--project-root <path>` | no | Project root; defaults to current Spec Kit project. |
| `--format json` | no | Canonical structured output. |

### Rules

Validation checks, in stable order:

1. supported profile and parseable maintained sources;
2. unique stable IDs and resolvable paths/references;
3. independently acyclic module containment, feature refinement, and feature containment;
4. exactly one providing module per feature, adjacent-module refinement, bidirectional immediate
   sub-feature registration, module inheritance, canonical two-level paths, and rejection of any
   third feature level;
5. explicit module and feature provided/required contract sets;
6. complete contract roles, flows, counterparties, representations, failures, compatibility, and
   evidence;
7. scenario participant scope and contracts on boundary crossings;
8. current module plus immediate-child-only architecture view visibility;
9. explicit evidence status without inference of agreement;
10. module summary shape — required sections, a structure link to the declared view or a recorded
    leaf rationale, inventory tables, and a reachable design reference — plus the reading budget as
    a warning-severity finding that never changes the status;
11. presence of a real, non-empty module `design.md` beside every `module.md`;
12. the feature-root durable trio: real `abstract.md`, `design.md`, and `implementation.md`, with no
    legacy `tldr.md`/`spec.md` files or `implementation/` attempt directory; and
13. feature abstract shape — exactly the five sections in order, a structure link or inline sketch,
    and `Logic` rules that cite requirement IDs defined in the adjacent `design.md` — plus the abstract
    reading budget as a warning-severity finding that never changes the status.

### Exit behavior

| Status | Process exit | Meaning |
|---|---:|---|
| `success` | 0 | Runtime completed and no error findings exist. Warnings may remain. |
| `invalid` | 1 | Runtime completed and one or more error findings exist. |
| `conflict` | 2 | Requested write would conflict; used by init apply. |
| `failed` | 3 | Runtime could not complete because of an execution/environment failure. |

Repeated runs over unchanged bytes and arguments produce byte-equivalent JSON and the same exit code.

## Portability Acceptance

- Codex skills mode contains one `SKILL.md` per canonical command under the active project-local
  skills root.
- One slash-command integration contains the five corresponding registered command artifacts.
- Each supported presentation exercises top-level and sub-feature selection through the standard
  Spec Kit pointer, phase routing, acceptance eligibility/apply, context, validation, and read-only
  workflow questions against the same fixture. Runtime-backed operations return equivalent normative JSON, parent context stays
  read-only and bounded, and the question surface preserves equivalent grounding, citation,
  uncertainty, bounded-context, and non-mutation behavior.
- Removal deletes only extension-owned registered artifacts; locally modified or unrelated agent
  content follows Spec Kit's ownership safeguards.

## Workflow Distribution Handoff

Feature 003 distributes this contract without becoming authoritative for its behavior. One release
handoff consists of:

| Item | Required identity |
|---|---|
| Workspace protocol | `feature-workspace.schema.json`, Protocol/schema version 8 (acceptance proposal v6), all examples, and their combined source digest |
| Normal phase obligations | `specify`, `clarify`, `checklist`, `plan`, `tasks`, `implement`, `analyze`, `converge`, and `taskstoissues` write only the selected feature/sub-feature root, except that every post-specification phase may record problems in the project reflection log returned as `workspace.reflections`; `specify` authors `abstract.md` and `design.md` and seeds placeholder `implementation.md`; only `specify` and `clarify` write `abstract.md` or feature `design.md`, and no normal phase writes feature `implementation.md` or module `design.md`; `analyze` preserves every non-reflection file and makes zero filesystem changes when it has no problem to record; a selected sub-feature additionally reads its parent durable trio as aggregate context and never reads/writes parent/sibling attempts implicitly |
| Additive fast-loop obligation | `speckit.fast-loop` treats the selected root as an anchor, explicitly resolves every affected existing root through Protocol v8, requires accepted/no-attempt baselines for all, reconciles bounded cross-feature and contract/architecture detail while preserving module responsibilities and dependency direction, rejects changes to project-level compatibility/migration policy, and admits an explicit pure naming migration that follows existing policy, preserves logic/non-name semantics, and passes a deterministic stale-name inventory; eligible architecture edits report validated diffs/hashes without separate post-edit review, and no attempt or acceptance artifact is created |
| Concorde command intents | The five canonical IDs and behavior sections in this contract; four are runtime-backed and `ask` is agent-followed/read-only |
| Installed support | Extension-relative workspace adapter, launchers, schemas, runtime sources, preset templates, and complete phase commands needed by those intents |
| Acceptance binding | Spec Kit host version, package versions/digests, handoff digest, actual registered winner, selected paths, outputs, and checkout-access result |

The source digest binds behavior to the reviewed contract/runtime set; it is not a digest of the
user project's mutable architecture sources. Feature 003 may choose supported preset composition and
agent presentation mechanisms, but its receipts must identify this handoff and may not redefine
phase paths, command arguments, result envelopes, or failures.
