```concorde-document
{
  "id": "document.distribution.module",
  "owner": "module.distribution",
  "main_visible": true
}
```

# Distribution

Build authored projections, install and configure owned integrations, provision the managed runtime and keep a source checkout's own projections bound to the worktree that built them.

## Purpose

Distribution turns authored Framework sources into the deterministic outputs a project actually
runs: rendered Agent instructions and Skills, an installed and configured integration, and a
verified managed Python and viewer runtime. Its users are developers installing or updating
Concorde into a consumer project, developers maintaining this source checkout, and every other
Framework capability that depends on fresh generated projections before it executes. It owns Skill
sources and shared invocation instructions; installed Skills are read by the developer's external
runtime, which submits requests to the Development capability boundary. Capability behavior remains
with its providing Module. Distribution's installation promises stop at owned, receipt-tracked
output: it never edits project-owned Specs or configuration, and it
never decides what those Specs should say.

## Requirements

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

### req.distribution.root-block-ownership — Root rule ownership is block-scoped

A root rule entry SHALL be owned only within its exact bounded block, including its separator.

### req.distribution.no-surrounding-text-rewrite — Surrounding user text stays untouched

Installation SHALL NOT hash or replace user text surrounding an owned root block.

### req.distribution.rollback-on-failure — Installation rolls back atomically on failure

A runtime or setup failure during installation SHALL roll back root bytes, modes and the receipt
together with the other installation outputs.

### req.distribution.guard-inspects-text — Guard decides from the submitted command text

The worktree guard SHALL decide from the submitted command text, including global git options such
as `-C` and `--git-dir=`.

### req.distribution.guard-not-agent-reliant — Guard does not rely on agent memory

The worktree guard SHALL NOT depend on an agent remembering the policy.

### req.distribution.guard-checkout-only — Guard protects only this checkout's sessions

The worktree guard SHALL protect only developer sessions of this source checkout.

### req.distribution.guard-not-in-consumer-projects — Guard is excluded from consumer projects

The worktree guard SHALL NOT be installed into consumer projects.

## Scenarios

Scenario definitions for installing, configuring and guarding this source checkout's own worktrees
are registered in [installation](installation.md). Scenario definitions for rendering and
freshness-checking projections are registered in [build](build.md). Scenario definitions for
provisioning the managed Python and viewer runtime are registered in [runtime](runtime.md).

## Ontology

Distribution's Ontology separates the three programs that do the work — Build, Installation and
Managed runtime — from the interfaces that expose them and the records that carry state between
them, then relates all of it in the diagram below.

### Entities

The three programs below realize build, installation and runtime provisioning; the interface
entities are their means of use, and the remaining entities name the data and actors those
interfaces exchange. Installation lists the `src/concorde/distribution/`,
`tests/concorde/distribution/` and `templates/` directories, build and runtime provisioning list the
golden Skill fixture directories and `viewer/`, and the exact entries those two keep inside a listed
directory stay with them. The Skill sources entity owns `skills/` and `prompts/workflow-host/` as complete
directory prefixes; the capability providers retain their own executable contracts.

