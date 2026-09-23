# Concorde workflow guide

[← Back to the project overview](../README.md)

Detailed installation, execution, delivery and maintenance reference. Shell commands assume the
Concorde checkout root unless an installed consumer path is shown.

Concorde centers on complete, architecture-aware Specs. Model work runs in native Pi Agents and in
pi workflows run by pi-subagents; deterministic Host code keeps admission, evidence, checks and
lifecycle authority. An Operation has exactly one control-flow kind — Host service, single Agent
call, pi workflow or LangGraph Graph (Graph API only) — and the catalog's eleven Operations, all
public, are the capabilities of the `concorde` tool. The Terminal Agent Operation embeds one Agent
call as a typed LangGraph `StateGraph` node whose trusted Agent service arrives in Runtime context.
An Agent's file, network and credential limits are instructions; the read-only boundary of
configured checks and tester commands is enforced. See the
[Terminal Agent Operation](../specs/concorde/harness/execution/control-flow.md#terminal-agent-operation)
and the [public capabilities](../README.md#choose-an-entry-point).

A Module is a responsibility, not an executable kind. The [Agents Module](../specs/concorde/agents/module.md)
defines the seven Agents and their contracts; [Operations](../specs/concorde/operations/module.md)
holds the Operation catalog and dispatch and contains the Modules that provide Operations. Planning,
Implementation, Review, Validation, Delivery and Issue solving keep their own artifacts and
acceptance rules.

The examples below use **Spec Protocol 12.0.0**. A project's Specs form one graph of declared nodes
and relations. Each Module has an entry `module.md` (Purpose, Terminology, Usage, Design,
Relationships) and may add explanatory topics; precise requirements, scenarios and versioned
contracts live in implementation documents owned by the same Module. Every document has paired
schema-3 `.md.json` metadata, and the entry's metadata declares the Module's own relations in a
`module` block.

A Module has at most one parent (`contains`). A shared provider is owned by none of its consumers;
a consumer declares `uses` and names exactly the promises it `relies_on`. Composition and file
reuse are separate: several Modules may bind the same file, and within one Module the longest
covering realization entry decides a file's realization. Every version-controlled file is bound by
some Module unless it is a document, generated output, external material or a control record.

A Module's context is computed from its own declarations, one level deep; a Markdown link never
imports anything. Assessors, planners and task authors see the names of the Module's files but never
their contents; only code writing and code review receive contents. When a shared file or document
changes, Concorde knows every Module it concerns and checks each one separately.

The Protocol standard is independent of the Specs that implement it:

```text
protocol/                 Independent standard, organized as ordinary chapters
specs/concorde/           Concorde's own Module Specs
.concorde/specs.json      Registry: every Module and a checked mirror of its entry's declarations
```

Start with the [Concorde Module](../specs/concorde/module.md), its
[Usage](../specs/concorde/module.md#usage) and [Design](../specs/concorde/module.md#design), and the
[Spec Protocol](../protocol/README.md). Protocol documents are outside the project Spec registry.
The docsite publishes them in a dedicated **Spec Protocol** tab.

## Install and initialize

The installer is Pi-only. It installs the eleven public capabilities, the rendered instructions of
the seven Agents, the pi workflows of plan, review and Issue solving, and the generic `tester` Task
subagent. The source-only `maintenance-worker` and the coordinator instructions are never consumer
assets. npm is required for the Pi extension dependencies; `python3 scripts/install-concorde.py
--help` lists the installer's options. Capability input is JSON, never positional or flag
arguments.

Install into a Git project and commit your project files, root guidance and the complete Protocol
bundle before initializing. The framework, managed runtime, receipt and `.pi` runtime assets may
stay ignored. A mutation requested from the primary worktree, including an initialization `apply`,
runs in a candidate worktree created from the committed `HEAD`: the Host installs and verifies a
complete local installation there from the exact invoking package, runs the same request with the
candidate's own interpreter and launcher, and returns the candidate's result, whose workspace names
its path, branch and `change_id`. The originating session stays where it is. An initialized
candidate reaches the primary branch like any other change: validate it, deliver it and request the
primary merge separately.

A fresh Pi session in a consumer candidate loads that candidate's own
`.pi/extensions/concorde-session.ts`. Each worktree has its own `.concorde/framework`,
`.concorde/.venv` and `.concorde/install.json`; system Pi and Node may be shared, but no framework or
managed environment is shared or symlinked. Only the primary persists durable status and runs.

Current installations are verified and reused. A failed installation keeps the candidate with a
`blocked` status in the primary. A later call never silently reinstalls missing, stale or
conflicting assets; recover, or install a normal Git-created worktree, with the installer:

```bash
python3 /explicit/provider/.concorde/framework/scripts/install-concorde.py \
  --target /absolute/consumer-worktree --preserve-project --preview
# Inspect the proposal and resolve conflicts, then repeat with --apply.
```

`--preserve-project` keeps existing root instructions and the complete Protocol bundle without
adopting their ownership; it never rewrites the configuration, registry, Specs or accepted binding.
See the [installation contract](../specs/concorde/distribution/installation.md#local-installations-in-worktrees).
Concorde's own source checkouts instead use their own build, development environment and explicit
private session selection, never an installation.

```json
{
    "type_id": "concorde-operation-invocation",
    "schema_version": 3,
    "operation_id": "concorde-init",
    "mode": "execute",
    "configuration": null,
    "input": {
        "type_id": "concorde-init-request",
        "schema_version": 4,
        "data": {
            "action": "propose",
            "name": "My project",
            "configuration": {
                "type_id": "concorde-operation-configuration",
                "schema_version": 2,
                "data": {
                    "model": "openai-codex/gpt-6-astra",
                    "thinking": "medium"
                }
            }
        }
    }
}
```

Send the JSON on stdin to `python3 .concorde/framework/scripts/run-operation.py concorde-init`; the
launcher re-executes itself inside the managed runtime `.concorde/.venv`, so any Python 3.11+ can
start it. `concorde-init` takes its configuration from its request, so the envelope's
`configuration` is null. Review the returned proposal, then send `action: "apply"` with that
complete proposal and the `proposal_digest` returned with it. Apply refuses another or edited
proposal (`invalid_proposal`) and a project whose files changed since the proposal
(`stale_proposal`).

Initialization creates the configuration, the registry and an honest root Module stub. Write its
Purpose, Terminology, Usage, Design and Relationships before precise requirements, scenarios and
implementation. `.concorde/config.json` pins the Protocol, names the registry `.concorde/specs.json`
and lists the project's configured checks. Each Module's relations are declared in its entry's
`module` block; the registry mirrors those blocks, and `validate` rejects any disagreement.

## Run a change

Model-backed capabilities run through the Pi `concorde` tool: `run` with the input returns an exact
native Agent call or workflow, which the user session invokes unchanged and, for a workflow, polls
with `result`. The same request sent to the bare launcher cannot start an Agent and is refused with
`native_required`. The request envelope for planning:

```json
{
    "type_id": "concorde-operation-invocation",
    "schema_version": 3,
    "operation_id": "concorde-plan",
    "mode": "execute",
    "configuration": null,
    "input": {
        "type_id": "concorde-plan-request",
        "schema_version": 1,
        "data": {
            "target_id": "module.transfer",
            "task": "Implement the specified transfer contract"
        }
    }
}
```

A null configuration makes the Host load the initialized settings. The user session reads the
complete Specs, answers questions and edits reading, metadata and registry under its task grant.
Every capability that acts on one Module receives an explicit target; `focus_id` names one of that
Module's scenarios and never trims its context.

`concorde-plan` assesses sufficiency and accepts a revision-bound plan, not a completed change.
The user session may next call `concorde-tasks`, then `concorde-implement`, reviews and validation.
Tasks require a current plan and implementation requires accepted tasks. Work for another Module
that the plan's tasks need is returned as component work and requested separately; no Module
develops its children automatically. A directly edited candidate needs no invented plan, but cannot
bypass unfinished planned work or a review the change requires.

`concorde-spec-review` reviews the Spec itself, including whether every imported term is used with
its owner's meaning. `concorde-code-review` reviews the implementation against its Spec. Each takes
an explicit `target_id` and `task`, with an optional `focus_id`, and runs fresh read-only reviewers
as a pi workflow in the current worktree. The Host returns structured findings and coverage; an
unmanaged Git checkout uses `HEAD` as the diff baseline.

`describe-policy` previews what a request would do without starting an Agent or changing project
state; initialization and configuration use their own propose and apply steps instead. The
primary-owned `.concorde/status/<change_id>.json` records a change's task, phase and status, the
providers' records (plans, progress, gaps, reviews, validation) and its cleanup. Working artifacts
live under `.concorde/work/`.

A blocked change keeps its evidence and names the missing contracts or the refused step. Add
missing promises to the owning Module's Spec and registry under explicit task authority, then call
the step again. Completed component work is reused while its inputs stay current. Partial Spec
changes stay in the candidate; they do not change the primary. A changed Spec or intent makes an
earlier plan or check evidence stale. Unmanaged live worktrees are discovered from Git without
inventing change records, and lifecycle observations never expose another worktree's contents.

To deliver, request `concorde-deliver` from the candidate or the primary worktree with its
`change_id`. The Host checks the candidate and its current integration, creates the branch
`concorde/delivered/<change_id>` and removes the candidate worktree unless `keep_worktree: true` is
given. The primary branch, index and files stay unchanged. Only an explicit user request to merge
into the primary branch authorizes a separate `merge_primary: true` request with the delivered
`change_id`, from the primary worktree. Lifecycle writes and final merges are serialized with a
repository lock and checked against the latest primary commit. Conflicts, failed checks or local
primary edits block the merge and keep the delivery branch; receipts let a retry continue without
merging twice.

For a directly edited candidate without plans, `concorde-validate` checks the whole project and
records readiness in the same change status. Any authored plans and tasks must still be completed.

Configured checks run with operating-system-enforced read-only access to the project, including
ignored files and `.concorde/runs`. Linux needs a system-installed
[bubblewrap](https://github.com/containers/bubblewrap) with working user, mount and PID namespaces
and pidfd support. Where the boundary cannot be set up, checks are refused with
`check_sandbox_unavailable`; there is no unrestricted fallback.

Checks may write only under the supplied `TMPDIR`, `XDG_CACHE_HOME` and `CONCORDE_CHECK_REPORT_DIR`;
`CONCORDE_CHECK_TMPDIR` names each check's own external scratch directory. These files disappear
after the check's process tree exits. Move project cache and report output to those paths, and run
source-changing formatters during implementation. Only the Host saves standard output, standard
error and lifecycle evidence in the project. The boundary does not restrict reads, network or
credentials.

For architecture changes, the user session edits the affected entries, document metadata and
reading together, regenerates the registry mirror (`python3 scripts/concorde.py registry --write`)
and validates the combined result before dependent work. A shared definition has one owner; other
Modules import or rely on it. A file may be listed by several Modules without merging their
responsibilities. A direct edit is never review or completion evidence.

See [Operations](../specs/concorde/operations/module.md) for the catalog and dispatch and
[Request admission](../specs/concorde/harness/admission/module.md) for the request boundary.

## Issues and the docsite

For problems that need tracking across sessions, use `concorde-issues` with `list`, `show`,
`report`, `reopen` or `solve`. [Issues](../specs/concorde/issues/module.md) records bug, gap and
limitation reports; stage blockers and review findings reference those reports. Reporting does not
stop an Agent or start a repair, and a workaround can leave an Issue open.

A `solve` request selects one Issue at its current revision. The Issue solver chooses verification,
a disposition, or a hand-back of the needed development or Spec repair to the caller. Verification
runs fresh Issue-specific and ordinary reviews; when they report blocking findings, the solver's
next decision also receives those findings' reports. Unsettled choices return `needs-decision`. A
close in a candidate is not a claim about the primary. See
[Issue solving](../specs/concorde/issue-solving/module.md).

The docsite publishes one page per document in **Module documents** and **Implementation
documents** tabs following the `contains` tree, with inline diagrams (illustrative ones labelled as
such) and optional source provenance, plus the **Spec Protocol** tab. Terminology import rows show
the imported definition at render time. Each capability and each Graph Spec is read in its owning
Module's Spec. Human navigation grants no extra Agent context.

## Concorde Spec Protocol entry and upgrades

Spec Protocol 12.0.0 defines Module Specs as a checked graph whose realizations bind the files that
realize each Module, and whose scenarios are declared by the tests that verify them. The installer
adds a receipt-owned `concorde-protocol` block to `AGENTS.md` that directs the user session to read
`.concorde/protocol/principles.md`. Agents do not use ambient instruction discovery; they receive the
Protocol through their controlled context, and root guidance never widens their permissions.

Commit the root entry and the complete Protocol bundle with the project, so that candidate worktrees
inherit the guidance and the accepted rule bytes. Their ignored execution assets are installed
locally, not inherited from the primary. The per-candidate `concorde-change-worktree` guidance block
stays local and is stripped at delivery; the `concorde-protocol` block is part of the project. The
installer preserves the root file's bytes outside its block, and reinstalling is idempotent. An
upgrade removes only unchanged receipt-owned outputs the new package no longer ships. Modified or
unowned blocks, ambiguous markers, symbolic links and non-file roots are conflicts. To preview
removing the root entries during uninstallation:

```bash
python3 /path/to/concorde/scripts/install-concorde.py --target /absolute/project --remove-protocol-guidance
```

Add `--apply` to remove those entries and their receipt records. This keeps user text, the
framework and runtime files and every other receipt record; it is not a full uninstaller.

Installing an updated package never rewrites `.concorde/config.json`. A project stays bound to the
Protocol version and digest it accepted, and any capability that loads the Specs refuses a mismatch
with `protocol_mismatch`. To adopt the installed Protocol, call `concorde-configure` with
`action: "propose"` and `accept_protocol: true`, review the proposal, and apply it with its
`proposal_digest`. Rewrite Specs that do not conform to the new Protocol first; changing the binding
is not a migration. In this source checkout the equivalent step is
`python3 scripts/concorde.py protocol-manifest --write --bind-project`. Without `--bind-project`,
`protocol-manifest` only reports whether the tracked manifest matches the current build, or (with
`--write` alone) records the current build's digests in the tracked manifest, leaving the
checkout's binding unchanged.

## Development

Run Python tests with `.venv/bin/python -m pytest`, the single test entry configured in
`pyproject.toml`: it collects every `unittest.TestCase` under `tests/concorde` and runs them on 16
pytest-xdist worker processes by default (`-n 0` runs in-process, `-n <N>` changes the worker
count, a file or node id selects tests, `--durations=20` lists the slowest). The local plugin
`tests/concorde/support/pytest_timing.py`, loaded by the root `conftest.py`, adds the evidence
options `--reason=`, `--scope=`, `--phase=`, `--attempt=`, `--prior=<summary>` and `--json=<path>`,
which writes a summary with input, test, runtime, lock and environment fingerprints, per-unit
queueing and execution intervals and the runtime spans each test wrote to its own
`CONCORDE_DIAGNOSTIC_TIMING_DIR`. Join these values with `=`: pytest picks its rootdir from the
bare arguments before the plugin registers its options, so a separate value that exists as a path
would relocate the rootdir. Run the docsite checks with `npm run typecheck`, `npm test`,
`npm run validate` and `npm run build`. The check and tester boundary tests need Linux with a
trusted system bubblewrap and a Pi installation on `PATH`; they fail rather than skip where the
boundary cannot be enforced.

Tests that install the Pi extensions run `npm ci` offline, so the suite has no online npm path.
Before such an install, `tests/concorde/support/managed_runtime.seed_npm_cache` copies the tarballs
locked by `pi/package-lock.json` into the npm cache in use (`npm_config_cache`, for example a
tester's scratch) from a local populated cache: npm's default cache, which `npm ci --prefix pi`
fills, or the cache named by `CONCORDE_TEST_NPM_CACHE`. Seeding happens once per cache under a file
lock. A tarball found nowhere locally fails the test with the missing input named.

The Agents' definitions under `agents/`, the authored prompts under `prompts/` (including each
capability's guidance under `prompts/operation-guidance/`) and the extensions under `pi/extensions/`
produce this checkout's Agent and session surfaces. Never edit `generated/`, which is untracked
build output; the build never installs into ambient discovery. After changing sources, run the
build and the deterministic checks in the same worktree:

```bash
python3 scripts/concorde.py build
python3 scripts/concorde.py build --check
python3 scripts/concorde.py validate
python3 scripts/concorde.py check-package
.venv/bin/python scripts/development/check-graph-specs.py --catalog concorde.operations.graph_catalog:catalog
```

`build` renders the Agents' instructions, the private session entry with its catalog, the Protocol
assets and the schemas from their sources; `build --check` verifies they are current without
writing; `validate` runs the Spec, registry, coverage and configured-input checks; the Graph Spec
check compares each compiled Graph with its Graph Spec. Every model-backed request needs a fresh
build. A new worktree must be built once before a tester can select its private session entry.
After changing the chapters under `protocol/`, accept the new digest with
`python3 scripts/concorde.py protocol-manifest --write --bind-project`.

[Agents](../specs/concorde/agents/module.md) defines the seven Agents: `context-assessor`,
`planner`, `task-author`, `programmer`, `spec-reviewer`, `code-reviewer` and `issue-solver`. Each
call is prepared by the Host with its context and tools, and its result is accepted by the Host
against the native records and unchanged inputs. The [Pi session](../specs/concorde/session/module.md)
defines the two Task subagents: the source-only `maintenance-worker` and the `tester`, which has
source and consumer instructions. Task subagents own a whole task and are not Agents. The user
session is the external caller that coordinates them.

Concorde maintains itself in candidates. The source user session stays in its initial worktree and
owns the work packages, ownership and testing gates, which are not Concorde `plan`/`tasks`
artifacts. It registers a candidate, launches one fresh `maintenance-worker` there, which edits,
formats, checks and commits and then stops, and binds and releases it through the primary's
`status` command. A separate fresh `tester` may then receive only the candidate's exact private
session entry and embedded catalog, selected with `select-session`. Neither inherits Concorde
catalogs or delegates. Failed tests return to maintenance and then to another fresh tester.
Ordinary Git integration is allowed after the checks and an explicit merge authorization. The
[source-checkout rules](../AGENTS.md) state the details.

Select a candidate's build with `select-session --mode test --pi-entry <absolute-private-entry.ts>
--runtime <absolute-candidate-launcher> --output <absolute-candidate-.concorde/work/selection.json>`
and reverify it with `select-session --verify <absolute-selection>` before launch. A fresh host
supplies `CONCORDE_SESSION_SELECTION`, its own Pi configuration directory, only the returned exact
`-e` entry and all returned discovery-disable flags. Missing or stale artifacts, or a missing
candidate Python environment, block without an ambient fallback. A selection is not proof of
extension loading, tool use or model execution, and never widens the actual task, file or tool
grant. The private entry reverifies it before registration and before every tool call, and the
launcher verifies it again.

Consumers may delegate a complete task to one Task subagent or do a simple authorized task
directly. Agents are not task delegates and never bypass the Host's limits. Task-authorized edits
may include `.concorde` files in the owned workspace when they preserve truthful evidence, task
scope and concurrency safety. The primary-only `.concorde/status/<change_id>.json` records the
change's coordination, delivery or manual merge and separate cleanup; durable runs, including
those of candidates, stay in the primary's `.concorde/runs/`. Terminal status remains after the
candidate is deleted.

## Source-selected installation testing and failed native observation

A private source selection cannot attest a newly installed path. Passing it unchanged into an
installed health check is correctly refused; neither relax the guard nor clear all provenance. For
an explicitly authorized fresh external fixture **inside `test_command` scratch**, the source-only
recipe verifies the governing selection and the admitted package bytes first, separates only the
process-local source provenance and import overrides for the installer and installed children, and
verifies the exact installed output with its own managed interpreter:

```python
from pathlib import Path
import os
from tests.concorde.support.install_output_handoff import install_selected_fixture

source_selection = Path(os.environ["CONCORDE_SESSION_SELECTION"])
record, installed_env = install_selected_fixture(
    Path(os.environ["CONCORDE_CHECK_TMPDIR"]) / "consumer", source_selection
)
# Parent source selection is STILL active. Only explicit installed subprocesses use installed_env.
# Use record["installed"]["python"], ["runtime"], ["entry"] and record["destination"] exactly.
```

Run this under the selected candidate's Python with that source root on the fixture import path;
the helper is not a consumer product or a new selection mode. The target must be fresh, canonical
and within issued scratch. Dependency acquisition needs the normal locked wheel and npm inputs;
offline caches must be readable in the check boundary or acquisition must be explicitly allowed
into issued scratch. `installed-output-provenance.json` binds the source selection and build, the
recipe bytes, the admitted package, the external destination, the installed entry, catalog,
launcher and build, the receipt and runtime and the interpreter. Read and return this record before
scratch cleanup. A native installed smoke test uses the installed entry in a separate process with
`installed_env`, never the source-private entry.

For an authorized live Issue diagnostic, use the checked-in source driver. First run the model-free
path **inside `test_command`**:

```bash
CONCORDE_SESSION_SELECTION="$PWD/.concorde/work/pi-first-diagnostic-selection.json" \
  .venv/bin/python tests/concorde/harness/run_issue_diagnostic.py --selftest \
  --selection "$PWD/.concorde/work/pi-first-diagnostic-selection.json" \
  --sdk /explicit/pi-coding-agent/package --native /explicit/pi-subagents/package
```

Only when the user session authorizes the one live attempt, use the same command with `--live`
instead of `--selftest`, plus `--model codex-lb/gpt-6-astra --auth-source /approved/auth.json
--models-source /approved/models.json`. The model name and both paths are explicit test inputs, not
defaults or permission to inspect other settings. The script keeps the approved mode-0600 scratch
copy of the credentials and a read-only link to the model file, disables ambient resources and
model retries, and drives the SDK's public extension hooks. It never prompts a coordinator model,
runs a second case or retries the Issue workflow. All fixture writes stay in issued scratch.

The driver correlates the issued `d-0` schema, ticket and native launch identity with the failed
child's transcript. Its parser merges assistant tool calls, native tool start and end events and
tool results by call ID and keeps the structured arguments, the complete available error text, the
error status and the terminal reason. A native missing `structured_output` means no successful
submission, not no attempts.

The only final standard output is a selected diagnostic envelope under 8000 UTF-8 bytes. Its
gzip+base64 payload holds the issued schema and the selected calls and results, with a SHA-256 digest
and the decoded and compressed sizes, and never arbitrary transcript text, credentials, environment
or provider registries. Decode it as data — `base64.b64decode`, `gzip.decompress`, SHA-256
verification against `payload.sha256` and `json.loads` — and enforce the declared 256-KiB decoded
bound; the tracked `unpackDiagnostic` helper also bounds decompression. If a complete first failure
cannot fit the export bound, the command refuses to claim complete evidence rather than dropping
its error.

A zero exit of the live diagnostic command means its selected evidence was complete enough to
transport, not that the Issue succeeded. Check `envelope.summary.result` and the decoded native
records separately.
