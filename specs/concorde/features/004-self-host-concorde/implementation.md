# Feature Implementation: Self-Host the Concorde Framework

**Realization status**: Candidate dual-integration realization verified on 2026-08-30 and awaiting explicit acceptance.

## Realization Overview

Concorde self-hosts through the repository bootstrap `scripts/development/self-host-concorde.py`. The bootstrap remains outside the installed extension so a checkout with no active Concorde installation can inspect, review, and install the framework. It uses Python 3.11 standard-library facilities and delegates component mutation to Spec Kit 0.16.4's public development-mode preset and extension lifecycle.

The maintained `presets/concorde/`, `extensions/concorde/`, and `bundles/concorde-bundle/` trees remain authoritative. Installed component copies, registries, composed templates, and active coding-agent skills are replaceable materializations. Protocol v1 now supports both the Codex and Claude skills integrations. A closed integration profile selects initialization arguments, registry keys, the owned skill root, and permitted surface representation for the active integration; inactive integration assets remain outside the proposal and rollback scope.

The bootstrap retains three JSON-producing operations:

- `propose` validates the source boundary and active integration, computes the source digest, checks active-integration ownership and collisions, and writes only the ignored proposal;
- `apply` accepts only that exact reviewed proposal, preflights the same integration in isolation, snapshots the active owned scope, installs through Spec Kit, verifies every evidence dimension, and writes the ignored receipt atomically; and
- `status` is read-only and independently classifies source, installed copy, registry, active-integration surfaces, and activation. `status --require-current` remains the non-mutating quality gate.

The durable JSON payload shape remains protocol v1. The human-readable contract now names Codex and Claude and the narrow Claude development-link rule; no schema or example shape changed.

## Module and Feature Collaboration

`module.concorde` continues to own this project-level feature across Distribution, Skills, and Scripts. Its responsibility, boundary, submodules, level views, and provided/required contracts remain unchanged.

Distribution supplies the local `concorde` preset, `concorde` extension, and `concorde-bundle` recipe. Skills receives the active integration's materialized commands. The root bootstrap coordinates review, verification, and recovery while Spec Kit remains authoritative for initialization, registry composition, template layering, and development installation.

Both integrations cross the existing `contract.concorde.spec-kit-installation` and `contract.concorde.spec-kit-platform` boundaries. Codex and Claude are alternative presentations of the existing active-project-materialization role in the feature's core architecture view, so no module responsibility, dependency direction, contract shape, or diagram participant changed.

## Scenario Realization

### Install the current framework

The source gate accepts exactly Spec Kit 0.16.4 with either `codex` or `claude`. Codex preflight retains the explicit skills-mode option and materializes regular skill files beneath `.agents/skills`. Claude is natively skills-based, so its preflight omits that Codex-only option and materializes beneath `.claude/skills`.

Preset skills and templates are regular files. Claude extension development skills may be either Spec Kit's canonical relative links into `.specify/extensions/concorde/.specify-dev/agent-commands/claude/` or its regular-file fallback. Verification accepts a link only for a declared Claude extension command, only when the link is relative, and only when it resolves to the exact expected regular file through non-symlink cache ancestors. Absolute, dangling, escaping, preset, nested, or retargeted links fail evidence.

Registry normalization and collision detection read the active `registered_commands` and `registered_skills` key. Proposal paths include exactly that integration's skill directories plus the shared component copies, registries, templates, and receipt.

### Refresh after a framework improvement

Refresh keeps the proposal-review-apply sequence and source-digest invalidation. The receipt's integration must equal the active integration; switching integrations therefore produces drift until a newly reviewed apply records the new active surface model. An unchanged result is possible only when source, installed copy, registry, active-integration surface digest, and receipt integration all match.

Surface evidence records path, byte digest, representation, and the canonical target for an accepted link. Changing a link into a file, retargeting it, or changing bytes is observable even when another representation contains equal content.

### Verify self-hosting freshness

`status` uses the active integration profile for registry projection, skill inventory, extra Concorde-owned surface detection, diagnostic paths, and receipt comparison. Missing, extra, altered, wrong-representation, unsafe-link, or wrong-integration evidence prevents `current`. Activation remains separately `reload_required`; on-disk equality does not claim that an already-running coding agent loaded the new instructions.

The live checkout was self-applied through Claude after implementation. The reviewed proposal contained 24 active Claude and shared `.specify` paths, no `.agents` path, and finished with all four deterministic dimensions matching. The inactive Codex skill tree retained the same aggregate digest before and after apply.

### Preserve work and recover safely

Proposal ownership, drift inventory, receipt evidence, and verification follow the active
integration root. Because Spec Kit 0.16.4's `preset remove` and forced `extension add`
unregister every agent recorded in the registry, `apply` additionally snapshots the inactive
integration's declared Concorde skill directories — and, for an inactive Claude, its extension
link cache — with the owned scope and restores them byte-for-byte after the host refresh, on
success and on rollback; an incomplete restoration raises `CONCORDE-SELF-HOST-023` and never
records success. Directory snapshot and restoration preserve symlinks as links, and a
preserved path nested inside an owned path is captured once within its ancestor's snapshot.
Inactive Codex or Claude surfaces, whether registered by an earlier apply or hand-created
sentinels, are byte-preserved.

