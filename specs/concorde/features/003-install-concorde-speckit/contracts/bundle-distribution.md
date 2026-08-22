# Contract: Concorde Starter Distribution

**Contract ID**: `contract.distribution.bundle-lifecycle`

**Format**: Spec Kit bundle, preset, extension, and catalog contracts

**Supported platform version**: Spec Kit 0.16.4

**Authoritative implementation references**:

- `spec-kit/src/specify_cli/bundler/models/manifest.py`
- `spec-kit/src/specify_cli/bundler/services/resolver.py`
- `spec-kit/src/specify_cli/bundler/services/installer.py`
- `spec-kit/extensions/EXTENSION-DEVELOPMENT-GUIDE.md`
- `spec-kit/presets/ARCHITECTURE.md`
- `spec-kit/docs/community/bundles.md`

## Purpose

Install, inspect, update, and remove Concorde through the same native component and bundle lifecycle
used by other Spec Kit ecosystem packages.

## Release Units

| Unit | Stable ID | Initial version | Required content |
|---|---|---:|---|
| Bundle | `concorde-starter` | `0.1.0` | One preset reference and one extension reference only. |
| Preset | `concorde-core` | `0.1.0` | Append-only spec, plan, and task template contributions. |
| Extension | `concorde` | `0.1.0` | Five workflow commands, phase-path adapter, and project-local runtime. |

Every version above is independently authoritative in its own manifest and matching catalog entry.
The bundle pins the exact preset and extension versions it has passed acceptance with.

## Role and Authority Boundary

| Role | Authority in the workflow |
|---|---|
| Spec Kit | Resolves catalogs and components, composes templates, selects the active integration, mutates projects, and owns registry/provenance lifecycle. |
| Catalog | Advertises identity, version, download location, compatibility, digest, and trust metadata; it does not contain behavior. |
| Bundle | Pins the accepted preset and extension as a non-executable recipe; it does not embed or install them itself. |
| Preset | Passively appends guidance during normal Spec Kit template resolution; it registers no command and owns no runtime. |
| Extension | Actively supplies portable commands and the deterministic runtime they invoke. |
| Active integration | Renders/registers portable commands using agent-native presentation and invocation syntax; it does not own behavior. |
| Architecture Core | Owns deterministic initialization, bounded context, and validation behavior behind the extension commands. |

The root platform and starter-workflow contracts own this cross-module meaning. This distribution
contract specializes it for packaging, catalog resolution, and lifecycle behavior.

## Bundle Manifest Profile

The root `bundle.yml` must contain:

```yaml
schema_version: "1.0"

bundle:
  id: "concorde-starter"
  name: "Concorde Starter"
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
| Build | Bundle source directory | Reproducible `concorde-starter-<version>.zip`. |
| Info | Catalog bundle ID | Full component plan, pins, priority, strategy, compatibility, integration inheritance, source, trust, and overlaps. |
| Install | Bundle ID, directory, manifest, or artifact | Apply exactly the resolved plan and record only attributable components after full success. |
| List/status | Initialized project | Bundle version and contributed component provenance; primitive registries expose component active/disabled state. |
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

## Failure Semantics

- Invalid manifests, incompatible Spec Kit versions, missing components, catalog trust refusal, pin
  mismatch, integration registration failure, or unsafe paths stop with non-zero status.
- Installation rolls back components newly installed in that attempt in reverse order.
- Previously installed or shared components are not rolled back as if they were newly owned.
- Update retains the prior successful record unless the complete new plan succeeds; any incomplete
  primitive mutation is reported.

## Compatibility

The initial contract is tested only with Spec Kit 0.16.4. Expanding the manifest range requires the
full clean-project lifecycle and both agent-registration suites to pass against every added version.
Changing stable component or command IDs is a breaking Concorde change.
