# Harness

## Purpose

The Harness configures and runs workers: from a frozen grant it decides what a worker may know,
what it may touch and how the run is controlled, and runs configured checks outside every worker so
a check result is never a worker's claim. Operation hosts rely on it to turn a grant and worktree
into a confined process, audited changes and a trustworthy run record. It does not choose the task
type, compute grants or judge output; enforcement guards against scope drift and mistakes, not a
malicious worker. A worker runs on Claude Code or on pi; both are confined by the same grant.

## Terminology

| Term | Definition |
| --- | --- |
| [Worker](../vocabulary.md#concept.concorde.worker) | |
| [Boundary](../vocabulary.md#concept.concorde.boundary) | |
| [Evidence](../vocabulary.md#concept.concorde.evidence) | |
| [Worker settings](workers/module.md#concept.workers.worker-settings) | |
| [Deny rules](workers/module.md#concept.workers.deny-rules) | |
| [Write hook](workers/module.md#concept.workers.write-hook) | |
| [Write audit](workers/module.md#concept.workers.audit) | |
| [Run record](workers/module.md#concept.workers.run-record) | |
| [Worker backend](workers/module.md#concept.workers.backend) | |
| [Permission extension](workers/module.md#concept.workers.permission-extension) | |
| [Configured check](checks/module.md#concept.checks.configured-check) | |
| [Read-only check boundary](checks/module.md#concept.checks.read-only-boundary) | |

A worker's boundary lives in its settings — deny rules, write hook, Bash sandbox — on Claude Code,
and in its permission extension and the same sandbox engine on pi. The write audit and checks
happen outside the worker; the run record keeps what the host observed.

## Usage

The Harness has no command of its own; an Operation host uses its two children in sequence, handing
a frozen grant, worktree and brief to [Workers](workers/module.md) — which pre-creates pending
files, generates settings or the permission extension, launches `claude -p` or `pi -p`, audits, runs checks through
[Check execution](checks/module.md), resumes the same session when checks fail, and returns the run
record. Operations needing only checks, such as validation, call Check execution directly.

A worker never sees the Harness, only its brief — the paths it may write, read or name — and the
denials its tools return when it strays.

## Design

The Harness exists so a worker's answer stays a proposal until the host checks it: the host, not
the worker, reads Git, audits changes, runs checks, writes records, and permissions never widen
mid-run. Neither backend puts an OS sandbox around the agent process itself.

### What is enforced in v1

The table describes the Claude Code backend; the pi backend enforces the same surfaces with its
permission extension and sandbox-runtime, as [Workers](workers/module.md#concept.workers.backend)
compares.

| Surface | Mechanism | What it stops |
| --- | --- | --- |
| Read, Glob, Grep | `permissions.deny` for the grant's complement in the task worktree; the primary worktree outside the run dir; `.git`, `~/.claude`, the credential | Ungranted/`names` reads; Grep silently omits them |
| Edit, Write | Same deny rules, plus a write-only PreToolUse hook denying non-`rw` paths, reason naming the level | `ro` edits or new files — deny alone can't, since deny beats allow |
| Bash | Sandbox: `denyRead` worktree/`$HOME`, `allowRead` granted files + runtime paths, `allowWrite` `rw` files + run dirs, no network, `allowUnsandboxedCommands: false` | Ungranted reads, `ro` writes, network, `dangerouslyDisableSandbox` |
| Permission mode | `bypassPermissions` via `--allow-dangerously-skip-permissions`; deny rules/hook/sandbox are the boundary | Nothing alone; `dontAsk` denies writes outside the working dir even when allowed |
| Working directory | The run's own directory, never the task worktree | Claude Code adding the worktree to the Bash sandbox's read/write set |
| Tool set | `--tools` per task type, never WebFetch/WebSearch, no agent tool | Web access via tools, workers starting other agents |
| MCP | `--strict-mcp-config` with no servers | Any tool beyond the listed ones |
| Claude state/instructions | Own `CLAUDE_CONFIG_DIR`, cleared env, `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` | User settings, memory, skills, plugins, transcripts, project instructions |
| Git | No tool reads `.git`; diffs/commits belong to the host | A worker inspecting or rewriting history |
| Changes | Host audits `git diff`/untracked files against the grant each round | Any remaining write outside `rw` counting as a result |
| Limits | Timeout, `--max-turns`, `--max-budget-usd`, kill of the process group at round end | Runaway runs and leftover processes |

Exact mechanics: [Workers](workers/module.md); check boundary: [Check execution](checks/module.md).

### Known limits of v1

- The Claude or pi process, the write hook and the permission extension are not sandboxed. The
  file-tool boundary is only as good as the generated deny rules, hook and extension are complete
  and correct.
- Deny rules cover the task worktree and home directory; system directories and other paths outside
  the home stay readable to every tool, since Bash needs them to run anything.
- A read denial's message is Claude Code's generic "denied by your permission settings", so the
  brief states the grant; write denials explain themselves via the hook.
- A single `rw` file granted to Bash is bind-mounted, so it can't be deleted or renamed from Bash,
  and a file created outside `rw` appears to succeed but lands on a throw-away filesystem, unseen by
  the audit — the brief warns of this.
- Writes to Git-ignored paths are not audited; the host audit is the last line of defense for a
  write outside `rw`.

Future work: an outer `srt` sandbox around the agent process, proxied credentials, and a leader
tier.

<a id="realization.harness.package"></a>

The **Harness package** is `concorde.harness`'s Python package marker, holding both children's code
with no behaviour of its own.

<a id="realization.harness.error-chain"></a>

**Error chain code** builds and renders the links of an
[error chain](../vocabulary.md#concept.concorde.error-chain) in the shape of the Framework's
[error contract](../contracts.md#contract.concorde.error): the schema, the reasons a level cannot
handle an error, helpers turning an exception or finding into a link, and the human rendering.
Workers and Check execution report their failures with it, and so do the Operation host, Tasks and
the Issues command, so every level's link has the same shape whoever wrote it. The contract stays
the root's, because every Module promises it; the Harness only owns the code. Spec tooling keeps
its own error types and does not use it.

## Relationships

Both children and the error-chain code, nested; the package marker carries no behaviour and is
left out:

```d2
harness: Harness {
  workers: Workers
  checks: Check execution
  errors: Error chain code {
    "errors.py"
  }
  workers -> checks
}
```

The children split by who acts: Workers runs a model process; Check execution runs deterministic
commands and never starts a model. Workers relies on Check execution each round; Check execution
knows nothing about Workers.

<a id="contains-harness-workers"></a>

**Workers** turns one frozen grant into worker settings, a brief and a launched process, auditing
the worktree each round, resuming on check failure, performing proposed deletions and writing the
run record. The Harness relies on it for every enforcement-table guarantee except the check
boundary. Unable to establish part of the boundary, e.g. a run directory a deny rule would cover, it
refuses to launch rather than run a weaker worker.

<a id="contains-harness-checks"></a>

**Check execution** runs Modules' configured checks in a read-only OS boundary with a fresh scratch
directory, ends every process it starts, and returns results bound to the digest measured, so checks
run outside workers and cannot change the files they judge. If the boundary can't be established,
none run.
