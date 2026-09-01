# Feature Implementation: One-Command Installation

**Realization status**: Accepted realization of the public bundle-plus-projector installer for Concorde 0.6.0.

**Selected level**: Immediate sub-feature of `feature.concorde.install-with-spec-kit`; parent and sibling durable sources remain aggregate read-only authorities.

## Realization Overview

Concorde provides one inspectable installer at `scripts/install-concorde.py`. A maintainer runs it inside the pinned `specify-cli==0.16.4` uv tool environment, so a fresh consumer needs `uvx`, a POSIX-style shell, and network access rather than a preinstalled Python environment, Spec Kit CLI, Concorde checkout, release build, or catalog server.

The installer resolves the current `release.json` pointer by default, an immutable version-specific pointer for `--version`, or a reproducibly built and verified local checkout for `--checkout`. It initializes only an empty non-project target, reconciles three managed catalogs, prints Spec Kit's native expanded bundle information, and delegates component install, update, or current-version no-op exclusively to public Spec Kit operations.

Component state is necessary but not sufficient for success. After bundle install, update, or no-op, the installer invokes only the agent projector shipped by the installed Concorde extension. It previews exact native Claude or Codex target actions, refuses ownership conflicts, synchronizes allowed outputs, verifies every output and receipt digest, and reports terminal success only afterwards. A successful target contains the normal Concorde commands plus one native reflection-triage skill, one investigator role, one implementer role, shared default configuration when absent, and `.specify/concorde-agent-assets.json` ownership evidence.

Preview resolves the same native component plan in a disposable project and calls that candidate's installed projector against the real target without mutation. Development mode builds and verifies the chosen checkout before target mutation, serves generated catalogs on an ephemeral loopback port for the run, follows the same bundle-plus-projector sequence, removes all transient `concorde-dev` registrations, and stops the server before success.

## Module and Feature Collaboration

The parent `feature.concorde.install-with-spec-kit` owns the installed component set, inspect-before-install rule, Spec Kit lifecycle authority, package provenance, command materialization, clean-project verification, and the bundle-then-projector invariant. This child owns only the one-command accelerator and its request, preview, orchestration, reporting, and cleanup behavior. The sibling `feature.concorde.install-with-spec-kit.publish-release` owns current and immutable release locations consumed by published mode.

Distribution supplies deterministic preset, extension, and bundle artifacts through `contract.distribution.component-packages` and `contract.distribution.bundle-lifecycle`. Skills packages the command surfaces and Feature 005's canonical triage bodies and platform wrappers through `contract.skills.agent-surface`. Scripts supplies the installed `agent-assets` operation and digest-safe projector. Workspace Files distinguishes the generated projection receipt from maintainer-owned configuration, plans, worktrees, logs, and durable specifications.

The root `contract.concorde.spec-kit-installation` and required `contract.concorde.spec-kit-platform` govern preview/apply parity, compatibility, trust, provenance, idempotence, preservation, and failure behavior. The child `contracts/installer-cli.md` profiles the public invocation, report, managed catalog identities, projection transaction, exit statuses, and cleanup obligations. No module responsibility, dependency direction, contract format, or architecture source changes.

The parent core component model remains sufficient for stable participants, and its supplemental installation flow explains bundle then projection order. This child adds no duplicate diagram.

## Scenario Realization

### Install a published release into a fresh project

The public command streams the maintained installer into `uvx --from specify-cli==0.16.4 python -`. The installer validates schema-1 release metadata, compatibility, bundle identity, tag/version agreement, and all three HTTPS catalog URLs. A fresh target requires an integration; Codex defaults to skills mode.

The installer initializes the target through `specify init --here`, registers the extension, preset, and bundle catalogs under `concorde`, obtains native `bundle info --json`, and installs `concorde-bundle`. It verifies the installed bundle record, then runs installed-projector preview, sync, and verify. The final report names bundle/preset/extension versions, integration, projection status and output count, receipt path, reload need, and `speckit-concorde-init` as the next step.

Checkout-isolated acceptance proves that the resulting component, command, projection, receipt, and shared-default state matches the documented manual bundle-plus-projector path. Fresh Codex and Claude runs each produce exactly three parsed native outputs.

### Preserve and update an existing project

For an existing Spec Kit project, the installer reuses the recorded integration and rejects a conflicting explicit integration before writes. It classifies each managed catalog as missing, current, or replace while preserving unrelated registrations and authored sources.

The native installed-bundle record selects install, update, or `already-current`. After the first successful run, three current-version repeats preserve the complete target byte map. An older installation updates through `specify bundle update` while retaining authored source, customized shared configuration, existing reflection plans, unrelated skills, and inactive integration state.

Projection ownership is digest-scoped. Byte-identical manual targets may be adopted; matching owned outputs may be updated or removed; modified, unowned, unrelated, inactive, configuration, plan, worktree, log, permission, and authored paths are preserved. A conflict names remediation and suppresses terminal success.

### Preview without target mutation

Preview classifies the target read-only, builds the component plan in a disposable initialized project, installs the candidate bundle only there, and invokes that disposable project's installed projector in preview mode against the real target. It prints release and compatibility data, catalog reconciliation, native bundle expansion, component action, and exact projection paths, digests, actions, conflicts, and findings.

