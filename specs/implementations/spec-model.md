```concorde-document
{
  "id": "document.implementation.spec-model",
  "targets": [
    "implementation.spec-model"
  ],
  "main_visible": false
}
```

# Spec model implementation

`implementation.spec-model` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.spec`.

## Responsibility

Realize registry admission, selection and reverse indexes, deterministic structural validation, project initialization, the `concorde-init` capability and the package entry points.

## Bound files

- `capabilities/init.py`
- `skills/concorde-init/SKILL.md`
- `src/concorde/__init__.py`
- `src/concorde/__main__.py`
- `src/concorde/diagnostics.py`
- `src/concorde/model.py`
- `src/concorde/specification/__init__.py`
- `src/concorde/specification/initialize.py`
- `src/concorde/specification/repository.py`
- `src/concorde/specification/validation.py`
- `tests/__init__.py`
- `tests/concorde/__init__.py`
- `tests/concorde/specification/__init__.py`
- `tests/concorde/specification/support.py`
- `tests/concorde/specification/test_distribution.py`
- `tests/concorde/specification/test_module_architecture.py`
- `tests/concorde/specification/test_module_model.py`
- `tests/concorde/support/__init__.py`
- `tests/concorde/support/paths.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/specification/repository.py` | Admits Profile 9 configuration with its Protocol binding and registry schema 2; builds immutable `SpecTarget` and `ImplementationSpec` records, file ownership and implementation-user indexes; parses documents, dependency declarations and structured contracts. |
| `src/concorde/specification/validation.py` | Emits the `CONCORDE-*` structural findings for Modules, documents, dependencies, focus definitions, contracts, implementation bindings and Reflection attribution. |
| `src/concorde/specification/initialize.py` | Proposes and applies the initial configuration, registry, Module stub and Reflection defaults. |
| `capabilities/init.py`, `skills/concorde-init/SKILL.md` | The `concorde-init` lifecycle capability and its installed Skill. |
| `src/concorde/model.py`, `src/concorde/diagnostics.py` | `Finding` and `ToolResult` records, canonical result envelopes and exit codes. |
| `src/concorde/__init__.py`, `src/concorde/__main__.py` | Package version and the `python -m concorde` entry. |
| `tests/concorde/specification/` model and architecture suites, shared test support | Exercise admission, selection, validation, initialization and the self registry. |

## Implementation interfaces, dependencies and constraints

`SpecRepository` rejects unknown parents, composition cycles, self dependencies, unknown Implementation references, duplicate file owners and control, generated or Spec paths in bindings, and requires a shared provider's consumers to be its siblings. `validate_repository` verifies the structure the Protocol requires and never reports semantic completeness. Dependencies are the typed-value and schema evaluators, front matter parsing and the file-transaction helper for initialization.

Three gaps are recorded honestly. `spec_files` and `spec_pair` are specified in the Spec Module's registry document but not yet implemented. `initialize.py` still writes an external JSON diagram at `specs/modules/project/diagrams/overview.architecture.json` although the initialization contract requires an inline Mermaid stub with `diagrams: []`. `model.py` retains Profile 7 entity classes beyond `Finding` and `ToolResult` until the legacy package is removed.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Cases must cover duplicate and unresolved identities, composition cycles, non-sibling shared providers, membership mismatches between registry and document declarations, dependency blocks that disagree with `uses`, contract provider mismatches, unique file ownership, initialization with absent-only destinations and complete recovery, and the self registry of this repository.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
