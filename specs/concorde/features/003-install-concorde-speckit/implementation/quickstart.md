# Quickstart Validation: Install Concorde through Spec Kit

**Feature**: `feature.concorde.install-with-spec-kit`
**Status**: Target-state acceptance guide for the current implementation attempt

This guide proves that a built Concorde release delivers the workflow into projects that cannot use
this checkout's locally modified skills or Spec Kit files. It does not test Feature 001 by invoking
repository-local `.agents/` or `.specify/` content.

## Prerequisites

- `uv` and the repository's pinned Python 3.11+ environment;
- Specify CLI / Spec Kit exactly `0.16.4`;
- this repository only for building the release and running the acceptance harness;
- Codex skills mode and one supported slash-command integration;
- two disposable target directories outside the Concorde checkout.

From the repository root:

```bash
uv --version
uv sync
uv run python --version
specify --version
```

Do not claim support for another Spec Kit version from manifest parsing alone. The nine normal
command replacements must be reviewed and rerun against every added host version.

## Mental Model

| Role | Installed responsibility | Boundary |
|---|---|---|
| Catalog | Advertises package identity, version, URL, compatibility, digest, and trust metadata. | Discovery metadata, not installed behavior. |
| Bundle `concorde-starter` | Pins one tested preset and one extension as an inspectable recipe. | Passive and non-executable. |
| Preset `concorde-core` | Appends three inherited lifecycle template layers, supplies the permanent design template, and replaces nine existing lifecycle command instructions with Concorde-aware routing. | No new runtime namespace; Spec Kit still owns normal phase meaning. |
| Extension `concorde` | Supplies six Concorde commands, the selected-workspace adapter, launchers, and deterministic runtime. | Does not own the nine normal lifecycle commands or agent syntax. |
| Active coding-agent integration | Materializes resolved normal-command winners and extension commands in agent-native form. | Presentation only; it cannot change intent or paths. |
| Architecture Core | Implements initialization, bounded context, and validation after installation. | Core-workflow behavior owned by Feature 001. |

The preset's template and command contributions use different composition strategies:

- spec, plan, and tasks templates use `append` because they add guidance, while the Concorde-owned
  permanent design template uses `replace`;
- `specify`, `clarify`, `checklist`, `plan`, `tasks`, `implement`, `analyze`, `converge`, and
  `taskstoissues` use complete `replace` layers because selected-workspace routing must occur before
  any lower instruction can choose legacy paths.

The bundle does not include this repository's `.agents/` or `.specify/` trees. Those are self-hosting
development state, not proof of what users receive.

Review the maintained [component model](../diagrams/spec-kit-component-model.json) and
[installation flow](../diagrams/starter-installation-flow.json). Their generated projections are the
[interactive component model](../../../../../generated/architecture/concorde-spec-kit-component-model.html)
and [interactive installation flow](../../../../../generated/architecture/concorde-starter-installation-flow.html).
The complete textual boundary is in
[Installed Concorde Command Surfaces](../contracts/installed-command-surfaces.md).

## 1. Build Reproducible Release Units

```bash
uv run python scripts/release/build-components.py --output dist \
  --base-url http://127.0.0.1:8765
specify bundle build --path bundles/concorde-starter --output dist
uv run python scripts/release/verify-release.py --dist dist
```

`--base-url` is written into the generated catalogs as the location from which installation will
later download artifacts. The builder does not contact that address. The server starts in the next
section.

Expected:

- separate bundle, preset, and extension archives exist;
- archive manifests, catalogs, versions, URLs, compatibility, and SHA-256 digests agree;
- the bundle pins exactly `concorde-core@0.1.0` and `concorde@0.1.0`;
- the preset contains three append template layers, one permanent design-template replacement, and
  nine complete replacement commands;
- the extension contains six command definitions plus every referenced adapter, launcher, schema,
  and runtime file;
- no `.agents/`, root `.specify/`, test, temporal design, or generated documentation file is in an
  archive; and
- two clean builds are byte-equivalent.

Run focused source/release contracts before installation:

```bash
uv run python -m unittest \
  tests.concorde.contract.test_manifests \
  tests.concorde.contract.test_release_artifacts \
  tests.concorde.contract.test_installed_command_surfaces
```

The last module is a planned acceptance contract. Until it exists and passes, the implementation
attempt remains partial.

## 2. Serve the Built Catalogs

In another terminal from the repository root:

```bash
uv run python tests/concorde/support/catalog_server.py --dist dist --port 8765
```

Only built `dist/` content is served. Localhost HTTP is allowed for this fixture; published release
locations use HTTPS.

## 3. Create Checkout-Isolated Targets

Create the targets from a shell whose import and executable search paths do not expose the Concorde
checkout:

