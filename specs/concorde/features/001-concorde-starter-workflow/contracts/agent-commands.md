# Contract: Concorde Core Workflow Agent Commands

**Contract ID**: `contract.integration.agent-skills`

**Representation**: Spec Kit extension command Markdown 1.0 rendered by the active integration

## Shared Rules

- Canonical names are `speckit.concorde.init`, `speckit.concorde.feature.create`,
  `speckit.concorde.feature.select`, `speckit.concorde.context`, and
  `speckit.concorde.validate`.
- Agent-specific invocation punctuation is presentation only. Codex skills and slash-command outputs
  must preserve the intent, arguments, runtime operation, result schema, and failure behavior below.
- The command body locates the installed extension runtime relative to the project and invokes it
  using the project's selected script flavor. It does not embed an absolute installation path.
- Architecture operation JSON conforms to `architecture-service.schema.json`; feature placement and
  selection JSON conforms to `feature-workspace.schema.json`. Agent prose may summarize either
  normative result but must not hide findings or claim stronger evidence.
- Context and validation are read-only. Initialization writes only after an explicit accepted
  proposal is supplied to apply mode.
- Feature creation changes durable intent only after explicit placement approval. Feature selection
  may write only the standard project-local Spec Kit selection record after validating the target.

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

Review architectural placement, create one nested feature root through the normal Spec Kit specify
phase, register it with the providing module, and select it for subsequent phases.

### Inputs

| Argument | Required | Meaning |
|---|---:|---|
| `--module-id <id>` | yes | Providing module chosen after bounded-context review. |
| `--feature-id <id>` | yes | Proposed stable feature identity. |
| `--short-name <name>` | yes | Safe 2–4 word directory suffix. |
| `--number <NNN>` | no | Explicit feature number; otherwise allocate deterministically inside the module. |
| `--approve` | apply only | Confirms acceptance of the exact placement proposal and source digest. |

### Behavior

1. Resolve the providing module and return its bounded context.
2. Propose the feature root, canonical spec path, module registration, affected contracts/view, and
   any conflict without writing maintained intent.
3. After explicit approval, invoke the normal Spec Kit specify phase with the exact
   `SPECIFY_FEATURE_DIRECTORY`; Spec Kit authors the one root `spec.md`.
4. Apply the approved architecture registration, validate it, and persist the feature root as the
   active selection atomically.
5. Return Concorde Feature Workspace Protocol v1 paths and findings.

### Failures

Unknown ownership, unsafe or occupied paths, duplicate IDs, changed source digest, a failed specify
phase, or invalid post-apply architecture returns `invalid`, `conflict`, or `failed`. The command does
not silently choose a different module or leave a partial selection.

## `speckit.concorde.feature.select`

### Intent

Select one existing nested feature root as the active workspace for normal Spec Kit phases.

### Inputs

| Argument | Required | Meaning |
|---|---:|---|
| `<feature-id-or-root>` | yes | Stable feature ID or project-relative feature-root path. |
| `--resume` | conditional | Explicitly resume an existing active implementation attempt. |

### Behavior

1. Resolve exactly one feature and verify its canonical root `spec.md`, providing module,
   registration, path confinement, and implementation-attempt state.
2. Derive root specification/contract/checklist paths and temporal implementation paths.
3. Atomically persist only the feature root in `.specify/feature.json`.
4. Return `selected` or `unchanged` with the complete derived path set.

### Failures

Unknown, ambiguous, unsafe, stale, or conflicting workspaces and non-explicit attempt resumption leave
the prior selection unchanged and return actionable findings.

## `speckit.concorde.context`

### Intent

Return exactly one bounded architectural level for a module or feature.

### Inputs

| Argument | Required | Meaning |
|---|---:|---|
| `<module-or-feature-id>` | yes | Stable ID to resolve. A feature resolves through its providing module. |
| `--project-root <path>` | no | Project root; defaults to current Spec Kit project. |
| `--format json` | no | Canonical format; JSON is the default for the core workflow. |

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

It must not contain child feature bodies, grandchildren, or deeper implementation details.

### Failures

An unknown or duplicate ID, invalid source profile, cyclic hierarchy, or unreadable current-level view
returns `invalid` with findings. It never guesses a target or modifies a source.

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
3. acyclic module containment and feature refinement;
4. exactly one providing module per feature and adjacent-level refinement;
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
- Each surface exercises placement, selection, proposal, context, and validation behavior against the same fixture and
  returns equivalent normative runtime JSON.
- Removal deletes only extension-owned registered artifacts; locally modified or unrelated agent
  content follows Spec Kit's ownership safeguards.

## Workflow Distribution Handoff

Feature 003 distributes this contract without becoming authoritative for its behavior. One release
handoff consists of:

| Item | Required identity |
|---|---|
| Workspace protocol | `feature-workspace.schema.json`, schema version 1, both examples, and their combined source digest |
| Normal phase obligations | Durable `specify`/`clarify`/`checklist`; temporal `plan`/`tasks`/`implement`/`analyze`/`converge`/`taskstoissues` |
| Concorde command intents | The five canonical IDs and behavior sections in this contract |
| Installed support | Extension-relative workspace adapter, launchers, schemas, and runtime sources needed by those intents |
| Acceptance binding | Spec Kit host version, package versions/digests, handoff digest, actual registered winner, selected paths, outputs, and checkout-access result |

The source digest binds behavior to the reviewed contract/runtime set; it is not a digest of the
user project's mutable architecture sources. Feature 003 may choose supported preset composition and
agent presentation mechanisms, but its receipts must identify this handoff and may not redefine
phase paths, command arguments, result envelopes, or failures.
