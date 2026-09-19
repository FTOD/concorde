# Concorde workflow guide

[← Back to the project overview](../README.md)

Detailed installation, execution, delivery and maintenance reference. Shell commands assume
the Concorde checkout root unless an installed consumer path is shown.

Concorde centers on writing and maintaining **architecture-aware Specs**. Its docsite publishes
them so developers can understand the project. **Agent observability** covers the working process:
[LangGraph Studio](../scripts/development/STUDIO.md) exposes execution graphs and live stage and
agent-process events, recorded usage shows what each worker launch consumed, and recorded context,
permission policies, checks and reviews make the work and its results inspectable. Specs guide each
worker's task, while the host limits its context and permissions to the declared scope and a
bubblewrap sandbox bounds every worker process. Twelve built-in Pi workers — one per lifecycle role,
from answering questions and routing through Spec authoring, review, planning and task definition to
implementation, code review and Issue solving — do this work behind the public Operations that
installed Skills or the Pi session tool invoke. The Issue system records classified bugs, contract
gaps and limitations as soon as a worker reports them, without stopping its task, and solves an
explicitly selected Issue to a verified candidate.

The development and delivery workflows below use **Spec Protocol 10.0.0**. It defines one Module
Spec content model and the human-readable subset of that content. Reading begins with Purpose,
Terminology, Usage, Design and Relationships in module-role entries, followed by explanatory topics
that each open with their own Terminology table. Formal requirements,
scenarios and canonical interfaces belong only in implementation-role companions owned directly by
the same Module. Both roles remain normative reading and complete agent context; a topic does not
own a separate set of obligations. Identity, explicit roles, mappings and file bindings live in
paired schema-2 `.md.json` metadata,
which points to canonical readable meaning. Neither an inventory nor a summary replaces design.

Each Module has one structural parent at most. A shared provider is owned by none of its
consumers and may sit at any level of the hierarchy; `uses` does not create another parent. Module composition and file reuse are separate
relationships: several Modules may bind the same implementation file. Within one Module the most
specific entry owns a file, an exact path before a directory prefix, so a directory prefix can list a
whole package while a shared file keeps its own entry. Every Module registers its
complete document-unit collection and one local `module.md` reading entry. A dependency link does not
import the provider's Spec or source.

Readers, planners and task authors determine behavior from their selected Module Spec alone; its
entity declarations name the entries and the files they bind, but never their contents. Only the
code-writing and code-review phases receive those file contents, in their declared subsets. The
Framework maintains a reverse file-listing index and checks each listing Module separately after a
shared file changes. Context, checks and reviews identify the exact contracts and revisions they
assessed.

The Protocol standard is independent of the software Specs that implement it:

```text
protocol/                 Independent standard, organized as ordinary chapters
specs/concorde/           Module contracts, entities and architectures
.concorde/specs.json       Registry schema 5: Modules and their relationships
```