```concorde-entities
[
  {
    "id": "entity.distribution.build",
    "title": "Build",
    "kind": "program",
    "responsibility": "Renders every Agent, Skill, rule, schema, documentation and Studio-graph output deterministically from authored sources, records their exact source/output digests in the build manifest, verifies freshness before ordinary capability execution, and runs package validation.",
    "files": [
      "agents/__init__.py",
      "capabilities/__init__.py",
      "concorde.json",
      "pyproject.toml",
      "src/concorde/distribution/build.py",
      "src/concorde/distribution/package_validation.py",
      "src/concorde/distribution/prompt_resolver.py",
      "tests/concorde/distribution/test_build.py",
      "tests/concorde/distribution/test_package_validation.py",
      "tests/concorde/distribution/test_prompt_resolver.py",
      "tests/concorde/fixtures/build/golden/claude/",
      "tests/concorde/fixtures/build/golden/codex/",
      "tests/concorde/support/build_fixture.py",
      "uv.lock"
    ]
  },
  {
    "id": "entity.distribution.installation",
    "title": "Installation",
    "kind": "program",
    "responsibility": "Plans and applies receipt-owned Framework, Skill and bounded root-guidance changes for a target project without replacing project-owned Specs or configuration, and hosts the source checkout's own deterministic maintenance CLI and worktree guard.",
    "files": [
      "capabilities/configure.py",
      "scripts/concorde.ps1",
      "scripts/concorde.py",
      "scripts/concorde.sh",
      "scripts/development/check-docsite-types.py",
      "scripts/development/run-tests.py",
      "scripts/install-concorde.py",
      "scripts/requirements.lock",
      "scripts/run-capability.py",
      "scripts/worktree-guard.py",
      "src/concorde/distribution/",
      "templates/",
      "tests/concorde/distribution/"
    ]
  },
  {
    "id": "entity.distribution.skill-sources",
    "title": "Skill sources",
    "kind": "authored instructions",
    "responsibility": "Own the public Skill wrappers and shared invocation instructions that adapt global and lifecycle capability contracts for the developer's external agent runtime.",
    "files": [
      "prompts/workflow-host/",
      "skills/"
    ]
  },
  {
    "id": "entity.distribution.installed-skills",
    "title": "Installed Skills",
    "kind": "instruction artifact",
    "responsibility": "The rendered Skill files installed into the target project's Codex or Claude integration, each exposing one public capability through instructions consumed outside Concorde's worker runtime."
  },
  {
    "id": "entity.distribution.developer-runtime",
    "title": "Developer runtime",
    "kind": "external actor",
    "responsibility": "The developer's Codex or Claude runtime that reads installed Skill instructions and invokes the declared capability boundary; installing a Skill grants no worker permission."
  },
  {
    "id": "entity.distribution.managed-runtime",
    "title": "Managed runtime",
    "kind": "program",
    "responsibility": "Plans, stages and verifies the locked Python interpreter and the official viewer package as versioned, hash-bound artifacts, recording a recoverable identity receipt.",
    "files": [
      "src/concorde/distribution/managed_runtime.py",
      "tests/concorde/support/managed_runtime.py",
      "viewer/"
    ]
  },
  {
    "id": "entity.distribution.spec",
    "title": "Spec",
    "kind": "used module",
    "target_id": "module.spec",
    "responsibility": "Defines the project configuration and registry that installation, configuration and initialization read or write, with exactly one pinned Protocol binding."
  },
  {
    "id": "entity.distribution.install-script",
    "title": "Install script",
    "kind": "interface",
    "responsibility": "The `python3 scripts/concorde.py` and `scripts/install-concorde.py` command surface that previews owned changes by default and applies them only with `--apply`, and the `concorde-configure` capability that changes a supported integration or enforcement setting on an initialized project."
  },
  {
    "id": "entity.distribution.build-command",
    "title": "Build command",
    "kind": "interface",
    "responsibility": "The `build`/`write_build`/`check_build`/`verify_fresh`/`load_agent` Python functions and the `python3 scripts/concorde.py build` CLI entry that render, write, compare and freshness-check the projections, and load one Agent's current rendered binding."
  },
  {
    "id": "entity.distribution.runtime-provisioning",
    "title": "Runtime provisioning interface",
    "kind": "interface",
    "responsibility": "The `load_runtime_spec`/`plan_runtime`/`provision_runtime` functions that describe local provisioning state and stage the reviewed action for the locked Python runtime and the official viewer."
  },
  {
    "id": "entity.distribution.worktree-guard",
    "title": "Worktree guard",
    "kind": "interface",
    "responsibility": "The `scripts/worktree-guard.py` Claude Code and Codex hook command that decides one hook payload and refuses native worktree creation in a developer session of this source checkout."
  },
  {
    "id": "entity.distribution.authored-sources",
    "title": "Authored sources",
    "kind": "concept",
    "responsibility": "The root `concorde.json`, canonical `prompts/`, `skills/`, `capabilities/`, Protocol chapters and the contract modules under `src/concorde/spec` that the build resolves through `@include` graphs into deterministic outputs."
  },
  {
    "id": "entity.distribution.build-manifest",
    "title": "Build manifest",
    "kind": "record",
    "responsibility": "The recorded source-to-output digest identity at `generated/build-manifest.json` that establishes freshness and that the host checks before every top-level capability invocation except a lifecycle capability."
  },
  {
    "id": "entity.distribution.package-inventory",
    "title": "Package inventory",
    "kind": "record",
    "responsibility": "The distributable `concorde.json` manifest naming the package version, accepted Protocol binding, workspace protocol, roles, capabilities, Skills and templates that installation selects assets from."
  },
  {
    "id": "entity.distribution.installation-proposal",
    "title": "Installation proposal",
    "kind": "record",
    "responsibility": "The preview of receipt-owned Framework, Skill and root-guidance replacements, computed from the package inventory and the target's current ownership receipt, that installation applies only once accepted and still current."
  },
  {
    "id": "entity.distribution.ownership-receipt",
    "title": "Ownership receipt",
    "kind": "record",
    "responsibility": "The hashed record of owned installed bytes, required runtime identity and root-guidance block boundaries that installation checks before accepting a change and restores from on failure."
  },
  {
    "id": "entity.distribution.target-project",
    "title": "Target project",
    "kind": "concept",
    "responsibility": "The initialized or uninitialized project directory that an installation, configuration or build proposal is applied to, whose project-owned Specs, configuration and unrelated files are always preserved."
  },
  {
    "id": "entity.distribution.verified-runtime",
    "title": "Verified managed runtime",
    "kind": "concept",
    "responsibility": "The staged, hash-verified Python interpreter and official viewer package that installation provisions and that runtime and viewer consumers read through the recorded receipt."
  },
  {
    "id": "entity.distribution.integration-configuration",
    "title": "Integration configuration",
    "kind": "concept",
    "responsibility": "The typed, supported integration and enforcement setting that `concorde-configure` applies atomically to an initialized project, leaving the previous configuration in place on any failure."
  },
  {
    "id": "entity.distribution.developer-session",
    "title": "Developer agent session",
    "kind": "external actor",
    "responsibility": "The Claude Code or Codex agent session in this source checkout whose native worktree creation the worktree guard refuses, so its loaded worktree-owned Skills never outlive the worktree that built them."
  }
]
```

