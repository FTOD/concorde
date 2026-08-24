# Data Model: Concorde Spec Kit Distribution

**Feature**: `feature.concorde.install-with-spec-kit`  
**Date**: 2026-08-22  
**Authority note**: These are implementation entities. Package manifests, durable contracts, and
Feature 001's workspace protocol remain authoritative for externally observable facts.

## Relationship Summary

```text
Feature 001 Workflow Handoff ── constrains ──┐
                                              ├─ Preset Command Overrides
Bundle Recipe ── pins ── Preset Package ─────┤
              └─ pins ── Extension Package ──┘

Release Source ── builds ── Release Artifact ── advertised by ── Catalog Entry
Catalog Entry ── resolved by Spec Kit ── Expanded Component Plan ── accepted as ── Installation Record

Preset Package ── contributes ── Template Layers + Normal Command Overrides
Extension Package ── contributes ── Concorde Commands + Workspace Adapter + Runtime
Spec Kit ── resolves winner ── Active Integration ── materializes ── Resolved Command Surface

Clean Target Project ── executes ── Resolved Command Surface ── produces ── Command Surface Receipt
Installation Record ── owns/references ── installed components and materialized surfaces
```

## 1. Workflow Handoff Reference

A release-bound reference to the Feature 001 semantics being distributed.

| Field | Type | Meaning |
|---|---|---|
| `protocol_version` | stable string | Feature Workspace Protocol version. |
| `source_digest` | SHA-256 | Digest of the accepted workspace/command handoff sources. |
| `workspace_adapter` | installed-relative path | Entry point used before path-sensitive work. |
| `normal_phase_obligations` | ordered set | Nine normal command intents and their durable or temporal roots. |
| `concorde_command_intents` | ordered set | Six Feature 001 command IDs and result contracts. |
| `compatibility` | version constraint | Supported Spec Kit host range. |

Feature 003 packages and presents this handoff. It may not change its paths, failures, or command
meaning. A receipt for a different digest cannot satisfy the current workflow.

## 2. Bundle Recipe

A passive, non-executable Spec Kit package containing exact component references.

| Field | Type | Meaning |
|---|---|---|
| `id` | stable ID | `concorde-starter`. |
| `version` | semantic version | Independently versioned bundle release. |
| `preset_pin` | component reference | Exact `concorde-core` version, priority, and bundle strategy. |
| `extension_pin` | component reference | Exact `concorde` version. |
| `requires` | compatibility record | Supported Spec Kit range and required tools. |
| `integration` | absent | The target project's active integration is inherited. |

The recipe never embeds component behavior and never installs components itself.

## 3. Preset Package

The passive contribution that modifies normal Spec Kit lifecycle surfaces.

| Field | Type | Meaning |
|---|---|---|
| `id` | stable ID | `concorde-core`. |
| `version` | semantic version | Preset release version. |
| `template_layers` | four references | Append-composed spec, plan, and tasks guidance plus the replaced permanent design template. |
| `command_overrides` | nine references | Complete authoritative replacements for affected normal commands. |
| `priority` | integer | Precedence within the resolved preset stack. |
| `compatibility_map` | map | Per-command parity with Spec Kit 0.16.4 responsibilities. |

The preset owns no runtime command namespace. Its command sources invoke the extension-provided
workspace adapter before any path-sensitive phase action.

## 4. Preset Template Layer

| Field | Type | Meaning |
|---|---|---|
| `target` | enum | `spec-template`, `plan-template`, or `tasks-template`. |
| `strategy` | constant | `append`. |
| `source_path` | package-relative path | Maintained template contribution. |
| `content_digest` | SHA-256 | Exact contribution content. |

These layers add architecture guidance without redefining normal phase execution.

## 5. Preset Command Override

| Field | Type | Meaning |
|---|---|---|
| `command_id` | enum | One of the nine normal Spec Kit lifecycle commands. |
| `strategy` | constant | `replace`. |
| `source_path` | package-relative path | Complete maintained command source. |
| `phase_kind` | enum | `durable-intent-with-temporal-review` or `temporal`. |
| `required_root` | path rule | Feature root for durable intent reads/writes, with generated review state and all attempt work confined to `implementation/`. |
| `bootstrap_order` | invariant | Workspace resolution precedes every path-sensitive action. |
| `upstream_version` | version | Spec Kit command version reviewed for parity. |
| `source_digest` | SHA-256 | Exact replacement source. |

The nine IDs are:

