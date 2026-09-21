# Distribution requirements

These precise specifications belong directly to the [Distribution Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term                                                | Meaning / definition                         |
| --------------------------------------------------- | -------------------------------------------- |
| [Pi integration](../module.md#terminology)          | Defined in Concorde Framework.               |
| [Installation](installation.md#terminology)         | Defined in Installing and updating Concorde. |
| [Update](installation.md#terminology)               | Defined in Installing and updating Concorde. |
| [Installation receipt](installation.md#terminology) | Defined in Installing and updating Concorde. |
| [Protocol binding](../spec/values.md#terminology)   | Defined in Identities and versions.          |
| [Worktree](../module.md#terminology)                | Defined in Concorde Framework.               |

## Distribution

### req.distribution.no-silent-protocol-rewrite — No silent Protocol rebinding

Install or update SHALL NOT silently rewrite a consumer's Protocol binding.

### req.distribution.explicit-binding-decision — Changed Protocol assets need explicit acceptance

A package with changed Protocol assets SHALL require the consumer's explicit binding decision
before execution.

### req.distribution.build-idempotent — Build output is deterministic and idempotent

`build` and `build --check` SHALL be idempotent and byte-identical across repeated runs.

### req.distribution.build-no-io — Build performs no network or process I/O

`build` and `build --check` SHALL perform no network or process I/O.

### req.distribution.one-worktree-build — Build stays within its own worktree

Every build invocation SHALL operate only on the worktree containing its named sources.

### req.distribution.no-cross-worktree-build — No cross-worktree build output

Build SHALL NOT point one worktree's build at another worktree's outputs.

### req.distribution.checkout-skills-user-invoked — Source-checkout Pi entry waits for the developer

Build SHALL render the source-checkout Pi entry only under private `generated/session/pi/`, never ambient client discovery directories or standalone Skill products.

There is no independent publishing step or supported Codex/Claude client renderer. Consumer
installation remains a separate Pi-only receipt-owned deployment. Fresh source-maintenance
isolation and private selection obligations remain independent of output generation.

### req.distribution.private-selection — Exact private candidate provenance

Private session selection SHALL reject missing, stale, unreadable or out-of-candidate Pi entry, embedded catalog, implementation and runtime paths without any global or name-based fallback.

A selection returns complete bytes and their provenance, not evidence of model loading or execution.

### req.distribution.pi-session-public-only — The Pi session tool exposes only public Operations

The Pi session extension SHALL offer exactly the public Operations as the operations of its
`concorde` tool.

The native context-assessor is callable only through a prepared native call; other internal stage Operations have no tool entry; the source checkout's shim additionally tells the
model to run an Operation only on the developer's explicit request.

### req.distribution.launcher-sigterm-cancels — SIGTERM cancels the launcher like Ctrl-C

The launcher SHALL treat SIGTERM as a host interrupt that cancels a running worker and prints the
result envelope before exiting.

A developer's client, such as the Pi session extension aborting a turn, ends a run it no longer
wants with SIGTERM; dying mid-write would leave the worker process and the change's lifecycle
record behind.

### req.distribution.launcher-managed-runtime — The installed launcher runs inside the managed runtime

In an installed project the launcher SHALL execute under the managed runtime's interpreter,
whatever interpreter started it.

The launcher may be started with ambient `python3`, which need not carry LangGraph, and the
managed runtime `.concorde/.venv` is the only environment the installer verified for the installed
framework. The launcher therefore re-executes itself with that runtime's interpreter when the
installer's verified runtime is present beside the framework, and the provisioner verifies each
public Operation with that same interpreter. An unavailable selected Graph backend reports
`missing_runtime` instead of a bare import failure. Direct Host-tool dispatch does not itself
require Graph compilation; complete installed-runtime verification remains mandatory.

### req.distribution.operation-guidance-fresh — Pi catalogs are complete fresh projections

Build and package validation SHALL check the complete Pi catalog's descriptions, guidance, request schemas and output/source identities against the authored public Operation inventory.

Eleven public entry names and seven legacy terminal worker renderings remain, plus the separately
rendered native context-assessor instructions. Public context-solve prepares a supported native Agent
call and verifies its result; it must not silently execute the legacy worker. Internal instructions are
not Skills. Missing or drifted output fails checking; `build` regenerates from authored inputs.

### req.distribution.pi-only-install — Installation supports only Pi

Installation SHALL install only the Pi client extension and its Protocol guidance, without invoking a Skills CLI or distributing standalone Skills.

The manifest explicitly declares `client: "pi"`. Retired client flags are rejected, not silently
mapped to Pi. npm remains required for actual Pi runtime dependencies.

### req.distribution.retired-installation-ownership — Legacy retirement preserves ownership

Installation SHALL remove retired outputs only under the existing receipt/digest and bounded root-block ownership rules.

External CLI-owned Skills and locks are not installer ownership and remain untouched, with an
explicit manual migration notice. Edited owned output conflicts rather than being discarded.

### req.distribution.root-block-ownership — Root rule ownership is block-scoped

A root rule entry SHALL be owned only within its exact bounded block, including its separator.

### req.distribution.no-surrounding-text-rewrite — Surrounding user text stays untouched

Installation SHALL NOT hash or replace user text surrounding an owned root block.

### req.distribution.rollback-on-failure — Installation rolls back atomically on failure

A runtime or setup failure during installation SHALL roll back root bytes, modes and the receipt
together with the other installation outputs.

### req.distribution.worktree-local-install — Independent local execution installation

The installation service SHALL return verified execution paths only for a complete target-local Pi entry, Framework, managed runtime/dependencies and receipt of the exact explicitly admitted package identity.

A source or installed provider supplies installation bytes, not a fallback runtime. Installation
adds no lifecycle authority: primary alone retains durable status and runs. A caller must complete
installation verification and ordinary project/Protocol admission before any local Operation or
worker launch; this service itself launches neither.

### req.distribution.outer-roles — Real outer task registration

Build and installation SHALL provide documented project-discovered outer role definitions with checked canonical prompt provenance, distributing tester but never source-only maintenance/coordinator instructions.

Exact names are maintenance-worker and tester. Role definitions and passive telemetry are allowed
project discovery assets, not public Operation entries. Source Operation shims remain private.
Existing user agent-file collisions and modified receipt-owned definitions block replacement.
Coordinator delivery is source-main-only through the explicit extension loading boundary, not a
project-wide append prompt. Actual Pi effective-prompt loading, including fresh and resumed sessions,
must keep maintenance-worker, tester and terminal node identities free of source-main instructions.
Unrelated consumer APPEND_SYSTEM content is not adopted, overwritten or removed.

### req.distribution.test-evidence — Input-bound test diagnostics

The test runner SHALL record declared reason, scope, phase and whitelisted input/test/runtime/lock/environment fingerprints without converting diagnostic timing into workflow authority.

Legacy CLI calls remain valid with manual reason and unspecified scope/phase. Discovery, queue,
execution intervals and prior/attempt references are observable; fixture setup is unknown unless
runtime spans measure it. Summed concurrent work is not elapsed wall time. Fingerprints do not
claim coverage of unobserved environment values, and telemetry excludes secret values and outputs.
