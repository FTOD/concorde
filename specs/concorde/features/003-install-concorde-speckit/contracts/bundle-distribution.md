# Contract: Concorde Bundle Distribution

**Contract ID**: `contract.distribution.bundle-lifecycle`

**Format**: Spec Kit bundle, preset, extension, and catalog contracts

**Supported platform version**: Spec Kit 0.16.4

**Authoritative implementation references**:

- [bundle manifest model](https://github.com/github/spec-kit/blob/v0.16.4/src/specify_cli/bundler/models/manifest.py)
- [bundle resolver](https://github.com/github/spec-kit/blob/v0.16.4/src/specify_cli/bundler/services/resolver.py)
- [bundle installer](https://github.com/github/spec-kit/blob/v0.16.4/src/specify_cli/bundler/services/installer.py)
- [extension development guide](https://github.com/github/spec-kit/blob/v0.16.4/extensions/EXTENSION-DEVELOPMENT-GUIDE.md)
- [preset architecture](https://github.com/github/spec-kit/blob/v0.16.4/presets/ARCHITECTURE.md)
- [bundle documentation](https://github.com/github/spec-kit/blob/v0.16.4/docs/community/bundles.md)

## Purpose

Install, inspect, update, and remove Concorde through the same native component and bundle lifecycle
used by other Spec Kit ecosystem packages.

## Release Units

| Unit | Stable ID | Initial version | Required content |
|---|---|---:|---|
| Bundle | `concorde-bundle` | `0.1.0` | One preset reference and one extension reference only. |
| Preset | `concorde-core` | `0.1.0` | Four template contributions and authoritative layers for nine existing lifecycle commands. |
| Extension | `concorde` | `0.1.0` | Five Concorde-specific surfaces: four runtime-backed operations, one agent-followed `ask` procedure, selected-workspace adapter, and project-local runtime. |

Every version above is independently authoritative in its own manifest and matching catalog entry.
The bundle pins the exact preset and extension versions it has passed acceptance with.

## Role and Authority Boundary

| Role | Authority in the workflow |
|---|---|
| Spec Kit | Resolves catalogs and components, composes templates, selects the active integration, mutates projects, and owns registry/provenance lifecycle. |
| Catalog | Advertises identity, version, download location, compatibility, digest, and trust metadata; it does not contain behavior. |
| Bundle | Pins the accepted preset and extension as a non-executable recipe; it does not embed or install them itself. |
| Preset | Composes templates and overrides existing lifecycle command instructions. It introduces no new runtime command namespace and owns no runtime; Spec Kit registers the resolved command layer. |
| Extension | Actively supplies five Concorde-specific command intents: four invoke the selected-workspace adapter or deterministic runtime, while `ask` is agent-followed, source-grounded, and read-only. |
| Active integration | Materializes both resolved normal-command overrides and Concorde-specific commands using agent-native presentation and invocation syntax; it does not own behavior or path semantics. |
| Architecture Core / workspace runtime | Own deterministic initialization, bounded context, validation, feature workspace, and hardening behavior behind the extension commands. |

The root platform and workflow-composition contracts own this cross-module meaning. This distribution
contract specializes it for packaging, catalog resolution, and lifecycle behavior.

## Bundle Manifest Profile

The root `bundle.yml` must contain:

```yaml
schema_version: "1.0"

bundle:
  id: "concorde-bundle"
  name: "Concorde Bundle"
  version: "0.1.0"
  role: "developer"
  description: "Concorde installation and setup components"
  author: "Concorde maintainers"
  license: "MIT"

requires:
  speckit_version: ">=0.16.4,<0.16.5"
  tools: []
  mcp: []

provides:
  extensions:
    - id: "concorde"
      version: "0.1.0"
  presets:
    - id: "concorde-core"
      version: "0.1.0"
      priority: 10
      strategy: "append"
  steps: []
  workflows: []

tags: ["architecture", "context", "validation", "spec-driven-development"]
```

The absence of an `integration` field is normative: Concorde inherits the target project's active
integration.

The bundle-level preset `strategy: append` describes how the preset participates in the target's
preset stack. It does not force every entry inside that preset to use append composition. The
`concorde-core` manifest keeps its three inherited template entries as `append`, adds the
Concorde-only `abstract-template` (the feature abstract that `speckit.specify` authors at a new feature
root) and `implementation-template` (the placeholder feature `design.md`) as `replace`, and declares each of
the nine path-sensitive command entries as `replace`, as required below. The preset and extension
that carry the six templates, Feature Workspace Protocol v6, and Architecture Source Profile 3 are
their 0.3.0 releases, which the bundle pins; preset 0.2.0 carried an `implementation-template`
instead, and preset 0.1.0 a `implementation-template` without a abstract.

## Installed Command Surface Profile

The released preset owns Concorde's modifications to these existing Spec Kit command surfaces:

| Artifact authority | Commands | Required location behavior |
|---|---|---|
| Durable feature intent plus temporal review state | `speckit.specify`, `speckit.clarify` | Resolve the selected nested feature before reading or writing root `design.md` or contracts, and write generated requirements-quality state only under `attempt/checklists/`. |
| Temporal implementation workspace | `speckit.checklist`, `speckit.plan`, `speckit.tasks`, `speckit.implement`, `speckit.analyze`, `speckit.converge`, `speckit.taskstoissues` | Resolve the selected feature's single active `attempt/` directory before writing checklists, plan, task, research, implementation-model, or delivery evidence. |

The released extension owns these five new command intents: `speckit.concorde.init`,
`speckit.concorde.feature.harden`, `speckit.concorde.context`, `speckit.concorde.validate`, and
`speckit.concorde.ask`. The first four are runtime-backed; `ask` is an agent-followed read-only
procedure with no launcher or runtime verb. Feature creation and selection are standard Spec Kit
behavior (`speckit.specify` with `SPECIFY_FEATURE_DIRECTORY`, and `.specify/feature.json`) that the
extension's workspace adapter resolves; they are not extension intents.
Platform-safe registered spellings may replace dots inside the final
operation name, but the canonical intent and behavior remain unchanged.

For every path-sensitive normal command, the winning installed instructions MUST establish the
selected workspace before invoking any inherited step that assumes a root-level plan or task path.
Merely appending corrective text after such a step is non-conforming. Command composition MUST use
Spec Kit's public preset command contract; the bundle MUST NOT depend on arbitrary replacement of
installed Spec Kit core scripts.

Repository-local `.agents/` and `.specify/` content is self-hosting state, not a release unit. Clean
acceptance installs the built bundle and catalogs into an isolated target and denies access to the
source checkout.

## Catalog and Trust Requirements

- Bundle, preset, and extension artifacts are separate reproducible archives.
- The bundle README lists the required component catalog URLs and their installation policy.
- `--base-url` is build input used to write later archive locations into generated catalog metadata;
  the release builder does not contact it. Local acceptance starts its HTTP server after building.
- Release URLs use HTTPS. Local acceptance may use an HTTP localhost server, which Spec Kit permits.
- Installation by bundle catalog ID is allowed only when the bundle catalog source is
  `install-allowed`.
- Component references resolve from active install-allowed component catalogs or an already installed
  component that is safely owned by another bundle.
- Catalog ID, version, download URL, and archive manifest must agree. Digest verification is required
  when the catalog contract supplies a digest.

## Operations

| Operation | Input | Required observable result |
|---|---|---|
| Validate | Bundle source directory or `bundle.yml` | Structural and component-reference findings; no project mutation. |
| Build | Bundle source directory | Reproducible `concorde-bundle-<version>.zip`. |
| Info | Catalog bundle ID | Full component plan, pins, priority, strategy, compatibility, integration inheritance, source, trust, and overlaps. |
| Install | Bundle ID, directory, manifest, or artifact | Apply exactly the resolved plan and record only attributable components after full success. |
| List/status | Initialized project | Bundle version and contributed component provenance; primitive registries expose component active/disabled state. |
| Verify command surfaces | Installed bundle and active integration | Execute the nine composed normal commands and four runtime-backed Concorde intents, inspect and semantically review `ask`, and prove the durable/temporal path matrix and cross-integration equivalence. |
| Update | Installed bundle ID | Preview/resolve new plan, reapply owned components, preserve configuration and architecture sources. |
| Remove | Installed bundle ID | Remove only solely owned components and the bundle record; retain shared components and project sources. |

## Guarantees

1. `info` and `install` resolve the same ordered component list for the same catalog state.
2. Compatibility is checked before project mutation.
3. Repeating the same install does not duplicate registry entries or touch project-authored sources.
4. A component installed independently before the bundle is not adopted as bundle-owned.
5. A component used by another installed bundle remains after Concorde removal.
6. The bundle never removes `.concorde/`, `specs/`, `docs/`, or other user-authored
   sources.
7. A failed install or update does not write a successful bundle record.
8. Residual partial state that cannot be rolled back is named in the diagnostic.
9. Disabling or reprioritizing the preset preserves already registered command surfaces while
   changing future resolution, as Spec Kit 0.16.4 specifies; update/removal materializes the accepted
   or next surviving layer without stale Concorde instructions.
10. Presence of expected text in a registered command is not sufficient evidence; the installed
    winning artifact must execute with the required selected-workspace behavior.

## Failure Semantics

- Invalid manifests, incompatible Spec Kit versions, missing components, catalog trust refusal, pin
  mismatch, command composition/materialization failure, integration registration failure, or unsafe
  paths stop with non-zero status.
- Installation rolls back components newly installed in that attempt in reverse order.
- Previously installed or shared components are not rolled back as if they were newly owned.
- Update retains the prior successful record unless the complete new plan succeeds; any incomplete
  primitive mutation is reported.

## Compatibility

The initial contract is tested only with Spec Kit 0.16.4. Expanding the manifest range requires the
full clean-project lifecycle and both agent-registration suites to pass against every added version.
Changing stable component or command IDs is a breaking Concorde change.
