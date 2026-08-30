---
name: speckit-concorde-init
description: Propose and explicitly apply a root Concorde specification hierarchy
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: concorde:commands/speckit.concorde.init.md
---

# Initialize Concorde

Treat `$ARGUMENTS` as optional `--module-id` and `--name` values. Run the installed launcher relative
to the project:

- POSIX: `.specify/extensions/concorde/scripts/bash/concorde.sh init --propose $ARGUMENTS`
- PowerShell: `.specify/extensions/concorde/scripts/powershell/concorde.ps1 init --propose $ARGUMENTS`

Treat the skill as the maintainer-facing interface, the launcher/runtime as supporting Scripts, and
the proposed or existing project sources as Workspace Files. Explain the returned `interaction_model`:
durable module and feature sources stay outside `attempt/`, current delivery memory stays below the
selected feature's `attempt/`, and generated projections never become source authority. These are
workflow roles; do not invent product modules named Skills, Scripts, or Workspace Files unless the
project itself provides those product responsibilities.

The proposed seed level view explicitly sets `meta.legend.mode` to `hidden`, matching the Concorde
policy for every maintained Archify diagram. Treat a proposal that omits that setting as invalid.

If the status is `unchanged`, report the existing `architecture` paths, children, features, and
contracts. Do not present a new starter proposal or overwrite the configured hierarchy. If the status
is `proposal`, present the complete JSON proposal, exact files, hashes, and conflicts. Do not
interpret silence as approval. After the maintainer explicitly accepts and the exact proposal JSON
has been saved at a project-relative path, invoke `init --apply --proposal <path>`. Never edit
maintained architecture outside that accepted operation. Report every finding and preserve the
runtime status.