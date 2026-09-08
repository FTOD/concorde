# Concorde Framework

Concorde Framework includes the **Concorde Spec Protocol**, installable Skills, automatic validation,
bounded agent workflows, developer views and feedback. The Protocol is the Framework's specification
standard: it defines how conforming Specs are organized and expressed, and the Framework's software
applies it. Concorde's own Specs follow the same Protocol as consumer projects.

The Framework runs agent work from explicit, self-contained resolved contexts. A global main coordinator may inspect
main-visible Domain and Service documents on demand to route a request; every routed worker then has one selected
target, one reproducible context and a host-enforced permission boundary.

Domain is a business/problem scope. Service and Module are component kinds: a Service offers Features
through precise exchanges; a Module offers APIs. Domain scope nesting, component composition and
multi-scope participation are independent relationships. Every target registers its complete ordered
Markdown collection. Every Domain has one local, main-visible `ontology.md` and a declared
System overview architecture diagram; other Spec filenames remain unrestricted. Each Markdown declares a stable document ID, exact
referencing targets and main visibility. A target's context separates singly referenced Target Spec
from one-hop collective Shared Specs; it never expands a co-referencing entity's remaining files.
Each direct `participates_in` edge is also described inside that Domain's Markdown through a
machine-readable participant entry containing stable ID, kind, local responsibility, selection
condition and relied-upon promises.

The shipped Concorde Spec Protocol governs Spec organization; its Framework execution profile governs
how this software uses those Specs. `concorde-main` is the single
public entry for global questions and topology design. Its internal coordinator starts at the entry
Domain or Service and appends only explicitly requested Domain/Service main-visible documents. It
cannot directly expand a Module target or read code. Once it returns typed routes, the host starts different fresh workers and injects
the pinned global principles plus each selected kind definition. Missing task-relevant facts yield
Spec incomplete, not a search for arbitrary files. See [the authored Concorde Spec Protocol](prompts/protocol/principles.md) and
[the Framework ontology](specs/concorde/ontology.md) and [Concorde Spec Protocol description](specs/concorde/spec-protocol.md).

## Install and initialize

The installer distributes a deterministic build's output — seven Skills exposing thirteen
capabilities, nine rendered Agent instructions (from `agents/<name>/spec.md`), and seven Markdown
templates — to Codex or Claude.
Check `python scripts/install-concorde.py --help` for installation
administration. Project task inputs use JSON, not positional or flag arguments. Install into a Git
project, then invoke the paired init entry in an isolated worktree (or use the trusted host's explicit
primary-worktree authorization). A mutation requested from the primary worktree prepares a linked
worktree from committed HEAD and returns its identity. The outer agent then starts a fresh session
in that worktree under P10, using its own Skills; when automatic startup is unavailable or cannot
establish that isolation, it provides a complete prompt for the user to open the session manually.
The originating session does not follow the task into a different checkout.

```json
{
  "type_id": "concorde-capability-invocation",
  "schema_version": 3,
  "capability_id": "concorde-init",
  "mode": "execute",
  "configuration": {"type_id":"concorde-capability-configuration","schema_version":1,"data":{"integration":"codex","enforcement":"native"}},
  "input": {"type_id":"concorde-init-request","schema_version":1,"data":{"action":"propose","name":"My project","configuration":{"type_id":"concorde-capability-configuration","schema_version":1,"data":{"integration":"codex","enforcement":"native"}}}}
}
```

Send the JSON on stdin to `python .concorde/framework/scripts/run-capability.py concorde-init`.
Review the returned proposal, then send action apply and that complete proposal. Initialization creates
an honest Domain stub; supply business rules and register Services/Modules before implementation.
`.concorde/config.json` pins the Protocol and references `.concorde/specs.json`; that registry explicitly
records document members, independent relationships, local Feature/API IDs, implementation ownership
and deterministic checks. Domain participant declarations make component routing locally meaningful;
validation keeps them aligned with registry participation. Arbitrary nearby Markdown is not context.
Document declarations are likewise checked against reverse registry membership.

## Run a change

Send this invocation on stdin to `scripts/run-capability.py concorde-dev-loop` (or
`.concorde/framework/scripts/run-capability.py` in an installed consumer project):

```json
{
  "type_id":"concorde-capability-invocation","schema_version":3,
  "capability_id":"concorde-dev-loop","mode":"execute","configuration":null,
  "input":{"type_id":"concorde-dev-loop-request","schema_version":1,
    "data":{"target_id":"service.transfer","task":"Implement the specified transfer contract"}}
}
```

Null configuration asks the trusted host to load initialized settings. The `ask` action of
`concorde-main` may omit target_id: a separate coordinator discovers Domain/Service Specs, routes one or more fresh
target readers, then synthesizes only their typed results. A supplied target_id is a routing hint,
not a context grant. The loop executes specification,
context assessment, plan, tasks, implementation and checks, ending at a ready candidate.

