# Contract: Concorde Starter Agent Commands

**Contract ID**: `contract.integration.agent-skills`

**Representation**: Spec Kit extension command Markdown 1.0 rendered by the active integration

## Shared Rules

- Canonical names are `speckit.concorde.init`, `speckit.concorde.context`, and
  `speckit.concorde.validate`.
- Agent-specific invocation punctuation is presentation only. Codex skills and slash-command outputs
  must preserve the intent, arguments, runtime operation, result schema, and failure behavior below.
- The command body locates the installed extension runtime relative to the project and invokes it
  using the project's selected script flavor. It does not embed an absolute installation path.
- Runtime JSON conforming to `architecture-service.schema.json` is the normative result. Agent prose
  may summarize it but must not hide findings or claim stronger evidence.
- Context and validation are read-only. Initialization writes only after an explicit accepted
  proposal is supplied to apply mode.

## `speckit.concorde.init`

### Intent

Propose, review, and initialize a minimal root architecture package.

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
- `architecture/<root-slug>/module.md`
- `architecture/<root-slug>/architecture.json`
- any accepted initial contract documents named in the proposal

### Failures

Unsafe paths, malformed proposals, duplicate IDs, changed target state, existing conflicting content,
or incomplete promotion return `conflict`, `invalid`, or `failed` with findings. Existing maintained
content is never silently overwritten.

## `speckit.concorde.context`

### Intent

Return exactly one bounded architectural level for a module or feature.

### Inputs

| Argument | Required | Meaning |
|---|---:|---|
| `<module-or-feature-id>` | yes | Stable ID to resolve. A feature resolves through its providing module. |
| `--project-root <path>` | no | Project root; defaults to current Spec Kit project. |
| `--format json` | no | Canonical format; JSON is the default in the starter release. |

### Result

The `result.context` object contains:

- the requested ID;
- the full current module responsibility, boundary, feature summaries, and provided/required
  contracts;
- immediate child module summaries and only their provided/required contract IDs;
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
- One slash-command integration contains the three corresponding registered command artifacts.
- Each surface exercises proposal, context, and validation behavior against the same fixture and
  returns equivalent normative runtime JSON.
- Removal deletes only extension-owned registered artifacts; locally modified or unrelated agent
  content follows Spec Kit's ownership safeguards.

