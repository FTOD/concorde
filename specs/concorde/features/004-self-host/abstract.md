# Feature Abstract: Self-Host the Concorde Framework

`feature.concorde.self-host-framework` · specified at `module.concorde` · about five minutes. This
page is enough to understand how Concorde installs itself into its own checkout, what that changes,
and what must hold; the links at the end only redirect you when you want more.

## Purpose

Concorde is both a distributable framework and the project in which that framework is developed.
This feature lets a maintainer install the checkout's current trusted framework sources — the same
preset, extension, and bundle responsibilities that form the distributed framework — into this same
checkout, refresh them after a framework change, and verify that the active installation has not
drifted from its authoritative sources. Every improvement to the framework or workflow is then used
while developing Concorde, and the project never claims to be dogfooding a change it has not
activated.

Authority flows in the opposite direction from a user-project install: the maintained sources are
the expected state, and project-local commands, skills, templates, and runtime copies are replaceable
materializations. Feature 003 keeps its checkout-isolated release proof; this feature adds a
development self-hosting mode and does not weaken that proof.

Protocol v1 supports both the Codex and Claude skills integrations. The active integration selects
the registry and agent-surface representation that self-hosting owns and verifies; surfaces belonging
only to an inactive integration remain preserved project assets.

## Functionality

**The lifecycle** — three explicit, reviewed journeys plus a safety property:

| Journey | What the maintainer does | What must be true afterwards |
|---|---|---|
| Install | Inspects a proposal naming the source identity, compatibility, planned owned changes, preserved content classes, and activation boundary; approves it. | One active preset and extension composition equivalent to the accepted local sources, with provenance that can reproduce and verify that state. |
| Refresh | After changing any authoritative source, previews and approves the refresh; satisfies the reported activation step. | The next new agent interaction uses the refreshed surfaces; an unchanged source set reports unchanged with no duplicate registrations. |
| Verify | Runs a read-only freshness check, with or without a selected feature workspace. | Source identity, on-disk materialization, component registration, host compatibility, and session activation are each classified as matching, disagreeing, missing, or unknown. |
| Preserve and recover | Seeds project-authored content and unrelated agent assets; a refresh succeeds or fails. | Only Concorde-owned materializations named in the approved proposal change; a failure keeps the prior usable framework or reports exact residual state. |

Bootstrap works before any Concorde command exists, because setup cannot depend on a command that
only successful setup creates. Self-hosting is a synchronization lifecycle, not a hot reload: when
the active integration needs a new session or an explicit reload, the result says so and never claims
the running session already uses the refreshed version.

The same reviewed lifecycle applies when either Codex or Claude is active. Integration-specific
registry fields, surface locations, and supported surface representations are evidence inputs, not
separate workflows.

**Not part of this feature**: replacing Feature 003's released installation, catalog, update, or
removal lifecycle for user projects; mutating the installation on every source-file save;
guaranteeing that a running coding agent hot-reloads instructions; promoting edits from installed
materializations back into framework sources; and treating self-hosting as proof that released
archives work.

## Structure

The core view is <a href="/architecture/concorde-self-hosting-components.html">self-hosting
components</a> (maintained source `diagrams/concorde-self-hosting-components.json`). It shows eight
roles: the maintainer, the authoritative framework sources, this feature, the required Spec Kit
component lifecycle, the active project materialization, the coding agent, the preserved Concorde
project sources, and the self-hosting drift gate. In one sketch:

```text
presets/concorde · extensions/concorde · bundles/concorde-bundle   (authoritative source set)
        │ propose ──▶ .specify/self-hosting-proposal.json ──▶ maintainer reviews, approves
        ▼ apply   ──▶ preflight in an isolated project ──▶ snapshot owned scope ──▶ Spec Kit local preset/extension install
                       ──▶ verify ──▶ .specify/self-hosting.json receipt ──▶ reload_required ──▶ coding agent (new session)
        status  ──▶ compare source · installed copy · registry · surfaces · activation  (read-only drift gate)
Preserved, never owned:  specs/** · docs/** · code · tests · project config · unrelated agent assets
```

- **Distribution** identifies the authoritative local component set: the `concorde-bundle` recipe
  pins the local `concorde` preset and `concorde` extension to one accepted version and
  constrains the composition without becoming a self-hosting runtime.
- **Skills** materializes that composition through Spec Kit's public development-mode
  preset and extension lifecycle, so the host owns registration, template composition, command
  layering, and the active integration's skills.
- **The bootstrap** is a repository development script outside the installed extension, offering
  `propose`, `apply`, and `status`; its JSON interface is the feature's self-hosting contract.
- **The boundaries** are `contract.concorde.spec-kit-installation` (what the maintainer previews and
  approves) and `contract.concorde.spec-kit-platform` (the host behavior relied on).

