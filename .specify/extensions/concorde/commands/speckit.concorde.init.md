---
description: "Propose and explicitly apply a root module-centered Concorde hierarchy"
---

# Initialize Concorde

Treat `$ARGUMENTS` as optional `--module-id` and `--name` values. Invoke the installed launcher from
the target project:

- POSIX: `.specify/extensions/concorde/scripts/bash/concorde.sh init --propose $ARGUMENTS`
- PowerShell: `.specify/extensions/concorde/scripts/powershell/concorde.ps1 init --propose $ARGUMENTS`

The Initialization Proposal 2 must select Architecture Source Profile 7 and create exactly
`.concorde/config.json`, `.concorde/reflections/log.md`, and one root `architecture.md`. The
architecture seed defines the root responsibility/boundary, immediate module and feature inventories,
typed entity vocabulary, directed relationship vocabulary, representative interactions, and any
external/conceptual locators. Do not invent product modules from Concorde's own implementation roles.

Any maintained diagram seed belongs to the module's `diagrams/`, has a textual counterpart in
`architecture.md`, uses `meta.legend.mode: hidden`, and declares one normalized unique generated
output. Initialization creates no attempt. A later feature is one direct `features/<NNN-name>.md`
file with embedded interface and Architecture Zoom sections. Only after its stable front-matter ID
exists may temporal work map to `.concorde/attempts/<stable-feature-id>/`; never infer the ID from
its filename.

If status is `unchanged`, report the existing profile, root architecture, immediate modules,
features, and findings; do not compare the project with starter prose or overwrite it. If status is
`proposal`, present exact files, digests, conflicts, and the complete JSON proposal. Silence is not
approval. After the maintainer explicitly accepts and saves that exact proposal at a safe
project-relative path, invoke `init --apply --proposal <path>`.

Never edit maintained architecture outside the accepted runtime operation. Preserve exit status and
report all findings, created paths, retained project files, and resulting source digest.
