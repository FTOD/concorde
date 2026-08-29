# Feature Implementation: Self-Host the Concorde Framework

**Realization status**: Accepted self-hosting realization proposed for acceptance on 2026-08-26.

## Realization Overview

Concorde self-hosts through the repository bootstrap `scripts/development/self-host-concorde.py`. The bootstrap is deliberately outside the installed extension so a checkout with no active Concorde installation can still inspect and install the framework. It uses only Python 3.11 standard-library facilities and delegates component mutation to Spec Kit 0.16.4's public development-mode preset and extension lifecycle.

The maintained `presets/concorde-core/`, `extensions/concorde/`, and `bundles/concorde-bundle/` trees form the authoritative framework source set. Installed copies under `.specify/`, composed templates, registries, and agent skills are replaceable materializations. They never flow back into maintained sources. The bootstrap exposes three JSON-producing operations:

- `propose` validates the source boundary and active integration, computes a deterministic source digest, inspects current ownership, and writes only the ignored `.specify/self-hosting-proposal.json`;
- `apply` accepts only that canonical proposal, rejects stale or changed review state, preflights the same local components in an isolated Spec Kit project, snapshots the exact owned scope, materializes through Spec Kit, verifies the result, and atomically writes the ignored `.specify/self-hosting.json` receipt; and
- `status` performs no writes and independently classifies source, installed-copy, registry, surface, and activation evidence. `status --require-current` provides a non-mutating quality gate whose exit status does not depend on feature selection.

The durable JSON interface is defined by `contracts/self-hosting.md`, `contracts/self-hosting.schema.json`, and its maintained examples. The feature's stable component collaboration is shown by `diagrams/concorde-self-hosting-components.json`; generated HTML remains delivery evidence rather than design authority.

## Module and Feature Collaboration

`module.concorde` owns this cross-component feature. Its bounded organization, participants, and external contracts remain authoritative in `specs/concorde/module.md` and `specs/concorde/architecture/diagrams/level-view.json`; this design records only how those maintained boundaries are used.

Distribution contributes `feature.distribution.package-concorde-bundle`, whose `concorde-bundle` recipe pins the local `concorde-core` preset and `concorde` extension to the same accepted version. The recipe constrains development self-hosting composition but is not executed as a self-hosting runtime and does not replace Feature 003's release lifecycle.

Skills contributes `feature.skills.compose-workflow`. The bootstrap invokes Spec Kit's public local preset and extension installation so the host owns registration, template composition, command layering, and Codex skill materialization. The accepted composition exposes nine preset-owned normal lifecycle skills, five extension-owned Concorde skills, and three top-level composed template surfaces; the installed component copies also retain the extension runtime, launchers, and complete preset template sources.

The maintainer crosses `contract.concorde.spec-kit-installation` to preview and approve the local composition. The implementation depends on `contract.concorde.spec-kit-platform` for version compatibility, public component lifecycle behavior, registry semantics, and active-integration materialization. The custom self-hosting JSON contract adds the cross-component proposal, receipt, status, ownership, failure, and activation information that Spec Kit's individual component operations do not provide as one reviewed transaction.

The coding agent consumes the materialized skills only after the integration's activation boundary. Project specifications, designs, contracts, diagrams, documentation, code, tests, configuration, generated evidence, and unrelated agent assets remain outside the mutation scope unless an exact path is separately present in the approved proposal.

## Scenario Realization

### Install the current framework

The maintainer runs `propose` before any Concorde command is required. Source inspection accepts only the fixed Concorde component identities, aligned versions, the supported Spec Kit metadata, regular project-contained files, and the Codex integration validated by protocol v1. Symlinks, escaping paths, incompatible versions, malformed manifests, and conflicting extension command ownership produce actionable findings before real mutation.

After explicit approval, `apply` recomputes the entire proposal and rejects any change in target, canonical proposal path, integration, source digest, or owned-change set. It then initializes an isolated same-integration Spec Kit project, installs both local components there, and verifies copied bytes, normalized registries, and declared surfaces. Only after that preflight passes does the bootstrap snapshot the real checkout's declared component directories, registry files, composed templates, Concorde-owned skill directories, and prior receipt. Successful public lifecycle installation is verified before the receipt is committed. The result reports `reload_required`; it never claims the executing agent already loaded the new instructions.

### Refresh after a framework improvement

Development-mode installation is treated as copied materialization, not a live link. Changing any authoritative preset, extension, or bundle input changes the source digest and requires another propose-review-apply cycle. A stale proposal cannot authorize refresh. Preset replacement and forced extension refresh still run through Spec Kit, preserving one registration for each component and the declared command inventories. If the receipt and all deterministic dimensions already match, apply returns `unchanged` without component mutation or duplicate ownership.

### Verify self-hosting freshness

`status` compares the current source digest with the receipt, installed preset and extension bytes with maintained sources, normalized registry identities/version/local provenance/priority/command ownership with the expected composition, and nineteen materialized files with receipt hashes. It also detects missing and unexpected `speckit-concorde-*` skill surfaces. Overall `current` requires all four deterministic dimensions to match. Activation is always reported separately as `reload_required` unless external new-session evidence is available; disk equality alone is never upgraded into an agent-session claim.

### Preserve work and recover safely

