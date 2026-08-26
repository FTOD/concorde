# Contract: Concorde Workflow Agent Commands

**Contract ID**: `contract.integration.agent-skills`

**Representation**: Spec Kit extension command Markdown 1.0 rendered by the active integration

## Shared Rules

- Canonical names are `speckit.concorde.init`, `speckit.concorde.feature.create`,
  `speckit.concorde.feature.select`, `speckit.concorde.feature.harden`,
  `speckit.concorde.context`, `speckit.concorde.validate`, and `speckit.concorde.ask`.
- Agent-specific invocation punctuation is presentation only. Codex skills and slash-command outputs
  must preserve the intent, arguments, runtime operation, result schema, and failure behavior below.
- The command body locates the installed extension runtime relative to the project and invokes it
  using the project's selected script flavor. It does not embed an absolute installation path.
- Architecture operation JSON conforms to `architecture-service.schema.json`; feature placement and
  selection JSON conforms to `feature-workspace.schema.json`. Agent prose may summarize either
  normative result but must not hide findings or claim stronger evidence.
- Context, validation, and hardening eligibility/proposal checks are read-only. Initialization and
  hardening apply write only after an explicit accepted proposal is supplied to apply mode.
- The question command is agent-answered and read-only. It does not claim deterministic runtime
  execution and does not invoke another lifecycle operation merely because that operation would help
  answer the question.
- Feature or sub-feature creation changes durable intent only after explicit placement approval.
  Feature selection may write only the standard project-local Spec Kit selection record after
  validating the target. Containment never implies cross-module refinement.

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

## `speckit.concorde.feature.create`

### Intent

Review architectural placement, create one top-level feature or immediate sub-feature root through
the normal Spec Kit specify phase, register it with its module or parent respectively, and select it
for subsequent phases.

### Inputs

| Argument | Required | Meaning |
|---|---:|---|
| `--module-id <id>` | top-level only | Providing module chosen after bounded-context review. Mutually exclusive with `--parent-feature`. |
| `--parent-feature <id>` | sub-feature only | Existing top-level parent feature. It supplies the providing module and canonical parent root. |
| `--feature-id <id>` | yes | Proposed stable feature identity. |
| `--short-name <name>` | yes | Safe 2–4 word directory suffix. |
| `--number <NNN>` | no | Explicit feature number; otherwise allocate deterministically inside the module. |
| `--approve` | apply only | Confirms acceptance of the exact placement proposal and source digest. |

### Behavior

1. Resolve either the providing module for a top-level feature or one valid top-level parent feature
   for an immediate sub-feature; reject missing/both placement modes and child-as-parent input.
2. Propose the canonical root/spec/design paths, module or parent registration, affected
   contracts/view, selected level, and any conflict without writing maintained intent. A child root
   is allocated directly under `<parent>/subfeatures/` and inherits the parent module.
3. After explicit approval, invoke the normal Spec Kit specify phase with the exact
   `SPECIFY_FEATURE_DIRECTORY`; Spec Kit authors the one root `spec.md` and seeds the adjacent
   `design.md` with an explicit no-hardened-realization state.
4. Apply the approved module/parent registration, validate both durable paths and bidirectional child
   metadata, and persist the created lifecycle root as the active selection atomically.
5. Return Concorde Feature Workspace Protocol v3 paths, relationship context, and findings.

### Failures

Unknown ownership/parent, child-as-parent or third-level placement, module disagreement, unsafe or
occupied paths, duplicate IDs, changed source digest, a failed specify phase, or invalid post-apply
architecture returns `invalid`, `conflict`, or `failed`. The command does not silently choose a
different module/parent or leave a partial selection.

## `speckit.concorde.feature.select`

### Intent

Select one existing top-level feature or immediate sub-feature root as the active workspace for
normal Spec Kit phases.

### Inputs

| Argument | Required | Meaning |
|---|---:|---|
| `<feature-id-or-root>` | yes | Stable feature/sub-feature ID or project-relative lifecycle-root path. |
| `--resume` | conditional | Explicitly resume an existing active implementation attempt. |

### Behavior

1. Resolve exactly one feature-shaped source and verify its allowed level, canonical root `spec.md`,
   durable root `design.md`, providing module, module/parent registration, path confinement, and
   implementation-attempt state.
2. Derive the selected root's durable and temporal paths. For a sub-feature, also derive nullable
   read-only parent ID/root/spec/design and ordered concise sibling summaries without bodies or
   attempt paths.
3. Atomically persist only the selected lifecycle root in `.specify/feature.json`.
4. Return `selected` or `unchanged` with the complete Protocol v3 path/relationship set.

### Failures

Unknown, ambiguous, unsafe, stale, or conflicting workspaces and non-explicit attempt resumption leave
the prior selection unchanged and return actionable findings.

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
- One slash-command integration contains the seven corresponding registered command artifacts.
- Each supported presentation exercises top-level and sub-feature placement, selection, phase
  routing, hardening eligibility/apply, context, validation, and read-only workflow questions against
  the same fixture. Runtime-backed operations return equivalent normative JSON, parent context stays
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
| Concorde command intents | The seven canonical IDs and behavior sections in this contract; six are runtime-backed and `ask` is agent-followed/read-only |
| Installed support | Extension-relative workspace adapter, launchers, schemas, runtime sources, preset templates, and complete phase commands needed by those intents |
| Acceptance binding | Spec Kit host version, package versions/digests, handoff digest, actual registered winner, selected paths, outputs, and checkout-access result |

The source digest binds behavior to the reviewed contract/runtime set; it is not a digest of the
user project's mutable architecture sources. Feature 003 may choose supported preset composition and
agent presentation mechanisms, but its receipts must identify this handoff and may not redefine
phase paths, command arguments, result envelopes, or failures.
