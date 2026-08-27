# Validation: Publish a Concorde Release

**Attempt date**: 2026-08-27 · **Release version under test**: `0.1.0` · **Tag**: `v0.1.0`

This is temporal attempt evidence. `evidence_status` in `spec.md` is `verified`: every automated
check passes and the live publication of `v0.1.0` (T012, T013, T017, T020) is recorded below. The
only scenario that cannot be exercised until a second version exists is "a newer release supersedes
the pointer while older locations stay unchanged" (US2 scenario 2); it is listed as pending.

## Automated evidence (passing)

| Check | Command | Result |
|---|---|---|
| Release unit + contract tests | `uv run python -m unittest tests.concorde.unit.test_publish_release tests.concorde.contract.test_release_publication tests.concorde.contract.test_release_artifacts` | 25 tests OK |
| Full Concorde suite (localhost acceptance path unchanged, FR-010) | `uv run python -m unittest discover -s tests/concorde -p 'test_*.py'` | 155 tests OK |
| Architecture validation | `.specify/extensions/concorde/scripts/bash/concorde.sh validate --format json` | `success`, 0 findings |
| Docsite gate (types, 49 tests, source validation, build) | `npm --prefix docsite run check` | 71 pages, 0 errors, build promoted |
| Version authority | `build-components.py --print-version` | `0.1.0` from `bundle.yml`; manifests and pins agree (FR-005) |
| Verifier with published base | `verify-release.py --dist dist --expect-version 0.1.0 --expect-base-url https://github.com/FTOD/concorde/releases/download/v0.1.0` | all locations match; rebuild byte-equivalent (FR-003, FR-004, SC-002 locally) |
| Publisher dry run | `publish-release.py --dist dist --tag v0.1.0 --dry-run` | outcome `dry-run`, exit 0, zero host operations |
| Publisher tag mismatch | `publish-release.py --dist dist --tag v9.9.9 --dry-run` | outcome `version-mismatch`, exit 1 |

### Archive digests (local deterministic build)

| Archive | SHA-256 |
|---|---|
| `concorde-0.1.0.zip` | `sha256:573dd3284a0ef254be0e6688e50fddbbd2744f70bc103add319b0044e0332efe` |
| `concorde-bundle-0.1.0.zip` | `sha256:ae0079f5e78b89bbb30eaa46279f036553395f1be1c94f9af8de962ab0670608` |
| `concorde-core-0.1.0.zip` | `sha256:17b48a8eafc99461c554ddc133cd219b78dfad04258046c5a2dca11cb0d482f7` |

### Dry-run plan for `v0.1.0`

1. `gh release create v0.1.0 --draft --verify-tag`
2. `gh release upload v0.1.0 concorde-core-0.1.0.zip`
3. `gh release upload v0.1.0 concorde-0.1.0.zip`
4. `gh release upload v0.1.0 concorde-bundle-0.1.0.zip`
5. `gh release upload v0.1.0 extensions.json`
6. `gh release upload v0.1.0 presets.json`
7. `gh release upload v0.1.0 bundles.json`
8. `gh release upload v0.1.0 release.json`
9. `gh release edit v0.1.0 --draft=false`

The dry run also rendered the release notes (component versions, Spec Kit range `>=0.16.4,<0.16.5`, digests, registration commands) and wrote `dist/release.json`, which validates against the schema in `contracts/release-publication.md`.

## Requirement coverage

| Requirement | Evidence |
|---|---|
| FR-001 tag-triggered, no manual upload | `.github/workflows/publish-release.yml` (`push.tags: v*`); workflow-shape contract test |
| FR-002 seven assets unchanged from the build | publisher uploads `dist/` files as built; unit test asserts the asset list |
| FR-003 advertised == published locations | verifier `--expect-base-url`; `repository` corrected to `FTOD/concorde` in builder and manifests |
| FR-004 verify before publish | workflow step order test; publisher runs `verify_release` before any host call (unit test) |
| FR-005 tag == manifest version | `read_release_identity` disagreement test; `version-mismatch` unit + CLI test |
| FR-006 immutable / idempotent | `already-published` no-op and `divergent` refusal tests; no `--clobber` anywhere (workflow test) |
| FR-007 pointer flips only when complete | draft → uploads → `edit --draft=false` last (unit test); pre-release excluded via `--prerelease` |
| FR-008 registrable from a clean project | live T013 below: registered and installed with only the public CLI |
| FR-009 release notes | `render_notes` test |
| FR-010 localhost path unchanged | full suite green, `catalog_server.py` untouched |

## Pending live evidence

