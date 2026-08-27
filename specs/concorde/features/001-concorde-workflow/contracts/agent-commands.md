# Contract: Concorde Workflow Agent Commands

**Contract ID**: `contract.integration.agent-skills`

**Representation**: Spec Kit extension command Markdown 1.0 rendered by the active integration

## Shared Rules

- Canonical names are `speckit.concorde.init`, `speckit.concorde.feature.harden`,
  `speckit.concorde.context`, `speckit.concorde.validate`, and `speckit.concorde.ask`.
- Agent-specific invocation punctuation is presentation only. Codex skills and slash-command outputs
  must preserve the intent, arguments, runtime operation, result schema, and failure behavior below.
- The command body locates the installed extension runtime relative to the project and invokes it
  using the project's selected script flavor. It does not embed an absolute installation path.
- Architecture operation JSON conforms to `architecture-service.schema.json`; selected-workspace
  resolution and hardening JSON conforms to `feature-workspace.schema.json`. Agent prose may
  summarize either normative result but must not hide findings or claim stronger evidence.
- Context, validation, and hardening eligibility/proposal checks are read-only. Initialization and
  hardening apply write only after an explicit accepted proposal is supplied to apply mode.
- The question command is agent-answered and read-only. It does not claim deterministic runtime
  execution and does not invoke another lifecycle operation merely because that operation would help
  answer the question.
- Feature creation and selection are standard Spec Kit behavior, not Concorde commands. A new
  top-level feature or immediate sub-feature is created through `speckit.specify` with
  `SPECIFY_FEATURE_DIRECTORY` set to its canonical root (`<module>/features/NNN-<short-name>` or
  `<parent root>/subfeatures/NNN-<short-name>`); an existing root is selected through the standard
  `.specify/feature.json` `feature_directory` record. Concorde adds no selection command and no
  second selection store. Before every normal phase the extension's workspace adapter resolves and
  validates the selected root (safe path, canonical `spec.md`/`design.md` pair, workspace kind,
  parent context and sibling summaries for a sub-feature, durable/temporal paths, and
  `implementation_state`), and `speckit.concorde.validate` enforces registration, canonical path,
  two-level containment, and identity rules deterministically. Containment never implies
  cross-module refinement.

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
   sets, immediate child summaries, proposed paths, and conflicts.
2. The agent presents that proposal for maintainer review and does not translate silence into
   acceptance.
3. With `--apply --proposal <path>`, validate the proposal and current target state, stage all files,
   and promote them only when no conflict exists.
4. Re-running against the same initialized package returns `unchanged` without modifying files.

### Success artifacts

- `.concorde/config.json`
- `specs/<root-slug>/module.md`
- `specs/<root-slug>/architecture.json`
- any accepted initial contract documents named in the proposal

### Failures

Unsafe paths, malformed proposals, duplicate IDs, changed target state, existing conflicting content,
or incomplete promotion return `conflict`, `invalid`, or `failed` with findings. Existing maintained
content is never silently overwritten.

## `speckit.concorde.feature.harden`

### Intent

Review and compact one completed implementation attempt into the selected feature/sub-feature's durable `design.md`, then
remove the temporal `implementation/` directory only after explicit approval.

### Inputs

| Argument | Required | Meaning |
|---|---:|---|
| `[feature-id-or-root]` | no | Stable feature ID or canonical feature root; defaults to the selected feature. |
| `--propose` | eligibility | Return task/checklist completion status, current paths, digest, and required proposal shape without mutation. |
| `--proposal <path>` | apply only | Project-relative reviewed hardening proposal containing the candidate design and exact cleanup manifest. |
| `--apply` | no | Apply the unchanged reviewed proposal; absent means eligibility/proposal-only. |

### Agent and runtime responsibilities

1. The installed command first invokes proposal mode. The runtime resolves the selected feature,
   requires a real active `implementation/tasks.md`, parses every Markdown task item and every real
   Markdown file directly under `implementation/checklists/`, and returns ineligible when no task
   exists, a task is unchecked or malformed, or an existing checklist item is unresolved or
   malformed. A missing optional checklist directory represents zero checklist items; symlinked
   checklist paths are unsafe and invalid.