### Relationships

Build, Installation and Managed runtime are independent programs that only meet at explicit
records: Build never writes into a target project, Installation never renders Framework assets
itself, and Managed runtime never chooses which files Installation replaces. Ownership receipt and
Build manifest play matching but distinct roles — one binds installed bytes in a target project,
the other binds authored sources to rendered outputs in this checkout or a build client — and
neither substitutes for the other. In this source checkout specifically, the worktree guard and the
developer session it constrains are the only entities with no counterpart in an installed consumer
project, because the guard is checkout policy and ships to no one else.

Skill sources are authored and owned here, Build renders them, and Installation places the rendered
Skills in the target integration. The external Developer runtime consumes those instructions and
calls the declared capability boundary. This distribution path creates no worker Harness input and
does not transfer ownership of executable capability behavior to Distribution.

```mermaid
flowchart TB
    accTitle: Distribution entities and relationships
    accDescr: Build renders Authored sources and Skill sources, records freshness in the Build manifest and validates the Package inventory. Installation installs rendered Skills for the external Developer runtime, applies receipt-owned proposals to the Target project and reads configuration through Spec. Managed runtime provisions the Verified managed runtime. In this source checkout the Worktree guard constrains the Developer agent session.
    authored["Authored sources"]
    build["Build"]
    buildCmd["Build command"]
    manifest["Build manifest"]
    inventory["Package inventory"]
    installScript["Install script"]
    installation["Installation"]
    proposal["Installation proposal"]
    receipt["Ownership receipt"]
    target["Target project"]
    config["Integration configuration"]
    runtimeIface["Runtime provisioning interface"]
    managedRuntime["Managed runtime"]
    verifiedRuntime["Verified managed runtime"]
    guard["Worktree guard"]
    session["Developer agent session"]
    spec["Spec"]
    skillSources["Skill sources"]
    installedSkills["Installed Skills"]
    developerRuntime["Developer runtime"]
    skillSources -->|are rendered by| build
    build -->|renders| installedSkills
    installation -->|installs| installedSkills
    developerRuntime -->|reads| installedSkills
    authored -->|are rendered by| build
    build -->|is exposed through| buildCmd
    build -->|records freshness in| manifest
    build -->|validates| inventory
    inventory -->|supplies distributable assets to| proposal
    installScript -->|is realized by| installation
    installation -->|computes| proposal
    receipt -->|supplies before-state to| proposal
    proposal -->|applies accepted replacements to| target
    proposal -->|requires| verifiedRuntime
    installation -->|records accepted ownership in| receipt
    installation -->|applies| config
    config -->|is applied to initialized| target
    runtimeIface -->|is realized by| managedRuntime
    managedRuntime -->|provisions and verifies| verifiedRuntime
    installation -->|reads project configuration and registry through| spec
    session -->|loads worktree-owned outputs rendered by| build
    guard -->|refuses native worktree creation in| session
```

## Dependencies and composition

```concorde-dependencies
[
  {
    "target_id": "module.spec",
    "responsibility": "Define the project configuration and registry that installation, configuration and initialization read or write.",
    "selection_condition": "When installing into or configuring an initialized project, or when a Protocol binding must be checked.",
    "relied_upon_promises": [
      "[Preserve the accepted binding and reject incompatible configuration](../spec/values.md#framework-configuration-and-storage-versions)"
    ]
  }
]
```

## Unresolved information

Managed runtime's replacement design intends to preserve the previous valid runtime until a rebuild
is verified and to restore it after a failed rebuild, but the current provisioning implementation
still removes an owned environment before rebuilding; this preservation promise is not yet fulfilled
by code, and callers must not infer recovery from the absence of success metadata.

Project initialization and Protocol-binding decisions belong to `module.spec`'s `concorde-init`
capability, not to this Module; installation never creates the registry or a Module stub itself.

## Ownership, context and implementation status

Runtime admission, initialization, installation inventory and package Spec/wire alignment support Protocol 5/Profile 12. Build success proves output freshness only. Project updates must preserve explicit owner/reference choices and never silently migrate consumers.
