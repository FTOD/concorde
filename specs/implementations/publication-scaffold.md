```concorde-document
{
  "id": "document.implementation.publication-scaffold",
  "targets": [
    "implementation.publication-scaffold"
  ],
  "main_visible": false
}
```
# Publication Scaffold implementation

`implementation.publication-scaffold` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.views`.

## Responsibility

Realize exact docsite scaffold proposals and template application for a registered project.

## Bound files

- `src/concorde/autodocs/__init__.py`
- `src/concorde/autodocs/docsite_scaffold.py`
- `src/concorde/autodocs/docsite_template.py`
- `tests/concorde/autodocs/__init__.py`
- `tests/concorde/autodocs/integration/__init__.py`
- `tests/concorde/autodocs/integration/test_docsite_scaffold.py`
- `tests/concorde/autodocs/unit/__init__.py`
- `tests/concorde/autodocs/unit/test_docsite_template.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/autodocs/` | Produces exact docsite scaffold proposals and deploys the current Module/Implementation publishing template without reading code to infer architecture. |

## Implementation interfaces, dependencies and constraints

The scaffolder renders a complete proposed file set from supplied site identity, repository and deployment options. Application depends on the exact-file transaction boundary and checks current before-digests before accepting the site. The template includes the scoped publication plugin, locked Mermaid Markdown integration and candidate build/deployment entry points. It must not fetch or install an external diagram Skill, create architecture JSON from source code, or alter project Spec membership. Scaffold files stay separate from authored project contracts.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Scaffold tests cover preview immutability, deterministic proposed bytes, unsafe/stale destinations, preservation of unrelated content, failed final verification and a fresh project using inline Mermaid. Deployment template coverage must establish the complete Node dependency/build path without an external renderer installation step.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
