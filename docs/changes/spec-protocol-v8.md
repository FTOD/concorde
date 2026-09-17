# Spec Protocol 8 migration

Protocol 8.0.0 separates explanatory Module Specs from precise Implementation Specs inside one
complete Module-owned specification. This is a source-checkout migration, not an installer-side
conversion or a second compatible runtime.

## Language and compatibility

Every document unit now uses metadata schema 2 with exactly `document.id`, `document.owner` and
`document.role`. Roles are `module` and `implementation`, without a default. The unique `module.md`
entry and explanatory topics have role module. Formal requirements, scenarios and canonical
structured contracts are valid only in implementation-role companions. Both roles remain normative
human-readable content and contribute both source members to complete Module/scenario contexts.

The Views pilot's `concorde.publication` extension is retired. Python source admission and TypeScript
publication reject it, missing/unknown roles, schema-1 metadata, an implementation-role entry and
formal definitions in explanatory reading. Fenced examples stay opaque. Initialization emits an
honest schema-2 module-role draft; it invents no business acceptance cases. Author/reviewer prompts
and templates use the same boundary.

Protocol binding advances to 8.0.0 and new exact asset digests. Framework Profile 14, registry schema
5, source-resolution schema 1 and publication model/manifest 21 retain their independent meanings;
none requires a serialization change for this migration. The Framework package release number is
independent of the specification-language version. Consumer updates still require explicit migration
and acceptance rather than silent rebinding.

## Complete checkout migration

All 17 Modules now own requirements and scenarios directly, with subject headings as organization,
not another ownership hierarchy. There are 95 document units (190 source members): 53 explanatory
units and 42 precise-specification units. The collection contains 134 requirements, 193 scenarios,
183 entities and 3 canonical structured contracts. One new scenario specifies document-role
admission; existing IDs and Module owners remain stable.

For example, `spec/registry.md` remains a Registry explanation under Spec in Module Specs. Its formal
obligations move to `spec/requirements.md` and `spec/scenarios.md`; detailed query interfaces move to
`spec/contracts.md`. Views' Publication, Pipeline, Viewer and UA-export topics return to explanatory
reading rather than being moved wholesale into the detail tab. Canonical contracts and their local
participation anchors move together with their metadata declarations. References to split documents
explicitly include newly required units; whole-Module references retain their existing semantics.

The offline audit `python3 scripts/development/check-spec-v5.py --base f8796206` retains its historical
command path and checks current Protocol-8 admission, all registered pairs, links/anchors, manifest
binding and preservation of the baseline's 570 document/requirement/scenario/entity/contract IDs and
owners. It does not claim semantic completeness. Stable definition IDs do not redirect obsolete
external page fragments automatically; retained project links and Agent Flows navigation have been
reconciled to the new canonical locations.

## Verification

Run the deterministic checks on final bytes:

```bash
python3 scripts/concorde.py build --check
python3 scripts/concorde.py validate
python3 scripts/development/check-spec-v5.py --base f8796206
python3 scripts/development/run-tests.py -j 8
CONCORDE_PYTHON="$PWD/.venv/bin/python" npm --prefix docsite run check
```

Regression coverage includes strict role admission in both parsers, opaque examples, one-level paired
context resolution, scenario ownership, metadata-only invalidation, authoring/topology transactions,
fresh consumer scaffolding, complete Module navigation, stable anchors and production link checks.
The legacy inline-source preview now plans explicit Protocol-8 pairs and required registration work;
it remains read-only and never claims that mechanical splitting finishes semantic editing.
