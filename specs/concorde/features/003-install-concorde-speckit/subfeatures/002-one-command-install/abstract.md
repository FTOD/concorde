# Feature Abstract: One-Command Installation

`feature.concorde.install-with-spec-kit.one-command-install` · specified at `module.concorde` ·
sub-feature of `feature.concorde.install-with-spec-kit` · about three minutes. This page is enough
to understand what the installer does and what it must never do; the links at the end only redirect
you when you want more.

## Purpose

A maintainer with nothing but a shell and network access turns a new or existing directory into a
Concorde-enabled Spec Kit project with one command, and the result is byte-for-byte the component
and native agent state produced by the parent's manual bundle-plus-projector path. It serves the
first-time maintainer who should not need a checkout, build, local server, or manual agent copying,
and the Concorde developer who wants the identical sequence against a local checkout.

## Functionality

The installer uses public Spec Kit commands for project/components, then invokes only the
deterministic agent projector supplied by the installed extension. The equivalent manual path is
documented; Spec Kit 0.16.4 simply lacks this native custom-agent primitive.

| Mode | What happens |
|---|---|
| Install | Obtains Spec Kit if absent, initializes when needed, registers catalogs, installs/updates the bundle, then previews, synchronizes, and verifies native Claude or Codex triage skill/roles from the installed extension. |
| Re-run | Preserves integration, components, shared triage state, inactive/modified/unrelated agent files, and authored sources; current components/projections change no bytes; conflicts stop before false success. |
| Preview | Prints public operations, release/component versions, native agent targets/digests/actions/conflicts, and writes nothing. |
| Development | Builds/verifies a checkout, serves catalogs only for the run, installs through the same bundle path, projects from the installed copy, and cleans up. |

The final report names versions, projection/receipt verification, reload need, and the Concorde
workflow as the next step. The installer remains plain, inspectable text.

**Not part of this feature**: what gets installed, Spec Kit's authority over the component lifecycle,
the inspect-before-install rule, Feature 005's triage behavior, the clean-project verification
matrix, user permission policy, and installing the preset or extension individually.

## Structure

The parent's supplemental <a href="/architecture/concorde-bundle-installation-flow.html">bundle
installation flow</a> (maintained source `../../diagrams/bundle-installation-flow.json`) already
shows the ordered stages the installer sequences; the core
<a href="/architecture/concorde-spec-kit-component-model.html">Spec Kit component model</a> shows
the components it installs.

```text
one command (target dir, integration) ──▶ obtain pinned Spec Kit CLI ──▶ init project (if needed)
     ──▶ register 3 catalogs (published release, or a checkout served for this run only)
     ──▶ install concorde-bundle through Spec Kit ──▶ preview/sync/verify installed agent assets
     ──▶ run report: versions · projection receipt · reload? · next: the workflow
```

The default version resolves through the sibling publication feature's stable locations; the
install itself is the Distribution module's bundle lifecycle. No realization is accepted yet.

## Logic

**One run**

1. Resolve the release: the current published release by default, an explicit version, or a local
   checkout in development mode.
2. Obtain the pinned Spec Kit CLI when it is missing.
3. Initialize the target only if it is not already a Spec Kit project.
4. Register the three catalogs and install the bundle natively; in preview mode, print this plan and
   include the agent-projection plan and stop.
5. Invoke the installed projector for the active integration: preview conflicts, synchronize only
   owned targets, and verify output/receipt digests.
6. Report versions, projection status, reload requirement, and next step; any failure stops before claiming
   success and names stage, remediation, and residual state.

**Rules the implementation must keep**

- One command from a public location, with at most the target directory and integration as required
  inputs (FR-001).
- Public Spec Kit operations own project/components; only the installed extension projector may
  generate native agent files, and the manual bundle-plus-projector path stays documented (FR-002,
  FR-014).
- The pinned Spec Kit CLI is obtained without the checkout, a project-specific virtual environment,
  or changes to other projects (FR-003).
- Initialization happens only for a non-project target; existing integration, components, and
  authored sources are preserved (FR-004).
- The three catalogs are registered and the bundle installed through the native lifecycle, never the
  preset or extension individually (FR-005).
- Repeated runs are idempotent across registries, commands, projections, receipt, and shared state
  (FR-006, FR-016).
- The default is the current published release; an explicit version is accepted; both resolve
  through the publication feature's stable locations (FR-007).
- Preview prints component and agent projection paths/digests/actions/conflicts and writes nothing
  (FR-008).
- Development mode builds, verifies, serves for the run only, installs through the same bundle path,
  and cleans up (FR-009).
- Failures stop before success and name the stage, remediation, and partial state; the report names
  versions, reload need, and the workflow; the installer is inspectable text; integration conflicts,
  unsupported versions, and unreachable releases give the native diagnostics (FR-010, FR-011,
  FR-012, FR-013).
- Projection creates exactly three model-neutral native outputs, uses digest ownership for
  update/removal, and preserves legacy/modified/inactive/user state unless explicitly adopted
  (FR-015 to FR-019).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): four user stories,
  FR-001 to FR-019, and SC-001 to SC-008.
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md) (a
  placeholder until a realization is accepted).
- **The parent** — [abstract](../../abstract.md) and [design.md](../../design.md) of
  `feature.concorde.install-with-spec-kit`, with its
  `../../contracts/bundle-distribution.md` contract; the sibling
  [publish-release](../001-publish-release/design.md) whose current-release pointer this installer
  reads (`../001-publish-release/contracts/release-publication.md`).
- **The level this feature belongs to** — [module.md](../../../../module.md) (the root summary) and
  [Distribution](../../../../architecture/modules/distribution/module.md).
- **The documented install paths** — [docs/quick-start.md](../../../../../../docs/quick-start.md).
