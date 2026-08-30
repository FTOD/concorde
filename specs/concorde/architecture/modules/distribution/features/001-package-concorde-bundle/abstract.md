# Feature Abstract: Package the Concorde Bundle

`feature.distribution.package-concorde-bundle` · specified at `module.concorde.distribution` ·
refines `feature.concorde.install-with-spec-kit` and `feature.concorde.self-host-framework` · about
three minutes. This page is enough to understand what the bundle is, what a release contains, and
what must hold; the links at the end only redirect you when you want more.

## Purpose

A maintainer can inspect, install, update, and remove one native Spec Kit bundle whose resolved plan
contains exactly the compatible Concorde preset and command extension, while project-owned sources
and shared components remain safe. The same maintained bundle recipe also constrains development
self-hosting: it proves that the local preset and extension identities and versions remain the pair
distributed to user projects, without turning the bundle into a self-hosting runtime.

## Functionality

| Part | Job | Presented as |
|---|---|---|
| `concorde-bundle` recipe | Pins one `concorde` preset and one `concorde` extension at one accepted version and inherits the active integration. | An installation recipe, not a runtime. |
| Release archives | Carry the exact preset template and command sources and the extension command and runtime sources a clean target needs; repository-local self-hosting files are excluded. | Independently versioned, inspectable components. |
| Catalogs | Advertise location, compatibility, digest, and trust for each archive. | Discovery and trust metadata, never installed components. |

**The lifecycle**: preview expands the recipe into its exact component plan; installation resolves
the same identities and versions and records ownership; repeat installation is idempotent; updates
are explicit; removal touches only owned components. A failure never records success and names any
residual state it could not roll back. Acceptance executes the installed winning command surfaces
rather than trusting archive membership or expected text.

**Not part of this feature**: preset content, agent command behavior, architecture semantics,
user-authored architecture sources, checkout mutation and freshness for self-hosting (owned by the
root self-hosting feature), and external catalog publication (a separate release action).

## Structure

The installation feature's core view
<a href="/architecture/concorde-spec-kit-component-model.html">Spec Kit component model</a> and
supplemental <a href="/architecture/concorde-bundle-installation-flow.html">bundle installation
flow</a> (maintained sources
`specs/concorde/features/003-install-concorde-speckit/diagrams/spec-kit-component-model.json` and
`.../bundle-installation-flow.json`) already isolate Distribution's package role and the bundle
lifecycle crossing; the module owns no diagram of its own.

```text
Skills ──component packages──▶ Distribution: concorde-bundle recipe + release tooling
                                                 ├─ builds preset · extension · bundle archives + catalogs
                                                 └─ contract.distribution.bundle-lifecycle ──▶ Spec Kit + maintainer
                                                        preview ▸ accept ▸ install ▸ status ▸ update ▸ remove
```

Distribution owns bundle composition, version pins, release metadata, lifecycle outcomes, and
component provenance; Spec Kit owns resolution, provenance recording, and materialization. The
preset and extension arrive across `contract.distribution.component-packages`.

## Logic

**One installation**

1. The maintainer asks Spec Kit to preview `concorde-bundle`; the recipe expands into its pinned
   preset and extension, resolved from permitted catalogs, with versions, trust source, and
   diagnostics.
2. The maintainer accepts; installation delegates each component to Spec Kit's preset or extension
   machinery and records ownership.
3. Later update and removal act only on owned components; unresolved or incompatible components stop
   the operation and are named.
4. Acceptance runs the installed winning commands in a clean target.

**Rules the implementation must keep**

- The bundle pins one preset and one extension and inherits the active integration (Requirements,
  item 1).
- Release archives contain exactly the preset and extension sources a clean target requires and
  exclude repository-local self-hosting files (Requirements, item 2).
- The bundle is an installation recipe; catalogs are discovery and trust metadata, not runtime
  components (Requirements, item 3).
- Preview and installation resolve the same component identities and versions (Requirements,
  item 4).
- Repeat installation is idempotent, updates are explicit, and removal respects ownership
  (Requirements, item 5).
- Failures never record success and name residual state that could not be rolled back
  (Requirements, item 6).
- Acceptance executes the installed winning command surfaces; archive membership or expected text
  alone is not evidence (Requirements, item 7).

## Read Next

- **Exact outcome, scenario, and requirements** — [design.md](design.md).
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md).
- **The contracts** — [bundle-lifecycle](../../architecture/contracts/bundle-lifecycle/contract.md) (provided)
  and [component-packages](../../architecture/contracts/component-packages/contract.md) (required).
- **The level this feature belongs to** — [module.md](../../module.md) (the Distribution summary)
  and its [design reference](../../design.md); the root summary is
  [module.md](../../../../../module.md).
- **The parent features** — [Install and Set Up Concorde with Spec Kit](../../../../../features/003-install-concorde-speckit/abstract.md)
  and [Self-Host the Concorde Framework](../../../../../features/004-self-host-concorde/abstract.md).
- **Maintainer guides** — [docs/releasing.md](../../../../../../../docs/releasing.md) and
  [docs/quick-start.md](../../../../../../../docs/quick-start.md).
