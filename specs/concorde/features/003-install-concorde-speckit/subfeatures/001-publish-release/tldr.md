# TL;DR: Publish a Concorde Release

`feature.concorde.install-with-spec-kit.publish-release` · specified at `module.concorde` ·
sub-feature of `feature.concorde.install-with-spec-kit` · about three minutes. This page is enough
to understand how a built release becomes publicly installable; the links at the end only redirect
you when you want more.

## Purpose

A maintainer publishes one versioned Concorde release from the maintained sources, and afterwards
any supported project can discover and install exactly that release from a stable public location —
without cloning Concorde, building archives, or serving catalogs locally. It exists for the release
maintainer who marks a version, and for every consumer who should never have to be a release
builder.

## Functionality

The parent defines what a release contains and how Spec Kit installs and verifies it. This child owns
only the step between "release built and verified" and "catalog discovered":

| Concern | What this sub-feature does |
|---|---|
| Trigger | Marking a release version on the maintained sources publishes automatically; no manual upload. |
| Content | The bundle, preset, and extension archives plus their three catalogs from the parent's release build, unchanged, and human-readable notes naming component versions and the supported Spec Kit range. |
| Location | Version-specific locations that are immutable once published, exactly where the catalogs advertise. |
| Discovery | A stable current-release location that names the newest fully published version and its catalog locations. |
| Trust | The parent's verification runs first; rebuilt archives match the published digests; a digest mismatch stops installation before success. |

**Not part of this feature**: package contents, bundle composition, installed command behavior, and
the local build-and-serve development path, which stays available and unchanged for acceptance
testing.

## Structure

The parent's core view <a href="/architecture/concorde-spec-kit-component-model.html">Spec Kit
component model</a> and supplemental
<a href="/architecture/concorde-bundle-installation-flow.html">bundle installation flow</a>
(maintained sources `../../diagrams/spec-kit-component-model.json` and
`../../diagrams/bundle-installation-flow.json`) already show release, discovery, and installation;
this child inserts publication between them and maintains no diagram of its own.

```text
maintainer marks v<version> ──▶ parent build + verification ──▶ publication ──▶ public location
                                                                                  ├─ 3 archives + 3 catalogs (immutable, per version)
                                                                                  ├─ release notes
                                                                                  └─ current-release pointer ──▶ clean project registers catalogs ──▶ Spec Kit preview / install
```

The Distribution module supplies the reproducible archives and catalogs; Spec Kit remains the
consumer through its public catalog registration; the sibling one-command installer reads the
current-release pointer; the docsite publishes the maintainer guide.

## Logic

**From marked version to installable release**

1. A maintainer marks a release version on the maintained sources.
2. The marked version is compared with the bundle, preset, and extension manifests; disagreement
   stops publication.
3. The parent's release build and verification run; any failure publishes nothing and names the
   failing check.
4. The archives, catalogs, and notes are published to the advertised version-specific location.
5. Only after the version is fully published does the current-release location move to it.
6. A clean project registers the published catalogs, previews the bundle, and installs — with no
   Concorde checkout and no local server.

**Rules the implementation must keep**

- Publication is triggered by marking a version and needs no manual upload (FR-001).
- Every release carries the parent build's three archives and three catalogs unchanged, plus notes
  naming component versions and the supported Spec Kit range (FR-002, FR-009).
- Catalogs advertise the exact public locations actually used; a mismatch fails publication
  (FR-003).
- Verification runs first and a failing version publishes nothing; the marked version must equal
  the manifests' version (FR-004, FR-005).
- A published version-specific location is immutable; re-running publication reproduces identical
  bytes or stops with a named conflict (FR-006).
- The current-release location identifies the newest version and its catalogs and is updated only
  after full publication (FR-007).
- Published catalogs are registrable from a clean supported project through public Spec Kit
  commands (FR-008).
- The local build-and-serve development path stays available and unchanged (FR-010).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [spec.md](spec.md): three user stories,
  FR-001 to FR-010, and SC-001 to SC-004.
- **How the accepted implementation realizes this feature** — [design.md](design.md) (the
  publication workflow, decision table, and pointer).
- **The interface profile** — `contracts/release-publication.md` (published
  layout and current-release pointer), governed by the parent's
  `../../contracts/bundle-distribution.md`.
- **The parent** — [TL;DR](../../tldr.md) and [spec.md](../../spec.md) of
  `feature.concorde.install-with-spec-kit`; the sibling
  [one-command-install](../002-one-command-install/spec.md).
- **The level this feature belongs to** — [module.md](../../../../module.md) (the root summary) and
  [Distribution](../../../../modules/distribution/module.md).
- **The maintainer guide** — [docs/releasing.md](../../../../../../docs/releasing.md).
