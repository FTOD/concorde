# Validation Record: Deliver Concorde through Spec Kit

**Feature**: `feature.concorde.install-with-speckit`
**Attempt state**: active
**Evidence status**: partial
**Accepted design SHA-256**: `e522513e43f6437d53b49dbf96e533d903b3765519a7cf90f179db4bbd3e55c8`

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
  | `concorde-0.1.0.zip` | `cee9da2f0698e93698ec3acad2f0d4a08bf43e8d51e420f0e14b3ded5e27eb36` |
  | `concorde-core-0.1.0.zip` | `adfd1502a795afa0f9b969f38fa1fcf1b74ee8e9e67a948a077091a4e22fbe94` |
  | `concorde-starter-0.1.0.zip` | `343ecb318685040f0048b63b3dd1178ab79bcc29882cd6c717c5c9796b35ae3a` |

- The preset archive contains exactly three append template layers, one Concorde-owned design
  template replacement, and nine complete command replacements. The extension archive contains six
  commands, four scripts, schemas, and the full
  runtime. Release tests reject files outside the maintained component allowlists.
- Native lifecycle tests cover trusted catalog, source directory, manifest, archive, initialized and
  uninitialized targets; preview/install parity; three-repeat idempotency; compatible update; rollback;
  shared components; local modifications; and safe removal.

### Installed command behavior

- The non-interactive complete Python discovery run passed **93 tests** in 45.505 seconds.
- Clean targets outside the checkout installed the built bundle through served generated catalogs.
  Codex skills and Gemini slash-command integrations materialized all **nine normal + six Concorde**
  command surfaces.
- Every normal command executed its installed workspace bootstrap before phase routing. Three
  byte-equivalent phase-matrix runs resolved specification/clarification intent to the durable
  feature root, every generated checklist to `implementation/checklists/`, and planning/tasks/
  implementation/analysis/convergence to `implementation/`, with no root checklist/plan/task aliases
  or symlinks.
- Installed extension commands executed the packaged adapter/runtime. Removing a required adapter
  member failed acceptance, proving there was no repository-local fallback.
- The clean installed Codex workflow exercised `feature harden --propose` to an `eligible` result;
  focused runtime tests proved incomplete refusal, stale conflict, approved atomic design promotion,
  exact attempt removal, and rollback. Both supported presentations materialized the hardening command.
- A lower-layer fixture verified Spec Kit 0.16.4's actual lifecycle for all nine commands: disable and
  priority changes preserve registered command artifacts while changing future resolution; bundle
  removal restores the surviving lower layer with zero stale Concorde instructions.
- Update/removal preserved project-authored `.concorde/`, `specs/`, and `docs/` hashes and retained
  shared components under the lifecycle fixtures.

### Diagrams and docsite

- Both Feature 003 maintained views passed **9/9 Archify showcase checks** with zero composition
  errors and warnings.
- Component model source/artifact digests:
  `28ad60b6151dd4044f1b917c2673eeb32969a850273a94398e05f4a83adc0bb5` /
  `f0eb2f57ef5e7d6af9649e9ebc9be919421ca42b2dd1657786d152fdab619c4a`.
- Installation flow source/artifact digests:
  `6c60625a0adbf854fe947a3de478c7dc4ad52b5496d178aa1db016dd554bfe6f` /
  `a8c888acb323c0dd4d0ac5745be5d9785bcffb570f8379004a74f3669afd0ac1`.
- Browser visual-check was attempted for both outputs but skipped because Chrome/Chromium is
  unavailable. Receipts retain `visualReview: pending`; containment and perceptual review are not
  fabricated.
- `npm run check` in `docsite/` passed TypeScript, **14 test files / 29 tests**, **39 pages** with
  **31 excluded sources**, zero validation errors, automatic diagram embedding, and production build.
- Concorde self-validation returned `success` over 35 canonical artifacts with zero findings and
  source digest `sha256:94fda1c23dd680f3b28f2990290afaa91e8c09b4d03d135d6e6a6a2a2e640565`.
- The requirements checklist is confined to `implementation/checklists/requirements.md`; no root
  copy or symlink remains.

## Pending Human or Browser Evidence

- SC-001 first-time setup-time/completion pilot: pending real participants.
- SC-007 five-minute ecosystem-role comprehension pilot: pending real participants.
- SC-008 browser containment, theme, and perceptual portion: pending Chrome/Chromium plus human review;
  deterministic showcase and freshness checks pass.

All other automated outcomes are supported by the evidence above; no human result is inferred from
automation.
