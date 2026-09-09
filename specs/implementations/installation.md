```concorde-document
{
  "id": "document.implementation.installation",
  "targets": [
    "implementation.installation"
  ],
  "main_visible": false
}
```
# Installation implementation

`implementation.installation` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.distribution`.

## Responsibility

Realize distribution entry points, receipt-owned installation and bounded root-guidance updates without replacing project-owned content.

## Bound files

- `capabilities/configure.py`
- `scripts/concorde.ps1`
- `scripts/concorde.py`
- `scripts/concorde.sh`
- `scripts/development/check-docsite-types.py`
- `scripts/install-concorde.py`
- `scripts/requirements.lock`
- `scripts/run-capability.py`
- `scripts/worktree-guard.py`
- `skills/concorde-configure/SKILL.md`
- `src/concorde/distribution/__init__.py`
- `src/concorde/distribution/protocol_guidance.py`
- `src/concorde/host/cli.py`
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
- `tests/concorde/distribution/unit/test_worktree_guard.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `scripts/install-concorde.py` | Plans and applies receipt-owned package and integration changes for Architecture Profile 9. |
| `scripts/concorde.py` | Exposes deterministic maintenance and developer CLI entry points. |
| `scripts/worktree-guard.py` | Decides Claude Code and Codex hook payloads for the source checkout, refusing native worktree creation in developer sessions. |
| `src/concorde/distribution/protocol_guidance.py` | Installs the explicit Protocol entry while preserving developer-owned root instructions. |
| `templates/` | Keeps entry links to the Protocol's Module, Implementation and Feature starters, plus Framework plan, task and reflection templates. |

## Implementation interfaces, dependencies and constraints

CLI wrappers normalize supported arguments and invoke deterministic package/install operations. The installer plans owned file changes and combines staged package assets with managed-runtime provisioning; protocol_guidance treats a marked block as the unit of ownership within a shared root file. It depends on package inventory/rendering, runtime acquisition and exact-file recovery. Receipts hash owned bytes, preserve unrelated text and modes, and reject malformed, modified or unowned blocks. Templates point to the independent Protocol starters; they are installation assets rather than new project Spec kinds. The worktree guard is a standard-library-only script so that a hook adds no import cost to every tool call; the checkout's `.claude/settings.json`, `.codex/hooks.json` and `.codex/rules/worktree.rules` invoke it and are agent-integration configuration outside any binding, and the installer's explicit script inventory leaves the guard out so consumers receive no hook.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Run installer and protocol-guidance cases for preview immutability, first install, update, integration switch, modified owned content, symlinks, absent-only defaults and rollback after provisioning failure. Fresh-clone and consumer end-to-end cases establish that installed paths and owned receipts agree, and that a fresh clone carries the worktree guard with its integration files. Guard cases cover refused and allowed events and commands, the process exit codes and outputs, and the registration in the checked-in Claude Code and Codex files.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
