# Concorde Development Self-Hosting Contract

## Purpose

Provide a reviewable, offline boundary through which the trusted current Concorde preset, extension,
and bundle composition becomes the active framework materialization used by this same checkout.

## Representation

Proposals, results, and freshness status use custom JSON conforming to
`self-hosting.schema.json`. JSON is inspectable by maintainers, portable across the bootstrap process
and tests, and deterministic after key/path ordering. Examples are maintained under `examples/`.

## Information Passed

- Operation/protocol version, feature target, and active integration.
- Component identities, versions, priority, compatibility, and source digest.
- Exact owned changes and explicitly preserved content classes.
- Proposal/receipt paths and installed-copy, registry, surface, and activation evidence.
- Findings with expected/observed state, lifecycle stage, and remediation.

## Obligations

- `status` is read-only; `propose` writes only its canonical machine-local proposal.
- Paths are project-relative, slash-normalized, non-parent, and resolve inside the checkout without
  symlink traversal, except that a declared Claude extension skill may use Spec Kit's canonical
  relative development link into the installed Concorde extension cache. That link must resolve to
  the exact expected regular file inside the checkout; other links remain invalid.
- Proposal arrays and inventories are sorted and duplicate-free.
- Apply accepts only the canonical proposal, rechecks every digest, and rejects stale review.
- Apply preflights the same components and integration before real mutation.
- Mutation is limited to Spec Kit-owned Concorde state, declared integration surfaces, and receipt.
- Project sources and unrelated agent assets remain excluded unless separately and exactly approved.
- Installed copies never flow back into authoritative sources.
- Session activation remains independent and is never inferred from equal on-disk bytes.
- Failure restores prior scoped state or reports every residual disagreement without success.

## Failure Semantics

Unsupported hosts, unsafe sources, incompatible identities, unknown integrations, collisions,
malformed proposals, wrong targets/paths, and stale digests return `invalid` before mutation.
Preflight failure returns `failed` without real mutation. Apply failure returns `rolled_back` after
exact restoration or `failed` with residual findings. Status reports `drift`, `absent`, or `unknown`
rather than mutating or guessing.

## Compatibility

Version 1 supports Spec Kit `>=0.16.4,<0.16.5` with either the Codex or Claude skills integration
selected in `.specify/integration.json`. Another host range or integration requires isolated
lifecycle, rollback, surface, and activation evidence before support is claimed.

## Evidence

Examples validate against the schema. Unit tests cover deterministic safety; integration tests cover
public development installation and rollback; acceptance tests cover checkout self-application and
preservation. Diagram/docsite checks prove the explanation is fresh, not runtime correctness.