| Task | Step | Status |
|---|---|---|
| T012 | `workflow_dispatch` with `dry_run=true` on GitHub | **done** — see "Workflow rehearsal" below |
| T013 | `git tag v0.1.0 && git push origin v0.1.0`; clean-project catalog registration + `bundle info` (SC-001, SC-003) | **done** — see "Live publication" below |
| T017 | `curl -fsSL https://github.com/FTOD/concorde/releases/latest/download/release.json` | **done** — see "Live publication" below |
| T020 | re-dispatch for the same ref → `already-published`; clean-clone rebuild digests == published (SC-002) | **done** — see "Live publication" below |
| US2 scenario 2 | newer version supersedes the pointer; `v0.1.0` locations unchanged | pending — verifiable at the next release |

## Workflow rehearsal (T012, live, no publication)

- Run: https://github.com/FTOD/concorde/actions/runs/33054887480 — `workflow_dispatch`, `dry_run=true`, ref `main` at `bad7dab`
- Conclusion: `success`; 20 s from start to completion (08:37:57Z → 08:38:17Z)
- Steps, all green in order: checkout → uv/Python 3.11 → `uv sync` → resolve tag (`v0.1.0` from `--print-version`) → unit tests → release contract tests → build → verify (`--expect-version 0.1.0 --expect-base-url https://github.com/FTOD/concorde/releases/download/v0.1.0`) → publish (dry run)
- Publication Record: `outcome: dry-run`, nine-operation plan (`create --draft --verify-tag`, seven uploads ending with `release.json`, `edit --draft=false`), `residual_state: null`; `gh release list` afterwards is empty
- Runner digests equal the local build in the table above (`concorde-0.1.0.zip` 573dd328…, `concorde-bundle-0.1.0.zip` ae0079f5…, `concorde-core-0.1.0.zip` 17b48a8e…), confirming cross-machine reproducibility ahead of SC-002

## Live publication (T013, T017, T020)

### T013 — publish `v0.1.0` (SC-001, SC-003, FR-001…FR-004, FR-007…FR-009)

- Tag `v0.1.0` on `bad7dab` pushed 2026-08-27 ~08:40:10Z; run https://github.com/FTOD/concorde/actions/runs/33055060670 started 08:40:18Z, release published 08:40:39Z (`publishedAt`), run completed 08:40:42Z — **under one minute** from tag to published (SC-001 < 15 min)
- Publication Record: `outcome: published`, "v0.1.0 published with 7 assets at https://github.com/FTOD/concorde/releases/download/v0.1.0", `residual_state: null`
- Release inventory (`gh release view v0.1.0`): `isDraft: false`, `isPrerelease: false`, seven assets — `concorde-core-0.1.0.zip` (60543 B), `concorde-0.1.0.zip` (52225 B), `concorde-bundle-0.1.0.zip` (1458 B), `extensions.json`, `presets.json`, `bundles.json`, `release.json`
- Clean-project check, in a fresh temporary directory with no Concorde checkout, using only `uvx --from specify-cli==0.16.4 specify …`: `init --here --integration claude` → three `catalog add` against the published URLs → `bundle info concorde-bundle --json` reported `concorde@0.1.0` and `concorde-core@0.1.0` (priority 10, append) → `bundle install concorde-bundle` = "Installed 'concorde-bundle' (2 added, 0 already present)". **Elapsed 7 s** (SC-003 < 2 min). `bundle list --json` shows both components at 0.1.0 and `.claude/skills/` contains all 17 materialized `speckit-*` skills.

### T017 — current-release pointer (FR-007)

`curl -fsSL https://github.com/FTOD/concorde/releases/latest/download/release.json` returned `version: 0.1.0`, `tag: v0.1.0`, the three catalog URLs under `…/releases/download/v0.1.0/`, and the three archive digests listed above. Superseding by a newer version remains pending until the next release.

### T020 — idempotence and reproducibility (FR-006, SC-002, SC-004)

- Re-dispatch with `dry_run=false` on `main` (same manifest version): run https://github.com/FTOD/concorde/actions/runs/33055138343 → `success`, Publication Record `outcome: already-published`, "v0.1.0 is already published with identical catalogs and digests; nothing changed"; the release still has exactly 7 assets
- Fresh `git clone --branch v0.1.0` into a scratch directory, `uv sync`, `build-components.py`: all three rebuilt digests equal the published `release.json` archives — **100 % match** (SC-002)

## Notes

- `specify bundle build --path bundles/concorde-bundle --output dist` produces a bundle archive with the same digest as the deterministic builder, so the workflow does not run it separately.
- The `dist/` and `catalogs/` directories remain git-ignored; `--publish-catalogs` is a local convenience only.
