# Development environment

The root [Module](glossary.json#concept.module) binds the files that set up development of this
checkout: the Python project and lock, the pytest configuration and its evidence plugin, the
reference initializer, the Claude Code documentation fetcher and the docsite type check. These
promises concern how Concorde's own tests and checks run, not what Concorde offers a consumer
project.

## Test evidence

### req.concorde.test-evidence — Test runs record why and on what they ran

The pytest evidence plugin SHALL record each run's reason, scope, phase, attempt and input fingerprints in its JSON report.

Each option has its own default: an omitted `--reason` records `manual`, an omitted `--scope` or
`--phase` `unspecified` and an omitted `--attempt` `1`. The report is written only to the file
`--json=PATH` names, for example
`.venv/bin/python -m pytest tests/concorde/spec --scope=targeted --json=report.json`. It keeps
discovery, queueing and execution times apart and never presents summed parallel test time as
elapsed time.

### scenario.concorde.test-timing — Test runs record reasons and input identity

- GIVEN pytest arguments with or without `--reason`, `--scope`, `--phase`, `--attempt` and `--prior`
- WHEN the suite runs with `--json` reporting
- THEN the report records the reason, scope, phase, attempt, prior run and fingerprints of the tests, inputs, runtime, locks and environment
- AND discovery, queueing, execution and total elapsed times are reported separately
- BUT summed parallel test time is never reported as elapsed time

### req.concorde.test-fingerprints — The fingerprints name what a run examined

The pytest evidence plugin SHALL record in the report's `fingerprint` a digest of the run's examined input files, of its collected tests, of its runtime, of its lock files and of its environment, and one `digest` of those five.

The examined inputs are the files below pytest's root directory that Git tracks or would track
under `src/`, `scripts/`, `tests/`, `prompts/`, `protocol/`, `specs/` and `.concorde/protocol/`,
and the files `CLAUDE.md`, `concorde.json`, `pyproject.toml`, `uv.lock`, `.concorde/config.json`
and `.concorde/specs.json`. `input` digests each such file's path with the SHA-256 of its bytes, and
`lock` the same for those whose path ends in `lock` or `lock.json`. `tests` digests the sorted node
identities of the collected tests; `runtime` the Python version and implementation and the pytest
version, which `runtime_facts` shows; `environment` the operating system, the machine and whether
bytecode writing is disabled, which `environment_facts` shows. Every digest is the SHA-256 of the
JSON of what it covers, with sorted keys. No other file and no environment variable is an input, so
`environment_complete` is always `false`. When Git cannot list the files or one of them cannot be
read, `input_complete` is `false` and `input` is `null`.

### req.concorde.test-prior — A prior run is compared by its fingerprint

When `--prior=PATH` names the summary of an earlier run, the pytest evidence plugin SHALL record that run's `run_id` as `prior_run_id` and, as `same_declared_inputs`, whether the two fingerprints' `digest` values are equal.

`same_declared_inputs` is `null` without `--prior`, and also when this run's input is incomplete or
its runtime facts are unknown, since equal digests would then prove nothing; when it is `true`, the
terminal says so and that the environment is covered only in part. A `--prior` that names no
readable JSON summary object is a usage error, pytest's exit status 4, before any test runs.
`--json=PATH` replaces whatever the file held.

### req.concorde.test-counting — The totals count collected tests

The pytest evidence plugin SHALL count in the report's `totals` one unit per collected test, a unit failing when any of its subtests fails.

Subtests are not counted on their own, so the units sum to the collected count. pytest's own
terminal line lists each failed subtest separately and counts its parent as passed, so its numbers
may differ from the totals; the report's `counting_note` says so.

### scenario.concorde.test-prior-unchanged — A rerun on unchanged inputs is recognized

- GIVEN the summary of a run of some tests
- WHEN the same tests run again with `--prior` naming that summary and no examined input changed
- THEN the new report's `prior_run_id` is the earlier run's `run_id`
- AND its fingerprint `digest` equals the earlier one and `same_declared_inputs` is `true`

### scenario.concorde.test-prior-changed — A rerun on a changed input is told apart

- GIVEN the summary of a run of some tests
- WHEN one examined input file changes and the same tests run again with `--prior` naming that summary
- THEN the new report's `prior_run_id` is the earlier run's `run_id`
- AND its `input` fingerprint differs from the earlier one while its `tests` fingerprint does not
- AND `same_declared_inputs` is `false`

### scenario.concorde.test-prior-unreadable — An unreadable prior summary stops the run

- GIVEN a `--prior` path that does not exist, is not JSON or holds no JSON object
- WHEN pytest runs with it and `--json`
- THEN pytest ends with exit status 4 and an error naming the `--prior` value
- AND no test runs and no report is written

### scenario.concorde.test-counting — A failed subtest fails its one unit

- GIVEN a test with three subtests, one of which fails, and a passing test
- WHEN they run with `--json` reporting
- THEN the report has one failed and one passed unit and counts no subtest on its own
- AND its `counting_note` says that subtests are not counted on their own

## External references

The third-party documentation and source that Modules include as `external` live under
`references/`. The Claude Code documentation is tracked as plain files under
`references/claude-code/`, refreshed by `scripts/development/fetch-claude-code-docs.py` as the
[documentation refresh](#documentation-refresh) below says. The pi, sandbox-runtime, pi-packages,
swe-bench, langgraph and langgraph-docs references are Git submodules pinned in
`.gitmodules` to the versions Concorde was built against, each with a sparse-checkout pattern
(`concorde-sparse`) that keeps only the documentation and source a reader needs. `langgraph` is
the LangGraph release `uv.lock` locks, and `langgraph-docs` the LangChain documentation
repository, whose LangGraph pages match that release; when the lock moves to another LangGraph
release, both move with it. `scripts/development/init-references.py` checks them out,
without their media, at exactly the recorded commits. A reference counts as checked out only when
its clone is at the recorded commit: a clone left elsewhere, such as one whose fetch of that
commit failed, is completed in place on the next run, which fetches the commit when the clone
lacks it, checks it out and names the commit it found; with `--check` it is reported as not at
the recorded commit.

A submodule's registration, its `url` and `active` settings, lives in the repository's shared
`.git/config`, which every worktree reads. Each task session prepares its own worktree, so several
may run the initializer at once; it registers only a submodule that is not registered yet, so the
usual preparation reads that file and never needs its lock, which another worktree's registration
holds meanwhile. When a submodule still needs registering while that lock is held, the initializer
stops before it clones any submodule, so that a worktree is never left with some references checked
out and others not.

### scenario.concorde.references-registered-once — Registered submodules are checked out while the configuration is locked

- GIVEN a worktree of this repository whose reference submodules are all registered in the shared `.git/config` but not checked out
- AND another worktree's preparation holding `.git/config.lock` of the shared Git directory
- WHEN `scripts/development/init-references.py` runs in that worktree
- THEN it checks out every submodule at the commit the worktree records
- AND it leaves `.git/config` unwritten and the lock in place

### scenario.concorde.references-unregistered-refused — An unregistered submodule stops the checkout while the configuration is locked

- GIVEN a worktree of this repository whose reference submodules are not checked out, one of them not registered in the shared `.git/config`
- AND another worktree's preparation holding `.git/config.lock` of the shared Git directory
- WHEN `scripts/development/init-references.py` runs in that worktree
- THEN it stops before cloning any submodule, registered or not, so that no reference is checked out
- AND its error names the unregistered submodule and the lock, says another Git command writing the shared configuration holds it, to run it again once that command ends and never to delete the lock
- AND it leaves `.git/config` unwritten and the lock in place

### scenario.concorde.references-registered-when-free — An unregistered submodule is registered while the configuration is free

- GIVEN a worktree of this repository whose reference submodules are not checked out, one of them not registered in the shared `.git/config`
- AND no lock held on `.git/config`
- WHEN `scripts/development/init-references.py` runs in that worktree
- THEN it registers that submodule as active in the shared `.git/config`
- AND it checks out every submodule

### scenario.concorde.references-completed — A clone whose fetch failed is completed on the next run

- GIVEN a worktree of this repository whose reference clone exists but sits on another commit than the one the worktree records, as a run whose fetch of that commit failed leaves it
- WHEN `scripts/development/init-references.py --check` runs there
- THEN it reports that reference as not at the recorded commit, naming the commit it is at, and exits 1
- AND when `scripts/development/init-references.py` runs there, it checks out the recorded commit in that clone and says so, naming the commit it found
- AND the worktree then shows no change of the reference

### Documentation refresh

`scripts/development/fetch-claude-code-docs.py` takes no argument. It reads the index
`https://code.claude.com/docs/llms.txt` and fetches, as Markdown, every page below `/docs/en/` that
the index lists; it refuses an index that lists no such page or names a page path with `..`. The
snapshot holds each page at its path below `references/claude-code/`, the index as `llms.txt` and
`SOURCE.json`, which records the index address, the UTC time of the fetch and the list of pages. The
script commits nothing: the developer reviews the change and commits it.

### req.concorde.docs-refresh-whole — A documentation refresh is published whole or not at all

The documentation fetcher SHALL replace `references/claude-code/` only with a complete snapshot, and leave it unchanged when a page cannot be fetched or the snapshot cannot be written.

Every page is fetched before anything is written; the snapshot is written into a temporary
directory beside `references/claude-code/` and swapped in only once complete, and the temporary
directories are removed either way. A file of the previous snapshot that the index no longer lists
is therefore gone after a refresh. A refused refresh exits with status 1 and names on standard error
every page it could not fetch, or the write that failed.

### scenario.concorde.docs-refresh-replaces — A refresh replaces the snapshot whole

- GIVEN `references/claude-code/` holding a snapshot with a page the index no longer lists
- WHEN the documentation fetcher runs and fetches every page the index lists
- THEN `references/claude-code/` holds exactly the listed pages, `llms.txt` and `SOURCE.json`
- AND the page no longer listed is gone and no temporary directory is left beside it

### scenario.concorde.docs-refresh-failed-unchanged — A failed refresh leaves the snapshot as it was

- GIVEN `references/claude-code/` holding a snapshot
- WHEN the documentation fetcher runs and a page cannot be fetched, or a file of the new snapshot cannot be written, or the new snapshot cannot be moved into place
- THEN it exits with status 1 and says why on standard error
- AND `references/claude-code/` holds exactly the files it held before, unchanged, and no temporary directory is left beside it

## Agent instructions

A session in this checkout, [main agent](glossary.json#concept.main-agent) or
[task session](glossary.json#concept.task-session), works as in any Concorde project, plus the
rules for developing Concorde itself. Both come as skills the build renders: `concorde`, the
[main-session guidance](glossary.json#concept.main-session-guidance) the installer places in every
project, and `concorde-development`, rendered from `prompts/development/skill.md`, which includes
Dogfooding's rule for observing runs. Skills load on demand, so `CLAUDE.md` keeps a short part that
is always in context: the instruction to load both skills before any work, the core rules of the
main agent and of a task session, and the import of the glossary. The main agent and its task
sessions are Claude Code sessions, which find the skills through `.claude/skills/<name>`, links
into `generated/skills/`; in a worktree not built yet, the instructions say to build first and to
read the rendered files directly.

### scenario.concorde.development-skills — Sessions in this checkout load both skills

- GIVEN this checkout, its primary worktree or a task worktree, after a build
- WHEN a Claude Code session starts there
- THEN `CLAUDE.md` tells it to load the `concorde` and `concorde-development` skills before any work
- AND `.claude/skills/concorde` and `.claude/skills/concorde-development` link to the folders of `generated/skills/` that hold the rendered skills
- AND `concorde-development` states Dogfooding's rule for observing runs word for word

## Docsite type check

### scenario.concorde.check-docsite-external — The docsite type check works on a disposable copy

- GIVEN this checkout with its docsite
- WHEN `scripts/development/check-docsite-types.py` runs
- THEN it copies the docsite to a temporary directory, derives the sidebar from the project registry there and runs the TypeScript compiler on the copy
- AND dependency installation and generated files stay inside that copy
- AND the command returns the compiler's exit status and removes the copy
