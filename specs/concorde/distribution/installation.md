# Installing and updating Concorde

Installation puts the Framework tools and instructions into a project so its developer can use
Concorde. It does not write the project's intended business behavior. The [Spec Module](../spec/module.md) owns initialization as a separate
step after installation.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| Installation | Placing and verifying the Framework-owned tools, instructions and runtime assets in a target project. |
| Update | Refreshing the outputs recorded as owned by the installer, while preserving project-owned content. |
| Installation receipt | A record of exactly which outputs the installer owns and which bytes it last installed. |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |
| [Initialization](../spec/initialize.md#terminology) | Defined in Project initialization. |
| [Protocol binding](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Registry](../module.md#terminology) | Defined in Concorde Framework. |

## A normal installation

Start by previewing the proposed installation into the intended project. Inspect the target and
owned changes before applying. The installer deploys Framework tools and the Protocol copy,
prepares the required runtime, and installs each chosen client's projection: for the Pi coding
agent the session extension shim, for Claude Code and Codex the Skills, which it does not copy
itself but has the Agent Skills CLI (`npx skills`, pinned by the package) place from the deployed
framework copy, in that tool's own layout with its own `skills-lock.json`. Several clients may be
chosen at once, and each gets its root instruction entry. The installer preserves project Specs,
configuration and unrelated files. The Skills name the launcher with the ambient `python3`; once
installed, the launcher runs itself inside the managed runtime, so that interpreter needs no
Concorde dependencies. Then initialize the project's own registry and first Spec, and
supply the business intent that the initial draft deliberately leaves unknown.

For example, installing Concorde into a service does not mean Concorde knows that service's retry or
payment policy. Installation supplies the tools; initialization creates an honest starting point;
Spec authoring establishes the actual promises.

## Updating without overwriting local work

An update compares the receipt with current bytes. A local change to an installer-owned output is a
conflict, not permission to discard it. Project-owned content remains outside that replacement scope.
A failed installation transaction attempts to recover its owned changes rather than present partial
state as a completed installation. The Skills the Agent Skills CLI placed are not owned outputs:
an update runs the CLI again so it refreshes them from the updated framework copy. Each run names
the complete client selection; a client left out loses its root entry, while the Skills the CLI
placed for it stay until you remove them with `npx skills remove`. A root file the installer
created only to hold its entry disappears with that entry; a file you created keeps your text, or
stays empty, and is never removed.

An installed Protocol update does not silently accept new rules for the project. Review any required
Spec migration, then explicitly accept the new binding. This separates receiving software from agreeing
to a specification-language change. [Build](build.md) explains instruction freshness, and
[runtime](runtime.md) states the current runtime-replacement limitation.

## Precise specifications

The Module-owned [installation scenarios](scenarios.md#installation-service) and
[requirements](requirements.md) define ownership conflicts, configuration, retries and failure behavior.
The Spec Module owns initialization and Protocol acceptance.