Capabilities fall into three classes, distinguished by who selects context. Global capabilities
(`concorde-main`, the development loop `concorde-dev-loop`, and `concorde-reflections-triage`)
receive only intent, at most with routing hints, and let main select the target. `concorde-dev-loop`
takes optional `specify`/`run_reviews` flags: `specify=false` skips Spec authoring (the former fast
loop) and `run_reviews=false` records an explicit skip for each review mode instead of running it; a
review already required for a change cannot be disabled by a later `run_reviews=false`. Lifecycle
capabilities (`concorde-init`, `concorde-configure`,
`concorde-validate`, `concorde-deliver`) are deterministic host behavior with no agent cognition.
Every other capability — `concorde-specify`, `concorde-review`, `concorde-context-solve`,
`concorde-plan`, `concorde-tasks`, `concorde-implement` — is a stage: it receives an
already bound target and one frozen context from its composing capability, and is never projected as a
Skill; stage capabilities have no executable entry.
No Skill returns a context manifest; `describe-policy` mode previews the exact stage
grants any capability would receive without launching an agent or mutating project state. One change
belongs to one linked worktree. `.concorde/worktree.json` records
its task, phase/status, per-target plans and progress, gaps and verified revision. Auxiliary artifacts
live under `.concorde/work/`; there is no separate attempt lifecycle.
For a Domain, context solving first reports missing or inconsistent participant declarations as
structured Spec gaps, before planning or task generation.

A blocked change preserves evidence and names missing contracts or failed admission. Author missing
facts through an explicit local Spec task, reconcile affected consumer/provider views and resolve a
new context. Completed component work can be resumed when its bound inputs remain current. Partial
Spec changes stay in the explicitly marked candidate worktree; they do not change the accepted
primary revision. Changed Spec/intent invalidates stale plan or check evidence.
The primary worktree maintains `.concorde/worktrees.json` with every live linked worktree's basic
metadata and change status. `concorde-main` receives this inventory and identifies whether its own
session is in the primary or a candidate worktree. Secondary AGENTS.md/CLAUDE.md guidance also points
to the local state and the primary worktree, without granting access to other worktrees' contents.

To deliver, request `concorde-deliver` from either the selected source worktree or the destination
primary worktree with the selected change_id. The destination is the primary worktree's current
branch; it need not be named main. Third-worktree and nested sessions cannot deliver that change.
The host verifies the exact candidate and integration before merging. It retains the source when
it owns the requesting session or `keep_worktree:true` is supplied; otherwise it removes the source
and local state. Destination local edits are preserved: a dirty destination blocks delivery until
those edits have been safely preserved outside the merge transaction. Delivery receipts distinguish
completed merges from pending cleanup, so retries never merge twice. Development loops stop at ready.


Reflection investigation is a separate, read-only implementation invocation; human
approval/disposition remains governed by project settings.

For a directly authored candidate without generated plans, `concorde-validate` checks the whole project and records readiness in the
same worktree state. Any already authored plans and tasks must still be completed. No placeholder
attempt is needed for a Spec-only change.

For architecture changes, invoke `concorde-main` with `action:design-topology`. It returns a complete
candidate registry and target-local Spec tasks without writing. Send the exact returned proposal with
`action:accept-topology` only after developer review. The host then runs private target authors and
stores exact registry/document bytes in an ignored application artifact, returning only its path and
digest. Review that artifact outside agent cognition, then send its ArtifactRef with
`action:apply-topology`. Stale inputs or invalid target state prevent writes; successful application
updates the registry and documents atomically. The former standalone ask capability does not exist.
Shared truth has no unique owner and cannot be changed by an ordinary single-target author. A
topology change tasks every affected reference and proceeds only when all candidate referencing
authors return identical shared bytes.

[Capability registry](specs/concorde/services/capability-registry.md) ·
[Workflow host boundary](specs/concorde/services/workflow-host-boundary.md)

## Developer view and feedback

The [Developer view and feedback Domain](specs/concorde/developer-view/ontology.md) covers the
Spec docsite, interactive diagrams, the Understand Anything code viewer and feedback into the
Framework's existing workflows. [Spec publication](specs/concorde/publication/ontology.md) is one
subdomain of this developer experience.

The [viewer service](specs/concorde/services/viewer-boundary.md) opens an existing raw Understand
Anything graph using the installer-owned runtime. Starting it does not generate a code graph or
prove that the graph agrees with the Spec. A developer can inspect the views, clarify feedback in
the agent conversation and proceed directly with an authorized change request.