- durable intent with temporal review: `speckit.specify`, `speckit.clarify`;
- temporal: `speckit.checklist`, `speckit.plan`, `speckit.tasks`, `speckit.implement`, `speckit.analyze`,
  `speckit.converge`, and `speckit.taskstoissues`.

Every generated requirements-quality file, including output produced while specifying or clarifying,
resolves below `implementation/checklists/`; a feature-root `checklists/` directory is invalid.

## 6. Extension Package

The active contribution containing new command intents and deterministic support code.

| Field | Type | Meaning |
|---|---|---|
| `id` | stable ID | `concorde`. |
| `version` | semantic version | Extension release version. |
| `commands` | six references | Init, feature create/select/harden, context, and validate. |
| `scripts` | declared file set | Platform launchers and workspace adapter. |
| `runtime` | declared file set | Project-local deterministic Concorde implementation. |
| `handoff_digest` | SHA-256 | Feature 001 handoff implemented by the package. |

All command dependencies resolve from the installed extension. Repository-local `.agents/`,
`.specify/`, tests, and source import paths are forbidden dependencies.

## 7. Release Artifact

| Field | Type | Meaning |
|---|---|---|
| `component_kind` | enum | Bundle, preset, or extension. |
| `component_id` | stable ID | Matches the archive manifest. |
| `version` | semantic version | Matches source and catalog. |
| `path` | build output path | Disposable release file under `dist/`. |
| `member_allowlist` | ordered paths | Exact permitted archive content. |
| `sha256` | digest | Artifact integrity. |
| `build_inputs_digest` | digest | Maintained sources used to build it. |

Artifacts are reproducible projections, not maintained intent.

## 8. Catalog Entry

Discovery and trust metadata for one independent release artifact.

| Field | Type | Meaning |
|---|---|---|
| `catalog_kind` | enum | Bundle, preset, or extension catalog. |
| `component_id` | stable ID | Package identity. |
| `version` | semantic version | Advertised release. |
| `download_url` | URL | Future archive location written from `--base-url`. |
| `sha256` | digest | Expected archive integrity. |
| `compatibility` | version constraint | Supported Spec Kit range. |
| `trust_metadata` | record | Policy inputs used by Spec Kit. |

The release builder writes the URL; it does not contact it.

## 9. Expanded Component Plan

The read-only result a maintainer accepts before installation.

| Field | Type | Meaning |
|---|---|---|
| `bundle` | identity/version/source | Recipe being installed. |
| `components` | ordered list | Exact preset and extension pins. |
| `preset_effects` | record | Priority, template strategies, and nine command replacements. |
| `integration` | inherited identity | Active target presentation. |
| `compatibility_findings` | list | Host or component constraints. |
| `trust_findings` | list | Source policy outcome. |
| `planned_changes` | ordered list | Registry and materialization effects. |
| `plan_digest` | SHA-256 | Accepted preview identity. |

The installed component identities and versions must equal the accepted plan.

## 10. Active Integration

The Spec Kit-selected adapter for agent-native presentation.

| Field | Type | Meaning |
|---|---|---|
| `id` | integration identity | Target project's active integration. |
| `presentation_family` | enum | Skills, slash commands, or another supported form. |
| `command_directory` | project-relative path | Materialization target owned by Spec Kit. |
| `renderer_version` | string | Presentation adapter version. |

It translates resolved command intent into presentation syntax. It does not own workflow behavior,
phase paths, or runtime semantics.

## 11. Resolved Command Surface

The winning instructions registered for one command after composition.

| Field | Type | Meaning |
|---|---|---|
| `canonical_command_id` | stable ID | One normal or Concorde-specific intent. |
| `winning_component` | component ID/version | Preset, extension, or restored lower layer. |
| `winning_source` | package-relative path | Maintained source of the selected layer. |
| `registered_path` | project-relative path | Materialized active-integration artifact. |
| `source_digest` | SHA-256 | Winning canonical source. |
| `materialized_digest` | SHA-256 | Rendered installed artifact. |
| `handoff_digest` | optional SHA-256 | Required for Concorde-owned surfaces. |
| `active` | boolean | Whether this is the current winner. |

Source text alone is not acceptance evidence; the materialized winner must execute the required
workspace bootstrap and phase outcome.

## 12. Clean Target Project