Start with the [Concorde Module](../specs/concorde/module.md), its
[Usage](../specs/concorde/module.md#usage) and
[Design](../specs/concorde/module.md#design), and the
[Spec Protocol](../protocol/README.md). The
[authored Protocol rules](../protocol/principles.md) define the standard. Protocol documents are
outside the project Spec registry and do not need to satisfy their own Module format.
The docsite publishes them in a dedicated **Spec Protocol** tab.

## Install and initialize

The installer distributes a deterministic build's output — ten Skills exposing selected entries
from one inventory of twenty-seven Operations, including twelve model-backed nodes. Their common
worker rules (`prompts/workers/common.md`) and local instructions (`operations/<name>/spec.md`)
render to the compatible `generated/agents/<hyphenated>.md` paths. Four Markdown templates and
the selected client projections accompany them: Codex or Claude Skills, which the installer has the
Agent Skills CLI (`npx skills add`) place, or for the Pi coding agent the session extension shim under
`.pi/extensions/`, whose `concorde` tool describes and runs the same public Operations.
Check `python3 scripts/install-concorde.py --help` for installation
administration. Project task inputs use JSON, not positional or flag arguments. Install into a Git
project and commit the installed framework and root guidance, then invoke the paired init entry.
A mutation requested from the primary worktree, including an initialization `apply`, prepares a
linked worktree from committed HEAD, runs the same request through that candidate's own launcher and
returns the candidate's result; its workspace names the candidate's path, branch and change_id, with
which the same session continues the change. The originating session never follows the task into a
different checkout. An initialized candidate reaches the primary branch like any other change:
validate it, deliver it, and request the primary merge separately.

```json
{
  "type_id": "concorde-operation-invocation",
  "schema_version": 3,
  "operation_id": "concorde-init",
  "mode": "execute",
  "configuration": {"type_id":"concorde-operation-configuration","schema_version":1,"data":{"model":"openai-codex/gpt-6-astra","thinking":"medium"}},
  "input": {"type_id":"concorde-init-request","schema_version":1,"data":{"action":"propose","name":"My project","configuration":{"type_id":"concorde-operation-configuration","schema_version":1,"data":{"model":"openai-codex/gpt-6-astra","thinking":"medium"}}}}
}
```

Send the JSON on stdin to `python3 .concorde/framework/scripts/run-operation.py concorde-init`;
the launcher re-executes itself inside the managed runtime `.concorde/.venv`, so any Python 3.11+
can start it.
Review the returned proposal, then send action apply and that complete proposal. Initialization creates
an honest reading/metadata pair. Supply Purpose, Terminology, Usage, Design and Relationships before precise
requirements/scenarios and implementation. Topic documents have their own metadata companions and
need not repeat the entry template. All selected pairs enter context whole.
`.concorde/config.json` pins the Protocol and references `.concorde/specs.json`; that registry explicitly
records document members, parent/uses relationships, each Module's `files` and deterministic checks.
Local dependency declarations state the promises needed for routing and planning; validation keeps
them aligned with direct relationships. Arbitrary nearby Markdown is not context.
Document declarations are likewise checked against reverse registry membership.

## Run a change

Send this invocation on stdin to `scripts/run-operation.py concorde-dev-loop` (or
`.concorde/framework/scripts/run-operation.py` in an installed consumer project):

```json
{
  "type_id":"concorde-operation-invocation","schema_version":3,
  "operation_id":"concorde-dev-loop","mode":"execute","configuration":null,
  "input":{"type_id":"concorde-dev-loop-request","schema_version":1,
    "data":{"target_id":"module.transfer","task":"Implement the specified transfer contract"}}
}
```

Null configuration asks the trusted host to load initialized settings. The `ask` action of
`concorde-main` may omit target_id: the router or answerer selects needed Module Spec contexts, Python
resolves their complete documents, grants them read-only beside an index, and the answerer
opens the originals it needs and answers directly from them. Shared documents are granted once
while preserving each Module's membership. A supplied target_id is a routing hint,
not a context grant. The loop executes specification,
context assessment, plan, tasks, implementation and checks, ending at a ready candidate.

Every callable entry is an Operation. Each independently declares public exposure, context
selection, determinism, an optional model execution profile and the Operations it uses; its size or
position in a Graph does not create a separate type. A Graph organizes calls, branches and loops. A Skill exposes a
public Operation to the developer's external agent runtime.

Operations with `CONTEXT_SELECTION="discover"` use the router to discover complete Module
contracts; `bound` consumes the selected Module without expanding its context; `none` performs
deterministic host work without Agent context selection. `PUBLIC` independently decides whether a
Operation has a Skill. For example, issues is public and uses a bound Module, while
specify is non-public and runs only through declared composition.

`concorde-specify-loop` routes a task, authors or revises its Spec and independently reviews it,
then returns completed. `concorde-dev-loop` calls that Operation before planning, tasks,
implementation, checks and code review. Both accept `specify` and `run_reviews` flags: the former
can skip authoring; the latter records explicit review skips without cancelling a review already
required for the change. The Spec loop affects only Spec review, while development also requires
code review for code-owning targets. Accepted Spec work can continue into development in the same
change without repeating current evidence.

`concorde-spec-review` reviews the specification itself, including every imported terminology
restatement's semantic consistency with its canonical definition. Different wording is allowed.
`concorde-code-review` reviews or diagnoses the admitted implementation against its Spec. Each
separate Operation accepts a `task` and optional target/focus routing hints, with no review_mode
selector. Each selects the owning Module and starts its own fresh read-only reviewer in the current
worktree, without requiring a development change or preexisting Issue. The host returns structured
findings and coverage; unmanaged Git checkouts use HEAD as the diff baseline. The former combined
review entry is removed, not retained as an alias; callers must select one of these two Operations.

No Skill returns a context manifest; `describe-policy` mode previews the exact stage
grants any operation would receive without launching an agent or mutating project state. One change
belongs to one linked worktree. the primary-owned `.concorde/status/<change_id>.json` records
its task, phase/status, per-target plans and progress, gaps and verified revision. Auxiliary artifacts
live under `.concorde/work/`; there is no separate attempt lifecycle.
Context solving reports missing or inconsistent local dependency promises as structured Module Spec
gaps before planning or task generation.

A blocked change preserves evidence and names missing contracts or failed admission. Author missing
facts through an explicit local Spec task, reconcile affected consumer/provider views and resolve a
new context. Completed component work can be resumed when its bound inputs remain current. Partial
Spec changes stay in the explicitly marked candidate worktree; they do not change the accepted
primary revision. Changed Spec/intent invalidates stale plan or check evidence.
The primary worktree maintains `.concorde/status/` with every live linked worktree's basic
metadata and change status. `concorde-main` receives this inventory and identifies whether its own
session is in the primary or a candidate worktree. Secondary AGENTS.md/CLAUDE.md guidance also points
to the local state and the primary worktree, without granting access to other worktrees' contents.

To deliver, request `concorde-deliver` from the selected source or primary worktree with its
change_id. The host checks the candidate and current integration, creates the independent branch
`concorde/delivered/<change_id>`, and removes the source worktree by default. `keep_worktree:true`
explicitly retains it; otherwise the source agent ends its session after delivery. The primary
branch, index and project files stay unchanged, including any local edits. Development loops stop
at ready and never deliver automatically.

Only an explicit user request to merge into the primary branch authorizes a separate
`merge_primary:true` request with the delivered change_id, from the primary worktree's sole writing
agent. Other agents develop in linked worktrees. The host serializes lifecycle writes and final
merges with a shared repository lock and checks integration against the latest primary commit.
Conflicts, failed checks or local primary edits block final merging and preserve the delivery
branch. Receipts distinguish staging, cleanup and final merging, allowing retries without duplicate
merges; after source removal, use the primary session to retry.

Issue reporting is independent of task control. Explicit solving uses ordinary providers and
Issue-specific reviews; the solver can make evidence-grounded dispositions without a mandatory
human gate, and asks only for genuinely unsettled decisions. Solving stops at ready, not delivery.

For a directly authored candidate without generated plans, `concorde-validate` checks the whole project and records readiness in the
same worktree state. Any already authored plans and tasks must still be completed. No placeholder
attempt is needed for a Spec-only change.

Configured checks run with OS-enforced read-only project access, including ignored files and
`.concorde/runs`. Linux currently requires a system-installed
[bubblewrap](https://github.com/containers/bubblewrap) with working user, mount and PID namespaces
and libc/kernel pidfd support. Unsupported platforms or denied sandbox setup block checks with
`check_sandbox_unavailable`; there is no unrestricted fallback. Project operation configuration
(the selected Pi worker model and thinking level) does not disable this check boundary.

Checks can read inputs and write temporary output under the supplied `TMPDIR`, `XDG_CACHE_HOME`
and `CONCORDE_CHECK_REPORT_DIR`; `CONCORDE_CHECK_TMPDIR` names each check's independent external
scratch directory. These files disappear after the entire check process tree exits. Move project
cache/report outputs to those paths, and run source-changing formatters during implementation.
Only the outside host saves stdout/stderr and lifecycle evidence in the project. The source
checkout's docsite type check prepares its sidebar and any missing dependencies in an external copy.
This boundary does not define finer read, network or credential policies.

For architecture changes, invoke `concorde-main` with `action:design-topology`. It returns a complete
candidate registry and target-local Spec tasks without writing. Send the exact returned proposal with
`action:accept-topology` only after developer review. The host then runs private target authors and
stores exact registry/document bytes in an ignored application artifact, returning only its path and
digest. Review that artifact outside agent cognition, then send its ArtifactRef with
`action:apply-topology`. Stale inputs or invalid target state prevent writes; successful application
updates the registry and documents atomically. The former standalone ask operation does not exist.
A shared document unit has one owner. Only that owner proposes its source replacements; each
consumer contributes separate compatibility evidence from its own complete context, never duplicate
replacement bytes. An implementation file may be listed by several Modules; a topology change to
its bindings reconciles every listing Module without transferring ownership or widening grants.

[Operation registry](../specs/concorde/operations/composition.md) ·
[Operation admission boundary](../specs/concorde/harness/admission.md)

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
ordinary development, Spec repair and read-only verification, then include the disposition in final
candidate checks. Unresolved choices return needs-decision; an explicit solve note supplies developer
clarification. A successful candidate-local close is not a claim about primary. See the
[Issue lifecycle](../specs/concorde/issues/lifecycle.md). Legacy data can be preserved explicitly with
`scripts/issues.py archive-reflections`; it is never automatically classified or approved.

Concorde 8 uses Package Manifest 3, Architecture Profile 15, registry schema 5, Workspace Protocol
16 and Delivery Proposal 10. Older profiles require an explicit migration; normal execution never
reinterprets old formats. The offline migration planner is not a second supported runtime.

The docsite publishes one canonical reading page per document unit, with parallel Module Specs and
Implementation Specs tabs sharing the same Module-parent hierarchy,
inline scoped diagrams and optional source-provenance disclosure. Reading and metadata both bind
build identity, but machine inventories do not appear in the main reading graph. Spec Protocol uses
an independent custom-document tab. There is no docsite Graph page, separate Operation-graph page or
unregistered Projections group: each Operation, and the Graph Spec of an Operation that runs a Graph,
is read in the owning Module's Specs. Source and link validation precede candidate promotion; human
navigation grants no extra agent context.

## Concorde Spec Protocol entry and upgrades

The Framework execution profile defines candidate worktrees in [P10](../prompts/protocol/framework-profile.md#p10-candidate-worktrees-not-session-moves).
Concorde Spec Protocol 10.0.0 defines readable Module specifications with paired metadata whose entities bind the
files that realize them, as exact paths or directory prefixes, and whose scenarios are declared by
the tests that verify them. Root instructions and runtime drafts refer to that rule; public Skills do
not carry another copy.
The installer adds a receipt-owned `concorde-protocol` block at the start of the selected root file:

- Codex: `AGENTS.md` explicitly tells the outer session to read
  `.concorde/protocol/principles.md`. A Markdown link is not treated as an automatic import.
- Claude: `CLAUDE.md` uses the native `@.concorde/protocol/principles.md` import outside a
  code span or fence. The path is relative to that root file.
- Pi: shares the Codex entry in `AGENTS.md`.

These loading choices follow the [Codex instruction discovery documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
and [Claude import documentation](https://code.claude.com/docs/en/memory), checked on 2026-09-07.
Codex overrides or instruction size settings and Claude exclusions can suppress project guidance;
verify the active instruction sources in your client when using such custom settings. Installation
tests verify entry bytes and asset resolution, not a model's compliance in a live conversation.
Internal agents retain disabled ambient instruction discovery and receive the same Protocol through
their controlled context; root guidance does not enlarge their permissions.

Commit the installed root entry and framework with the consumer project so committed-base linked
worktrees inherit them. Runtime `concorde-change-worktree` blocks remain local and are stripped at
delivery; the installed `concorde-protocol` entry remains part of the project.
The installer preserves root bytes outside its block, including later user edits and file mode.
Reinstall is idempotent; integration changes remove only the previous receipt-owned entry.
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
to their accepted version/digest; execution rejects a mismatch with `protocol_mismatch`. The outer
entry points at the installed rules, but does not accept them for project execution. After reviewing and explicitly accepting new Protocol assets for the same profile, a consumer
developer can update that binding from the project root. A project older than Profile 15 must first migrate its complete registered collection to
reading/metadata document units and registry schema 5; changing a version or digest alone is not
migration. The explicit offline conversion planner reports preserved definitions and remaining
editorial work and does not enable an old-format runtime. For a structurally compatible project:

```python
import hashlib
import json
from pathlib import Path

manifest = Path(".concorde/framework/protocol/manifest.json").read_bytes()
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

[LangGraph Studio setup and usage](../scripts/development/STUDIO.md) covers all Skill entries and
stage events, CLI/Skill forwarding, live execution events, debugging and worktree isolation. Studio
is optional; existing JSON stdin/stdout calls continue to work without a server.

Run Python tests with `python3 scripts/development/run-tests.py`, which runs every module under
`tests/concorde` in its own subprocess in parallel and reports per-module durations
(`--filter <substring>` selects modules, `--sequential` runs them one at a time, `--json <path>`
writes a summary). The plain serial command
`python -m unittest discover -s tests/concorde -t . -p 'test_*.py'` remains valid. Run docsite
checks with `npm run typecheck`, `npm test`, `npm run validate`, `npm run build`.

Known intermittent failure: under the parallel runner,
`tests.concorde.operations.test_review.ReviewTests.test_changed_review_instructions_reassess_without_erasing_gaps_on_failure`
has failed once with `review_required` ("required spec review is missing, incomplete, blocking, or
stale") and passed on every isolated rerun. The cause is undiagnosed; treat a single failure of
that test as suspect and rerun it alone before drawing conclusions. The worker runtime tests and
the worker sandbox tests need Linux with a trusted system bubblewrap and a Pi installation on
PATH; the sandbox tests fail rather than skip where the boundary cannot be enforced.

`prompts/` (including the Skill sources `prompts/skills/`), `pi/extensions/` and the top-level
`operations/` package produce this checkout's agent surfaces. Never edit `generated/`,
`.agents/skills/concorde-*`, `.claude/skills/concorde-*`, `.pi/extensions/concorde-session.ts` or
generated Issue-solving agents directly; they are untracked build output. The published Skills
under `skills/` are tracked rendered output: never edit them by hand either; after changing a Skill
source, run `python3 scripts/concorde.py skills --write` and commit `skills/` with the source.
After changing their sources, run the build and the deterministic checks in the same primary or
linked worktree:

```bash
python3 scripts/concorde.py build
python3 scripts/concorde.py skills --write
python3 scripts/concorde.py build --check
python3 scripts/concorde.py validate
```

`build` renders every worker, this checkout's Skill projections, Protocol asset and runtime schema
deterministically from `protocol/`, `prompts/` and `operations/`; `skills --write` renders the
tracked published Skills the Agent Skills CLI installs; `build --check` verifies those outputs,
the published Skills and `protocol/manifest.json` are current without writing anything; `validate` runs the complete Spec,
operation-module, contract, Spec-alignment and build-output checks. Top-level model-backed operations and every Agent launch require a fresh build; deterministic
lifecycle entry points retain their separate admission/evidence checks. A freshly created worktree
must be built once before an agent can load Concorde Skills. After changing the standard chapters under `protocol/` or their runtime adapters, accept the
new digest with `python3 scripts/concorde.py protocol-manifest --write --bind-project` (see above).

Each of the twelve workers is defined under `operations/<name>/`: an authored role `spec.md` plus a
Python `__init__.py` binding its task contract, workspace kind (`capsule` or `project`), Pi tools,
children and timeout as optional execution configuration on that Operation. Each worker launches one Pi coding agent
process (`pi --mode rpc`) for exactly one invocation. The build renders each worker's instructions
to `generated/agents/<hyphenated>.md`, combining the common worker rules
(`prompts/workers/common.md`) with only that worker's role Spec, traceable through the build
manifest; `describe-policy` mode (see above) shows the bound worker, its profile and effective
timeout for every stage it previews, alongside its read/write grants.

The worker inventory follows stable context and authority boundaries: answerer, router and
topology-designer handle ask, route and design-topology; spec-author, topology-author,
spec-reviewer, context-assessor, planner and task-author handle specify, topology-author,
spec-review, context-solve, plan and tasks; programmer and code-reviewer handle implementation and
code review, while the Spec-only issue-solver selects bounded actions for an explicit Issue. Each worker's task contract explicitly
pairs input and output types, admits specific stage artifacts and narrows its permission ceiling.
The Host applies structured Spec replacements. Only the programmer may write granted code; reviews
and the Issue solver remain read-only. Every phase and target gets a fresh invocation and context
identity, so a reviewer never inherits the author's conversation, artifacts or write authority
merely because they share the common worker rules. A worker with declared children (spec-reviewer:
fact-check, consistency; planner: scout; programmer: scout, planner, verifier; code-reviewer: scout,
verifier) may delegate one level deep through its `subagent` tool, only in the foreground and with
fresh context; a child runs inside the worker's sandbox under the same gate and grant, cannot
delegate again and cannot submit the worker's result.

One registry contains twenty-seven Operations, ten exposed through public Skills. All use State
contracts and `run(state, runtime)`. DETERMINISTIC means no supported model-call path when true,
including transitive USES. Only init, configure, validate and deliver are true in the current
inventory. USES is the sole composition relation, including model nodes; it does not install
arbitrary Operation calls as worker tools.

**Operation** is the canonical name for a callable or composed Framework function. Harness owns the operation invocation boundary, and
Operations owns the Operation catalog and the dispatch to each provider. Distribution owns `prompts/skills/`, `prompts/workflow-host/` and the published
`skills/`, renders the public Skill instructions, has the Agent Skills CLI install them, and keeps
their projections current. The developer's external agent
runtime reads those Skills and submits typed operation requests to Harness admission; a Pi session
instead loads the rendered `.pi/extensions/concorde-session.ts`, whose `concorde` tool submits the
same requests through the launcher. Skills are not part of a worker's Harness. See [Operations and Harnesses](../specs/concorde/harness/agents-and-harnesses.md)
and the [Operation registry](../specs/concorde/operations/composition.md) for definitions and mappings.

Concorde source maintenance defaults to a new candidate and a fresh Skill-free maintenance child.
The main stays in its initial worktree. The writer edits, formats, checks and commits, then stops.
A separate fresh sibling test child receives only explicit candidate-built private Skills from
`generated/session/`, with runtime and build provenance checked through `select-session`. Neither
child inherits/discovers Concorde catalogs, forks old Skill bodies or delegates tasks. Failed tests
return to maintenance and then another fresh tester. Ordinary Git integration is permitted after
checks and explicit merge authorization; maintenance is not required to use Concorde delivery.

Consumers may delegate complete tasks one layer deep or edit simple authorized tasks directly in
primary. Bounded Operation workers are not task delegates and never bypass actual harness limits.
Task-authorized edits may include `.concorde` files in the owned workspace; preserve truthful
evidence, task scope and concurrency safety. Primary-only `.concorde/status/<change_id>.json`
records stable task coordination, delivery or manual merge and separate cleanup. Durable runs,
including candidate executions, remain primary-only in `.concorde/runs/`. Terminal status remains
after candidate deletion. Preview legacy migration with `migrate-status`; accept explicitly with
`--apply` only after inspecting collisions and preserving backups. No live migration is automatic.