Concorde 4 uses Package Manifest 3, Architecture Profile 8, Workspace Protocol 14 and Delivery Proposal
10. Profile 7 is rejected for agent execution and has no migration capability. Legacy readers
remain deterministic diagnostic utilities only.

The docsite publishes explicit registry members with separate scope/component navigation and a typed
relationship graph. Clicking a Domain opens its registered `ontology.md`, independently of member
order, with an embedded Archify System overview showing internal and external relationships. Diagram
builds own `generated/diagrams/` and preserve Framework build outputs. It also publishes "Agent instructions" and "Wire contracts" pages under a
Projections group, rendered directly from the current build's `generated/docs/*.json` outputs; both
are explicitly labelled projections, never agent context authority, and `npm run validate` fails
when the Concorde build behind them is stale. Run the docsite's validate/build scripts to create a
candidate whose routes and source digests are checked before promotion. Human navigation does not
grant agent context access.

## Concorde Spec Protocol entry and upgrades

The Framework execution profile defines session handoffs in [P10](prompts/protocol/framework-profile.md#p10-copyable-agent-handoffs).
Concorde Spec Protocol 1.2.0 adds the Domain main-Spec and System overview conventions.
Root instructions and runtime drafts refer to that rule; public Skills do not carry another copy.
The installer adds a receipt-owned `concorde-protocol` block at the start of the selected root file:

- Codex: `AGENTS.md` explicitly tells the outer session to read
  `.concorde/framework/generated/protocol/principles.md`. A Markdown link is not treated as an automatic import.
- Claude: `CLAUDE.md` uses the native `@.concorde/framework/generated/protocol/principles.md` import outside a
  code span or fence. The path is relative to that root file.

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

Add `--apply` to remove those entries and their receipt records. This cleanup keeps user text, empty
root files, framework/runtime files and all other receipt records. It is not a full-package uninstaller.
Remove the entry before separately removing the framework; do not delete whole user instruction files.

Installing an updated package never rewrites `.concorde/config.json`. Existing projects remain bound
to their accepted version/digest; execution rejects a mismatch with `protocol_mismatch`. The outer
entry points at the installed rules, but does not accept them for project execution. After reviewing
and explicitly accepting the new Protocol assets, a consumer developer can update only that binding
from the project root:

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

[LangGraph Studio setup and usage](scripts/development/STUDIO.md) covers all Skill entries and
stage events, CLI/Skill forwarding, live execution events, debugging and worktree isolation. Studio
is optional; existing JSON stdin/stdout calls continue to work without a server.

Run Python tests with `PYTHONPATH=src python -m unittest discover -s tests/concorde -v` and docsite checks
with `npm run typecheck`, `npm test`, `npm run validate`, `npm run build`.

`prompts/`, `skills/`, and the top-level `capabilities/` package produce this checkout's agent
surfaces. Never edit `generated/`, `.agents/skills/concorde-*`, `.claude/skills/concorde-*`, or
generated reflection agents directly; they are untracked build output. After changing their
sources, run the build and the deterministic checks in the same primary or linked worktree:

```bash
python3 scripts/concorde.py build --check
python3 scripts/concorde.py build
python3 scripts/concorde.py validate
```

`build` renders every role, Skill, Protocol and docs-projection output deterministically from
`prompts/`, `skills/` and `capabilities/`; `build --check` verifies those outputs and
`protocol/manifest.json` are current without writing anything; `validate` runs the complete Spec,
capability-module, contract, Spec-alignment and build-output checks. The host refuses to run any
capability on a stale build; a freshly created worktree must be built once before an agent can load
Concorde Skills. After changing `prompts/protocol/principles.md` or a kind definition, accept the
new digest with `python3 scripts/concorde.py protocol-manifest --write --bind-project` (see above).

Each named Agent is defined under `agents/<name>/`: an authored `spec.md` plus a Python
`__init__.py` binding it to a registered Harness and its effective Constraints (Agent = `spec.md` +
Harness + Constraints). The build renders each Agent's instruction view to
`generated/agents/<hyphenated-name>.md`, traceable back to its `spec.md` source through the build
manifest; `describe-policy` mode (see above) shows the bound agent, harness and effective loop
timeout for every stage it previews, alongside its read/write grants.

Root `AGENTS.md`/`CLAUDE.md` bind an agent to the worktree that supplied its project Skills. If work
targets another worktree, open a new agent there; verify affinity explicitly with:

```bash
python3 scripts/concorde.py verify-worktree --project-root . \
  --loaded-skill-path <absolute-runtime-advertised-SKILL.md-path>
```

User-authorized delivery is the bounded exception: a session in either participating worktree can
complete the integration while retaining its own Skills.
See [source-checkout distribution](specs/concorde/services/install-boundary.md#featureinstallationself-distribute).
