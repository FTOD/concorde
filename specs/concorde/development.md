# Development environment

The root [Module](glossary.json#concept.module) binds the files that set up development of this
checkout:

- The Python project and lock.
- The pytest configuration and its evidence plugin.
- The reference initializer.
- The Claude Code documentation fetcher.
- The docsite type check.
- The part dependency check.
- The style check of the prompts.

These promises concern how Concorde's own tests and checks run, not what Concorde offers a consumer
project.

## Test evidence

### req.concorde.test-evidence — Test runs record why and on what they ran

The pytest evidence plugin SHALL record these details of each run in its JSON report:

- Reason.
- Scope.
- Phase.
- Attempt.
- Input fingerprints.

Each option has its own default:

- An omitted `--reason` records `manual`.
- An omitted `--scope` or `--phase` records `unspecified`.
- An omitted `--attempt` records `1`.

`--reason` accepts these values:

- `manual`.
- `local-edit`.
- `coherent-change`.
- `stable-final`.
- `changed-input`.
- `failure`.
- `independent`.
- `bootstrap`.

`--scope` accepts these values:

- `unspecified`.
- `targeted`.
- `full`.

`--phase` accepts these values:

- `unspecified`.
- `maintenance`.
- `tester`.
- `postcommit`.

For any other value, pytest refuses with its usage message. The report is written only to the file
`--json=PATH` names. An example is
`.venv/bin/python -m pytest tests/concorde/spec --scope=targeted --json=report.json`.
The plugin keeps these times apart:

- Discovery.
- Queueing.
- Execution.

It never presents summed parallel test time as elapsed time.

### scenario.concorde.test-timing — Test runs record reasons and input identity

- GIVEN pytest arguments with or without `--reason`, `--scope`, `--phase`, `--attempt` and `--prior`
- WHEN the suite runs with `--json` reporting
- THEN the report records the reason, scope, phase, attempt, prior run and fingerprints of the tests, inputs, runtime, locks and environment
- AND discovery, queueing, execution and total elapsed times are reported separately
- BUT summed parallel test time is never reported as elapsed time

### req.concorde.test-fingerprints — The fingerprints name what a run examined

The pytest evidence plugin SHALL record these digests in the report's `fingerprint`:

- A digest of the run's examined input files.
- A digest of its collected tests.
- A digest of its runtime.
- A digest of its lock files.
- A digest of its environment.
- One `digest` of those five.

The examined inputs are regular files below pytest's root directory. They are not symbolic links.
They are the files that Git tracks or would track under these directories:

- `src/`.
- `scripts/`.
- `tests/`.
- `prompts/`.
- `protocol/`.
- `specs/`.
- `.concorde/protocol/`.

They also include these files:

- `CLAUDE.md`.
- `concorde.json`.
- `pyproject.toml`.
- `uv.lock`.
- `.concorde/config.json`.
- `.concorde/specs.json`.

When a path Git lists is no such file, it is no input. Examples are a tracked file deleted from
the working tree or a symbolic link. Its absence from the inputs is what changes their digest.
No other file and no environment variable is an input, so `environment_complete` is always `false`.
When Git cannot list the files or a file cannot be read, `input_complete` is `false`.
In that case, `input` is `null`.

Each digest of the fingerprint is the lowercase hexadecimal SHA-256 of one JSON value's UTF-8
bytes. The value is written as Python's `json.dumps(value, sort_keys=True)` writes it:

- Object keys are sorted.
- Items have `", "` between them.
- A key and its value have `": "` between them.
- Every character outside ASCII is escaped as `\uXXXX`.

Sorting the keys makes the order in which files are listed or read irrelevant. The value each
digest covers is:

| Digest | JSON value |
| --- | --- |
| `input` | an object mapping each examined input's path, relative to the root with `/` between its names as Git lists it, to the lowercase hexadecimal SHA-256 of its bytes |
| `lock` | the same object, restricted to the paths that end in `lock` or `lock.json` |
| `tests` | the array of the collected tests' node identities, sorted |
| `runtime` | `{"implementation", "pytest", "python"}`: the Python implementation, the pytest version and the Python version, which `runtime_facts` shows; `null` when they are unknown |
| `environment` | `{"bytecode_disabled", "machine", "platform"}`: whether bytecode writing is disabled, the machine and the operating system, which `environment_facts` shows |
| `digest` | `{"environment", "input", "lock", "runtime", "tests"}`: the five digests above, `input` being `null` when the input is incomplete |

For a run that collected only `t.py::A::test_one`, the `tests` digest is the SHA-256 of
`["t.py::A::test_one"]`. That digest is
`8aa528e6d583124b22694dd542edd2390a7c00000f0c58574a450be32829bbf5`.

### req.concorde.test-prior — A prior run is named by its report

When `--prior=PATH` names the JSON report of an earlier run, the pytest evidence plugin SHALL record that report's `run_id` as `prior_run_id`.

The report `--prior` names is one this plugin wrote with `--json`.
When any of these conditions holds, pytest treats `--prior` as a usage error before any test runs:

- Its file cannot be read.
- Its file is not JSON.
- Its file holds no JSON object.
- Its object holds no string `run_id`.
- Its object holds no `fingerprint` object with a string `digest`.

In that case, the exit status is 4.
Without `--prior`, `prior_run_id` is `null`. `--json=PATH` replaces whatever the file held.

### req.concorde.test-prior-compare — A prior run is compared by its fingerprint

When `--prior=PATH` names the JSON report of an earlier run, the pytest evidence plugin SHALL record as `same_declared_inputs` whether that report's fingerprint `digest` equals this run's when this run's input is complete and its runtime facts are known, and `null` otherwise.

Without `--prior` too, `same_declared_inputs` is `null`. Since equal digests of incomplete input or
unknown runtime facts prove nothing, this value is `null`. When it is `true`, the terminal says
so. In that case, the terminal also says that the environment is covered only in part.

### req.concorde.test-counting — The totals count the tests that ran

The pytest evidence plugin SHALL count in the report's `totals` one unit per collected test that ran, a unit failing when any of its subtests fails, beside the number of collected tests as `collected`.

When every collected test runs, the units sum to the collected count because subtests are not
counted on their own. When a run stops early through `-x` or a crashed xdist worker, it has fewer
units (`tests`) than `collected`. Since a test that never ran has no times or outcome to report, it has
no unit. pytest's own terminal line lists each failed subtest separately. Since pytest counts the
parent as passed, its numbers may differ from the totals. The report's `counting_note` says so.

### scenario.concorde.test-prior-unchanged — A rerun on unchanged inputs is recognized

- GIVEN the report of a run of some tests whose input was complete and whose runtime facts were known
- WHEN the same tests run again with `--prior` naming that report, on the same Python, pytest, operating system and machine, with bytecode writing disabled or not as before
- AND no examined input changed and every one could be read
- THEN the new report's `prior_run_id` is the earlier run's `run_id`
- AND its fingerprint `digest` equals the earlier one and `same_declared_inputs` is `true`

### scenario.concorde.test-prior-changed — A rerun on a changed input is told apart

- GIVEN the report of a run of some tests whose input was complete and whose runtime facts were known
- WHEN one examined input file changes and the same tests run again with `--prior` naming that report, on the same Python, pytest, operating system and machine
- AND every examined input could be read
- THEN the new report's `prior_run_id` is the earlier run's `run_id`
- AND its `input` fingerprint differs from the earlier one while its `tests` fingerprint does not
- AND `same_declared_inputs` is `false`

### scenario.concorde.test-prior-unreadable — An unusable prior report stops the run

- GIVEN a `--prior` path that does not exist, is not JSON, holds no JSON object, or holds an object without a `run_id` or without a fingerprint `digest`
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
`references/claude-code/`. It is refreshed by `scripts/development/fetch-claude-code-docs.py` as the
[documentation refresh](#documentation-refresh) below says. These references are Git submodules:

- pi.
- sandbox-runtime.
- pi-packages.
- swe-bench.
- langgraph.
- langgraph-docs.

They are pinned in `.gitmodules` to the versions Concorde was built against. Each has a
sparse-checkout pattern (`concorde-sparse`) that keeps only the documentation and source a reader
needs. `langgraph` is the LangGraph release `uv.lock` locks. `langgraph-docs` is the LangChain
documentation repository. Its LangGraph pages match that release. When the lock moves to another
LangGraph release, both move with it. `scripts/development/init-references.py` checks them out,
without their media, at exactly the recorded commits.

When its clone is at the recorded commit, and only then, a reference counts as checked out. On the
next run, a clone left elsewhere is completed in place. One example is a clone whose fetch of that
commit failed. Completion follows these steps:

- When the clone lacks the commit, the initializer fetches it.
- The initializer checks out the commit.
- The initializer names the commit it found.

With `--check`, the initializer reports such a clone as not at the recorded commit.

A submodule's registration lives in the repository's shared `.git/config`. It consists of its
`url` and `active` settings. Every worktree reads that file. Each task session prepares its own
worktree, so several may run the initializer at once. When a submodule is not registered yet, and
only then, the initializer registers it. Therefore, the usual preparation reads that file and
never needs its lock. Another worktree's registration holds that lock meanwhile. When a
submodule still needs registering while that lock is held, the initializer stops before cloning any
submodule, so that a worktree is never left with some references checked out and others not.

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
`https://code.claude.com/docs/llms.txt`. It fetches every page below `/docs/en/` that the index
lists. It fetches each page as Markdown. When an index lists no such page or names a page path
with `..`, the script refuses it. The snapshot holds these items:

- Each page at its path below `references/claude-code/`.
- The index as `llms.txt`.
- `SOURCE.json`, which records the following details:
  - The index address.
  - The UTC time of the fetch.
  - The list of pages.

The script commits nothing. The developer reviews the change. The developer commits it.

### req.concorde.docs-refresh-whole — A documentation refresh is published whole or not at all

The documentation fetcher SHALL replace `references/claude-code/` only with a complete snapshot, and leave it unchanged when a page cannot be fetched or the snapshot cannot be written.

Every page is fetched before anything is written. The snapshot is written into a temporary
directory beside `references/claude-code/`. When the snapshot is complete, and only then, it is
swapped in.
The temporary directories are removed either way. A file of the previous snapshot that the index
no longer lists is therefore gone after a refresh. A refused refresh exits with status 1.
On standard error, it names each failure:

- Every page it could not fetch because the request failed.
- Every page it could not fetch because its body was cut short.
- The write that failed.

Before any page is fetched, the script refuses an index listing a page whose name would lead
outside the snapshot. Such a name is absolute or has a `..` component. When both the swap and
moving the previous snapshot back fail, and only then, the directory is left changed. In that
case, the refusal says so. It names where the previous snapshot is kept. That snapshot is not removed.

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

A session in this checkout works as in any Concorde project. The session is a
[main agent](glossary.json#concept.main-agent) or
[task session](glossary.json#concept.task-session).
It also follows the rules for developing Concorde itself. Both sets of rules come as skills the
build renders:

- `concorde`, the project skill composed of the installed parts' sections
  ([req.distribution.composed-guidance](distribution/requirements.md#req.distribution.composed-guidance)).
  With every part installed, as in this checkout, it holds the
  [main-session guidance](glossary.json#concept.main-session-guidance).
- `concorde-development`, rendered from `prompts/development/skill.md`.
  It includes Dogfooding's rule for observing runs
  ([req.dogfooding.one-observation-rule](dogfooding/requirements.md#req.dogfooding.one-observation-rule)).

Skills load on demand, so `CLAUDE.md` keeps a short text that is always in context. It contains:

- The instruction to load both skills before any work.
- The core rules of the main agent and of a task session.
- The import of the glossary.

The main agent and its task sessions are Claude Code sessions. They find the skills through
`.claude/skills/<name>`, links into `generated/skills/`. Git does not track the links, and
`.gitignore` ignores them. The reference initializer `scripts/development/init-references.py`, the
first step of a worktree's preparation, makes them:

- It creates each missing link.
- It replaces a link that points elsewhere.
- It leaves a real file or directory in the place of a link as it is, and says so.

With `--check`, it reports the links and changes nothing. In a worktree not prepared yet, the
instructions say to run the initializer and the build first. They then say to read the rendered
files directly.

### scenario.concorde.development-skills — Sessions in this checkout load both skills

- GIVEN this checkout, its primary worktree or a task worktree, after its preparation
- WHEN a Claude Code session starts there
- THEN `CLAUDE.md` tells it to load the `concorde` and `concorde-development` skills before any work
- AND `.claude/skills/concorde` and `.claude/skills/concorde-development` link to the folders of `generated/skills/` that hold the rendered skills
- AND Git tracks neither link
- AND `concorde-development` states Dogfooding's rule for observing runs word for word ([req.dogfooding.one-observation-rule](dogfooding/requirements.md#req.dogfooding.one-observation-rule))

### scenario.concorde.skill-links-prepared — The reference initializer links the skills and never replaces a real directory

- GIVEN a worktree of this repository without the link `.claude/skills/concorde`, with `.claude/skills/concorde-development` a link to another place
- WHEN `scripts/development/init-references.py --check` runs there
- THEN it reports both links as not linked, changes nothing and exits 1
- AND when `scripts/development/init-references.py` runs there, each is a link to its folder of `generated/skills/`, and a second run changes nothing
- AND when a real directory stands at `.claude/skills/concorde` instead, the initializer leaves it and its contents as they are and says so

## Style of the prompts

The Markdown under `prompts/` follows the Spec Protocol's *Sentence style* (`protocol/style.md`).
This is an extra requirement of Concorde's own checkout, not a rule of the Protocol. The prompts
are no [Spec](glossary.json#concept.spec) documents. `concorde spec-validation` never reads them.
Models read the prompts. The same short sentences serve a model as they serve a person.
The [development guidance](module.md#realization.concorde.development-guidance) states the
requirement. `scripts/development/check-style.py` measures it with the checks that Spec core uses
for the Specs. It also measures any other Markdown it is given, such as the Protocol's chapters
under `protocol/`. A change of a prompt adds no new style problem to it.

### scenario.concorde.check-style — The style check measures Markdown that is no Spec

- GIVEN Markdown files with a sentence of more than 35 words, a semicolon in prose and a sentence with two requirement keywords
- WHEN `scripts/development/check-style.py` runs on them
- THEN it prints each problem with its path, line and rule, then the count of each rule and of each file
- AND the problems are those that Spec core's style checks report for the same text
- AND it exits with status 1, and with status 0 for files without a problem

## Docsite type check

### scenario.concorde.check-docsite-external — The docsite type check works on a disposable copy

- GIVEN this checkout with its docsite
- WHEN `scripts/development/check-docsite-types.py` runs
- THEN it copies the docsite to a temporary directory, derives the sidebar from the project registry there and runs the TypeScript compiler on the copy
- AND dependency installation and generated files stay inside that copy
- AND the command returns the compiler's exit status and removes the copy

## Part dependency check

Each [part](glossary.json#concept.part)'s code is one directory of `src/concorde/`:

- `spec/`.
- `kernel/`.
- `worker_harness/`.
- `execution/`.
- `workflows/`.
- `issues/`.
- `coordination/`.
- `method/`.
- `distribution/`.

`__main__.py` counts as Distribution's code. `dogfooding/` counts as no part. A part's code also
includes the Python files outside that tree that its registration ships under `install.files`.
One example is `scripts/issues.py` of the issues part.

The part dependency check is one of the development environment's tests. It reads the allowed
directions from the table of
[req.concorde.part-dependencies](requirements.md#req.concorde.part-dependencies).
When a `concorde.*` import crosses from that code to a part its own part does not depend on, the
check fails without exception. This covers imports at module or function level. It includes the
`"module:attribute"` strings a catalog imports by name. An
[optional integration](glossary.json#concept.optional-integration) imports no code of the part it
uses. Distribution depends on no part. It reaches a part's code only by the names its registration
gives. The check requires each name to lie in that part's own directory.

Dogfooding's code imports no part. No part imports Dogfooding's code. Distribution reaches
Dogfooding through one entry, by name: the package descriptor's `develop.check`. The check requires
that entry to name Dogfooding's code. This is the reliance Distribution's `uses` of Dogfooding
declares. The check also checks the registrations. Each names its part. Each names exactly the
dependencies that table gives it.
