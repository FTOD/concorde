# Feature Implementation: One-Command Installation

**Realization status**: Accepted implementation.

**Selected level**: Immediate sub-feature of `feature.concorde.install-with-spec-kit`; the parent and sibling durable sources remain read-only aggregate authorities.

## Realization Overview

Concorde provides one inspectable installer at `scripts/install-concorde.py`. A maintainer runs it inside the pinned `specify-cli==0.16.4` uv tool environment, so a fresh consumer needs `uvx`, a shell, and network access rather than a preinstalled Python environment, Spec Kit CLI, Concorde checkout, release build, or catalog server. The installer validates the selected release, initializes only an empty non-project target, prints Spec Kit's expanded bundle information, and delegates component installation or update to Spec Kit's public bundle lifecycle.

Published mode resolves the current `release.json` pointer by default or an immutable version-specific pointer for `--version`. Preview resolves the same native component plan in a disposable project and never creates or changes the target. Development mode accepts `--checkout`, builds and reproducibly verifies that checkout before target mutation, serves its generated catalogs on an ephemeral loopback port for the run, and performs the same native catalog and bundle sequence.

The command reports the selected action, bundle/preset/extension versions, active integration, reload requirement, next workflow command, or a staged failure with remediation and known residual state. It never copies or edits installed component files itself.

## Module and Feature Collaboration

The parent `feature.concorde.install-with-spec-kit` remains authoritative for the installed component set, inspect-before-install, Spec Kit lifecycle ownership, provenance, command materialization, and clean-project verification. This child owns only the convenience orchestration surface. The sibling `feature.concorde.install-with-spec-kit.publish-release` supplies the current and immutable `release.json` locations consumed by published mode.

Distribution realizes release and lifecycle work through `contract.distribution.component-packages` and `contract.distribution.bundle-lifecycle`: its maintained builder and verifier produce the preset, extension, bundle, and matching catalogs, while Spec Kit records bundle ownership and performs install/update. Skills supplies the packaged command surfaces through `contract.skills.agent-surface`; the installer selects the target integration but does not change command meaning or Scripts behavior.

The root `contract.concorde.spec-kit-installation` and required `contract.concorde.spec-kit-platform` continue to govern preview/apply parity, compatibility, trust, provenance, idempotence, preservation, and failures. The child-specific `contracts/installer-cli.md` profiles the public invocation, report, catalog identities, exit status, and cleanup obligations without redefining those module boundaries. No root module design or architecture amendment is required.

## Scenario Realization

### Install a published release into a fresh project

The public command streams the maintained installer into `uvx --from specify-cli==0.16.4 python -`. The installer verifies the active `specify` version, fetches and validates schema-1 release metadata, requires an integration for a fresh target, and invokes `specify init --here` with that integration. Codex defaults to skills mode.

It registers the release's extension, preset, and bundle catalogs under the managed project identity `concorde`, obtains native `bundle info --json`, and installs `concorde-bundle`. Final verification reads the native installed-bundle record and refuses success if its version differs from the accepted plan. The success report names the bundle, both contributed components, integration, reload need, and `speckit-concorde-init` as the next step.

### Preserve and update an existing project

For an existing Spec Kit project, the installer reads the recorded default integration and rejects a conflicting explicit integration before writes. It reads catalog configuration only to classify each managed source as missing, current, or replace; every catalog mutation still uses the corresponding public Spec Kit add/remove command. Unrelated catalog entries and project-authored sources are not rewritten.

The native installed-bundle record selects one of three actions: absent installs, a different version updates through `specify bundle update`, and an equal version is `already-current` with no lifecycle write. Three consecutive current-version runs preserve the complete target byte map.

### Preview without target mutation

Preview classifies and inspects the target read-only, then creates a temporary Spec Kit project with the requested or recorded integration. It registers the selected catalogs there and asks Spec Kit for the expanded bundle plan. After the temporary project is removed, it prints the release, compatibility range, catalog reconciliation states, native component plan, and planned install/update/no-op action. Empty targets remain empty, absent targets remain absent, and initialized projects retain identical file hashes.

### Install current checkout sources

Development mode validates the checkout's release scripts and three component manifests, binds a loopback server to an ephemeral port, and passes that exact base URL to the maintained release builder and verifier. Only after verification passes does the server start and target orchestration begin.

