---
name: concorde-init
description: "Propose and explicitly apply a root module-centered Concorde hierarchy"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-init/SKILL.md"
  kind: "skill"
  exposure: "public"
---
# Initialize Concorde

Treat `$ARGUMENTS` as optional `--module-id` and `--name` values. From the target project run
`python3 scripts/concorde.py init --propose $ARGUMENTS`.

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
project-relative path, invoke `python3 scripts/concorde.py init --apply --proposal <path>`.

## Project docsite

When the maintainer asks for a project docsite, or `$ARGUMENTS` includes `--docsite`, run the
scaffold only after the configured root architecture exists (status `unchanged` or a just-applied
proposal). From the project root run
`python3 ./scripts/concorde.py --project-root . docsite --propose` with any explicit
`--title`, `--repository`, `--url`, `--base-url`, or `--github-pages` values. Present the Docsite
Scaffold Proposal 1: every path with its digest, the derived site identity, conflicts, and
prerequisite findings (Node.js 20+, npm, the pinned Archify skill). Silence is not approval. After
the maintainer explicitly accepts and saves that exact proposal at a safe project-relative path,
invoke `python3 ./scripts/concorde.py --project-root . docsite --apply --proposal <path>`.
The scaffold copies the packaged adapter, writes only `docsite/site.json` as project identity, adds
a minimal `README.md` only when none exists, never overwrites an existing `docsite/`, and installs
nothing; `npm ci` and `npm run check` in `docsite` remain the maintainer's steps.

Never edit maintained architecture outside the accepted Runtime Tool. Preserve exit status and
report all findings, created paths, retained project files, and resulting source digest.
