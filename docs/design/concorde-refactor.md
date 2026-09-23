# Concorde refactor design

Status: accepted, 2026-09-24. Items marked **Proposed** were not decided explicitly; they are
adopted as defaults for implementation and may still be revised. Everything else was agreed.

## 1. Goals and non-goals

Goals:

- Make Spec Tooling an independent part that maintains Specs (validation, review, docsite) and
  serves other projects' agents through a local MCP server, `spec-mcp`.
- Replace the LangGraph and Pi harness with a two-tier agent model on Claude Code: a **main
  agent** and **worker agents**. Workers run under Spec-derived, per-file permissions.
- Keep **Operations**, redefined as deterministic host steps plus agent workers.
- Make the **task** (branch, worktree, record and decision log) a first-class concept.
- Propagate errors fully: every tier reports what it cannot handle with a description and evidence.

Non-goals for this version:

- **Only Claude Code is supported.** Pi and pi-subagents are explicitly unsupported. The project
  README and root Spec say so.
- No backward compatibility, migration shims or transitional adapters.
- No LangGraph, no pi workflows, and no Claude Code Dynamic Workflows.
- No leader tier and no outer OS sandbox around workers (see [Future work](#10-future-work)).

## 2. Spec Tooling

Spec Tooling has two parts with different dependencies.

| Part            | Contents                                                                                                            | Calls a model |
| --------------- | ------------------------------------------------------------------------------------------------------------------- | ------------- |
| **spec-core**   | Protocol model and loading, deterministic validation, registry, boundary and grant computation, `spec-mcp`, docsite | no            |
| **spec-review** | Agent-based Spec review                                                                                             | yes           |

Validation and review maintain the Specs themselves. `spec-mcp` serves agents in any project that
uses Concorde. The docsite publishes Specs for humans.

### spec-mcp

- A local **stdio** MCP server. It is rooted at the worktree it runs in and answers from **that
  worktree's Specs**, so different Spec content gives different answers. It rejects paths outside
  its root, using `CLAUDE_PROJECT_DIR` or MCP `roots/list`. The server's code version does not
  matter; changing it is an ordinary change inside a worktree.
- Core query:

  ```text
  boundary(modules: [ModuleId], task_type: TaskType)
    -> { context_identity, entries: [{ path, level }] }
  level ∈ names | ro | rw          # deny entries are omitted from the list
  ```

  The result is computed exactly from the Protocol's boundary sets and the task-type table in
  [section 3](#3-protocol-changes). A multi-Module task receives the union. The shared-file rule
  still applies: a task that writes a file bound by several Modules must be bound to every one of
  them.

- Read-only queries (**Proposed**): `modules()`, `module(id)` (entry, owned documents and
  relations), `context(module)` (the SpecContext document list with digests), `impact(paths)`, and
  `validate(target?)`.
- **Grants are frozen at launch.** The Operation host requests a grant and freezes it into the
  worker's configuration. A worker never requests or changes its own grant.
- Workers get no MCP server in v1 (`--strict-mcp-config` with an empty set). `spec-mcp` is for
  the main agent and for other projects' agents. The Operation host calls the same spec-core
  library directly, with `--root <task worktree>`, so a grant always comes from the task
  worktree's Specs and never from the primary's.

### spec-review

- v1 is simple and does not use `spec-mcp`. Reviewers read the Specs directly. When stuck, they
  return to a global view of the project to find the problem rather than staying inside one
  Module's context. Two agents may work back and forth, for example a reviewer and a checker of
  its findings.
- The review "dimensions" (readability, requirement and scenario form, design explanation,
  views, terminology) stay one checklist per reviewer in v1. **Proposed:** splitting them into
  parallel reviewers is future work.

### Docsite

The docsite stays part of Spec Tooling. It uses Docusaurus and renders `specs/` directly.

## 3. Protocol changes

### Task types

The Protocol now defines the task types and each type's access level per boundary set. This
turns the illustrative table in `protocol/boundaries.md` into a normative one.

| Task type     | `SpecContext` | `ImplementationContext` | `ImplementationScope` | `SpecScope` | `ExternalContext` | Notes                                                        |
| ------------- | ------------- | ----------------------- | --------------------- | ----------- | ----------------- | ------------------------------------------------------------ |
| `understand`  | read          | names                   | none                  | read¹       | read              | Understand a Module: explain, plan, assess                   |
| `specify`     | read          | names                   | none                  | **write**   | read              | Change the Module's Specs, including declaring pending files |
| `implement`   | read          | names                   | **write**             | read¹       | read              | Change the Module's code                                     |
| `test`        | read          | names                   | read                  | read¹       | read              | Read code and tests; checks run through the host             |
| `review-spec` | read          | names                   | none                  | read¹       | read              | Judge the Module's Specs                                     |
| `review-code` | read          | names                   | read                  | read¹       | read              | Judge code against Specs; the diff is task material          |

¹ `SpecScope(M)` ⊆ `SpecContext(M)`, so read is implied. The column is listed for completeness.

- "Understand" replaces "plan" as the name of the reading task type, because planning is only one
  use of understanding a Module.
- `test` never runs commands inside the worker. The host runs the configured checks outside the
  worker and returns the results (see [section 5](#5-operations)).
- Task material, such as a plan, a brief or a diff, still adds no source (rule 4).

### Access levels

The levels stay `none | names | read | write`. `spec-mcp` serializes them as omitted, `names`,
`ro` and `rw`.

- **`names`**: the path is listed and visible, but its contents may not be read. Typical use: an
  `understand` or `specify` worker learns that Module X is realized by `src/x/foo.py` and
  `src/x/bar.py`. It can then plan where code goes or declare a pending file without reading
  code.
- **Write-only is not a level.** "Write implies read" (rule 2) stays.

### Sentences that change

| Location                                                           | Current text                                                                                                                               | Change                                                                                                                                                            |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `protocol/boundaries.md:8-10`                                      | "Which sets a given task receives, at which access level, and how the boundary is enforced are decisions of the harness running the task." | The task type determines which sets a task receives and at which level. Only enforcement, and the choice of task type for a task, remain the harness's decisions. |
| `protocol/boundaries.md:120`                                       | "This table is illustrative; the Protocol does not prescribe task kinds."                                                                  | Replace with the normative task-type table above.                                                                                                                 |
| `protocol/boundaries.md:123-124`                                   | "…the union of their sets at the levels the harness chooses."                                                                              | "…at the levels its task type assigns."                                                                                                                           |
| `protocol/principles.md:185` ("What the Protocol does not define") | "Which boundary a particular task receives and how a harness enforces it."                                                                 | "Which task type a harness assigns to a task, and how it enforces the resulting boundary."                                                                        |
| `protocol/principles.md:84` (glossary)                             | "**Boundary** — the read and write sets a harness assigns to one task."                                                                    | "…the read and write sets a task type assigns to a task bound to Modules."                                                                                        |

The Protocol still says nothing about enforcement mechanisms (permission rules, hooks, sandboxes, MCP). These
changes set the major version: an existing harness's own task kinds are no longer conformant.

## 4. Agents

The two tiers are the main agent and the worker. The leader tier is deferred.

### Main agent

- It runs in the primary worktree as the user-facing Claude Code session. Concorde adds no
  permission limits, but the main agent normally does not modify the project directly.
- It discusses status with the user, answers questions and sets direction and large plans.
- It splits work into **tasks** at the branch and worktree level and sets the project-level
  parallelism strategy. Parallelism exists only between worktrees.
- It runs Operations inside task worktrees, reads their structured results and keeps each task's
  decision log.
- It decides design uncertainties itself, records them and reports them at the end. It escalates
  to the user only for decisions with major impact.
- It merges verified task branches into main **without asking the user for authorization**.

### Worker agent

- It is an independent headless process:
  `claude -p --settings <generated> --tools <per type> --json-schema <result> --output-format json`.
  Its working directory is its run directory, not the task worktree, and its brief uses absolute
  worktree paths (see [Spike results](#spike-results)).
- It does one bounded task of one task type, for one or more Modules.
- It never touches `.git`, never runs Operations and never starts other agents.
- It needs no human input. It reports to the Operation host through its structured result.

## 5. Operations

An Operation is a set of deterministic host steps plus agent workers. Its control flow is plain
Python: LangGraph is deleted, pi workflows are removed and Dynamic Workflows are not used. Each
Operation keeps a step table in its owning Module's Spec. Operations need no user consent to run.

The main agent invokes an Operation through the CLI in background Bash:

```text
concorde run <operation> --task <task-id> [--modules …] [operation arguments]
```

The session is woken when the process exits and reads the result file.

### Host sequence of a worker-backed Operation

| #   | Step                                                                                                                                                                       | Actor                    |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| 1   | Compute the grant from the **task worktree's** Specs (task type × Modules) and freeze it with its context identity                                                         | host (spec-core)         |
| 2   | Pre-create pending files that the grant makes writable                                                                                                                     | host                     |
| 3   | Generate the worker's `settings.json` (sandbox, `permissions.deny` and the write hook, all from the grant), tool list and brief (the grant's `rw`, `ro` and `names` lists) | host                     |
| 4   | Launch the worker (`claude -p …` in `bypassPermissions`, working directory = run directory) with its own `CLAUDE_CONFIG_DIR` and a clean environment                       | host                     |
| 5   | Audit: compare `git diff` and untracked files with the grant, and reject any write outside `rw`                                                                            | host, outside the worker |
| 6   | Run the configured checks outside the worker                                                                                                                               | host                     |
| 7   | On check failure, resume the same worker (`claude -p --resume <session>`) with the failures; repeat up to N rounds (**Proposed** N = 3, configurable)                      | host                     |
| 8   | Write the run record: grant, context identity, worker transcript path, audit, checks and rounds                                                                            | host                     |
| 9   | Return the structured result (see [section 9](#9-error-propagation))                                                                                                       | host                     |

### Operation catalog (**Proposed** v1)

| Operation           | Task type(s)         | Notes                                                                                |
| ------------------- | -------------------- | ------------------------------------------------------------------------------------ |
| `understand`        | understand           | Replaces `plan` and `context_solve`; produces a plan or an assessment                |
| `specify`           | specify              | New: a Spec change by a worker                                                       |
| `tasks`             | understand           | Kept if a separate task breakdown remains useful; otherwise folded into `understand` |
| `implement`         | implement            |                                                                                      |
| `test`              | test                 | New                                                                                  |
| `spec_review`       | review-spec          | v1 reads Specs directly                                                              |
| `code_review`       | review-code          |                                                                                      |
| `validate`          | none (deterministic) |                                                                                      |
| `delivery`          | none (deterministic) | Commits on the task branch together with its evidence; the main agent only merges    |
| `issues`            | understand/implement | Kept; reworked onto workers                                                          |
| `init`, `configure` | none (deterministic) |                                                                                      |

## 6. Tasks

A task is a branch, a worktree, a task record and a decision log.

- **Proposed** location: the primary owns the durable records.
  - `.concorde/tasks/<task-id>.json` holds the branch, worktree path, goal, Modules, state and
    Operation runs.
  - `.concorde/tasks/<task-id>.decisions.md` is the decision log: choices made without the user
    and escalations.
  - Run records stay in `.concorde/runs/<run-id>/`, which also holds the worker's generated
    configuration, `CLAUDE_CONFIG_DIR`, `HOME` and `TMPDIR`. This replaces `.concorde/status/` and
    `.concorde/worktrees.json`.
- **Proposed** because it follows from the rule that Operation hosts write run records: the
  Operation host writes to the primary's `.concorde/runs/` even when it runs in a task worktree.
- Task states (**Proposed**): `open → active → delivered → merged | abandoned`.

## 7. Worker enforcement (v1)

v1 uses only the worker's Claude configuration. There is no outer OS sandbox around the Claude
process.

| Surface                       | Mechanism                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Read, Edit, Write, Glob, Grep | Two layers generated from the grant (user decision B). (1) **`permissions.deny`** lists the complement of the grant: `Read` and `Edit` deny for every ungranted path, `Edit` deny for every `ro` and `names` path, a single `/**` rule for each directory with no granted file below it, and `.git/**`, `~/.claude/**` and the worker's credentials file. Deny rules still apply in `bypassPermissions`, and Grep filters denied files out of its results. (2) **A small write-only PreToolUse hook** on Edit and Write. It denies any path that is not in the grant's `rw` list, and its reason names the path's level (for example: undeclared file, so declare it as pending through `specify` first). For `rw` paths it returns no decision. It never governs reads. |
| Bash                          | Claude's built-in sandbox: `sandbox.enabled: true`, `filesystem.denyRead` covering the worktree and `$HOME`, `allowRead` for granted files and the runtime paths the Operation configures (toolchain, `.venv`, `node_modules`), `allowWrite` for `rw` files and the run directory, no network, and **`allowUnsandboxedCommands: false`**                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Permission mode               | `--permission-mode bypassPermissions --allow-dangerously-skip-permissions`. In `-p`, `dontAsk` denies every Edit or Write outside the working directory even when an allow rule matches. The deny rules and the Bash sandbox are the boundary.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Working directory             | The run directory, **never the worktree**. Claude adds its working directory, and every `--add-dir`, to the Bash sandbox's readable and writable set, which would defeat per-file Bash confinement. Briefs therefore use absolute paths.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Tool set                      | `--tools` per task type. WebFetch and WebSearch are never included. `understand` and `review-*` get no Edit or Write.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Claude state                  | Its own `CLAUDE_CONFIG_DIR` under the run directory. The host places the credential there: v1 copies the credentials file; a token in an environment variable is untested. The user's `~/.claude` (transcripts, memory, credentials) is never readable.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| MCP                           | `--strict-mcp-config` with no servers                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Environment                   | Cleared, then allowlisted: `PATH`, `LANG`, the credential, `HOME`, `TMPDIR` and `CLAUDE_CONFIG_DIR`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| git                           | No `.git` access in any form. Diffs and commits belong to the host and to `delivery`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Ambient instructions          | The worker's instructions come only from the Operation brief. Set `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` and `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`; a fresh `CLAUDE_CONFIG_DIR` carries no user skills, plugins or settings. Do not use `--safe-mode` or `--bare`: they also disable hooks, including the write hook.                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Limits                        | Timeout, `--max-turns` and `--max-budget-usd`; the process group is killed on exit                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |

Honest limits of v1:

- The Claude process and the hook script are not sandboxed. File-tool boundaries depend on the
  generated deny rules being complete and on the hook being correct.
- Read denials carry a generic "denied by your permission settings" message. The brief therefore
  states the grant explicitly. Write denials come from the hook and explain themselves.
- Bash writes to single files inherit Linux bind-mount limits.
- The host audit (step 5) remains the last line of defense for any write outside `rw`.

These limits guard against scope drift and mistakes, not against a malicious actor; a worker's
permissions must never widen.

### Spike results

Run on 2026-09-24 against Claude Code 2.1.280 on Linux, with `claude -p`, Haiku 4.5, a fixture
worktree, a hook and a settings file generated from a grant (`ro` spec, `rw` source file, `names`
source file, a pre-created empty pending file, and an ungranted secret). Evidence was taken from
`--output-format stream-json` tool results and the resulting `git status`.

| Check                                                                                          | Result                                                                                                                                                                                                                                                |
| ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hook denies Read, Edit, Write, Grep outside the grant, including `names` files and `~/.claude` | **Works.** The model receives the hook's reason text verbatim.                                                                                                                                                                                        |
| Grep or Read on a granted file                                                                 | Works                                                                                                                                                                                                                                                 |
| Edit or Write on an `rw` file, and on a pre-created pending file                               | Works only in `bypassPermissions`. With `dontAsk` it is always denied, whatever the hook or allow rules say.                                                                                                                                          |
| Bash reads of ungranted files, `.git` and `~/.claude`                                          | Denied when the working directory is outside the worktree. Denied files do not exist inside the sandbox, so `ls` shows only granted files and `git` finds no repository. **Not denied when the working directory is the worktree or an `--add-dir`.** |
| Bash write to an `rw` file, and to a pre-created pending file                                  | Works                                                                                                                                                                                                                                                 |
| Bash write to a `ro` file                                                                      | Denied with "read-only file system"                                                                                                                                                                                                                   |
| Bash creating a new file in a denied directory                                                 | Appears to succeed, but writes to a throw-away tmpfs and never reaches the worktree. The model is misled, and the host audit sees no change.                                                                                                          |
| `dangerouslyDisableSandbox: true` with `allowUnsandboxedCommands: false`                       | Ignored: the command still runs sandboxed                                                                                                                                                                                                             |
| Network from Bash with `allowedDomains: []`                                                    | Denied (403 from the sandbox proxy)                                                                                                                                                                                                                   |
| Separate `CLAUDE_CONFIG_DIR` with a copied credentials file                                    | Authenticates. The directory holds sessions, backups and shell snapshots, about 1 MB per run.                                                                                                                                                         |
| `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`                                                             | A CLAUDE.md in the working directory is not loaded. Without it, it is loaded.                                                                                                                                                                         |
| `claude -p --resume <session>` with a check failure                                            | The same worker continues with its context and fixes the file. The result carries a **new session id**, and the host must keep the latest one.                                                                                                        |

File tools without a hook, same sandbox settings:

| Variant                                                              | Result                                                                                                                                                                                                                                                                                                                                                                                      |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sandbox only, no hook, no permission rules                           | **File tools are not confined.** Read returned an ungranted file, the secret and the worker's own credentials file. Edit changed a `ro` Spec, Write created an ungranted file, and Grep returned matches from an ungranted file. The sandbox governs only Bash and its child processes.                                                                                                     |
| Sandbox and `permissions.deny` listing every ungranted path, no hook | Reads of listed paths and Edit of a `ro` file are denied with a generic "denied by your permission settings". **Grep filters ungranted files out of its results**, which is better than the hook's all-or-nothing directory rule. **Write of a new, unlisted file succeeds**: deny beats allow, so "only these files are writable" cannot be expressed, and only the host audit catches it. |

Consequences for the design:

1. The worker runs in `bypassPermissions` with the run directory as its working directory. The
   boundary is three layers derived from the same grant: deny rules for reads and known files,
   a write-only hook that makes `rw` the exact write allowlist, and the sandbox for Bash. A
   sandbox alone does not confine file tools. Deny rules alone cannot stop new undeclared files,
   because deny beats allow. `--tools` limits the tool set.
2. The run directory must not lie under any denied prefix. In the spike, a `~/.claude/**` rule
   silently denied the whole fixture because it lived under `~/.claude/jobs/`.
3. Pending files are pre-created by the host (confirmed). **Proposed:** deleting a file and creating an
   undeclared one is not possible for a worker; deletions are proposed in the structured result
   and performed by the host after the audit.
4. The Bash tmpfs illusion is documented in the worker brief: files created by Bash outside `rw`
   paths are lost.
5. Credentials: v1 copies the credentials file into the run's config directory. A long-lived
   token passed by environment variable was not tested. Credential isolation is future work.

## 8. Responsibilities

| Action                                                      | Main agent                | Operation host                     | Worker                                         |
| ----------------------------------------------------------- | ------------------------- | ---------------------------------- | ---------------------------------------------- |
| Split work into tasks and set the parallelism strategy      | ✓                         |                                    |                                                |
| Create and remove task branches and worktrees               | ✓                         |                                    |                                                |
| Compute and freeze the grant                                |                           | ✓                                  |                                                |
| Pre-create pending files, generate the worker configuration |                           | ✓                                  |                                                |
| Edit files within the grant                                 | (normally not)            |                                    | ✓                                              |
| Read git, diff and audit against the grant                  |                           | ✓ (read-only git)                  | ✗                                              |
| Run checks and feed back failures                           |                           | ✓                                  |                                                |
| Commit on the task branch with evidence                     |                           | ✓ (`delivery`)                     | ✗                                              |
| Merge into main                                             | ✓ (no user authorization) |                                    |                                                |
| Escalate                                                    | major impact → user       | adds deterministic evidence → main | structured `blocked` or `failed` result → host |

## 9. Error propagation

Every worker ends with a result validated by `--json-schema`:

```json
{
  "status": "ok | blocked | failed",
  "summary": "…",
  "problem": "what could not be done and why",
  "attempts": ["what was tried"],
  "evidence": [
    { "kind": "file|command|output|spec", "ref": "…", "detail": "…" }
  ],
  "options": ["possible ways forward"],
  "recommendation": "…",
  "blocking": true,
  "impact": "what else is affected"
}
```

- The host adds deterministic evidence: grant and context identity, audit violations, check
  commands with exit codes and log paths, rounds used, transcript path and stderr. It never
  paraphrases the worker's claims into facts.
- The host's own failures (a grant that cannot be computed, a launch error, a timeout) use the
  same envelope with host evidence.
- The main agent records every non-`ok` result and every choice made in the task's decision log.
  It escalates to the user only when the impact is major. Otherwise it decides, records the
  decision and reports it in the final summary.

## 10. Future work

- **Outer srt wrapper** (`@anthropic-ai/sandbox-runtime`) around the whole worker process, with
  its own `srt.json`: writes and network denied by default, the worker's config directory and
  `api.anthropic.com` allowed. On Linux, the bubblewrap bind-mount limits must be designed for:
  - a writable single file cannot be deleted or renamed;
  - an atomic write by rename onto a mounted file may fail;
  - pending files must be created before launch;
  - read-denied files are invisible, so `names` entries come only from the brief.
- **Credential injection** through the srt proxy, so the worker never sees the API credential.
- **Leader tier**: a per-task Claude session that owns its worktree and talks to the main agent
  by cross-session messaging.
- **Pi and pi-subagents** support.
- **Review through `spec-mcp`**, and review dimensions as parallel reviewers.
- **Dynamic Workflows** for parallel workers that share one permission set, such as a large
  multi-file implementation.

## 11. Module restructure and deletions

### Proposed Module tree (by capability)

```text
concorde (root)
├── spec-tooling            Spec Tooling as an independent part
│   ├── spec                Protocol model, loading, validation, registry,
│   │                       boundary sets, task-type grants          src/concorde/spec
│   ├── spec-mcp            stdio MCP server                          new: src/concorde/spec_mcp
│   ├── spec-review         agent-based Spec review                   from review/ + agents/spec_reviewer
│   └── views               docsite                                   src/concorde/views, docsite/
├── harness                 worker configuration and execution
│   ├── workers             grant → settings.json (sandbox, deny rules, write hook), launch,
│   │                       resume, run records                       replaces native_driver et al.
│   └── checks              host-run checks and the write audit       harness/checks + check_executor
├── tasks                   task records, branch and worktree lifecycle,
│                           decision log                              from harness/worktrees, status_store
├── operations              catalog and `concorde run` dispatch       src/concorde/operations
├── understanding           understand, tasks                         from planning/
├── specification           specify                                   new
├── implementation          implement, test                           src/concorde/implementation
├── code-review             review-code                               from review/
├── validation              validate                                  src/concorde/validation
├── delivery                delivery (commit with evidence)           src/concorde/delivery
├── issues / issue-solving  kept, reworked onto workers
├── main-session            Claude Code main-session configuration    replaces session/
└── distribution            build, install, CLI                       src/concorde/distribution
```

The `agents` Module is dissolved: each worker definition (prompt, tool list, result schema) moves
to the Module that owns its Operation, in line with organizing by capability. **Proposed.**

### Deleted

Verified to exist at HEAD `0693972f`:

- LangGraph:
  - Python: `src/concorde/harness/operation_node.py`, `src/concorde/harness/graph_specs.py`,
    `src/concorde/operations/graph_catalog.py`
  - scripts: `scripts/development/check-graph-specs.py`, `scripts/run-operation.py`
  - the `langgraph` dependency in `pyproject.toml` and `scripts/requirements.lock`
  - reference submodules `reference/langgraph` and `reference/langchain-docs`
  - LangGraph handling in `src/concorde/distribution/managed_runtime.py`,
    `local_installation.py` and `scripts/development/check-reference-versions.py`
  - tests: `tests/concorde/harness/test_graph_specs.py`, `test_operation_node.py`,
    `tests/concorde/support/sample_graph.py` and
    `tests/concorde/operations/test_run_operation.py`
- Pi:
  - `pi/` in full: extensions, workflows `plan.js`, `review.js` and `issues.js`, and the
    native-*-host.mjs files
  - `.pi/`
  - `reference/pi`, and the untracked local `reference/pi-subagents`
  - `src/concorde/harness/native_driver.py`, `native_runtime.py`, `native_evidence.py` and
    `native_result.py`
  - the Pi parts of `review/native.py` and `issue_solving/native.py`
  - `tests/concorde/harness/native_*_probe.mjs`
- Session and source-checkout machinery:
  - the `select-session` command in `src/concorde/distribution/cli.py`
  - `src/concorde/distribution/session_selection.py`, `task_subagents.py` and `tester_check.py`
  - `prompts/user-session/`, `prompts/task-subagent/` and `prompts/workflow-host/`
  - `agents/task_subagent.py` and `agents/source/`
  - `generated/session/` and `generated/native/`
  - the maintenance-worker, tester and candidate-registration rules in `AGENTS.md`, which is
    rewritten for the main-agent and task model
- Harness pieces replaced by the new design (**Proposed**):
  - `harness/admission.py`, `operation_state.py` and `relay.py` (graph-shaped admission)
  - `harness/capsule.py` (context copies; workers read in place under the deny rules and sandbox)
  - `harness/status_store.py` and `.concorde/status/`, replaced by `tasks`
  - Specs `specs/concorde/harness/admission/`, `harness/execution/` (rewritten as
    `harness/workers`), `harness/observation/`, `session/` and `agents/`

### Kept or moved

- `src/concorde/spec/*` → spec-tooling/spec, extended with task-type grants.
- `harness/check_executor.py`, `checks.py` and `check_evidence.py` → harness/checks, used by
  the host outside the worker.
- `harness/change_worktree.py` → tasks, simplified to branch and worktree lifecycle.
- `harness/context.py` (context identity and digests) → spec-tooling/spec.
- `agents/*/spec.md` and `prompts/native/*.md` → worker briefs in their owning Modules.
- `operations/*.py` declarations → rewritten for the new catalog.
- `docsite/` and `src/concorde/views/` → spec-tooling/views, unchanged in v1.

## 12. Implementation order

| #   | Milestone                                                                                                                            | Done when                                                                                |
| --- | ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| 0   | Spike: worker enforcement on Claude Code 2.1.280                                                                                     | Spike results recorded in section 7, and the design adjusted where needed                |
| 1   | Protocol: task types, access-level table, sentence changes; bump version; `protocol-manifest --write --bind-project`                 | `validate` passes on the project                                                         |
| 2   | Spec restructure: new Module tree and Specs for spec-tooling, harness/workers, tasks, operations, main-session; delete retired Specs | `validate` and the registry mirror are clean                                             |
| 3   | spec-core: task-type grant computation and CLI `concorde grant --root … --modules … --type …`                                        | Unit tests pass for every task type, including multi-Module and shared-file cases        |
| 4   | `spec-mcp` stdio server over spec-core                                                                                               | Tested over MCP stdio, with the root confined                                            |
| 5   | harness/workers: settings generation (sandbox, deny rules, write hook), launch, audit, check-and-resume loop, run records            | An `implement` worker is fenced end to end; audit catches an injected out-of-grant write |
| 6   | tasks and `concorde run`; the `delivery` commit with evidence                                                                        | The main agent can open a task, run an Operation and deliver                             |
| 7   | Port Operations: understand, specify, implement, test, code_review, spec_review (direct read), issues                                | Each has a step table in its Spec and an integration test                                |
| 8   | Delete LangGraph, Pi, the session and source-checkout machinery; rewrite AGENTS.md and README; state Claude Code-only support        | `build --check`, `validate`, `check-package` and the full Python suite pass              |
