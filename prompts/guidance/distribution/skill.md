---
audience: shared
---

## Installed parts and updates

`concorde` is the `.concorde/bin/concorde` command of the worktree you are in (in Concorde's own
source checkout `python3 scripts/concorde.py`), composed of the Concorde parts the project
installed, which the receipt `.concorde/install.json` names under `parts`. This guidance holds the
sections of those parts alone, and the project MCP server `concorde` presents only their tools: a
command or tool of a part that is not installed is refused with `part_missing`, naming the part.
Never work around it; tell the developer, who may install that part with `concorde update --parts
<part>`, which adds it with the parts it depends on.

Update Concorde only when the developer asks, with `concorde update` in the primary worktree, in
background Bash. It installs the parts the receipt names again from the Concorde checkout the
receipt names as its `source` (or `--from <checkout>`), and refuses with `concorde_busy` while a run
of the project still runs. Start no other `concorde` command, in any worktree of the project, until
it ends. Where the spec part is installed, it binds the new Protocol copy and marks the project
Concorde unvalidated until `concorde spec-validation` finds no other error; its result lists the
open tasks of the project where the coordination part is installed.