```bash
concorde_skills_target="$(mktemp -d)"
concorde_slash_target="$(mktemp -d)"

cd "$concorde_skills_target"
env -u PYTHONPATH specify init --here --integration codex --integration-options="--skills"
```

Initialize the second target with the supported slash-command integration selected for portability
acceptance. Neither target may be nested under the checkout or use a development-directory install.

For each target, add the three localhost catalogs as project-scoped, install-allowed sources:

```bash
specify extension catalog add http://127.0.0.1:8765/extensions.json \
  --name concorde-dev --install-allowed
specify preset catalog add http://127.0.0.1:8765/presets.json \
  --name concorde-dev --install-allowed
specify bundle catalog add http://127.0.0.1:8765/bundles.json \
  --id concorde-dev --policy install-allowed
```

The acceptance harness must record all file reads made while resolving and executing installed
surfaces. Any path inside the Concorde checkout invalidates SC-010.

## 4. Inspect and Accept the Exact Plan

```bash
specify bundle info concorde-starter --json > concorde-plan.json
```

Review the plan before installing. It must identify:

- bundle `concorde-starter@0.1.0`;
- preset `concorde-core@0.1.0`, priority `10`, three inherited template append layers, one permanent
  design-template replacement, and nine command replacement layers;
- extension `concorde@0.1.0` and its six command intents;
- host requirement `>=0.16.4,<0.16.5`;
- inherited active integration, package provenance, catalog trust, and planned files/state changes;
- no workflow component, reusable steps, second feature store, or separate installer.

Retain the plan digest. Installed component identities and versions must match it exactly.

Before the catalog-ID journey, the automated lifecycle suite must also prove that an approved source
directory, `bundle.yml`, and built bundle archive resolve the same component plan. A development
directory may assist package authors but cannot satisfy clean-product acceptance.

## 5. Install and Inventory the Actual Winners

```bash
specify bundle install concorde-starter
specify bundle list --json > installed-bundles.json
specify preset list
specify extension list
```

Expected:

- one active bundle, one preset, and one extension match the accepted plan;
- the active integration has fifteen Concorde-owned surfaces: nine normal and six
  Concorde-specific;
- every surface records its winning source component and materialized artifact;
- every Concorde-owned surface identifies the Feature 001 handoff version and digest packaged by the
  extension;
- repository-local command files are absent from the provenance chain.

Run the installed-surface inventory harness from the checkout against the isolated target. The
harness may inspect the target and built archives; the target's installed commands may not import or
read the checkout:

```bash
uv run python -m unittest tests.concorde.contract.test_installed_command_surfaces
```

Expected: the harness resolves the registered winner rather than accepting matching text in any
package or inactive file.

## 6. Exercise the Durable and Temporal Path Matrix

In the clean target, use the installed Concorde commands to initialize the root architecture, create
a nested feature under its providing module, and select that feature. Initialization and feature
creation remain review-first: inspect the proposal and explicitly approve the exact mutation.

The selected feature must have this durable/temporal shape:

```text
specs/<root>/modules/<module>/features/<number>-<slug>/
├── spec.md
├── design.md
├── contracts/
├── diagrams/
└── implementation/
    ├── checklists/
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── tasks.md
    └── validation.md
```

Execute every normal installed surface through the target integration:

| Commands | Required location |
|---|---|
| Specify and clarify | Selected feature root for `spec.md`/contracts; generated review state under `implementation/checklists/` |
| Checklist | Selected feature's `implementation/checklists/` directory |
| Plan, tasks, implement, analyze, converge, taskstoissues | Selected feature's single `implementation/` workspace |

After each command, verify that workspace resolution occurred before any path-sensitive setup or
prerequisite action. No root `checklists/`, root `plan.md`, root `tasks.md`, root design copy,
compatibility symlink, or second active implementation attempt may exist.

Run the deterministic full matrix three times:

```bash
uv run python -m unittest tests.concorde.integration.test_clean_phase_matrix
```

Expected: every run produces the same selected paths and observable results, with no root aliases and
no checkout reads.

## 7. Exercise All Six Concorde Commands

Through the installed presentation, exercise:

1. initialization proposal, approval, apply, and idempotent rerun;
2. nested feature-create proposal, approval, creation, and collision refusal;
3. feature selection and project-scoped selection-state update;
4. root, child, and active-feature bounded context;
5. deterministic validation success plus seeded failure output.

Repeat equivalent scenarios in the slash-command target. Agent-specific filenames, separators, or
front matter may differ. Canonical intent, arguments, selected paths, result envelopes, failures, and
source immutability must match.

The extension test fails if a launcher, adapter, schema, or runtime file is removed from a copied
release archive. It must not fall back to this checkout.

## 8. Prove Idempotency and User-Source Preservation

