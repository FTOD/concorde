# Decision log: session-mcp-approval

Goal: A task session never stalls on Claude Code's approval dialog for the project's .mcp.json servers: its settings disable the project's concorde entry, which the --mcp-config server replaces, carry over the primary worktree's approvals for the other .mcp.json servers and disable those never approved

## Brief (main agent, 2026-10-01)

### Developer's decision

The developer approved this fix after the main agent reproduced the defect: a task session's
settings disable the project `.mcp.json` entry `concorde`; the other `.mcp.json` servers keep the
approval the primary worktree already gave them, and a server never approved there is disabled
instead of prompting, since nobody answers a prompt in a background session.

### What the main agent established (Claude Code 2.1.285, live probes on 2026-10-01)

- `claude --bg` in a project whose repository root is trusted but whose `.mcp.json` server
  `concorde` was never approved stops at "New MCP server found in this project: concorde … Use
  this MCP server / Use this and all future MCP servers in this project / Continue without using
  this MCP server", in the primary directory and in its worktree alike, although `--mcp-config`
  also passes a server `concorde`. Seen for real in `/tmp/concorde-e2e/requests-5414` (trusted,
  no approval recorded), which a main agent used like a user's project.
- An untrusted repository root makes `claude --bg` refuse at once ("Workspace not trusted"), so
  no hang there. `claude -p` never shows the dialog.
- A worktree inherits the primary's approval: in this checkout the approval is only in the
  primary's `.claude/settings.local.json` (`enabledMcpjsonServers: ["concorde"]`,
  `enableAllProjectMcpServers: true`; `~/.claude.json` has `enabledMcpjsonServers: []`), and
  `claude --bg` in a worktree under `.claude/worktrees/` or outside the repository, with no local
  settings of its own, shows no dialog.
- With `--settings` holding `{"disabledMcpjsonServers": ["concorde"]}` the dialog is gone
  (`--bg`), and `--strict-mcp-config` also removes it (rejected: it drops every other server).
- Name collision: with and without that setting a `claude -p` session loads exactly one
  `concorde`, `source: "dynamic"` (the `--mcp-config` one) with all `mcp__concorde__*` tools; the
  `.mcp.json` copy is never used today, so disabling it loses nothing. The flag setting is not
  persisted to any settings file or `~/.claude.json`.
- `--mcp-config` is variadic: a prompt placed after it is taken as a config path.

### Left to the task session

- Where exactly Claude Code records `.mcp.json` approvals (primary `.claude/settings.local.json`,
  `.claude/settings.json`, user settings, `~/.claude.json` `projects[<root>]`, managed settings)
  and how the task session's settings compute "approved in the primary"; how Claude Code merges
  `enabledMcpjsonServers`/`disabledMcpjsonServers` across sources. Decide, record the reasoning.
- Read the project `.mcp.json` from the task worktree (the one the session actually loads); a
  missing or unreadable `.mcp.json` must not stop the session from starting, but say in the
  decision log how you handle it.
- Update the Task sessions Spec (`specs/concorde/coordination/task-session/`: contracts row of
  `concorde task session`, requirements and scenarios, module text) and correct the docstring of
  `src/concorde/tasks/session.py`, which wrongly says a background session in an untrusted folder
  would not load `.mcp.json`. Add tests to `tests/concorde/tasks/test_session.py`.
- A live probe of the unapproved case needs a trusted but unapproved project, which means writing
  a trust entry into `~/.claude.json`, outside your boundary: do not attempt it; the main agent
  will run that probe after delivery. You may probe `--dry-run` output and anything inside your
  boundary.

## Task session decisions (2026-10-01)

Evidence: strings of Claude Code 2.1.285's bundled source (`claude.exe`), read inside the boundary.

- **How Claude Code judges a `.mcp.json` server.** Its status function first rejects a server listed
  in the merged `disabledMcpjsonServers` of any settings source (disabled wins over everything),
  then approves it when any source lists it in `enabledMcpjsonServers` or sets
  `enableAllProjectMcpServers` (in a trusted workspace over the merged settings; untrusted, per
  source with project settings skipped), and otherwise shows the dialog. Arrays such as
  `disabledMcpjsonServers` are concatenated across sources. Names compare after replacing every
  character but `[a-zA-Z0-9_-]` with `_`. The dialog writes its answer only to `localSettings`.
  Decision: the task session's settings compute "approved in the primary" the same way.
- **Sources read.** User settings (`$CLAUDE_CONFIG_DIR/settings.json` or `~/.claude/settings.json`),
  `.claude/settings.json` and `.claude/settings.local.json` of the primary worktree and of the task
  worktree, managed settings (`/etc/claude-code/managed-settings.json` and
  `managed-settings.d/*.json`, Linux path only), and `projects[<realpath of primary>]` of Claude
  Code's global config (`$CLAUDE_CONFIG_DIR/.claude.json` or `~/.claude.json`), whose legacy
  approval fields Claude Code migrates into local settings at startup. Reason: a server approved in
  any of them is approved for Claude Code, so disabling it would wrongly override that approval;
  the task worktree's own files are included because the session itself reads them. A missing,
  unreadable or non-object file approves nothing.
