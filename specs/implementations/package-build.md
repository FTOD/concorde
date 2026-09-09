```concorde-document
{
  "id": "document.specs.implementations.package-build",
  "targets": [
    "implementation.package-build"
  ],
  "main_visible": false
}
```

# Package Build implementation

This Implementation Spec binds the exact files below. It is reused by `module.installation`, `module.package-assets`.

## Responsibility

Install, initialize, configure and upgrade Concorde while preserving user-owned content. Build deterministic Agent, Skill, Protocol, schema and documentation assets from authored sources. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `agents/__init__.py`
- `capabilities/__init__.py`
- `concorde.json`
- `prompts/workflow-host/dev-loop-flags.md`
- `prompts/workflow-host/gap-reporting.md`
- `prompts/workflow-host/host-bound-invocation.md`
- `prompts/workflow-host/init-request-and-no-flags.md`
- `prompts/workflow-host/invoke-capability-opener.md`
- `prompts/workflow-host/lifecycle-no-cognition.md`
- `prompts/workflow-host/loop-completion-and-reviews.md`
- `prompts/workflow-host/loop-task-request-fields.md`
- `prompts/workflow-host/main-may-inspect.md`
- `prompts/workflow-host/review-scope-and-result.md`
- `prompts/workflow-host/stdin-invocation-config-input.md`
- `prompts/workflow-host/stdin-invocation-open.md`
- `prompts/workflow-host/target-identity-opener.md`
- `prompts/workflow-host/task-request-fields.md`
- `prompts/workflow-host/worktree-handoff.md`
- `pyproject.toml`
- `skills/concorde-configure/SKILL.md`
- `skills/concorde-deliver/SKILL.md`
- `skills/concorde-dev-loop/SKILL.md`
- `skills/concorde-init/SKILL.md`
- `skills/concorde-main/SKILL.md`
- `skills/concorde-reflections-triage/SKILL.md`
- `skills/concorde-validate/SKILL.md`
- `src/concorde/host/build.py`
- `src/concorde/host/effects.py`
- `src/concorde/host/package_validation.py`
- `src/concorde/host/prompt_resolver.py`
- `tests/concorde/fixtures/build/golden/claude/concorde-configure/SKILL.md`
- `tests/concorde/fixtures/build/golden/claude/concorde-deliver/SKILL.md`
- `tests/concorde/fixtures/build/golden/claude/concorde-dev-loop/SKILL.md`
- `tests/concorde/fixtures/build/golden/claude/concorde-init/SKILL.md`
- `tests/concorde/fixtures/build/golden/claude/concorde-main/SKILL.md`
- `tests/concorde/fixtures/build/golden/claude/concorde-reflections-triage/SKILL.md`
- `tests/concorde/fixtures/build/golden/claude/concorde-validate/SKILL.md`
- `tests/concorde/fixtures/build/golden/codex/concorde-configure/SKILL.md`
- `tests/concorde/fixtures/build/golden/codex/concorde-deliver/SKILL.md`
- `tests/concorde/fixtures/build/golden/codex/concorde-dev-loop/SKILL.md`
- `tests/concorde/fixtures/build/golden/codex/concorde-init/SKILL.md`
- `tests/concorde/fixtures/build/golden/codex/concorde-main/SKILL.md`
- `tests/concorde/fixtures/build/golden/codex/concorde-reflections-triage/SKILL.md`
- `tests/concorde/fixtures/build/golden/codex/concorde-validate/SKILL.md`
- `tests/concorde/host/unit/test_build.py`
- `tests/concorde/host/unit/test_package_validation.py`
- `tests/concorde/host/unit/test_prompt_resolver.py`
- `uv.lock`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/host/build.py` | Renders deterministic Module/Implementation rule, Agent, Skill, schema and documentation projections and records source digests. |
| `src/concorde/host/prompt_resolver.py` | Resolves declared instruction includes and rejects unreachable or invalid source composition. |
| `src/concorde/host/package_validation.py` | Checks package contracts and build consistency against the current model. |
| `skills/` | Defines the installed public adapters; generated projections are not authoring files. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
