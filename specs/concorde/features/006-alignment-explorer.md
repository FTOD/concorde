---
id: feature.concorde.explore-alignment
kind: feature
module: module.concorde
related_features:
  - feature.concorde.define-project-ontology
interfaces:
  provided:
    - contract.concorde.alignment-explorer
  required:
    - contract.understand-anything.knowledge-graph
    - contract.runtime.tools
evidence_status: verified
evidence:
  - kind: implementation
    target: src/concorde/alignment.py
    status: verified
    producer: concorde
  - kind: test
    target: tests/concorde/integration/test_alignment_explorer.py
    status: verified
    producer: unittest
  - kind: test
    target: tests/concorde/acceptance/test_alignment_explorer_journey.py
    status: verified
    producer: unittest
---

# Feature Design: Alignment Explorer

## Outcome and Scope

A maintainer can use one deterministic read-only Tool to browse bounded
module/entity/feature/interface architecture beside optional Understand Anything implementation-graph
subjects and inspect explicit evidence-qualified alignments, unknowns, and disagreements.

The explorer validates and projects maintained inputs; it does not scan code, generate a UA graph,
persist an index, mutate either source, infer mappings from names/similarity, or provide an interactive
browser UI.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.concorde.cli` | Dispatches native `explore` target, graph, alignment, revision, query, and status options. |
| `entity.concorde.alignment-explorer` | Validates inputs, projects bounded subjects, qualifies evidence, filters results, and serializes one canonical Tool result. |
| `entity.concorde.understand-anything` | Supplies the optional pinned implementation knowledge-graph nodes and directed edges. |
| `entity.concorde.specification` | Supplies validated Profile 7 module architecture and direct feature-interface truth. |

## Interfaces

### `contract.concorde.alignment-explorer` — Evidence-qualified architecture exploration

- **Consumer**: Maintainer, CI, or coding agent exploring architecture and specification-to-code agreement.
- **Direction**: Validated specification plus optional implementation graph and explicit alignment evidence to one bounded read-only JSON result.
- **Entry points**: `scripts/concorde.py --project-root <root> explore [stable-id]`; importable `concorde.alignment.explore_alignment`.
- **Inputs**: Optional safe project-relative `--graph` containing the pinned formal UA model; optional schema-1 `--alignment` sidecar containing `implementation_revision` and unique records with `subject_id`, requested status, basis, implementation/evidence node IDs, finding IDs, and rationale; optional expected `--revision`, case-insensitive `--query`, and repeatable effective `--status` filters. The target defaults to the configured root module.
- **Outputs**: Canonical architecture-service envelope 2 with a `tool` discriminator whose result
  carries Profile 7/source digest/target, pinned upstream and graph provenance, revision freshness,
  bounded specification subjects/relationships/interactions, mapped or text-matched UA nodes plus
  one-hop edges and filtered layers/tour, total/returned counts, and Alignment Schema 1 records/summary
  in unknown, partial, verified, or disagrees states.
- **Obligations**: Preserve Concorde stable identity/ownership/path/Profile kind separately from UA adapter node/edge metadata; preserve accepted upstream IDs/types/directions; validate Profile 7 before projection; require explicit current evidence; never infer verification from names, paths, similarity, or adapter types; emit no output file or source mutation.
- **Failures**: Invalid target, unsafe/symlinked/unreadable JSON, unsupported pinned type, malformed collection, duplicate/dangling ID, unknown subject/node, or malformed sidecar returns findings and an invalid result while keeping projected alignment unknown. Missing graph/sidecar, absent expected revision, revision mismatch, candidate-only basis, or insufficient evidence returns informational/warning findings and unknown effective state rather than invented agreement/disagreement.
- **Compatibility**: Result and sidecar use Alignment Schema 1; the Tool envelope uses schema 2;
  source uses Profile 7; UA compatibility is pinned to
  `Egonex-AI/Understand-Anything@ba450c43425f3de6d43daf76526950ad8ca93536` with 27 node and 38 edge
  types. `explore` is a native Runtime Tool, not a leaf Skill or LangGraph Operation.
- **Implementing entities**: `entity.concorde.cli`, `entity.concorde.alignment-explorer`.
- **Example**: `python3 scripts/concorde.py --project-root . explore feature.example.checkout --graph .ua/knowledge-graph.json --alignment evidence/alignment.json --revision <commit> --status verified` returns only effectively verified bounded subjects and their relevant implementation neighborhood.

### `contract.understand-anything.knowledge-graph` — Required implementation graph

- **Provider**: `external:Egonex-AI/Understand-Anything@ba450c43425f3de6d43daf76526950ad8ca93536`.
- **Consumer**: Alignment Explorer adapter and ontology comparison.
- **Direction**: Read-only graph input to evidence-qualified Concorde projection.
- **Entry points**: An explicitly supplied project-relative UA Graph JSON conforming to the pinned formal `types.ts`/`schema.ts` model.
- **Inputs**: Version; optional graph kind; project name/languages/frameworks/description/analyzedAt/gitCommitHash; nodes; directed edges; layers; and tour steps.
- **Outputs**: Strictly validated implementation subjects/relations retaining upstream IDs, node types, edge types, directions, metadata, graph version, analyzed time, and implementation revision.
- **Obligations**: Preserve upstream representation and provenance, reject duplicate/dangling IDs, never auto-fix evidence, and never reinterpret a flat layer or path as Concorde module containment/identity.
- **Failures**: Invalid JSON/schema/reference, unsupported pinned type, missing revision, unsafe path, or stale input yields findings and unknown effective alignment state.
- **Compatibility**: The pinned formal model has 27 node and 38 edge types; aliases, auto-fix behavior, current-main drift, and narrative counts are non-authoritative. Extra accepted node metadata is preserved but supplies no implicit alignment.
- **Implementing entities**: `entity.concorde.understand-anything`, `entity.concorde.alignment-explorer`.
- **Example**: A UA shell-script scanner output remains a `file` node; a separate explicit sidecar may correlate it with a Concorde `script` entity while both identities and types remain visible.

## Usage Scenarios

1. Invoke `explore` for a module or feature without a graph and browse bounded Profile subjects whose alignment records are truthfully unknown.
2. Supply a pinned graph, explicit sidecar, and matching expected revision; inspect only claims qualified by their basis/evidence, while stale, candidate-only, or insufficient claims become unknown.
3. Search specification and implementation text or filter effective statuses; receive matching bounded subjects plus mapped/text-matched implementation nodes and exactly one directed-edge neighborhood, with totals disclosing omitted graph content.

## Requirements

- **FR-001**: Every projected Concorde subject MUST retain stable ID, owning or declaring module/feature, canonical path, Profile 7 kind, and separate adapter type.
- **FR-002**: UA representation type/edge MUST remain adapter metadata and MUST NOT assert identity/equivalence.
- **FR-003**: Alignments MUST name their evidence basis, implementation revision, freshness, bounded status, referenced nodes/findings, and rationale; names/similarity alone cannot verify.
- **FR-004**: Missing, stale, unsafe, malformed, incompatible, ambiguous, or insufficient input MUST yield findings and unknown effective state rather than invented agreement or disagreement.
- **FR-005**: Exploration MUST be read-only, deterministic, target-bounded, query-bounded, and reproducible from validated maintained/executable inputs with stable ordering and total/returned counts.
- **FR-006**: Distribution MUST expose the implemented `explore` surface as a native Tool and MUST NOT
  classify it as a leaf Skill or Operation without adding the corresponding canonical capability.

## Edge Cases

- A physical file defines multiple logical services/schemas; one explicit UA node may correlate with several distinct Concorde subjects without becoming any of them.
- Unrelated modules reuse a label but retain different stable entity identities; text search never creates a mapping.
- A sidecar requests verified status but has no executable-evidence basis/evidence node; effective status is unknown.
- A deterministic finding may establish disagreement only at the exact current revision and with at least one explicit finding ID.
- A graph is valid but no sidecar is supplied; graph subjects can be text-searched while all Concorde alignments remain unknown.
- A query matches a child-internal implementation label outside the selected Profile altitude; it cannot introduce an unprojected Concorde subject.
- An input layer/tour contains returned and omitted nodes; the result preserves the view only with its returned node IDs.
