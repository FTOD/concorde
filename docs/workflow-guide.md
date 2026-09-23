# Concorde workflow guide

[← Back to the project overview](../README.md)

Detailed installation, execution, delivery and maintenance reference. Shell commands assume
the Concorde checkout root unless an installed consumer path is shown.

Concorde centers on complete architecture-aware Specs. Native Pi Agents and authored pi-subagents
workflows perform cognition; finite Host services retain admission, evidence, checks and lifecycle
authority. LangGraph Operations are explicitly selected StateGraph boundaries, not mirrors or mandatory
schedulers for native capabilities. Native file/network/credential policy is prompt-level; tester and
configured-check subprocess isolation remains enforced. See the
[Terminal Agent Operation](../specs/concorde/harness/execution/module.md#concept.execution.terminal-agent-operation)
and [public capability examples](../README.md#choose-an-entry-point).

A Module is a responsibility, not an executable kind. The [Agents Module](../specs/concorde/agents/module.md)
is the entry for callable Pi Agents and their interaction contracts; [Operations](../specs/concorde/operations/module.md)
covers genuine StateGraph composition. Native workflows compose Agents without becoming Operations.
Public `concorde-*` names and `operation_id` fields are compatibility entry identifiers, not backend claims.
Planning, Implementation, Review and Issues retain their business artifacts and acceptance rules.

The work and delivery examples below use **Spec Protocol 11.0.0**. A project's Specs form one
graph of declared nodes and relations. Each Module has an entry `module.md` (Purpose, Terminology,
Usage, Design, Relationships) and may add explanatory topics; precise requirements, scenarios and
versioned contracts live in implementation documents owned by the same Module. Every document has
paired schema-3 `.md.json` metadata, and the entry's metadata declares the Module's own relations in
a `module` block.

A Module has at most one parent (`contains`). A shared provider is owned by none of its consumers;
a consumer declares `uses` and may name exactly the promises it `relies_on`. Composition and file
reuse are separate: several Modules may bind the same file, and within one Module the longest
covering realization entry decides a file's realization. Every version-controlled file is bound by
some Module unless it is a document, generated output, external material or a control record.

A Module's context is computed from its own declarations, one level deep; a Markdown link never
imports anything. Assessors, planners and task authors see the names of the Module's files but never
their contents; only code writing and code review receive contents. When a shared file or document
changes, Concorde knows every Module it concerns and checks each one separately.

The Protocol standard is independent of the software Specs that implement it:

```text
protocol/                 Independent standard, organized as ordinary chapters
specs/concorde/           Concorde's own Module Specs
.concorde/specs.json      Registry: every Module and a checked mirror of its entry's declarations
```

Start with the [Concorde Module](../specs/concorde/module.md), its
[Usage](../specs/concorde/module.md#usage) and
[Design](../specs/concorde/module.md#design), and the
[Spec Protocol](../protocol/README.md). The
[authored Protocol rules](../protocol/principles.md) define the standard. Protocol documents are
outside the project Spec registry and do not need to satisfy their own Module format.
The docsite publishes them in a dedicated **Spec Protocol** tab.

## Install and initialize

The Pi-only installer distributes eleven public capability entries, seven Domain
Agents, the consumer tester Task subagent and authored plan/review/Issue workflows. Source-only maintenance and
coordinator instructions are not consumer assets. Canonical Domain Agent definitions and native preludes
render into owned `generated/native/` assets. The user session prepares with `concorde`, invokes the exact returned
native call, and separately observes Host acceptance. Host tools run without a model. Internal wire
spellings do not assert LangGraph execution. npm is required for the Pi extension dependencies.
Check `python3 scripts/install-concorde.py --help` for installation
administration. Project task inputs use JSON, not positional or flag arguments. Install into a Git
project and commit project inputs, root guidance and the complete Protocol bundle, then invoke the
paired init entry. Framework, managed environment, receipt and `.pi` runtime assets may be ignored;
committing installed binaries is not a prerequisite. A mutation requested from the primary worktree,
including an initialization `apply`, prepares a linked worktree from committed HEAD, installs and
verifies a complete local installation from the exact invoking package before execution, runs the
same request through that candidate's own managed interpreter and launcher and
returns the candidate's result; its workspace names the candidate's path, branch and change_id, with
which the same session continues the change. The originating session never follows the task into a
different checkout. An initialized candidate reaches the primary branch like any other change:
validate it, deliver it, and request the primary merge separately.

A fresh Pi session in that consumer candidate can load its own `.pi/extensions/concorde-session.ts`
and use all eleven public capability entries. Normal Pi project trust applies; accept the local extension
only after reviewing it. Each worktree has its own `.concorde/framework`, `.concorde/.venv` with
independent Python/TypeBox dependencies, and `.concorde/install.json`. System Pi/Node may be shared,
but no Framework or managed environment is shared, symlinked to primary or temporarily staged.
Local execution does not fork lifecycle authority: only primary persists durable status and runs.

Current installations are verified and reused without dependency acquisition or receipt/marker
rewrites. A failed bootstrap retains the candidate and its primary-owned blocked status. A later
call does not silently reinstall missing, stale or conflicting local assets. Use the supported
installer explicitly to recover, or to install a normal Git-created consumer worktree:

```bash
python3 /explicit/provider/.concorde/framework/scripts/install-concorde.py \
  --target /absolute/consumer-worktree --preserve-project --preview
# Inspect the proposal and resolve conflicts, then repeat with --apply.
```

The provider is an explicit verified source or installed package, never a global-name lookup or
an execution fallback. `--preserve-project` preserves existing root instructions and the complete
Protocol bundle without adopting inherited ownership; it does not rewrite config, registry, Specs
or the accepted binding. Partial bundles and modified locally owned assets conflict. Installation
must finish and verify before project/Protocol admission and worker launch. See the
[installation contract](../specs/concorde/distribution/installation.md#installing-another-worktree)
for preservation, locking and retry limits. Concorde source checkouts instead use their own build,
local development environment and explicit private Pi selection; they receive no ambient install.

```json
{
    "type_id": "concorde-operation-invocation",
    "schema_version": 3,
    "operation_id": "concorde-init",
    "mode": "execute",
    "configuration": {
        "type_id": "concorde-operation-configuration",
        "schema_version": 2,
        "data": { "model": "openai-codex/gpt-6-astra", "thinking": "medium" }
    },
    "input": {
        "type_id": "concorde-init-request",
        "schema_version": 3,
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

Send the JSON on stdin to `python3 .concorde/framework/scripts/run-operation.py concorde-init`;
the launcher re-executes itself inside the managed runtime `.concorde/.venv`, so any Python 3.11+
can start it.
Review the returned proposal, then send action apply and that complete proposal. Initialization creates
an honest reading/metadata pair. Supply Purpose, Terminology, Usage, Design and Relationships before precise
requirements/scenarios and implementation. Topic documents have their own metadata companions and
need not repeat the entry template. All selected pairs enter context whole.
`.concorde/config.json` pins the Protocol, names the registry `.concorde/specs.json` and lists the
project's deterministic checks. Each Module's relations are declared in its entry's `module` block;
the registry lists every Module and mirrors those blocks, and `validate` rejects any disagreement.
Arbitrary nearby Markdown is not context.
Document declarations are likewise checked against reverse registry membership.

## Run a change

The compatibility request envelope for planning is shown below. Execute planning through the Pi
`concorde` tool: action run with the input data prepares an exact native workflow call; invoke that
call unchanged and poll action result. Sending this envelope to the bare Python launcher cannot
start a native workflow and refuses with `native_required`:

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

Null configuration asks the trusted host to load initialized settings. The caller reads and
selects complete Specs directly, answers questions and edits reading, metadata and registry under
its task grant. Every bounded domain invocation receives an explicit Module target; `focus_id` is an
optional scenario of that Module, never permission to trim its context.

`concorde-plan` assesses sufficiency and accepts a revision-bound plan, not a completed change.
The caller may next select `concorde-tasks`, then `concorde-implement`, reviews and validation.
Tasks require a current plan and implementation requires accepted tasks. The caller selects
component work separately; no parent develops children automatically. Direct manual candidates
need no invented plan, but cannot bypass unfinished planned work or already-required reviews.

The typed inventory distinguishes native Agents, Agent entries, Workflows and Host services.
Only explicitly selected StateGraph Operations have graph State contracts. Canonical Agents carry
their profiles without Python State/run aliases; capability wire adapters retain compatibility fields. `bound` receives one selected Module without context expansion; `none` performs
deterministic host work without worker context selection. Discovery, automatic Spec authoring,
topology proposal/application and development-loop entries are retired, not aliases. `PUBLIC`
controls entry availability independently of these guarantees.

`concorde-spec-review` reviews the specification itself, including every imported terminology
restatement's semantic consistency with its canonical definition. Different wording is allowed.
`concorde-code-review` reviews or diagnoses the admitted implementation against its Spec. Each
separate native review workflow accepts an explicit `target_id` and `task`, with optional local `focus_id`.
Each binds the selected Module and starts its own fresh read-only reviewer in the current
worktree, without requiring a development change or preexisting Issue. The host returns structured
findings and coverage; unmanaged Git checkouts use HEAD as the diff baseline.

No public capability returns a context manifest; where supported, `describe-policy` mode previews
its stage grants without launching an Agent or mutating project state. Initialization and
configuration use their explicit proposal/apply contracts instead of a policy preview. A stable
task ID names one workspace: a candidate, or primary for direct consumer work. The primary-owned
`.concorde/status/<change_id>.json` records
its task, phase/status, per-target plans and progress, gaps and verified revision. Auxiliary artifacts
live under `.concorde/work/`; there is no separate attempt lifecycle.
Context solving reports missing or inconsistent local dependency promises as structured Module Spec
gaps before planning or task generation.

A blocked change preserves evidence and names missing contracts or failed admission. Edit missing
promises directly in the owning paired Spec and registry under explicit task authority, reconcile affected consumer/provider views and resolve a
new context. Completed component work can be resumed when its bound inputs remain current. Partial
Spec changes stay in the explicitly marked candidate worktree; they do not change the accepted
primary revision. Changed Spec/intent invalidates stale plan or check evidence.
The primary keeps stable task records, including terminal outcomes, under `.concorde/status/`;
unmanaged live worktrees are discovered from Git without inventing task records. Inspect status
directly; lifecycle observations do not expose other worktrees' Spec or implementation contents. Secondary worktree guidance also points
to the primary-owned status and primary worktree, without granting access to other worktrees' contents.

To deliver, request `concorde-deliver` from the selected source or primary worktree with its
change_id. The host checks the candidate and current integration, creates the independent branch
`concorde/delivered/<change_id>`, and removes the source worktree by default. `keep_worktree:true`
explicitly retains it; otherwise the source agent ends its session after delivery. The primary
branch, index and project files stay unchanged, including any local edits. The caller establishes current readiness
through selected evidence; no automatic development sequence delivers.

Only an explicit user request to merge into the primary branch authorizes a separate
`merge_primary:true` request with the delivered change_id, from the primary worktree's sole writing
agent. Other agents develop in linked worktrees. The host serializes lifecycle writes and final
merges with a shared repository lock and checks integration against the latest primary commit.
Conflicts, failed checks or local primary edits block final merging and preserve the delivery
branch. Receipts distinguish staging, cleanup and final merging, allowing retries without duplicate
merges; after source removal, use the primary session to retry.

Issue reporting is independent of task control. Explicit solving uses a native workflow with
Issue-specific reviews; the solver can make evidence-grounded dispositions without a mandatory
human gate, and asks only for genuinely unsettled decisions. Solving stops at ready, not delivery.

For a directly authored candidate without generated plans, `concorde-validate` checks the whole project and records readiness in the
same worktree state. Any already authored plans and tasks must still be completed. No placeholder
attempt is needed for a Spec-only change.

Configured checks run with OS-enforced read-only project access, including ignored files and
`.concorde/runs`. Linux currently requires a system-installed
[bubblewrap](https://github.com/containers/bubblewrap) with working user, mount and PID namespaces
and libc/kernel pidfd support. Unsupported platforms or denied sandbox setup block checks with
`check_sandbox_unavailable`; there is no unrestricted fallback. Project worker configuration
(the selected Pi worker model and thinking level) does not disable this check boundary.

Checks can read inputs and write temporary output under the supplied `TMPDIR`, `XDG_CACHE_HOME`
and `CONCORDE_CHECK_REPORT_DIR`; `CONCORDE_CHECK_TMPDIR` names each check's independent external
scratch directory. These files disappear after the entire check process tree exits. Move project
cache/report outputs to those paths, and run source-changing formatters during implementation.
Only the outside host saves stdout/stderr and lifecycle evidence in the project. The source
checkout's docsite type check prepares its sidebar and any missing dependencies in an external copy.
This boundary does not define finer read, network or credential policies.

For architecture changes, the user session edits the affected entries, document metadata and
reading together, regenerates the registry mirror (`python3 scripts/concorde.py registry --write`)
and validates the combined result before dependent work. A shared definition has one owner; other
Modules import or rely on it and receive it in their own context, never a copy or a broader grant.
A file may be listed by several Modules without merging their responsibilities. No deleted author
or topology artifact is required, and a direct edit is never fabricated review or completion evidence.

[Executable composition](../specs/concorde/operations/composition.md) ·
[Capability admission boundary](../specs/concorde/harness/admission.md)

## Developer view and feedback

The [Developer experience](../specs/concorde/module.md#developer-entry-points) covers the
Spec docsite, interactive diagrams and feedback into the Framework's existing workflows.
[Spec publication](../specs/concorde/views/module.md#design) provides the authored-Spec view in
this experience. A developer can inspect the views, clarify feedback in the agent conversation and
proceed directly with an authorized change request.

For problems that need tracking across sessions, use `concorde-issues` with list, show, report,
reopen or solve. The [Issue system](../specs/concorde/issues/module.md) records bug, gap and limitation
observations during work. Stage blockers and review judgments reference those immutable reports.
Reporting does not itself stop an agent or start a repair, and a workaround can leave an Issue open.

An explicit solve request selects one Issue and its current revision. The bounded solver can use
read-only verification or return needed development/Spec repair intent to the caller.
Caller-performed edits require fresh verification before supported disposition and final candidate checks. Unresolved choices return needs-decision; an explicit solve note supplies developer
clarification. A successful candidate-local close is not a claim about primary. See the
[Issue lifecycle](../specs/concorde/issues/lifecycle.md).

Concorde uses Pi-only Package Manifest 5, installation receipt 2, Architecture Profile 16 with
Spec Protocol 11, registry schema 3, Workspace Protocol 16 and Delivery Proposal 10. Other formats
are refused; normal execution never reinterprets them, and there is no migration path from Spec
Protocol 10.

The docsite publishes one canonical page per document, with parallel Module Specs and
Implementation Specs tabs following the `contains` tree, inline diagrams (illustrative ones labelled
as such) and optional source provenance. Terminology import rows show the imported definition at
render time. Spec Protocol uses an independent custom-document tab. Capability behaviour and each
StateGraph Operation's Graph Spec are read in their owning Modules' Specs.
Source and link validation precede candidate promotion; human
navigation grants no extra agent context.

## Concorde Spec Protocol entry and upgrades

The Framework execution profile defines candidate worktrees in [P10](../prompts/protocol/framework-profile.md#p10-fresh-task-sessions-never-session-moves).
Concorde Spec Protocol 11.0.0 defines Module Specs as a checked graph whose realizations bind the
files that realize each Module, and whose scenarios are declared by the tests that verify them.
Root instructions and runtime drafts refer to that rule; the Pi
catalog does not carry another copy. The installer adds a receipt-owned `concorde-protocol` block
to `AGENTS.md`, directing the user session to read `.concorde/protocol/principles.md`. A
Markdown link alone is not an automatic import. Verify active context and extension loading when
using custom discovery settings; installation tests verify entry bytes and asset resolution, not
a model's compliance in a live conversation.
Internal agents retain disabled ambient instruction discovery and receive the same Protocol through
their controlled context; root guidance does not enlarge their permissions.

Commit the root entry and complete Protocol bundle with the consumer project so committed-base
linked worktrees inherit project guidance and accepted rule bytes. Their ignored execution assets
are installed locally as described above, not inherited from primary at runtime.
Runtime `concorde-change-worktree` blocks remain local and are stripped at delivery; the
`concorde-protocol` entry remains part of the project.
The installer preserves root bytes outside its block, including later user edits and file mode.
Reinstall is idempotent. An upgrade removes only unchanged receipt-owned outputs the new package
no longer ships; a receipt of an earlier schema is refused.
Modified/unowned blocks, ambiguous markers, symlinks and non-file roots conflict without replacement.
To preview removal of root entries during uninstall, run:

```bash
python3 /path/to/concorde/scripts/install-concorde.py --target /absolute/project --remove-protocol-guidance
```

Add `--apply` to remove those entries and their receipt records. This cleanup keeps user text,
framework/runtime files and all other receipt records. A root file you created stays even when the
removal leaves it empty; a root file the installer created for its entry alone is removed with that
entry unless you have written into it. It is not a full-package uninstaller.
Remove the entry before separately removing the framework; do not delete whole user instruction files.

Installing an updated package never rewrites `.concorde/config.json`. Existing projects remain bound
to their accepted version/digest; execution rejects a mismatch with `protocol_mismatch`. The user session
entry points at the installed rules, but does not accept them for project execution. After reviewing and explicitly accepting new Protocol assets for the same profile, a consumer
developer can update that binding from the project root. A project written for Spec Protocol 10
must be rewritten for Protocol 11 first; changing a version or digest alone is not migration. For a
project whose Specs already conform:

```python
import hashlib
import json
from pathlib import Path

manifest = Path(".concorde/protocol/manifest.json").read_bytes()
config_path = Path(".concorde/config.json")
config = json.loads(config_path.read_text())
config["protocol"] = {
    "version": json.loads(manifest)["version"],
    "digest": "sha256:" + hashlib.sha256(manifest).hexdigest(),
}
config_path.write_text(json.dumps(config, indent=2) + "\n")
```

Then run project validation and resolve fresh contexts; older context/check identities cannot be
reused. In this source checkout, the equivalent explicit maintenance step is
`python3 scripts/concorde.py protocol-manifest --write --bind-project`. Without `--bind-project`,
`protocol-manifest` only reports whether the tracked manifest matches the current build, or (with
`--write` alone) accepts the current build's digests into that tracked manifest, leaving the
checkout's existing binding unchanged.

## Development

Run Python tests with `.venv/bin/python -m pytest`, the single test entry configured in
`pyproject.toml`: it collects every `unittest.TestCase` under `tests/concorde` and runs them on
16 pytest-xdist worker processes by default (`-n 0` runs in-process, `-n <N>` changes the worker
count, a file or node id selects tests, `--durations=20` lists the slowest). The local plugin
`tests/concorde/support/pytest_timing.py`, loaded by the rootdir `conftest.py`, adds the
evidence options `--reason=`, `--scope=`, `--phase=`, `--attempt=`, `--prior=<summary>` and
`--json=<path>`, which writes a summary with input/test/runtime/lock/environment fingerprints,
per-unit queue/execution intervals and the runtime spans each test wrote to its own
`CONCORDE_DIAGNOSTIC_TIMING_DIR`. Join these values with `=`: pytest picks its rootdir from the
bare arguments before the plugin has registered its options, so a separate value that exists as
a path (a prior summary always does) would relocate the rootdir and drop this configuration.
Run docsite checks with `npm run typecheck`, `npm test`, `npm run validate`, `npm run build`.

Known intermittent failure: under parallel execution,
`tests/concorde/operations/test_review.py::ReviewTests::test_changed_review_instructions_reassess_without_erasing_gaps_on_failure`
has failed once with `review_required` ("required spec review is missing, incomplete, blocking, or
stale") and passed on every isolated rerun. The cause is undiagnosed; treat a single failure of
that test as suspect and rerun it alone (`.venv/bin/python -m pytest -n 0 <node id>`) before
drawing conclusions. The worker runtime tests and the worker sandbox tests need Linux with a
trusted system bubblewrap and a Pi installation on PATH; the sandbox tests fail rather than skip
where the boundary cannot be enforced.

Tests that install the Pi worker extensions run `npm ci` offline, so the suite has no online npm
path and no test depends on which worker installs first. Before such an install,
`tests/concorde/support/managed_runtime.seed_npm_cache` copies the tarballs locked by
`pi/package-lock.json` into the npm cache in use (`npm_config_cache`, for example a tester's
issued scratch) from a local populated npm cache: npm's default cache, which the bootstrap
`npm ci --prefix pi` fills, or the cache named by `CONCORDE_TEST_NPM_CACHE`. Seeding happens
once per cache under a file lock; the extracted `pi/node_modules` cannot serve because a locked
install accepts only the exact tarball bytes. A tarball found nowhere locally fails the test with
the missing input named rather than falling back to the network.

Canonical Agent definitions, `prompts/` (including public capability guidance under
`prompts/operation-guidance/`) and `pi/extensions/` produce this checkout's Agent surfaces. Never edit
`generated/`, the private `generated/session/pi/` entry or generated worker instructions directly;
they are untracked build output. Build never installs into ambient discovery.
After changing their sources, run the build and the deterministic checks in the same primary or
linked worktree:

```bash
python3 scripts/concorde.py build
python3 scripts/concorde.py build --check
python3 scripts/concorde.py validate
```

`build` renders every worker, the private Pi entry/catalog, Protocol assets and runtime schemas
deterministically from authored Protocol, prompt, Agent, capability and Pi sources; `build --check` verifies
those outputs, ordinary guidance and `protocol/manifest.json` are current without writing anything; `validate` runs the complete Spec,
executable-inventory, contract, Spec-alignment and build-output checks. Native capability preparation
and every Agent launch require a fresh build; deterministic
lifecycle entry points retain their separate admission/evidence checks. A freshly created worktree
must be built once before a fresh tester can select its private Pi entry. After changing the standard chapters under `protocol/` or their runtime adapters, accept the
new digest with `python3 scripts/concorde.py protocol-manifest --write --bind-project` (see above).

[Agents](../specs/concorde/agents/module.md) covers nine explicit Pi Agents: `context-assessor`, `planner`,
`task-author`, `programmer`, `spec-reviewer`, `code-reviewer`, `issue-solver`, `maintenance-worker` and
`tester`. The seven Domain Agents have native instruction projections and Host-prepared invocation
capsules. Their file/network/credential policy is explicitly prompt-level; tester/configured-check
boundaries remain actually enforced. The maintenance-worker and tester Task subagents use project registration
and task-specific grants, not the domain stage schema or single-Module context policy. The former is
source-only; tester has distinct source and installed consumer instructions. The user session is the external
caller/coordinator, not another registered Agent profile. Context, plan, tasks, implementation, review and Issue decisions use native
Agent/workflow calls, not hidden RPC workers. Gates only stage proposals. Host acceptance binds actual
native terminal evidence and current inputs; closure remains journaled and final validation separate.

The public catalog preserves eleven compatibility entry names; it is not the inventory of Agents. `kind`
distinguishes Agent entry, Workflow and Host actions; StateGraph Operations are a separate optional
boundary with an explicitly supplied trusted native service. See the
[Terminal Agent Operation](../specs/concorde/harness/execution/module.md#concept.execution.terminal-agent-operation)
and [current examples](../README.md).

Concorde source maintenance defaults to a new candidate and a fresh Concorde-catalog-free writer.
The user session stays in its initial worktree. Its high-level decomposition into work packages, ownership,
native workflow steps and integration/testing gates is not product Concorde plan/tasks. The writer
edits, formats, checks and commits, then stops.
A separate fresh sibling tester receives only the exact candidate-built private Pi entry and its
embedded catalog, with implementation/build/runtime provenance checked through `select-session`.
Neither child inherits/discovers Concorde catalogs, forks old instructions or delegates tasks. Failed tests
return to maintenance and then another fresh tester. Ordinary Git integration is permitted after
checks and explicit merge authorization; maintenance is not required to use Concorde delivery.

Issue selection with `select-session --mode test --pi-entry <absolute-private-entry.ts> --runtime
<absolute-candidate-launcher> --output <absolute-candidate-.concorde/work/selection.json>`. Reverify
using `select-session --verify <absolute-selection>` before launch. The fresh host supplies
`CONCORDE_SESSION_SELECTION`, a separate host-owned Pi configuration directory, only the returned
exact `-e` entry and all returned discovery-disable flags. Missing/stale artifacts or a missing
candidate Python environment block without ambient fallback. Selection is not proof of extension
loading, tool use or model execution, and never widens the actual task/file/tool grant. The
private extension reverifies before registration and every tool call; the launcher independently
reverifies. Private selection rejects linked-source-worktree redirects, while explicitly
scoped disposable consumer data remains allowed. `--skill` and schema-1 selections are rejected.

Consumers may delegate complete tasks one layer deep or edit simple authorized tasks directly in
primary. Bounded domain Agents are not task delegates and never bypass actual harness limits.
Task-authorized edits may include `.concorde` files in the owned workspace; preserve truthful
evidence, task scope and concurrency safety. Primary-only `.concorde/status/<change_id>.json`
records stable task coordination, delivery or manual merge and separate cleanup. Durable runs,
including candidate executions, remain primary-only in `.concorde/runs/`. Terminal status remains
after candidate deletion.

## Source-selected installation testing and failed native observation

A private source selection cannot attest a new installed path. Passing it unchanged into an
installed health check correctly refuses; neither relax the guard nor silently clear all provenance.
For an explicitly authorized fresh external fixture **inside `test_command` scratch**, the source-only
recipe verifies governing selection and admitted package bytes first, separates only process-local
source provenance/import overrides for the installer and installed children, and verifies exact
installed output identity with its own managed interpreter:

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
the helper is not a consumer product or new general selection mode. The target must be fresh,
canonical and within issued scratch. Dependency acquisition needs the normal locked wheel/npm
inputs; offline caches must be available in the explicit host-/tmp read-only view or acquisition
must be explicitly allowed into issued scratch. The recipe does not change global npm settings.
`installed-output-provenance.json` binds source selection/build, recipe bytes, admitted package,
external destination, installed entry/catalog/launcher/build, receipt/runtime and interpreter. Read
and return this bounded record before scratch cleanup. Maintain quiescent source/output bytes.
Native installed smoke uses the installed entry in a separate process with `installed_env`, never
the source-private entry pretending that copied assets are an installation.

For the next authorized live Issue diagnostic, use the checked-in source driver rather than building
or regex-patching another JavaScript collector. First run the model-free path **inside test_command**:

```bash
CONCORDE_SESSION_SELECTION="$PWD/.concorde/work/pi-first-diagnostic-selection.json" \
  .venv/bin/python tests/concorde/harness/run_issue_diagnostic.py --selftest \
  --selection "$PWD/.concorde/work/pi-first-diagnostic-selection.json" \
  --sdk /explicit/pi-coding-agent/package --native /explicit/pi-subagents/package
```

Only when the user session authorizes the one live attempt, use the same command with `--live` instead of
`--selftest`, plus `--model codex-lb/gpt-6-astra --auth-source /approved/auth.json
--models-source /approved/models.json`. The model name and both credential/model-file paths are
explicit test inputs, not defaults or permission to inspect other settings. The script preserves the
approved mode-0600 scratch auth copy and read-only canonical model-file link, disables ambient
resources and model retries, and drives the actual SDK/public ExtensionRunner hooks. It never prompts
a coordinator model, runs a conditional second case or retries the Issue workflow. Source selection
stays active. All fixture writes remain in issued scratch.

This path does **not** install a child-session factory setter or infer SDK effective-start state from
an unrelated Jiti module instance. Effective start remains unknown. It correlates issued d-0 schema,
ticket and native launch identity with the genuine failed-child transcript, independently of success
emissions. The parser merges assistant toolCall, native tool_start/tool_end and toolResult records by
call ID and retains actual structured arguments, complete available error text, isError/status and
terminal reason. Native Missing structured_output means no successful submission, not no attempts.

The only final stdout is a whitelisted selected diagnostic envelope under 8000 UTF-8 bytes. Its
bounded gzip+base64 payload contains the issued schema and selected structured calls/results, with
SHA-256 and decoded/compressed byte counts. It never contains arbitrary transcript/read-tool output,
authentication stores, environment or provider registries. Parent may decode it as **data**, verify the
hash/size and persist it in primary evidence. Native source truncation/missing records are distinct
from explicit omitted reporting; the first actual failed call is not silently replaced by counts.
The raw scratch is ephemeral, but these selected arguments/errors survive in returned stdout.

Decode without evaluating anything, for example with `base64.b64decode`, `gzip.decompress`, SHA-256
verification against payload.sha256, and `json.loads`; enforce the declared 256-KiB decoded bound.
The tracked `unpackDiagnostic` helper additionally bounds decompression. If a complete first failure
cannot fit the fixed export bound, the command refuses an evidence-complete claim rather than retrying
or silently dropping its error. Selftest exercises the actual native transcript writer and lossless
codec before any credential read; the live path repeats this check with its issued schema before the
first subagent call.

A zero exit from the live **diagnostic command** means its selected evidence was complete enough to
transport, not that the Issue succeeded. Check envelope.summary.result and the decoded native/attempt
records separately. A failed business/native result may have a successful diagnostic export. No
specific discarded error from a previous run is inferred or reconstructed.
