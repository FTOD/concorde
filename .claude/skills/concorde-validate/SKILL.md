---
name: concorde-validate
description: "Deterministically validate module-centered Concorde sources"
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-validate/SKILL.md"
  kind: "skill"
  exposure: "public"
user-invocable: true
disable-model-invocation: false
---
# Validate Concorde

Run `python3 scripts/concorde.py validate $ARGUMENTS --format json` from the project root.

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
- one Archify `architecture` system overview per module showing principal entities and directed
  relationships, plus architecture-owned diagram textual linkage, showcase profile, hidden legends,
  safe unique outputs, provenance, and freshness; and
- stable-ID `.concorde/attempts/<feature-id>/` isolation, per-file `.concorde/reflections/<bucket>/R-NNN.md` grammar and allocation index,
  project-control path safety, generated-source boundaries, and complete
  rejection of obsolete durable layout residue.

For every finding, show stable code, severity, source path/field, message, and remediation. This
Tool never repairs or migrates a project.

After structural validation succeeds, run Archify showcase validation for every declared system
overview. Require the nine artifact checks, zero composition errors, and zero warnings; a basic
four-check receipt is not acceptance. Report structural and Archify results separately.

## Semantic review boundary

Report structural validation separately from semantic architecture review. A successful check does
not prove that core concepts, cardinality/lifetime rules, or producer-to-consumer payload mappings
are complete, nor that target JSON Operation contracts are implemented. Name those limits in the
report and preserve the validation Tool's actual result.
