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
includes and embeds those bytes with the exact versioned request schema in one Pi catalog. The
extension's `concorde` tool describes or runs the selected Operation through the shared launcher;
Pi supplies the invocation envelope, so guidance contains no standalone stdin mechanics. Building
or installing the catalog does not execute an Operation or grant worker authority. Operation
behavior stays with its providing Module.

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
commits and stops, the main starts a separate fresh sibling tester in the same candidate. Both
disable inherited/discovered Concorde catalogs; only the tester explicitly loads the candidate Pi
entry. Failed tests return to maintenance followed by another fresh tester. Neither child delegates tasks.

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
explicit entry with all returned discovery-disable flags. It must reject extension loading errors.
The source extension requires explicit saved selection and the candidate Python environment (no ambient interpreter fallback),
checks selection before registration and each tool call, and rejects changed session provenance.
The launcher independently reverifies before execution. The host may retain selection in primary
run evidence without claiming the model loaded it. Maintenance authoring uses deterministic
commands, never public Operations governing their own implementation.

Private selection refuses Studio runtime redirects. Candidate code may operate on explicitly
scoped disposable consumer project data; it cannot redirect into another linked worktree of the
source repository. The test session remains in its candidate. Consumer installation is separate.