The run uses the distinct managed identity `concorde-dev`. After native install/update and final bundle verification, it removes all three transient catalog registrations through public Spec Kit commands before reporting success and stopping the server. Permanent `concorde` catalogs remain untouched. This lifetime split prevents dead loopback URLs and makes a same-version local rerun byte-identical.

### Fail without false success

Request failures exit 2, release discovery/build/verification failures exit 3, and Spec Kit lifecycle failures exit 4. Each handled failure names its stage, remediation, and residual state while preserving native diagnostics. Release verification occurs before target mutation. Temporary projects, release directories, and servers are context-managed, and development success is emitted only after mandatory transient catalog cleanup completes.

## Durable Implementation Decisions

- The convenience surface is one readable Python script, not a new package, workflow component, or component-file installer.
- The script runs inside the exact supported Spec Kit tool environment and delegates all lifecycle writes to public `specify` commands.
- Release pointers must use schema major 1, agree on version and `v<version>` tag, name `concorde-bundle`, declare `>=0.16.4,<0.16.5`, and provide all three HTTPS catalog URLs; development permits loopback HTTP only.
- Published discovery uses persistent `concorde` catalog identities for later update. Ephemeral development discovery uses transient `concorde-dev` identities removed before success.
- Target state and the native installed-bundle record, rather than command replay, select install, update, or byte-identical no-op.
- Preview uses a disposable initialized project so Spec Kit remains the authority for component expansion while the target remains unchanged.
- Checkout mode reuses the maintained release builder and verifier and owns one in-process loopback server whose lifetime encloses native resolution.
- Terminal success is part of the operation transaction: it follows native final verification and every mandatory development cleanup.
- The parent core component diagram and supplemental installation flow already explain the stable components and sequence, so no child diagram duplicates them.

## Traceability and Evidence

Behavioral authority remains `design.md` together with `contracts/installer-cli.md`; accepted realization authority is this document. The implementation is `scripts/install-concorde.py`. Public usage and the retained manual native fallback are documented in `README.md` and `docs/quick-start.md`.

`tests/concorde/unit/test_install_concorde.py` covers request conflicts, release validation, target and catalog classification, action selection, installed-record shape, staged failures, and success ordering. `tests/concorde/acceptance/test_one_command_install.py` builds isolated releases and proves manual/native parity, three-run byte idempotence, integration-conflict non-mutation, native update with authored-source preservation, preview non-mutation and apply parity, checkout build/verify/install, server cleanup, transient-catalog cleanup, and seeded verification failure. `tests/concorde/contract/test_ecosystem_explanation.py` keeps source, CLI contract, README, quick start, and parent ecosystem explanation aligned.

The accepted evidence includes 23 focused installer/contract/acceptance tests, the complete 253-test Concorde suite, deterministic Concorde validation with zero findings across 50 artifacts, and the docsite gate with 77 tests, 100-page source validation, and a production build. A live immutable `v0.1.0` preview resolved the published bundle and both contributed components while leaving an absent target absent.

## Known Limitations

- The first public presentation targets POSIX-style shells and requires `uvx`; a Windows-native presentation remains future scope.
- The newest published product release observed by this attempt is `v0.1.0`, which predates the checkout's current `0.4.0` document model. Published mode installs that release; `--checkout` is the verified one-command path for current sources until a newer release is published.
- The installer source is currently served from the maintained repository's `main` branch rather than a versioned release asset. The documented download-and-inspect path supports source review; a future release may add an immutable installer asset without changing this CLI contract.
- **R-021** records that an immediate plain TCP rebind can observe normal `TIME_WAIT` state after the development server closes. Acceptance uses reusable-address rebinding to prove no listener remains.
- **R-022** records the corrected transient-catalog lifetime bug. Development now uses and removes `concorde-dev`; permanent `concorde` sources remain intact and reruns are byte-stable.
- **R-023** records the corrected README/contract terminology drift. A contract test now requires the shared `manual native` fallback label without imposing letter case.
- **R-024** records a zsh validation-wrapper portability mistake. The evidence rerun used a task-specific variable name; the installer itself does not rely on that wrapper.
- **R-025** records the corrected success-ordering issue. Development success is deferred until transient catalog cleanup succeeds, and a seeded cleanup failure cannot emit success.

The project reflection log remains maintainer-owned and byte-identical; all five entries remain open for later maintainer disposition even though their implementation effects were mitigated in this milestone.