The approved change set is a sorted list of project-relative paths classified as `create`, `update`, or `adopt`. Source and target traversal rejects symlinks and parent or absolute paths. Before real mutation, the bootstrap snapshots only this owned set. A failure after mutation restores it in reverse order and suppresses a success receipt. Complete restoration returns `rolled_back`; incomplete restoration returns `failed` with every residual path and remediation. Locally edited materializations are observable drift and are never promoted back into framework sources.

## Durable Implementation Decisions

1. **Use public Spec Kit development primitives.** Local preset and extension installation preserves host compatibility, ownership, registry, command-composition, and active-integration behavior. Direct copying, custom symlinks, and a parallel command registry are rejected.
2. **Keep first-install bootstrap outside the extension.** A repository development script avoids a circular dependency on a command that exists only after successful setup. It is not distributed as another user-project Concorde command.
3. **Make review digest-bound and exact.** Canonical JSON, sorted inventories, SHA-256 digests, safe relative paths, and a single canonical proposal file make source and ownership changes invalidate prior approval.
4. **Preflight before checkout mutation.** A temporary same-integration project exercises actual public installation and complete surface verification before the real project is touched.
5. **Recover only the owned scope.** The bootstrap snapshots component copies, relevant registry files, composed template files, declared skill directories, and the receipt rather than treating the repository as installer-owned. Recovery reports residual disagreement instead of recording partial success.
6. **Keep machine state non-authoritative.** The proposal and receipt are ignored local evidence. Maintained manifests and files remain the only framework source authority.
7. **Separate five evidence dimensions.** Source, installed copy, registry, surface, and agent-session activation answer different questions and are never collapsed into an unqualified installed flag.
8. **Retain a programmer-readable protocol.** Proposal, result, and status payloads conform to the closed JSON Schema v1 contract and use structured findings with authority, stage, affected path, expected/observed state where relevant, and safe remediation.
9. **Bind compatibility to proved behavior.** Protocol v1 accepts Spec Kit `>=0.16.4,<0.16.5` and Codex skills mode. Broader versions or integrations require equivalent isolated installation, surface, rollback, and activation evidence before support is declared.

## Traceability and Evidence

The runtime implementation is `scripts/development/self-host-concorde.py`. Contract behavior is exercised by `tests/concorde/contract/test_self_hosting_contract.py`; deterministic source, path, compatibility, and status primitives by `tests/concorde/unit/test_self_hosting.py`; lifecycle, collision, drift, quality-gate, idempotence, and rollback behavior by `tests/concorde/integration/test_self_hosting_lifecycle.py`; and complete surface plus preservation behavior by `tests/concorde/acceptance/test_self_hosted_checkout.py` with reusable fixtures under `tests/concorde/fixtures/self-hosting/`. `tests/concorde/contract/test_agent_commands.py` verifies the maintained and self-hosted command surfaces use the canonical checklist workspace authority.

The focused Feature 004 suite covers valid schema examples, unsafe paths, symlink rejection, clean bootstrap, adoption of known unregistered surfaces, foreign command collision rejection, stale proposals, refresh and unchanged idempotence, source/installed/registry/missing/extra-surface drift, read-only status without feature selection changes, preflight isolation, mutation-stage rollback, residual reporting, and preservation of project-authored content. The complete Concorde suite passes 134 tests against the actual self-hosted materialization.

The Concorde validator reports zero architecture findings. The compacted core component diagram passes all nine Archify 2.16 showcase checks with zero errors and warnings and has a fresh provenance-bearing HTML delivery at `generated/architecture/concorde-self-hosting-components.html`; its maintained source digest is `97a806f9b700fb20d2a9b1dba31f5fb778c0d3e09bac4fb7c85a0be08667f6ca` and its delivered HTML digest is `7ec2d4e3f2ccae85e9edf682a15d158bdec110d0456c6603a3710a02added9e7`. The docsite's manifest and production tests verify that the canonical Feature 004 page embeds that diagram and publishes `docs/self-hosting.md`.

The framework was applied to this checkout from an explicitly approved exact proposal. Post-apply status reports source, installed, registry, and surfaces as matching with no findings. A later fresh agent interaction exposed all seven installed Concorde skills, including the five surfaces absent before self-hosting, providing separate activation evidence without rewriting the original apply receipt.

The retained authorities after acceptance are `design.md`, this `implementation.md`, the feature contracts and core diagram, root and child architecture sources, the bootstrap source, documentation, tests, maintained component sources, and reproducible generated projections.

## Known Limitations

- Protocol v1 is intentionally limited to Spec Kit 0.16.4 and the Codex skills integration. It does not claim Gemini, other presentation modes, or later Spec Kit compatibility.
- The bootstrap validates the fixed Concorde manifests with a narrow standard-library scalar reader; it is not a general YAML or third-party component installer.
- On-disk status cannot prove what an already-running external coding agent loaded. Apply receipts remain honest about `reload_required`; fresh-session activation evidence must be established separately.
- Self-hosting verifies local-source materialization, not released archive isolation. Feature 003's clean catalog/archive installation and removal evidence remains independently required.
- Browser-based containment and perceptual review of the Feature 004 diagram remain pending because Chrome/Chromium was unavailable; structural showcase validation and docsite embedding are verified.
- Freshness findings are implemented by the root-owned bootstrap rather than by invoking the Scripts runtime. Maintained root prose currently describes Scripts as contributing deterministic freshness findings; a future architecture revision should make clear that this is a shared diagnostic convention, not a runtime call in the accepted implementation.
