# Harness library interface

This document states the exact calling contract of the Harness as a library. Through it, Workers
generates a worker's configuration once per worker run, before the first round. The contract
covers these parts:

- the entry points and their inputs
- what each entry point returns
- its effects
- its failures
- what a repeated call returns

The [entry](module.md#calling-the-harness) names the entry points and follows one call through
them. The [Claude Code mechanics](claude-code.md) and the [pi mechanics](pi.md) state what the
returned configuration holds and how it decides.

## Python entry points

The Python entry points are in the module `concorde.worker_harness.settings`:

| Entry point | Returns |
| --- | --- |
| `RunPaths(root, trace=None, run_id="")` | The paths of one worker run: `control`, `config`, `groups`, `home`, `tmp` and `work` below the [runtime directory](../../glossary.json#concept.runtime-directory) `root`, and `own()`, the worker's own `(work, home, tmp)` |
| `grant_view(grant)` | A `GrantView` of the grant: `level(path)` gives a worktree-relative path's level, `paths(*levels)` the sorted entries at those levels |
| `worker_settings(worktree, grant, run, *, python, runtime=(), home=None, primary=None, git=())` | The complete [worker settings](claude-code.md#worker-settings) as a JSON-ready `dict` |
| `deny_rules(worktree, grant, run, runtime=(), home=None, primary=None, git=())` | The [deny rules](claude-code.md#deny-rules) alone, a `list` of rule strings, which `worker_settings` places in `permissions.deny` |
| `sandbox_filesystem(worktree, grant, run, runtime=(), home=None, primary=None, git=())` | The four sandbox lists `denyRead`, `allowRead`, `allowWrite` and `denyWrite`, shared by both backends, as a `dict` |
| `write_hook_source(worktree, grant)` | The source text of the [write hook](claude-code.md#write-hook) with the task worktree and the grant's `rw`, `ro` and `names` lists embedded |
| `tool_set(tool_sets, task_type, grant)` | The tool set of a [task type](../../glossary.json#concept.task-type) as a `--tools` string, from a backend's table: `TOOL_SETS` for Claude Code, `PI_TOOL_SETS` for pi |
| `TASK_TYPES` | The eight task types of the Protocol, in the order of the [grant input](../workers/contracts.md#contract.workers.grant-input) |

### Inputs

The entry points take these inputs:

| Input | Meaning |
| --- | --- |
| `worktree` | The task worktree, which the Harness resolves to its real path |
| `grant` | The frozen grant in Workers' [grant input](../workers/contracts.md#contract.workers.grant-input). The Harness reads only its `entries` |
| `run` | The `RunPaths` of the run, whose directories Workers created |
| `python` | The interpreter whose command the settings give the [write hook](../../glossary.json#concept.write-hook) |
| `runtime` | The runtime paths, exactly as Workers checked them ([Reading beside the grant](../workers/launch.md#reading-beside-the-grant)), each resolved to its real path |
| `home` | The user's home directory. Without one, the Harness takes the home of the process |
| `primary` | The primary worktree of the task worktree's repository. Without one, the Harness hides only the home |
| `git` | The Git administrative paths, as real paths, in the order [Placement](../workers/launch.md#placement) lists them |
| `task_type`, `tool_sets` | A task type of `TASK_TYPES` and a backend's tool set table |

### Effects

The entry points write nothing. Workers writes what they return into the runtime directory's
`control/`. `RunPaths` and `grant_view` touch no file. The other entry points read the file
system:

- `worker_settings`, `deny_rules` and `sandbox_filesystem` resolve every path they are given.
- `worker_settings` and `deny_rules` also list the task worktree and, to find the way to the task
  worktree and the run's own paths, the home and the primary worktree.
- `write_hook_source` reads the source of `write_hook.py`.

### Failures

A grant the Harness cannot read is refused with a `SettingsError`, a `ValueError` whose `code`
names the refusal. Its message says what is wrong:

| Code | When |
| --- | --- |
| `grant_unavailable` | The grant is no object, or it has no `entries` |
| `grant_malformed` | Its `entries` are no list, or an entry breaks the grant input's shape or names a path an earlier entry names. The message names the first such entry by its index |
| `run_directory_denied` | A deny rule `worker_settings` generated covers the run's `work/`, `home/` or `tmp/` |

The two grant codes are those of the grant input. Workers checks the grant itself before it calls
the Harness. An `OSError` of the file system, such as a directory that cannot be listed, reaches
the caller unchanged.

### Repeated calls

Each entry point returns its value in a fixed order. Called again with equal inputs over an
unchanged file tree, it returns an equal value. The
[deny rules](../../glossary.json#concept.deny-rules) follow the file tree at the moment of the
call. So a call after a file or directory appeared can return other rules. Workers therefore
generates the configuration once per run and keeps it for every round
([req.workers.unchanged-across-rounds](../workers/launch.md#req.workers.unchanged-across-rounds)).
The write hook and the
[permission extension](../../glossary.json#concept.permission-extension) judge each tool call by
the file system at that moment, with the lists embedded once.

## The pi sources

The pi harness is two TypeScript sources beside `settings.py`. Workers places them:

1. It reads `pi_permission.ts`.
2. It replaces the line `const POLICY: Policy = {} as Policy;` once, by the same declaration with
   the run's policy as JSON.
3. It replaces the module specifier `"@concorde/sandbox-runtime"` once, by the absolute path of the
   sandbox-runtime package's `dist/index.js`, as a JSON string.
4. It writes the result as the runtime directory's `control/permission.ts`.
5. It copies `pi_policy.ts` unchanged beside it.

pi loads `control/permission.ts` as its only extension. Each of the two replaced texts occurs once
in the source. A source without one is a broken installation.

### The policy

The policy is a JSON object of the `Policy` type of `pi_policy.ts`. Every path in it is absolute.
It has exactly these fields:

| Field | Value |
| --- | --- |
| `worktree` | The task worktree's real path |
| `rw`, `ro`, `names` | The grant's entries at each level, as `grant_view(grant).paths(level)` gives them, relative to the task worktree |
| `hidden` | The runtime directory's `control/` and `config/` |
| `own` | The run's `work/`, `home/` and `tmp/`, in that order. Commands of `grep`, `find` and `ls` start in the first |
| `runtime` | The runtime paths' real paths |
| `git` | The Git administrative paths |
| `primary` | The primary worktree, or the user's home when Workers hands over none |
| `userHome` | The user's real home directory |
| `sandbox` | `sandbox_filesystem`'s lists, with the sandbox-runtime package's `vendor/` added to `allowRead` |
| `programs` | The absolute paths of `rg` and `fd` |
| `groups` | The runtime directory's `control/groups/`, which exists before the first round |
| `limits` | The run's `maxTurns`, and its `maxBudgetUsd` or `null` for no budget |
| `resultSchema` | The [worker result](../workers/contracts.md#contract.workers.worker-result) schema the run composed |

The extension trusts its policy. It checks no field of it. The sandbox lists come from
`sandbox_filesystem`, so both backends share them. The read and write decisions of `pi_policy.ts`
take the policy and a path. They return `null` to allow, or the reason of a denial.
