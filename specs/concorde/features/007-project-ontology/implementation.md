# Feature Implementation: Define Project Ontology

**Realization status**: Accepted implementation milestone (2026-09-01).

**Selected level**: Top-level feature provided by module.concorde.

## Realization Overview

Concorde realizes the project ontology as a maintained Markdown contract, deterministic validation, authoring guidance, self-applied terminology declarations, and a generated relationship view. Every current module, feature, and immediate sub-feature design contains one local terminology declaration. Descendants reuse terms from the permitted module and parent-feature ancestry without copying definitions.

The normalized representation is governed by <code>contract.concorde.ontology</code>, Concorde Terminology Table Profile 1, and its schema/example under this feature's <code>contracts/</code>. The project-wide semantic vocabulary remains in <code>docs/ontology.md</code>. Generated documentation and Archify HTML remain read models rather than ontology authorities.

## Module and Feature Collaboration

- **Skills** carries the authoring contract through the design template and the specify, clarify, fast-loop, initialization, and acceptance instructions. Installed Codex and Claude projections are generated from these canonical sources.
- **Scripts** implements deterministic parsing and validation in <code>extensions/concorde/runtime/concorde/validation/terminology.py</code> and registers it in the normal validation pipeline.
- **Workspace Files** supplies the canonical module/feature hierarchy, local design tables, feature contracts, attempt evidence, and the distinction between durable sources and generated projections.
- **Auto-Docs** preserves terminology tables as maintained page content, discovers the declared ontology diagram, validates routes and provenance, and publishes the generated view.
- **Distribution and self-hosting** materialize the canonical preset and extension into project-local Spec Kit, Codex, and Claude surfaces while preserving shared reflection-triage state.

The root module's summary, design reference, contract inventory, and level views continue to own the surrounding architecture. This feature owns the ontology behavior and its accepted realization.

## Scenario Realization

### Define a level's vocabulary

The composed feature design template requires an exact <code>Term | Meaning | Relationships</code> table or the exact inherited-only declaration. Initialization seeds a valid root vocabulary, and authoring guidance requires ontology reconciliation whenever a design changes. Concorde's thirty current design levels have been migrated to concise local declarations.

### Reuse ancestor terminology consistently

The validator builds ordered module ancestry for every module, adds the providing-module chain for a feature, and adds the immediate parent feature for a sub-feature. Preferred terms and aliases are normalized with Unicode compatibility normalization, case folding, punctuation-to-space conversion, and whitespace collapse. Local duplicates, inherited redefinitions, ambiguous visible aliases, unresolved relationship targets, malformed declarations, and empty semantic fields produce deterministic findings without changing sources. Unrelated branches retain distinct qualified identities even when they use the same surface word.

### Explore concept relationships

The maintained Archify architecture source at <code>specs/concorde/features/007-project-ontology/diagrams/concorde-ontology-model.json</code> visualizes levels, terminology tables, concepts, relationships, inheritance, and attempts. Its delivered HTML is published at <code>generated/architecture/concorde-ontology-model.html</code>. The diagram supplements the feature design, terminology tables, contracts, and project ontology; it does not define behavior independently.

## Durable Implementation Decisions

- Local-only terminology declarations are the maintained source. A descendant never copies an unchanged ancestor row.
- Concorde Terminology Table Profile 1 uses exact headers, backticked preferred expressions and aliases, and semicolon-separated typed relationship expressions.
- Qualified concept identity is the defining stable level ID plus the normalized preferred term.
- Normalization is deterministic and deliberately avoids stemming, synonym inference, and singular/plural guessing; alternate expressions are equivalent only through explicit aliases.
- Inheritance is bounded to ancestor modules, the providing module chain, and for a sub-feature its immediate parent feature. Siblings and descendants are never implicit inputs.
- The six ontology diagnostic families are a focused validator inside the existing non-mutating validation pipeline.
- Semantic completeness of the important-concept inventory remains a review responsibility; deterministic validation proves structure, identity, inheritance, and reference resolution.
- The feature maintains one core Archify architecture view with a hidden generic legend. Dynamic supplemental views are unnecessary for this stable structural model.
- Canonical preset and extension sources are authoritative; installed Spec Kit, Codex, and Claude surfaces are refreshed through the reviewed self-host workflow rather than patched directly.

## Traceability and Evidence

| Requirement area | Realization | Evidence |
|---|---|---|
| Local declarations, meanings, aliases, and table grammar (FR-001–FR-006) | Feature contract/profile, composed template, initialization seed, focused parser | Terminology unit tests, workflow contract tests, initialization and preset-composition tests |
| Bounded inheritance and consistency (FR-007–FR-011) | Ordered ancestry and expression indexes in the terminology validator | Module, feature, sub-feature, branch-local, conflict, ambiguity, and non-mutation tests |
| Authoring workflow (FR-012) | Specify, clarify, fast-loop, initialization, and acceptance guidance | Canonical-source contract tests and current Codex/Claude installed-surface verification |
| Ontology relationship view (FR-013–FR-015) | Maintained Archify source plus generated standalone HTML | 9/9 showcase checks, zero composition errors, zero warnings, source/artifact SHA-256 receipts |
| Publication (FR-016) | Auto-Docs registry, materialization, diagram delivery, route inventory, and production build | TypeScript typecheck, 19 docsite test files with 85 passing tests, 118-page validation, successful production build |
| Self-application (FR-017–FR-018) | Thirty maintained design tables, project ontology 1.2.0-draft, root contract registration | Full Concorde validation with zero findings and complete Python suite with 322 passing tests |
| Installed workflow freshness | Reviewed 0.6.0 self-host application for Codex and Claude | Current self-host status; matching source, installed bytes, registries, and active surfaces; both agent-asset verifications succeed |

The ontology diagram specification digest is <code>2232856ccad1745f3da8a465a23ae080cb60cf16ea822a6281e7d17b3d261e6f</code>; the delivered artifact digest is <code>308dd5391a1d0933ea3b4fc645ae93c145c6f687d26e855b20819f05c8354609</code>. Full project validation completed with no errors, warnings, or informational findings.

## Known Limitations

- Chrome or Chromium was unavailable, so automated desktop containment captures and human perceptual review of the delivered ontology diagram remain pending. Structural showcase validation is not presented as visual proof.
- Refreshed Codex and Claude instructions require a new agent session before they count as active runtime evidence.
- Deterministic validation cannot decide whether an author omitted a semantically important concept; reviewers remain responsible for that completeness judgment.
- The feature and ontology contract retain partial evidence status while visual review and session activation remain pending.