Empty targets remain empty, absent targets remain absent, and existing projects retain identical hashes. The planned component result matches a later apply for the same inputs.

### Install current checkout sources

Development mode validates the checkout's release scripts and component manifests, binds an ephemeral loopback server, and passes that exact base URL to the maintained release builder and verifier. Only verified artifacts proceed to target orchestration.

The run uses transient `concorde-dev` catalog identities, installs through the same native bundle path, and projects from the installed extension copy rather than checkout-local agents. Before reporting success it removes all transient catalogs through public Spec Kit commands and stops the server. Repeating the same checkout install is byte-identical. A seeded verification failure leaves the target unchanged.

### Fail without false success

Request failures exit 2, release discovery/build/verification failures exit 3, and Spec Kit component or projection failures exit 4. Each handled failure names its stage, remediation, and known residual state while preserving native diagnostics. Target validation and checkout verification occur before mutation; projection conflict preserves target bytes; development cleanup completes before terminal success.

## Durable Implementation Decisions

- **One readable accelerator**: the surface remains one inspectable Python script, not another package or lifecycle authority.
- **Spec Kit owns components**: project initialization, catalogs, bundle inspection, install, and update use public `specify` commands only.
- **Installed extension owns projection**: installer-local or checkout-local rendering is rejected because it could diverge from accepted package bytes.
- **Projection is terminal installation work**: success follows installed-projector preview, sync, verify, and required development cleanup.
- **Preview exercises candidate bytes**: a disposable project installs the candidate bundle so preview never guesses from checkout sources and never mutates the target.
- **Digest-scoped ownership**: receipts authorize only matching generated paths; filenames alone never authorize overwrite or deletion.
- **Shared maintainer state**: Claude and Codex projections use one `.concorde/reflections/` state model while integration receipts remain independent.
- **Separate persistent and transient catalogs**: published mode uses `concorde`; development uses and removes `concorde-dev`.
- **Native bundle state selects action**: absent installs, different versions update, and equal versions are byte-identical no-ops.
- **No child diagram**: the parent component model and installation workflow already answer the stable-structure and sequence questions.

## Traceability and Evidence

Behavioral authority remains `design.md` and `contracts/installer-cli.md`. The implementation is centered in `scripts/install-concorde.py`, with installed projection behavior supplied by `extensions/concorde/runtime/concorde/agent_assets.py` and canonical assets under `extensions/concorde/agent-assets/reflections/`. Public usage and the manual native fallback remain in `README.md` and `docs/quick-start.md`.

Executable evidence includes:

- 11 installer unit tests for requests, release validation, target/catalog/action decisions, installed-projector envelopes, staged failures, and cleanup ordering;
- 5 ecosystem explanation contract tests;
- 11 One-command Install acceptance tests covering manual parity, fresh Claude/Codex projection, three-repeat idempotence, integration conflicts, native update and preservation, modified-target conflict refusal, receipt-scoped removal, preview non-mutation/parity, checkout install/repeat/cleanup, and verification failure;
- 16 installed-surface, manifest, triage-distribution, and release-artifact contract tests;
- the full Concorde suite: 308 tests passed;
- deterministic Concorde validation: zero findings, source digest `sha256:3873dfd81ce0f2a11d743046cfb6d7ffdda88c2a9ae6079579308d14fc255239`;
- the full docsite gate: TypeScript, 19 test files / 83 tests, 108-page validation with zero errors, and successful optimized production promotion.

Planning and implementation preserved exact hashes for the child accepted baseline and contract, parent and sibling durable trios, root module summary/design, project reflection log, and both parent diagrams. The project reflection log contains no entry attributed to this feature.

## Known Limitations

- The public presentation currently targets POSIX-style shells and requires `uvx`; a Windows-native presentation remains future scope.
- Compatibility is intentionally pinned to Spec Kit `>=0.16.4,<0.16.5`.
- The default published path depends on the repository's current-release pointer and published assets. This acceptance proves isolated 0.6.0 release artifacts and the checkout path; it does not claim live public hosting availability or a first-time remote timing result.
- The installer source is served from the maintained repository's `main` branch rather than an immutable release asset. The documented inspect-before-run path supports source review; a future release may add a versioned installer asset without changing the CLI contract.

### Installer transaction detail

`execute_install` resolves native bundle state, reconciles catalogs, performs install/update/no-op, verifies the installed bundle version, invokes `agent-assets preview`, `sync`, and `verify` through the installed launcher, and only then constructs the successful `InstallResult`. Stage-specific errors retain component and projection facts and suppress success.

### Projection preservation detail

The projector validates safe paths, canonical sources, platform wrappers, receipt structure, and current digests. Synchronization creates, adopts, updates, removes, preserves, or conflicts per target; verify compares desired, materialized, and receipt state. Shared configuration and triage plans are never receipt-owned.

### Development cleanup detail

Checkout mode reuses the maintained release builder and verifier. Its temporary directory, catalog server, and `concorde-dev` registrations are bounded to the run. Cleanup failures use the same exit-4 lifecycle classification and occur before success output.