Successful and injected-failure fixtures cover Codex and Claude. Every preset, extension, and verification mutation boundary restores the prior owned scope; residual rollback failure remains exact and cannot record success.

## Durable Implementation Decisions

1. **Keep public Spec Kit development primitives.** Component copies, registry ownership, templates, and integration surfaces continue to be produced by the host lifecycle rather than a parallel installer.
2. **Keep first-install bootstrap independent.** The repository script remains usable before Concorde commands exist.
3. **Use a closed integration profile.** Protocol v1 recognizes exactly Codex and Claude and retains the exact Spec Kit 0.16.4 compatibility check.
4. **Own only the active integration.** Profile-specific registry keys and skill roots prevent one integration's refresh from mutating or judging the inactive integration. The inactive tree is preserved by restoration around the host lifecycle, never by editing Spec Kit's registry or skipping its removal step.
5. **Model surface representation as evidence.** Path, digest, file/link representation, and canonical target participate in the receipt surface digest.
6. **Permit only the canonical Claude extension link.** Broad in-project symlink following was rejected because it could bind self-hosting evidence to unrelated content.
7. **Bind receipts to integration identity.** Equal shared source or registry content cannot make an old integration receipt current after an integration switch.
8. **Keep review and rollback exact.** Proposal equality, isolated preflight, active-scope snapshot, reverse restoration, and residual reporting remain unchanged.
9. **Keep the public JSON schema at v1.** The integration field was already shape-generic; compatibility prose and executable evidence changed without a payload migration.
10. **Preserve the existing architecture view.** Codex and Claude occupy the same stable active-materialization role, so a new component or dynamic diagram would add noise rather than architecture.
11. **Read coverage-defining fixtures strictly.** The preservation fixture's object keys are the seeded paths, so `tests/concorde/self_hosting_support.py` loads it through `load_preserved_fixture`, which rejects a repeated key or non-string content instead of letting ordinary JSON parsing keep the last value silently.

## Traceability and Evidence

The runtime implementation is `scripts/development/self-host-concorde.py`. Reusable disposable-checkout support is in `tests/concorde/self_hosting_support.py`; contract, unit, lifecycle, and acceptance evidence remains under the corresponding `tests/concorde/{contract,unit,integration,acceptance}/` paths.

Focused Feature 004 evidence covers supported and unsupported profiles, integration-specific initialization, active registry keys and collision detection, canonical Claude links, regular-file fallback, unsafe and retargeted links, receipt mismatch, proposal/apply, unchanged and changed refresh, source/installed/registry/surface drift, every injected rollback boundary, read-only status, inactive-integration preservation, cross-integration refresh in both directions including rollback with registered inactive surfaces, and strict loading of the preservation fixture. A repeated path key or non-string content is rejected, and every preserved content class, including distinct abstract, design, and implementation paths, is seeded.

The complete Concorde suite, deterministic Feature 004 validation, and docsite gate are the project-level evidence. The docsite gate covers TypeScript, source validation, canonical Feature 004 diagram embedding, and production build promotion. The maintained core diagram keeps its layout and `meta.legend.mode: hidden`; only repository evidence changed, and no new perceptual review is claimed.

The core diagram's repository evidence pins `106f1b2` and cites the authoritative `presets/concorde/preset.yml` for the framework-sources role, replacing the former materialized-skill citation. `tests/concorde/integration/test_self_architecture.py` verifies that every maintained repository-evidence diagram cites paths that exist both in the checkout and at its pinned revision, and that this diagram's framework-sources role cites no materialization, so an identity or path migration is caught by the Python suite before the docsite build runs Archify.

The live Claude self-apply ends `current` with source, installed copy, registry, and surfaces matching, no findings, and activation honestly reported as `reload_required`. This supported evidence supersedes the former `CONCORDE-SELF-HOST-005` workaround.

## Known Limitations

- Protocol v1 supports only Spec Kit 0.16.4 with Codex or Claude skills integrations. Gemini, other presentation modes, and later Spec Kit versions still require equivalent isolated lifecycle, surface, rollback, preservation, and activation evidence.
- Status cannot prove what an already-running external coding agent loaded. Every successful apply remains `reload_required` until fresh-session evidence exists.
- The bootstrap's standard-library manifest reader is deliberately narrow and is not a general YAML or third-party component installer.
- Self-hosting verifies local-source materialization, not release-archive isolation; Feature 003 remains the release proof.
- Browser-based perceptual review of the Feature 004 diagram remains pending (its layout is unchanged; only its repository evidence moved) from the accepted baseline; deterministic structure, freshness, embedding, and production delivery pass.
- The inactive integration's Concorde tree is preserved, not verified: `status` judges only the active integration, and the preserved tree becomes current only through its own reviewed apply after switching.
- Root architecture prose still describes Scripts as contributing deterministic freshness findings, while the accepted runtime keeps those findings in the root-owned bootstrap; a future architecture revision may clarify that shared diagnostic convention.
