---
audience: shared
---

## Installed parts and updates

`concorde` is the `.concorde/bin/concorde` command of the worktree you are in. In Concorde's own
source checkout, the command is `python3 scripts/concorde.py`. The command is composed of the Concorde
parts the project installed. The receipt `.concorde/install.json` names those parts under `parts`.
This guidance holds the sections of those parts alone. The project MCP server `concorde` presents
only their tools. When a part is not installed, a command or tool of that part is refused with
`part_missing`. The refusal names the part. Never work around it. Tell the developer. The developer
may install that part with `concorde update --parts
<part>`. The command adds that part with the parts it depends on.

Update Concorde only when the developer asks. Run `concorde update` in the primary worktree, in
background Bash.

The update installs the parts the receipt names again. It installs them from the Concorde checkout
the receipt names as its `source` (or `--from <checkout>`). While a run of the project still runs,
the update refuses with `concorde_busy`. Until the update ends, start no other `concorde` command in
any worktree of the project.

Where the spec part is installed, the update binds the new Protocol copy. Where the spec part is
installed, it also marks the project Concorde unvalidated until `concorde spec-validation` finds no
other error.

Where the coordination part is installed, the update's result lists the open tasks of the project.
