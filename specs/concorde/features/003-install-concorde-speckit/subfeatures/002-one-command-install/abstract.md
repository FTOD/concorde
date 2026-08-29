# Feature Abstract: One-Command Installation

`feature.concorde.install-with-spec-kit.one-command-install` · specified at `module.concorde` ·
sub-feature of `feature.concorde.install-with-spec-kit` · about three minutes. This page is enough
to understand what the installer does and what it must never do; the links at the end only redirect
you when you want more.

## Purpose

A maintainer with nothing but a shell and network access turns a new or existing directory into a
Concorde-enabled Spec Kit project with one command, and the result is byte-for-byte the component
set the parent's native step-by-step Spec Kit path produces. It serves the first-time
maintainer who should not need a checkout, a build, a local server, and eight commands, and the
Concorde developer who wants the identical sequence against a local checkout.

## Functionality

The installer is an optional accelerator: every step it performs remains a documented public Spec
Kit command, so the parent's "no separate installer is required" rule holds.

| Mode | What happens |
|---|---|
| Install | Obtains the pinned Spec Kit CLI if absent, initializes the target as a Spec Kit project only when it is not one already, registers the release's three catalogs, and installs the bundle through the native bundle lifecycle. |
| Re-run | Preserves the existing integration, components, and authored sources; an already current installation changes no bytes; an older version is previewed and updated through the native update path; a different integration stops with a named conflict. |
| Preview | Prints the ordered public operations, release version, and pinned component versions, and writes nothing. |
| Development | Takes a local Concorde checkout, builds and verifies its release, serves its catalogs only for the run, installs through the same bundle path, and cleans up. |

The final report names the installed versions, whether the coding agent must be reloaded, and the
Concorde workflow as the next step. The installer is plain, readable text a maintainer can inspect
before running.

**Not part of this feature**: what gets installed, Spec Kit's authority over the component lifecycle,
the inspect-before-install rule, the clean-project verification matrix, and installing the preset
or extension individually.

## Structure

The parent's supplemental <a href="/architecture/concorde-bundle-installation-flow.html">bundle
installation flow</a> (maintained source `../../diagrams/bundle-installation-flow.json`) already
shows the ordered stages the installer sequences; the core
<a href="/architecture/concorde-spec-kit-component-model.html">Spec Kit component model</a> shows
the components it installs.

```text
one command (target dir, integration) ──▶ obtain pinned Spec Kit CLI ──▶ init project (if needed)
     ──▶ register 3 catalogs (published release, or a checkout served for this run only)
     ──▶ install concorde-bundle through Spec Kit ──▶ run report: versions · reload? · next: the workflow
```

The default version resolves through the sibling publication feature's stable locations; the
install itself is the Distribution module's bundle lifecycle. No realization is hardened yet.

## Logic

**One run**

1. Resolve the release: the current published release by default, an explicit version, or a local
   checkout in development mode.
2. Obtain the pinned Spec Kit CLI when it is missing.
3. Initialize the target only if it is not already a Spec Kit project.
4. Register the three catalogs and install the bundle natively; in preview mode, print this plan and
   stop.
5. Report versions, the reload requirement, and the next step; any failure stops before claiming
   success and names stage, remediation, and residual state.

**Rules the implementation must keep**

- One command from a public location, with at most the target directory and integration as required
  inputs (FR-001).
- Only public Spec Kit operations; the installer never copies, edits, or generates component files,
  and the native path stays documented and sufficient (FR-002).
- The pinned Spec Kit CLI is obtained without the checkout, a project-specific virtual environment,
  or changes to other projects (FR-003).
- Initialization happens only for a non-project target; existing integration, components, and
  authored sources are preserved (FR-004).
- The three catalogs are registered and the bundle installed through the native lifecycle, never the
  preset or extension individually (FR-005).
- Repeated runs are idempotent: no byte changes when current, no duplicated registrations (FR-006).
- The default is the current published release; an explicit version is accepted; both resolve
  through the publication feature's stable locations (FR-007).
- Preview prints the complete ordered plan with versions and writes nothing (FR-008).
- Development mode builds, verifies, serves for the run only, installs through the same bundle path,
  and cleans up (FR-009).
- Failures stop before success and name the stage, remediation, and partial state; the report names
  versions, reload need, and the workflow; the installer is inspectable text; integration conflicts,
  unsupported versions, and unreachable releases give the native diagnostics (FR-010, FR-011,
  FR-012, FR-013).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): four user stories,
  FR-001 to FR-013, and SC-001 to SC-006.
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md) (a
  placeholder until a realization is hardened).
- **The parent** — [abstract](../../abstract.md) and [design.md](../../design.md) of
  `feature.concorde.install-with-spec-kit`, with its
  `../../contracts/bundle-distribution.md` contract; the sibling
  [publish-release](../001-publish-release/design.md) whose current-release pointer this installer
  reads (`../001-publish-release/contracts/release-publication.md`).
- **The level this feature belongs to** — [module.md](../../../../module.md) (the root summary) and
  [Distribution](../../../../architecture/modules/distribution/module.md).
- **The documented install paths** — [docs/quick-start.md](../../../../../../docs/quick-start.md).
