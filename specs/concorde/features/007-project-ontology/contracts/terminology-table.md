# Concorde Terminology Table Profile 1

## Purpose

Define the human-readable and deterministically parseable local ontology declaration required in every maintained module, feature, and sub-feature `design.md`.

## Section

Each design contains exactly one second-level heading:

```markdown
## Terminology
```

The section contains either one terminology table or exactly this inherited-only declaration:

```text
No local terminology. This level uses inherited terminology unchanged.
```

## Table

The header is exact and ordered:

```markdown
| Term | Meaning | Relationships |
|---|---|---|
```

- **Term**: one backticked preferred expression, optionally followed by `<br>Aliases:` and a comma-separated list of backticked aliases.
- **Meaning**: non-empty prose that distinguishes the concept without relying on descendants or siblings.
- **Relationships**: `None` or semicolon-separated expressions of the form `` `predicate` → `Target term` ``.

Relationship targets use preferred terms or declared aliases visible locally or through the permitted ancestor chain. Predicates are lower-case verb phrases. A relationship does not create its target concept.

## Normalization

Remove Markdown code delimiters, apply Unicode case-folding, replace punctuation runs with a single space, collapse whitespace, and trim. Do not infer singular/plural, acronym, stemming, or synonym equivalence. Alternate expressions are equivalent only when declared as aliases.

## Identity and Inheritance

The qualified concept identity is `<defining-level-id>#<normalized-preferred-term>`. Modules inherit parent-module terminology. Features inherit the root-to-provider module chain. Sub-features inherit that module chain followed by their immediate parent feature. Descendants never load sibling or descendant declarations implicitly.

## Failure Semantics

Validation fails for a missing/malformed declaration, duplicate local expression, inherited redefinition, ambiguous visible alias, unresolved relationship target, empty meaning, or empty predicate. Findings name the current and defining levels and do not mutate maintained sources.

## Compatibility

Profile 1 is strict. Adding optional cell syntax is backward-compatible only when Profile 1 readers can ignore it without changing concept identity or relationship meaning. Changing headers, normalization, ancestry, identity, or relationship grammar requires a new profile version and migration.