Record project-source hashes, install the same bundle three more times, and compare:

```bash
find .concorde specs docs -type f -print0 2>/dev/null \
  | sort -z | xargs -0 sha256sum > concorde-sources-before.txt

specify bundle install concorde-starter
specify bundle install concorde-starter
specify bundle install concorde-starter

find .concorde specs docs -type f -print0 2>/dev/null \
  | sort -z | xargs -0 sha256sum > concorde-sources-after.txt
cmp concorde-sources-before.txt concorde-sources-after.txt
```

Expected: registry cardinality remains one bundle, one preset, and one extension; command winners are
unchanged; project-authored source hashes are identical.

## 9. Prove Recomposition

Install a known lower-priority fixture that contributes all nine normal command surfaces. Then test
each transition:

1. Concorde enabled: its nine replacement layers win.
2. Concorde disabled: its already registered command artifacts remain active, as Spec Kit 0.16.4
   documents; future template resolution excludes the preset.
3. Priority changed: registered artifacts remain active while future resolution uses the new priority.
4. Compatible Concorde update: the accepted new layer wins with its new digest.
5. Concorde removed: the lower layer is restored with no stale Concorde instructions.

Run:

```bash
uv run python -m unittest tests.concorde.integration.test_command_recomposition
```

Checking preset registry state is insufficient. The test must resolve, execute, and compare all nine
materialized winners after every transition.

## 10. Exercise Failure and Recovery Paths

Seed unsupported host, untrusted source, missing component, digest mismatch, command collision,
missing preset override, missing extension runtime member, materialization failure, and partial update
fixtures.

Expected for every case:

- non-zero status and actionable diagnostics;
- no false successful installation/update record;
- no fallback to checkout files or managed core-script patching;
- previous successful state retained or restored when possible;
- any unrecoverable residual state named explicitly;
- unchanged project-authored sources.

If Spec Kit's public `replace` composition cannot establish selected-workspace routing before the
legacy helper path on 0.16.4, stop this implementation. Record the missing upstream capability and
required host version; do not add an undocumented installer patch.

## 11. Update and Remove Safely

Preview and accept a compatible fixture release, apply it, and compare the resulting component state
with the accepted update plan. Then remove the bundle:

```bash
specify bundle info concorde-starter --json > concorde-update-plan.json
specify bundle update concorde-starter
specify bundle remove concorde-starter
```

Expected:

- only approved component versions change;
- shared components remain installed;
- solely bundle-owned components and records are removed;
- lower command layers are rematerialized;
- `.concorde/`, `specs/`, `docs/`, and unrelated agent artifacts remain unchanged.

## 12. Validate Diagrams and Publication

Validate both declared Feature 003 sources and their generated outputs:

- `diagrams/spec-kit-component-model.json` answers package ownership and static composition;
- `diagrams/starter-installation-flow.json` answers release, install, materialization, use, update,
  and removal order.

Require all Archify showcase checks, source/generator provenance, fresh generated HTML, four desktop
containment sizes, light/dark perceptual evidence when a browser is available, and automatic
embedding on the Feature 003 documentation page.

Then run:

```bash
cd docsite
npm run check
```

The component model is the core architecture view and the installation flow is supplemental. The
prose in the spec and contracts must remain understandable without them, and neither diagram may
redefine the bounded root module architecture.

## 13. Human Outcomes

### SC-001 first-use pilot

Recruit first-time maintainers who did not implement the feature. Give each participant only this
quickstart and a supported clean target. Record start/end time, platform, assistance, completion, and
failure point. At least 90% must inspect the plan and complete setup within 15 minutes.

### SC-007 role-comprehension pilot

Allow at most five minutes to review the mental model and diagrams. Without coaching, ask the
participant to explain:

1. catalog discovery/trust;
2. the bundle's passive pins;
3. the preset's template layers and normal-command replacements;
4. the extension's six active commands/runtime;
5. active-integration presentation;
6. Architecture Core behavior;
7. why Spec Kit still owns the normal lifecycle.

A participant passes only by distinguishing all seven roles/boundaries correctly. At least 90% must
pass. Automated diagram or documentation checks do not substitute for participant evidence.

## Acceptance Record

Record platform and Spec Kit versions, accepted plan digest, package and catalog digests, Feature 001
handoff digest, fifteen installed-surface receipts, phase matrix, source-access audit, recomposition,
failure and lifecycle results, diagram/docsite evidence, and human pilot data in
`implementation/validation.md`.

Historical validation that proved bundle lifecycle or command text presence remains useful baseline
evidence, but it must not be remapped to FR-006–008, FR-018–021, FR-029, SC-004, or SC-009–011 until
the clean installed execution and recomposition evidence above exists.
