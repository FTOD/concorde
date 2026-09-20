# Build

Build renders terminal worker instructions, a private Pi session entry with the public Operation
catalog, Studio graph configuration, runtime schemas and Protocol assets. It reads authored
Operation guidance under `prompts/operation-guidance/`, worker instructions and Protocol adapters;
there is no independent Skill product, publishing command or client selector. Consumer installation
uses the same pure renderer with its explicit framework prefix and owns deployment separately.

The principles asset bundles the independent standard with the separate Framework execution profile.
Configuration, phase authority and authoring conventions belong to that profile, not the standard.

## Terminology

| Term                                                      | Meaning / definition                |
| --------------------------------------------------------- | ----------------------------------- |
| [Pi integration](../module.md#terminology)                | Defined in Concorde Framework.      |
| [Worker](../module.md#terminology)                        | Defined in Concorde Framework.      |
| [Operation](../module.md#terminology)                     | Defined in Concorde Framework.      |
| [Public operation](../operations/module.md#terminology)   | Defined in Operations.              |
| [Internal operation](../operations/module.md#terminology) | Defined in Operations.              |
| [Host](../module.md#terminology)                          | Defined in Concorde Framework.      |
| [Worktree](../module.md#terminology)                      | Defined in Concorde Framework.      |
| [Protocol binding](../spec/values.md#terminology)         | Defined in Identities and versions. |
| [Document role](../spec/values.md#terminology)            | Defined in Identities and versions. |
| [Worker profile](../harness/module.md#terminology)        | Defined in Harness.                 |

The build no longer emits the docsite-only `generated/docs/instructions.json` or
`generated/docs/wire.json`; normal owned-output cleanup retires old copies. This does not remove
runtime Agent instructions, exported schema APIs or `generated/protocol/schemas.json`.

## Rendering and freshness

Distribution owns each public Operation's authored description and guidance. Build resolves its
whole-line `@path.md` references and embeds those bytes with the exact versioned request schema in one Pi catalog. The
extension's `concorde` tool describes or runs the selected Operation through the shared launcher;
Pi supplies the invocation envelope, so guidance contains no standalone stdin mechanics. Building
or installing the catalog does not execute an Operation or grant worker authority. Operation
behavior stays with its providing Module. The [reference grammar](contracts.md#prompt-reference-grammar)
defines parameters and rejection rules; the old `@include path.md` spelling is retired.

The checkout's own entry is `generated/session/pi/concorde-session.ts`, outside ambient discovery.
It imports the checkout's extension and requests explicit developer authorization to run an
Operation. Installation instead places its receipt-owned shim under `.pi/extensions/`, importing
the deployed Framework and selecting the managed runtime. Both catalogs contain exactly eleven
public Operations; internal Operations have no catalog entry. Seven worker projections remain
independent internal instructions, not Skills.

Rebuilding may retire obsolete output only after complete safety preflight. An old manifest's
exact digest proves ownership of a retired file; a familiar Operation name alone does not. Modified
retired output, extra retired directory content, unknown generated files and symlinks stop writing
rather than authorizing deletion. External CLI-owned Skills and their lock are untouched; remove
only your own retired entries manually. See the [retirement contract](scenarios.md#scenario.distribution.build-retired-skills).

### Protocol and runtime support are separate

The package supports Protocol 10.0.0 with source_profile 15 and document metadata schema 2. Its tracked manifest binds the exact
generated rule and versioned schema bytes; project configuration binds the exact manifest bytes.
Context payloads and worker wrappers retain their independently versioned wire agreements; the
Protocol document-role migration does not change those envelopes. Build freshness establishes projection integrity;
structural validation, configured checks and review evidence remain separate. Updates to exported
schemas require a rebuild and explicit manifest rebinding in the same worktree. Consumer package
updates preserve the existing binding until explicitly accepted.

## Design

### Projection identity

Agent builds publish seven independent worker projections and no separate common one. Each
rendered `generated/agents/<name>.md` concatenates the shared common worker rules
(`prompts/workers/common.md`) and that worker's own role Spec source; the manifest records both
sources. Package
validation compares the unified `concorde.operations` metadata with every executable declaration:
exposure, context selection, determinism, USES, State and optional workspace/tools.

Agent instruction file membership must equal the declared worker inventory. Agent Python bindings,
role Spec bodies and available operation/wire sources are recorded build
inputs; changing them makes verify_fresh reject the old build even when the shared common
instruction body is unchanged.

### Projection test fixtures

The explicit fixture command `PYTHONPATH=src .venv/bin/python -m tests.concorde.support.build_fixture`
refreshes the tracked projection goldens from this checkout's pure build renderer. It records exactly
seven worker bodies and one Pi shim embedding eleven public Operations. It does not copy ambient
client assets or build another worktree. It retires only exact historical fixture members after
rejecting symlinks and unknown content. Golden comparisons remain byte-exact.

## Precise specifications

The Distribution Module owns the exact obligations and interface details in [contracts](contracts.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.

## Fresh source-maintenance selection

Source maintenance starts a new Concorde-catalog-free writer in a candidate, never a fork carrying
old instructions. The main remains outside that authoring context. After the writer checks,
commits and stops, main chooses independent testing as none, targeted or full with scope and reason.
When selected, main starts a separate fresh sibling tester in the same candidate. Both
disable inherited/discovered Concorde catalogs; only the tester explicitly loads the candidate Pi
entry. Failed tests return to the same maintenance session, then another fresh tester when selected.
Neither child delegates tasks. Ordinary milestones do not replace the maintenance session.

## Outer task roles and observation

`maintenance-worker` and `tester` are project-discovered pi-subagents task roles, not LangGraph
workers. Canonical prompts under `prompts/outer/` render checked project definitions in
`.pi/agents/`. Source build projects the separate coordinator prompt into the discovered
`.pi/extensions/concorde-coordinator.ts` extension, with a separate passive native-event observer entry.
Only the outer source main loads that coordinator: child profiles disable ambient extensions and
list only their own assets; terminal workers load only their granted extension. The coordinator
uses Pi's before-agent-start prompt hook and grants no tools or control. It does not infer role from
task text or inject contradictory instructions into children. Pi discovers APPEND_SYSTEM separately
from context files, so replacement prompts and context inheritance flags cannot isolate it.
Build retires the former source `.pi/APPEND_SYSTEM.md` only with exact prior-manifest ownership;
modified owned bytes fail preflight, while unowned user append files remain untouched. Consumer
installation never ships the source coordinator and preserves unrelated user append content. These explicit assets are not an ambient Operation
catalog. Source-only prompts and the maintenance observer wrapper never ship to consumers;
installer-owned generic tester definitions use the installed local Framework/runtime instead.
Outer pi-subagents is a host prerequisite, not a new worker dependency.

### Source-main discussion and task collection

Source main can answer questions, inspect relevant sources and clarify changes without starting
maintenance. It can retain a sufficiently discussed actionable change as a lightweight TODO note
when the user requests or approves recording. Maturity concerns the goal, scope and expected
behavior, not a detailed plan or verified Spec. An underspecified TODO request leads to a choice
between more clarification and saving an issue, not an automatic record. This keeps open questions
out of the actionable list without losing the user's option to retain an immature concern.

The notes preserve the discussion's rationale and decisions for later work rather than replacing
planning or implementation artifacts. Main updates the same change instead of duplicating it.
Promotion of a mature issue transfers its relevant background before removing its source, with
consent, write verification and unresolved-content safeguards. Ordinary Issue dispositions still
retain observations under the [Issues storage contract](../issues/execution-reference.md#issues-disposition-boundary);
record transfer does not claim a verified resolution or change that runtime API. Unsafe deletion
or associated-record ownership conflicts preserve the source instead of widening authority.

Collection is always available, not another mode, Operation or delegated task. Recording alone
creates no maintenance candidate or child ownership record and changes no implementation or Spec.
Explicit implementation requests still use maintenance; an accumulated list never triggers work
without a user request. The [collection scenarios](scenarios.md#scenario.distribution.main-todo-collection)
define the source-main instruction contract, not a promise of deterministic model decisions.
These instructions use the existing main-only projection boundary and never ship to consumers.

### Coordination and validation

Main owns scope, worktree assignment, continuation decisions, selected checks/independent testing
and integration authorization. Source-main instructions make primary status registration a launch
prerequisite: each candidate has a verified stable task identity before its maintenance child starts,
then main binds the actual launched child rather than a workflow container. Before transferring
ownership to a tester or resumed author, main verifies the previous child stopped, releases that
exact owner and verifies the new binding. Failed registration or handoff stops dependent work;
run evidence and mission notes cannot replace status. Terminal records remain available, and
integration and separately authorized cleanup stay distinct. These are host-coordination duties,
not a new runtime or child grant; the [outer-role scenario](scenarios.md#scenario.distribution.outer-roles)
defines the instruction obligation. Already-running sessions retain their loaded instructions.
Maintenance directly edits and self-checks, never delegates or
integrates. Tester starts fresh, keeps governing artifacts read-only and returns failures rather
than repairing. Its command tool uses the existing OS read-only check executor with disposable
external fixtures and the trusted tester-only scratch-backed private `/tmp` profile; unavailable
isolation fails closed. Real host `/tmp` inputs use the explicit read-only `CONCORDE_TEST_HOST_TMP`
view, except governing/runtime locations preserved at their canonical names. This permits normal
nested terminal preparation without staging runtime assets or making host `/tmp` writable.
The command schema remains only command/timeout; the model cannot select mounts or weaken this policy.
Explicit extension lists disable ambient
catalogs without granting additional tools. Effective discovery/preflight remains host-owned.

Local edits need format/static/targeted checks, coherent changes affected integration, final
stable input one full Python suite and applicable gates. Stage handoff alone adds no full suite;
a same-tree commit only needs HEAD/bootstrap checks. Changed relevant input/environment invalidates
corresponding evidence. Same-input reruns state their reason; self-tests never become independent.
Same-session complete unchanged Specs need no repeated bundle read; new seams/readers do.
Resource handoff requests distinguish observed capacity/current input/cache/reserve/compaction
from cumulative usage, document size or missing tools. Unknown metrics remain unknown and main
verifies handoff need; quality concerns are separately labelled.

Passive timing reuses Pi lifecycle, provider, tool and compaction hooks and native session entries;
it changes no prompts, tools, providers or settings. Main may analyze these local diagnostics and
persist evidence under its existing primary authority; child hooks receive no primary write grant.

`select-session --mode test --runtime <absolute-candidate-launcher> --pi-entry <absolute-private-entry.ts>`
checks all current candidate source, manifest, entry and embedded catalog bytes. Maintenance mode
accepts no Pi entry or catalog. Removed `--skill` and schema-1 selections fail explicitly. Missing,
unreadable, symlinked, stale or outside paths block without fallback. These are launch inputs,
not receipts for loading an extension, using a tool or executing a model. The external host enforces
fresh non-forked context, discovery disablement and the actual task/file/tool ceiling.

Save selection only to ignored candidate `.concorde/work/` scratch with `--output`; no shared Git
excludes or ambient installer settings are changed. `select-session --verify <absolute-selection>`
reverifies without issuing replacement inputs. The fresh Pi host supplies that same path in
`CONCORDE_SESSION_SELECTION`, a separate host-owned configuration directory and only the returned
Operation entry with all returned discovery-disable flags, plus the explicitly registered bounded
observation/check assets. Native pi-subagents launches use fresh context, no skills, async true and
the [per-launch selection binding](contracts.md#private-session-selection), not a global alias or
settings/environment mutation. It must reject extension loading errors.
The source extension requires explicit saved selection and the candidate Python environment (no ambient interpreter fallback),
checks selection before registration and each tool call, and rejects changed session provenance.
The launcher independently reverifies before execution. The host may retain selection in primary
run evidence without claiming the model loaded it. Maintenance authoring uses deterministic
commands, never public Operations governing their own implementation.

Private selection refuses Studio runtime redirects. Candidate code may operate on explicitly
scoped disposable consumer project data; it cannot redirect into another linked worktree of the
source repository. The test session remains in its candidate. Consumer installation is separate.