- **Which `.mcp.json`.** Claude Code 2.1.285 loads `.mcp.json` of every folder from the cwd up to,
  not including, `/` (closer ones override). So the servers are read the same way from the task
  worktree, which includes the primary's `.mcp.json` when the worktree lies inside it (the
  default `.claude/worktrees/<task>`). A missing, unreadable, non-JSON file or one without an
  `mcpServers` object names no server (Claude Code loads none from it, so it asks about none) and
  never stops the session from starting.
- **Settings written.** `disabledMcpjsonServers` = `concorde` followed by the sorted never-approved
  others; `enabledMcpjsonServers` = the sorted approved others (possibly empty). No
  `enableAllProjectMcpServers` is written. The `--dry-run` output is unchanged; the settings file
  shows the lists. Probe of this checkout: `{"enabledMcpjsonServers": [], "disabledMcpjsonServers":
  ["concorde"]}`.
- **Spec.** Added `req.task-session.mcp-approval`, `scenario.task-session.mcp-approval` (three tests
  verify it), a module section anchored `#project-mcp-approvals` replacing the wrong claim that a
  background session skips an untrusted folder's `.mcp.json`, and the contracts row of
  `concorde task session`. The docstring of `src/concorde/tasks/session.py` is corrected likewise.
- **Not changed (outside module.task-session).** The Harness's "Task-session settings" list
  (`specs/concorde/harness/claude-code.md`) names what the settings hold for the session boundary;
  the MCP approvals are not part of the boundary, and that list does not claim to be exhaustive, so
  it is left as is.
- The live probe of the unapproved case was not run (needs a trust entry in `~/.claude.json`,
  outside the boundary), as the brief says; the main agent runs it after delivery.
- `ruff check` reports two findings (ISC004 at the brief's list, TRY004 in `claude_sessions`) in
  lines this task did not touch; left alone.

## Report 1 to the main agent (Claude session启动时MCP信任提示阻塞), 2026-09-30T17:02:20Z

Delivered session-mcp-approval: delivery commit 1a7d43a8 (on f6d4027b), task-validation and delivery ready, 5 checks passed, full suite 835 passed.

What changed: src/concorde/tasks/session.py mcp_approvals() puts into the task session's settings disabledMcpjsonServers = concorde + every other .mcp.json server the primary worktree never approved, and enabledMcpjsonServers = those it approved. Spec: req/scenario task-session.mcp-approval, module section #project-mcp-approvals (replaces the wrong 'untrusted folder skips .mcp.json' claim), contracts row of concorde task session; the session.py docstring is corrected; 3 new tests.

Decisions taken without the developer (reasons in the decision log), based on Claude Code 2.1.285's bundled source:
1. Approval judged as Claude Code does it: a server in disabledMcpjsonServers of any source is rejected; otherwise enabledMcpjsonServers or enableAllProjectMcpServers in any source approves it; names compared with non [A-Za-z0-9_-] characters read as _.
2. Sources: user settings, .claude/settings.json and settings.local.json of the primary AND the task worktree, managed settings (/etc/claude-code + managed-settings.d, Linux path only), and projects[<primary realpath>] of ~/.claude.json (or $CLAUDE_CONFIG_DIR/.claude.json), whose legacy fields Claude Code migrates into local settings.
3. .mcp.json: read like Claude Code does, every folder from the task worktree up to, not including, / (so the primary's too for .claude/worktrees/<task>). A missing, unreadable or malformed file names no server and never blocks the start.
4. No enableAllProjectMcpServers is written; --dry-run output is unchanged (the settings file shows the lists). On this checkout: enabled [], disabled [concorde].
5. Harness's 'Task-session settings' list (specs/concorde/harness/claude-code.md, not this task's Module) is left alone: the approvals are not part of the boundary, and that list does not claim to be complete.

Still open: the live probe of the unapproved case in a trusted but unapproved project (e.g. /tmp/concorde-e2e/requests-5414) is for you after merge, as the brief says. Nothing escalated.

## Live probe after delivery (main agent, 2026-10-01)

Delivery commit 1a7d43a8 checked before merging, as the brief said. A scratch repository in
`/tmp` whose `.mcp.json` names `concorde` and an unapproved `other`, trusted for the probe through
a temporary `hasTrustDialogAccepted` entry in `~/.claude.json` (removed afterwards), with a worktree
under `.claude/worktrees/`. The branch's `mcp_approvals` gave `enabledMcpjsonServers: []`,
`disabledMcpjsonServers: ["concorde", "other"]`. `claude --bg` (2.1.285) started in the worktree
with those settings and the branch's `mcp_config` as `--mcp-config`, in the order `task session`
uses, showed no "New MCP server found" dialog; its ToolSearch found all 14 `mcp__concorde__*`
tools and no `mcp__other__*` tool. The same repository without these settings had stalled on the
dialog in the probes before the task. Result: the fix works; merging.

## Closed: merged, 2026-09-30T17:05:45Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 1a7d43a8a73e666709c1d2e4d79294ff24f5b2d8 into main and closed it as merged. Nobody answers a report after that.