2. An eligible schema-v3 result directly returns `proposal_path`, `task_summary`, and
   `checklist_summary` alongside `workspace` and `source_digest`; the agent never derives or guesses
   the proposal location.
3. When eligible, the coding agent reads `spec.md`, current `design.md`, the complete attempt, relevant
   architecture/contracts, code, and tests. It drafts a concise current `design.md` covering module and
   feature collaboration, flows, scenario realization, durable decisions, evidence references, and
   limitations. It does not copy the transient task log or redefine module architecture.
4. The agent writes a project-contained proposal at the returned `proposal_path` that names the exact design path, full candidate
   content, exact `implementation/` removal target, target feature, and runtime-provided source digest.
   It presents the candidate design and cleanup manifest to the maintainer.
5. Silence, checked tasks and checklists, passing validation, or prior acceptance do not authorize apply. Only after
   explicit approval does the agent invoke `--apply --proposal <path>`.
6. Apply re-resolves every path, level, parent relationship, task, checklist, symlink, target, and
   digest; stages only the selected root's design update and recoverable directory move; and commits
   both outcomes or restores the prior state. Parent, sibling, and child roots remain byte-identical.

### Success artifacts

- `<feature-root>/design.md` containing the reviewed accepted realization
- no `<feature-root>/implementation/` directory
- canonical result listing prior/resulting design digests, removed artifacts, and retained authorities

### Failures

Missing or incomplete tasks, unresolved or malformed checklist items, an empty/placeholder candidate
design, a stale digest, unsafe or partial cleanup targets, symlinked paths, changed sources, or an interrupted apply returns `invalid`,
`conflict`, or `failed`. The prior `design.md` and complete implementation attempt remain recoverable.

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
  contracts;
- immediate child module summaries, their organization, and concise provided/required contract
  information including ID, role, flow, and counterparty;
- permitted external actors from the current view;
- current-level scenarios and their contract-governed interactions;
- adjacent feature-refinement links; and
- stable references for deliberate navigation to deeper modules or features.

For a requested parent feature it additionally contains authored-order summaries of immediate
sub-features: ID, title, `## Outcome`, evidence status, and canonical navigation root. For a requested
sub-feature it contains the parent summary and concise sibling summaries. These containment records
never include another root's specification/design body or any parent/sibling attempt path.

It must not contain lower-module feature bodies, sub-feature bodies outside the requested root,
grandchildren, third feature levels, or deeper implementation details.

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

The command reads installed Concorde guidance and only the project sources needed for the question.
It does not write files, change active feature selection, regenerate outputs, invoke an implementation
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
8. current module plus immediate-child-only architecture view visibility; and
9. explicit evidence status without inference of agreement.

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
  Spec Kit pointer, phase routing, hardening eligibility/apply, context, validation, and read-only
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
| Workspace protocol | `feature-workspace.schema.json`, Protocol/schema version 3, all examples, and their combined source digest |
| Normal phase obligations | `specify`, `clarify`, `checklist`, `plan`, `tasks`, `implement`, `analyze`, `converge`, and `taskstoissues` write only the selected feature/sub-feature root; a selected sub-feature additionally reads its parent durable spec/design as aggregate context and never reads/writes parent/sibling attempts implicitly |
| Concorde command intents | The five canonical IDs and behavior sections in this contract; four are runtime-backed and `ask` is agent-followed/read-only |
| Installed support | Extension-relative workspace adapter, launchers, schemas, runtime sources, preset templates, and complete phase commands needed by those intents |
| Acceptance binding | Spec Kit host version, package versions/digests, handoff digest, actual registered winner, selected paths, outputs, and checkout-access result |

The source digest binds behavior to the reviewed contract/runtime set; it is not a digest of the
user project's mutable architecture sources. Feature 003 may choose supported preset composition and
agent presentation mechanisms, but its receipts must identify this handoff and may not redefine
phase paths, command arguments, result envelopes, or failures.