| Field | Type | Meaning |
|---|---|---|
| `root` | temporary absolute path | Must be outside the Concorde checkout. |
| `spec_kit_version` | version | Exactly supported host under test. |
| `integration` | Active Integration | Skills or slash-command fixture. |
| `environment_policy` | record | Sanitized import and command paths. |
| `source_access_log` | ordered paths | Files read during acceptance. |
| `fixture_kind` | enum | Clean initialized, clean uninitialized, or failure fixture. |

Any read from the Concorde checkout invalidates clean-target acceptance.

## 13. Command Surface Receipt

Deterministic evidence for one installed winning surface.

| Field | Type | Meaning |
|---|---|---|
| `command_id` | stable ID | Executed installed surface. |
| `registered_path` | project-relative path | Actual winning artifact. |
| `component_id` / `version` | identity | Package that supplied it. |
| `source_digest` / `materialized_digest` | digests | Provenance chain. |
| `handoff_digest` | digest | Feature 001 semantics being exercised. |
| `workspace_result` | paths | Selected feature root and implementation root. |
| `outputs` | ordered paths | Read/written artifacts. |
| `exit_status` | integer | Observable completion or failure. |
| `checkout_reads` | ordered paths | Must be empty. |

Receipts are generated validation evidence. They are not a new public command protocol.

## 14. Installation Record

| Field | Type | Meaning |
|---|---|---|
| `bundle_identity` | ID/version/source | Successful installed bundle. |
| `accepted_plan_digest` | digest | Preview accepted by the maintainer. |
| `components` | ownership records | Installed preset and extension provenance. |
| `materialized_surfaces` | references | Current resolved command surfaces. |
| `handoff_digest` | digest | Feature 001 semantics packaged by the release. |
| `status` | enum | Active, disabled, partial, or removed. |

The record is written only after the complete plan and command materialization succeed.

## 15. Feature Explanatory View

| Field | Type | Meaning |
|---|---|---|
| `source_path` | feature-relative path | Maintained Archify JSON under `diagrams/`. |
| `role` | enum | One `core` architecture view and zero or more `supplemental` dynamic views. |
| `kind` | enum | Component architecture or installation workflow. |
| `question_answered` | text | Static ownership or temporal invocation flow. |
| `textual_counterpart` | paths | Spec/contract prose that remains accessible authority. |
| `generated_output` | path | Reproducible HTML projection. |
| `source_digest` / `generator_version` | provenance | Freshness inputs. |
| `validation_receipt` | reference | Showcase, containment, theme, and publication evidence. |

These views are feature-owned explanations, not canonical module `architecture.json` views. For
Feature 003, the component model is core and the installation workflow is supplemental.

## State Transitions

### Release

```text
authored -> source-validated -> built -> cataloged -> acceptance-tested -> publishable
               |                 |            |
               └-- invalid ------┴-- mismatch ┴-- rejected
```

A release cannot become publishable without reproducible artifacts, catalog parity, a matching
Feature 001 handoff digest, and clean-target command receipts.

### Installation

```text
absent -> previewed -> accepted -> installing -> active
                         |            |          |-> disabled -> active
                         |            |          |-> updating -> active
                         |            |          |-> removing -> removed
                         |            └-> failed/rolled-back-or-partial
                         └-> declined
```

Update retains the previous successful record until the new plan is fully active. Removal preserves
shared components and project-authored sources.

### Command composition

```text
lower layer -> Concorde replacement wins -> materialized -> executed/receipted
                    | disable/reprioritize       | update/remove
                    v                            v
             keep registered winner       materialize accepted/next layer
             change future resolution           -> execute/receipted
```

## Invariants

1. One bundle version pins exactly one preset version and one extension version.
2. The preset has exactly three append-composed template layers and nine `replace` command layers.
3. The extension has exactly six Concorde-specific command intents and every referenced support
   file is present in its archive.
4. Every Concorde-owned resolved surface identifies one Feature 001 handoff digest.
5. Durable phases resolve the feature root; temporal phases resolve its single active
   `implementation/` workspace before any path-sensitive work.
6. No release artifact contains or depends on repository-local `.agents/`, root `.specify/`, tests,
   temporal feature design files, or generated documentation.
7. Preview and installation component identities/versions are identical.
8. No successful installation record exists after failed component or command materialization.
9. Install, update, disable, priority change, and removal preserve project-authored sources.
10. Disable and priority change preserve current registered artifacts; update/removal materializes
    the accepted or actual next surviving winner for all nine affected normal commands.
11. Clean acceptance has zero checkout reads and fails when any required archive member is absent.
12. Generated diagrams and receipts never become maintained behavioral authority.
