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

Present the complete JSON proposal, exact files, hashes, and conflicts. Do not interpret silence as
approval. After the maintainer explicitly accepts and the exact proposal JSON has been saved at a
project-relative path, invoke `init --apply --proposal <path>`. Never edit maintained architecture
outside that accepted operation. Report every finding and preserve the runtime status.