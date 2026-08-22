# Validation Record: Deliver Concorde through Spec Kit

**Feature**: `feature.concorde.install-with-speckit`
**Attempt state**: active
**Evidence status**: partial

## Automated Evidence

### Release identity and native lifecycle

- `uv run python scripts/release/build-components.py --output dist --publish-catalogs` built explicit-
  allowlist, deterministic preset, extension, and bundle archives. `--base-url` was serialized into
  catalogs and was not contacted during the build.
- `uv run python scripts/release/verify-release.py --dist dist` passed catalog identity, URL, digest,
  safe-member, and byte-equivalent rebuild checks.
- Current release digests:

  | Artifact | SHA-256 |
  |---|---|
  | `concorde-0.1.0.zip` | `a2611f58fca7d9bef67b1a703f0bc6a509cf72d74b1cb513f0bf4a6a70893d60` |
  | `concorde-core-0.1.0.zip` | `307fdddaae9cb13a8cc74e844ad431af826028b8d344fa8aac298cd64289f10f` |
  | `concorde-starter-0.1.0.zip` | `343ecb318685040f0048b63b3dd1178ab79bcc29882cd6c717c5c9796b35ae3a` |

- The preset archive contains exactly three append template layers and nine complete `replace`
  command layers. The extension archive contains five commands, four scripts, schemas, and the full
  runtime. Release tests reject files outside the maintained component allowlists.
- Native lifecycle tests cover trusted catalog, source directory, manifest, archive, initialized and
  uninitialized targets; preview/install parity; three-repeat idempotency; compatible update; rollback;
  shared components; local modifications; and safe removal.

### Installed command behavior

- The complete Concorde Python suite passed: **86 tests**.
- Clean targets outside the checkout installed the built bundle through served generated catalogs.
  Codex skills and Gemini slash-command integrations materialized all **nine normal + five Concorde**
  command surfaces.
- Every normal command executed its installed workspace bootstrap before phase routing. Three
  byte-equivalent phase-matrix runs resolved specification/clarification/checklists to the durable
  feature root and planning/tasks/implementation/analysis/convergence to `implementation/`, with no
  root plan/task aliases or symlinks.
- Installed extension commands executed the packaged adapter/runtime. Removing a required adapter
  member failed acceptance, proving there was no repository-local fallback.
- A lower-layer fixture verified Spec Kit 0.16.4's actual lifecycle for all nine commands: disable and
  priority changes preserve registered command artifacts while changing future resolution; bundle
  removal restores the surviving lower layer with zero stale Concorde instructions.
- Update/removal preserved project-authored `.concorde/`, `specs/`, and `docs/` hashes and retained
  shared components under the lifecycle fixtures.

### Diagrams and docsite

- Both Feature 003 maintained views passed **9/9 Archify showcase checks** with zero composition
  errors and warnings.
- Component model source/artifact digests:
  `a6f787e0581e796d31e29748aa255b58a677abc1120a0f14aea1a477e87e2817` /
  `3f2b02327654ea0bf40936ddc44ee24fa58ff0571dd63f22492d97eb5998286f`.
- Installation flow source/artifact digests:
  `bdd306524e5ae34ad23ee6c8bb4531f84aba02a5f7efb3b6019fd8997e5b3194` /
  `06f1a04adcf029ae9884ebce155e5618daded6eeff37d547a6ee0dec5d2e324d`.
- Browser visual-check was attempted for both outputs but skipped because Chrome/Chromium is
  unavailable. Receipts retain `visualReview: pending`; containment and perceptual review are not
  fabricated.
- `npm run check` in `docsite/` passed TypeScript, **14 test files / 29 tests**, **31 pages** with
  **31 excluded sources**, zero validation errors, automatic diagram embedding, and production build.

## Pending Human or Browser Evidence

- SC-001 first-time setup-time/completion pilot: pending real participants.
- SC-007 five-minute ecosystem-role comprehension pilot: pending real participants.
- SC-008 browser containment, theme, and perceptual portion: pending Chrome/Chromium plus human review;
  deterministic showcase and freshness checks pass.

All other automated outcomes are supported by the evidence above; no human result is inferred from
automation.
