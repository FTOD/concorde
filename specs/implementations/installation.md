```concorde-document
{
  "id": "document.specs.implementations.installation",
  "targets": [
    "implementation.installation"
  ],
  "main_visible": false
}
```

# Installation implementation

This Implementation Spec binds the exact files below. It is reused by `module.installation`.

## Responsibility

Install, initialize, configure and upgrade Concorde while preserving user-owned content. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `scripts/concorde.ps1`
- `scripts/concorde.py`
- `scripts/concorde.sh`
- `scripts/development/check-docsite-types.py`
- `scripts/install-concorde.py`
- `scripts/requirements.lock`
- `scripts/run-capability.py`
- `src/concorde/distribution/__init__.py`
- `src/concorde/distribution/protocol_guidance.py`
- `templates/feature-template.md`
- `templates/implementation-template.md`
- `templates/module-template.md`
- `templates/plan-template.md`
- `templates/reflections-template.md`
- `templates/tasks-template.md`
- `tests/concorde/distribution/__init__.py`
- `tests/concorde/distribution/acceptance/__init__.py`
- `tests/concorde/distribution/acceptance/test_consumer_install_end_to_end.py`
- `tests/concorde/distribution/acceptance/test_fresh_clone_bootstrap.py`
- `tests/concorde/distribution/contract/__init__.py`
- `tests/concorde/distribution/contract/test_manifests.py`
- `tests/concorde/distribution/integration/__init__.py`
- `tests/concorde/distribution/unit/__init__.py`
- `tests/concorde/distribution/unit/test_install_concorde.py`
- `tests/concorde/distribution/unit/test_protocol_guidance.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `scripts/install-concorde.py` | Plans and applies receipt-owned package and integration changes for Architecture Profile 9. |
| `scripts/concorde.py` | Exposes deterministic maintenance and developer CLI entry points. |
| `src/concorde/distribution/protocol_guidance.py` | Installs the explicit Protocol entry while preserving developer-owned root instructions. |
| `templates/` | Supplies Module, Implementation, feature and work-artifact authoring templates. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
