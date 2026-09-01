---
name: speckit-concorde-validate
description: Deterministically validate module-centered Concorde sources
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: concorde:commands/speckit.concorde.validate.md
---

# Validate Concorde

Run the installed project-relative launcher with optional target `$ARGUMENTS`:

- POSIX: `.specify/extensions/concorde/scripts/bash/concorde.sh validate $ARGUMENTS --format json`
- PowerShell: `.specify/extensions/concorde/scripts/powershell/concorde.ps1 validate $ARGUMENTS --format json`

Present the canonical status, complete sorted findings, source digest, and summary. Preserve exit
codes: success 0, invalid 1, conflict 2, and failed 3. Do not hide errors, modify sources, or
reinterpret `unknown` evidence as agreement.

Validation covers Architecture Source Profile 7:

- a recursive acyclic module tree with one `architecture.md` per module and canonical immediate
  `modules/`, level-local `features/`, and architecture-owned `diagrams/` placement;
- unique stable module, feature, entity, relationship, interaction, and interface identities;
- required module responsibility/boundary/inventories plus entity type, definition, locator, and
  visible relationship endpoints;
- parent architectures exposing child modules as bounded entities without copying child internals;
- one direct `features/<NNN-name>.md` file per feature, no wrapper directory, and no feature containment;
- complete embedded interface semantics and implementing-entity resolution;
- Architecture Zoom references resolving through the providing module's permitted ancestry without
  redefining entity identity or ownership;
- architecture-owned diagram textual linkage, hidden legends, safe unique outputs, provenance, and
  freshness; and
- stable-ID `.concorde/attempts/<feature-id>/` isolation, `.concorde/reflections/log.md` grammar,
  project-control path safety, generated-source boundaries, and complete
  rejection of obsolete durable layout residue.

For every finding, show stable code, severity, source path/field, message, and remediation. This
command never repairs or migrates a project.