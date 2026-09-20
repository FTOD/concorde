# Installing and updating Concorde

Installation puts the Framework tools and instructions into a project so its developer can use
Concorde. It does not write the project's intended business behavior. The [Spec Module](../spec/module.md) owns initialization as a separate
step after installation.

## Terminology

| Term                                                | Meaning / definition                                                                                  |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Installation                                        | Placing and verifying the Framework-owned tools, instructions and runtime assets in a target project. |
| Update                                              | Refreshing the outputs recorded as owned by the installer, while preserving project-owned content.    |
| Installation receipt                                | A record of exactly which outputs the installer owns and which bytes it last installed.               |
| [Initialization](../spec/initialize.md#terminology) | Defined in Project initialization.                                                                    |
| [Protocol binding](../spec/values.md#terminology)   | Defined in Identities and versions.                                                                   |
| [Spec](../module.md#terminology)                    | Defined in Concorde Framework.                                                                        |
| [Registry](../module.md#terminology)                | Defined in Concorde Framework.                                                                        |

## A normal installation

Start by previewing the proposed installation into the intended project. Inspect the target and
owned changes before applying. The installer deploys Framework tools and the Protocol copy,
prepares the required runtime, and installs the Pi session extension shim and its `AGENTS.md`
Protocol entry. Pi is the only supported client; the installer has no client-selection flag and
rejects the retired `--integration` option. It neither installs public Skills nor invokes the
Agent Skills CLI. The installer preserves project Specs, configuration and unrelated files.
The internal launcher runs inside the verified managed runtime, so the bootstrap interpreter
needs no Concorde dependencies. Then initialize the project's own registry and first Spec, and
supply the business intent that the initial draft deliberately leaves unknown.

For example, installing Concorde into a service does not mean Concorde knows that service's retry or
payment policy. Installation supplies the tools; initialization creates an honest starting point;
Spec authoring establishes the actual promises.

## Installing another worktree

Each consumer worktree needs its own complete installation, even when its Framework, runtime and
receipt are Git-ignored. Its normal Pi session loads its local entry and uses its own Framework
and managed dependencies. Use an explicitly admitted source or installed package as the provider,
not a global package name or a primary-runtime fallback. An installed package includes the same
supported installer, so a consumer can bootstrap another ordinary Git-created worktree:

```sh
python3 /explicit/project/.concorde/framework/scripts/install-concorde.py \
  --target /explicit/new-worktree --preserve-project --preview
# Inspect the plan, then repeat with --apply.
```

Preservation leaves existing root instructions and complete project Protocol bytes untouched and
does not adopt inherited ownership. This handles committed AGENTS guidance without requiring an
ignored receipt to have been committed too. Missing assets can be seeded only under the
[project preservation contract](contracts.md#preserve-project-contract). Locally receipt-owned
edits still conflict; an incomplete Protocol tree is never completed from a different version.
The accepted binding is not updated. Receiving a complete installation does not make an
incompatible project runnable until its real Protocol/configuration admission succeeds.

The host can use the [local installation service](contracts.md#local-installation-service) with
explicit bootstrap authority before admission. Later calls verify/reuse current local assets,
without reinstalling them. Failed or stale verification stops; it never redirects execution to
the provider's environment. Package provenance is distinct from project/lifecycle authority:
primary alone still holds durable status and runs. Installation does not create worktrees,
move sessions, coordinate work or change worker grants. The installer needs exclusive target
ownership; it refuses an active Concorde source checkout and unsupported/concurrent locking.

## Updating without overwriting local work

An update compares the receipt with current bytes. A local change to an installer-owned output is a
conflict, not permission to discard it. Project-owned content remains outside that replacement scope.
A failed installation transaction attempts to recover its owned changes rather than present partial
state as a completed installation. Upgrading a legacy multi-client receipt removes only
unchanged receipt-owned retired files and exact owned root blocks. Modified files or blocks,
symlinks and stale previews conflict before writing. A root file the installer created solely
for its entry disappears only when removing the entry leaves it empty; a user-created file stays.
Unrelated files and all text outside the owned block remain unchanged.

Skills previously placed by the external `npx skills` CLI, and its `skills-lock.json`, were never
receipt-owned. The installer leaves them untouched and reports a manual migration notice in both
text and JSON output. Inspect `.agents/skills` and `.claude/skills` and manually remove only retired
Concorde entries you own. Do not delete those directories or the CLI lock wholesale, and do not run
the retired CLI merely to install or upgrade Concorde. Empty legacy directories may remain.

An installed Protocol update does not silently accept new rules for the project. Review any required
Spec migration, then explicitly accept the new binding. This separates receiving software from agreeing
to a specification-language change. [Build](build.md) explains instruction freshness, and
[runtime](runtime.md) states the current runtime-replacement limitation.

## Precise specifications

The Module-owned [installation scenarios](scenarios.md#installation-service) and
[requirements](requirements.md) define ownership conflicts, configuration, retries and failure behavior.
The Spec Module owns initialization and Protocol acceptance.