## Logic

**From checkout to active, verified self-hosting**

1. **Propose**: validate the source boundary and active integration, compute a deterministic source
   digest, inspect current ownership, and write only the proposal file.
2. **Review and approve**: the maintainer sees source identity, compatibility, every owned path to
   create, update, or adopt, the preserved content classes, and the activation boundary.
3. **Apply**: recompute the proposal and reject any stale or changed review state; preflight the
   same components in an isolated project; snapshot the exact owned scope; install through Spec
   Kit; verify; then write the receipt atomically.
4. **Activate**: the result reports the reload or new-session boundary; only a fresh interaction
   counts as evidence that the change is in use.
5. **Refresh**: any authoritative change alters the digest and needs a new propose–review–apply
   cycle; a matching state returns unchanged.
6. **Verify**: `status` compares source, installed copies, registry, and surfaces against the receipt
   and reports activation separately; the quality gate fails while drift is unresolved.
7. **Recover**: a failure after mutation restores the snapshot in reverse order and suppresses the
   success receipt; incomplete restoration lists every residual path and its remediation.

**Rules the implementation must keep**

- A supported lifecycle installs the current trusted sources into this checkout, and the source set
  carries the same preset, extension, and bundle responsibilities as the distributed framework
  (FR-001, FR-003).
- Authoritative sources are distinct from materializations: no installed skill, command, template,
  runtime copy, catalog, generated diagram, or generated page is treated as source authority, and
  locally edited materializations are drift, never copied back (FR-002, FR-017).
- Initial bootstrap needs no Concorde command that exists only after setup (FR-004).
- No mutation before the maintainer approves a proposal naming source identity, compatibility, owned
  changes, preserved content classes, and the required activation step (FR-005).
- Self-hosting uses the supported Spec Kit component and active-integration lifecycle, never a
  second command registry or parallel workflow; a success materializes all and only the declared
  surfaces and records provenance binding them to the accepted source state and host compatibility
  (FR-006, FR-007, FR-008).
- Protocol v1 supports both Codex and Claude through the active integration's declared registry and
  surface model; collision checks, ownership, verification, drift, rollback, and receipt evidence
  follow that model while inactive-integration assets remain preserved (FR-023).
- Refresh is available after any source change, and repeating setup or refresh against unchanged
  sources is idempotent with no duplicated ownership, registration, command, skill, or template
  (FR-009, FR-010).
- A read-only freshness check compares the complete declared source set and expected
  materializations with the installation, reports source, materialization, registration,
  compatibility, and session activation separately, and turns every missing, stale, altered, extra,
  incompatible, or unverifiable state into a deterministic finding that blocks a current
  self-application claim (FR-011, FR-012, FR-013).
- A framework change counts as used only after it is refreshed and activated; without hot reload,
  the reload or new-session boundary is named and the running session is never assumed current
  (FR-014, FR-015).
- Project-authored content and unrelated integration assets are preserved unless an exact item is in
  the approved change; setup and refresh either activate the complete materialization or keep the
  prior usable state, reporting partial residue exactly and never as success (FR-016, FR-018).
- Status works with no selected workspace and changes neither selection nor an active attempt
  (FR-019).
- The self-hosted workflow stays behaviorally equivalent to installing the same components through
  Feature 003, apart from documented provenance and activation differences (FR-020).
- Quality gates detect unresolved drift whenever an improvement claims self-application, and every
  diagnostic names authority, expected state, observed state, lifecycle stage, and safe remediation
  without exposing unrelated file contents (FR-021, FR-022).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): the self-hosting
  boundary, four user stories, FR-001 to FR-023, and SC-001 to SC-009.
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md) (the
  bootstrap script, the proposal and receipt, the five evidence dimensions).
- **The contract** — `contracts/self-hosting.md` with its
  schema (`contracts/self-hosting.schema.json`) and examples
  (proposal (`contracts/examples/proposal.json`), applied result (`contracts/examples/applied-result.json`),
  current status (`contracts/examples/status-current.json`)); the crossed boundaries are
  [contract.concorde.spec-kit-installation](../../architecture/contracts/spec-kit-installation/contract.md) and
  [contract.concorde.spec-kit-platform](../../architecture/contracts/spec-kit-platform/contract.md).
- **The level this feature belongs to** — [module.md](../../module.md) (the root summary) and the
  modules that contribute: [Distribution](../../architecture/modules/distribution/module.md) and
  [Skills](../../architecture/modules/skills/module.md).
- **The neighbours** — the released path this feature mirrors:
  [Install and Set Up Concorde with Spec Kit](../003-installation/abstract.md); the workflow
  it activates: [Concorde Workflow](../001-concorde-workflow/abstract.md).
- **The maintainer guide** — [docs/self-hosting.md](../../../../docs/self-hosting.md).
