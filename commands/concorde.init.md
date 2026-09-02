---
description: "Propose and explicitly apply a root module-centered Concorde hierarchy"
scripts:
  py: scripts/concorde.py init
---

# Initialize Concorde

Treat `$ARGUMENTS` as optional `--module-id` and `--name` values. From the target project run
`{SCRIPT} --propose $ARGUMENTS`.

The Initialization Proposal 3 must select Architecture Source Profile 7 and create exactly
`.concorde/config.json`, `.concorde/reflections/log.md`, one root `architecture.md`, and its
`diagrams/system-overview.json`. The
architecture seed defines the root responsibility/boundary, immediate module and feature inventories,
typed entity vocabulary, directed relationship vocabulary, representative interactions, and any
external/conceptual locators. Do not invent product modules from Concorde's own implementation roles.

The system overview is a required Archify `architecture` source that shows the principal entities and
directed relationships from the root architecture. It belongs to the module's `diagrams/`, has a
textual counterpart in `architecture.md`, uses `meta.quality_profile: showcase` and
`meta.legend.mode: hidden`, and declares one normalized unique generated output. Run Archify showcase
validation on the proposal's diagram before presenting it; do not accept a basic four-check receipt.
Initialization creates no attempt. A later feature is one direct `features/<NNN-name>.md`
file with embedded interface and Architecture Zoom sections. Only after its stable front-matter ID
exists may temporal work map to `.concorde/attempts/<stable-feature-id>/`; never infer the ID from
its filename.

If status is `unchanged`, report the existing profile, root architecture, immediate modules,
features, system overview, and findings; do not compare the project with starter prose or overwrite it. If status is
`proposal`, present exact files, digests, conflicts, and the complete JSON proposal. Silence is not
approval. After the maintainer explicitly accepts and saves that exact proposal at a safe
project-relative path, invoke `{SCRIPT} --apply --proposal <path>`.

Never edit maintained architecture outside the accepted runtime operation. Preserve exit status and
report all findings, created paths, retained project files, and resulting source digest.
