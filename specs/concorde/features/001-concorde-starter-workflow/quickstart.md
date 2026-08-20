# Quickstart Validation: Concorde Starter Workflow

This guide is the end-to-end acceptance path for Feature 001. It is intended to be runnable after
implementation and uses only the normal Spec Kit lifecycle plus the commands installed by Concorde.

## Prerequisites

- `uv`, using the repository's pinned Python 3.11 development environment.
- Spec Kit/Specify CLI 0.16.4 available as `specify`.
- A checkout of this repository.
- Codex for the primary skills-mode run. Repeat the registration section with one supported
  slash-command integration for portability acceptance.

Confirm versions from the repository root:

```bash
uv --version
uv sync
uv run python --version
specify --version
```

Expected: Python is at least 3.11 and Specify reports 0.16.4. Do not claim compatibility from a run
against another Spec Kit version.

## 1. Build and Verify Release Inputs

```bash
uv run python scripts/release/build-components.py --output dist \
  --base-url http://127.0.0.1:8765
specify bundle build --path bundles/concorde-starter --output dist
uv run python scripts/release/verify-release.py --dist dist
```

Expected:

- the preset and extension install-contract tests pass, and native bundle build validates the bundle
  manifest structurally;
- the bundle contains exactly `concorde-core@0.1.0` and `concorde@0.1.0`;
- no workflow or step is declared;
- catalog metadata, archive manifests, versions, and digests agree; and
- two identical builds produce byte-equivalent release archives.

## 2. Serve the Development Catalogs

In a second terminal from the repository root:

```bash
uv run python tests/concorde/support/catalog_server.py --dist dist --port 8765
```

Keep the server running. It exposes the generated catalogs and archives from localhost, allowing the
real catalog download and trust paths to be tested without publishing a release.

## 3. Initialize a Clean Codex Skills Project

```bash
validation_root="$(mktemp -d)"
cd "$validation_root"
specify init --here --integration codex --integration-options="--skills"
```

The validation directory is disposable. Do not point these commands at a project containing
uncommitted user architecture sources.

Add the three development catalogs as explicitly trusted install sources:

```bash
specify extension catalog add http://127.0.0.1:8765/extensions.json \
  --name concorde-dev --install-allowed
specify preset catalog add http://127.0.0.1:8765/presets.json \
  --name concorde-dev --install-allowed
specify bundle catalog add http://127.0.0.1:8765/bundles.json \
  --id concorde-dev --policy install-allowed
```

Expected: each source is recorded at project scope as install-allowed. Localhost HTTP is for this
fixture only; release catalogs and artifact URLs must use HTTPS.

Validate the local bundle structure without asking the native validator to rediscover external
component catalogs (the later `bundle info` and install steps resolve and verify those exact pins):

```bash
concorde_checkout=/path/to/concorde
specify bundle validate --offline --path "$concorde_checkout/bundles/concorde-starter"
```

Expected: the manifest is valid. Spec Kit may print offline reference-verification warnings; these are
resolved by the catalog-backed preview and install assertions below.

Before the catalog-ID journey, exercise every supported local bundle source form against the same
component catalogs:

```bash
specify bundle install "$concorde_checkout/bundles/concorde-starter"
specify bundle remove concorde-starter
specify bundle install "$concorde_checkout/bundles/concorde-starter/bundle.yml"
specify bundle remove concorde-starter
specify bundle install "$concorde_checkout/dist/concorde-starter-0.1.0.zip"
specify bundle remove concorde-starter
```

Expected: directory, manifest, and built artifact resolve and install the same two catalog-provided
components, and each removal leaves user-authored sources untouched. The automated lifecycle suite
also repeats the artifact path from an uninitialized directory using Spec Kit's bundle initialization
path and isolated user-scope catalogs.

## 4. Preview the Exact Plan

```bash
specify bundle info concorde-starter --json > concorde-plan.json
```

Verify `concorde-plan.json` reports:

- bundle `concorde-starter` version `0.1.0`;
- Spec Kit compatibility `>=0.16.4,<0.16.5`;
- no fixed integration;
- extension `concorde` version `0.1.0`;
- preset `concorde-core` version `0.1.0`, priority `10`, strategy `append`;
- no workflows or steps; and
- source/trust information for the selected catalog.

This file is the accepted expanded plan used for the install comparison.

## 5. Install and Discover Commands

```bash
specify bundle install concorde-starter
specify bundle list --json > installed-bundles.json
specify extension list
specify preset list
find .agents/skills -maxdepth 2 -name SKILL.md -print | sort
```

Expected:

- the installed record names the same two components as `concorde-plan.json`;
- the preset and extension are active at the pinned versions; and
- Codex skills exist for `speckit-concorde-init`, `speckit-concorde-context`, and
  `speckit-concorde-validate`.

Repeat installation three times:

```bash
specify bundle install concorde-starter
specify bundle install concorde-starter
specify bundle install concorde-starter
```

Expected: every repetition succeeds, registry cardinality remains one bundle/one preset/one
extension, and no project-authored source changes after the first successful installation.

## 6. Initialize the Root Architecture

Start Codex in the clean project and invoke:

```text
$speckit-concorde-init
```

Expected first response: a reviewable proposal only. It names the root module ID, responsibility,
boundary, explicit provided and required contract sets, immediate submodules, one-level view, exact
target files, and any conflicts. No architecture file exists yet.

Approve the proposal explicitly in the agent conversation. The command then applies that exact
proposal and reports created project-relative paths. Verify:

```bash
find .concorde specs -type f -print | sort
```

Invoke the init skill again. Expected: `unchanged`; no maintained source is overwritten.

For the normative operation and result shapes, see
[Agent Commands](contracts/agent-commands.md) and
[Architecture Service Schema](contracts/architecture-service.schema.json).

## 7. Retrieve Bounded Context

Invoke the installed skill with the root module ID reported by initialization:

```text
$speckit-concorde-context module.<project-slug>
```

Expected JSON/result summary includes only:

- the root module's responsibility, boundary, features, and I/O contracts;
- immediate child summaries and their I/O contracts;
- permitted external actors;
- root-level scenarios and adjacent refinement links; and
- stable references for navigating deeper.

It must not expand child feature bodies or any grandchild module. Compare the result shape with
[context-response.json](contracts/examples/context-response.json).

## 8. Validate and Test Determinism

Invoke:

```text
$speckit-concorde-validate
```

Expected: status `success`, no error findings, and explicit `unknown` evidence where implementation
evidence has not been supplied.

Run the installed deterministic entry point three times and compare bytes:

```bash
.specify/extensions/concorde/scripts/bash/concorde.sh validate --format json > validation-1.json
.specify/extensions/concorde/scripts/bash/concorde.sh validate --format json > validation-2.json
.specify/extensions/concorde/scripts/bash/concorde.sh validate --format json > validation-3.json
cmp validation-1.json validation-2.json
cmp validation-2.json validation-3.json
```

Expected: both comparisons succeed and all runs return the same exit status.

Seed one broken reference in a copy of the fixture and rerun validation. Expected: non-zero status and
a finding containing rule ID, severity, project-relative source/location, message, and actionable
remediation, without any source modification. See
[validation-response.json](contracts/examples/validation-response.json).

## 9. Verify Preset Composition

Create a throwaway feature with the normal Spec Kit specify command, explicitly targeting the owning
module's nested `features/<number-name>/` workspace. Verify the resulting single `spec.md` contains
the feature's textual outcome and requirements plus Concorde stable-ID, providing-module, refinement,
representative-scenario, contract, architecture-view, and evidence prompts in addition to the normal
Spec Kit content.

Run the normal plan and task phases. Verify:

- the plan contains architecture ownership and boundary review gates; and
- tasks require affected maintained architecture sources, contracts, validation, tests, and generated
  freshness where applicable.

There must be no second Concorde feature specification and no separate top-level architecture source
tree.

## 10. Verify Slash-Command Portability

Repeat Sections 3 through 8 in a second clean project initialized with one supported slash-command
integration. Use the registered slash syntax shown by that integration.

Expected: all three commands are discoverable, exercise the same primary scenarios, invoke the same
runtime operations, and return results conforming to the same schema. Agent-specific filenames or
invocation separators may differ; intent and behavior may not.

## 11. Update and Failure Recovery

Publish a compatible fixture release in the local catalogs, then preview and update:

```bash
specify bundle info concorde-starter --json > concorde-update-plan.json
specify bundle update concorde-starter
specify bundle list --json
```

Expected: component versions match the accepted update plan, while `.concorde/`, `specs/`, and all
user configuration remain byte-identical.

Run the injected-failure fixture from the repository test suite:

```bash
cd /path/to/concorde
uv run python -m unittest tests.concorde.integration.test_bundle_lifecycle
```

Expected: a failed install/update is not recorded as successful, newly installed components are
rolled back where possible, and any remaining partial state is named.

## 12. Remove Safely

Return to the clean project and record source hashes before removal:

```bash
find .concorde specs -type f -print0 | sort -z | xargs -0 sha256sum > sources-before.txt
specify bundle remove concorde-starter
find .concorde specs -type f -print0 | sort -z | xargs -0 sha256sum > sources-after.txt
cmp sources-before.txt sources-after.txt
specify bundle list
```

Expected:

- the Concorde bundle record and solely owned preset/extension registrations are removed;
- a component shared with another installed bundle is retained;
- project-authored `.concorde/` and `specs/` sources are unchanged; and
- no unrelated agent artifacts are deleted.

## Acceptance Evidence

Record the commands, platform, Spec Kit version, agent integration, artifact hashes, test results, and
requirement mapping in `specs/concorde/features/001-concorde-starter-workflow/validation.md` during implementation.
Pilot completion time and unassisted completion rate for SC-001 and SC-009 require human participant
evidence; automated tests may support but must not replace those measurements.
