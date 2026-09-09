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

`implementation.package-build` follows Spec Protocol 2.0.0 and binds the exact files below. It is reused by `module.installation`, `module.package-assets`.

## Responsibility

Realize deterministic source inclusion, public Skill adapters, runtime projections and package inventories for checkout distribution and installation.

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

## Implementation interfaces, dependencies and constraints

build returns rendered outputs; write_build replaces only owned projections; check_build compares a fresh render without changing sources. The include resolver depends on explicit Agent/Skill roots, Protocol adapters and capability declarations; layering, cycles, diamond inclusion and unreachable sources fail admission. Manifest source digests bind load_agent/verify_fresh. The package inventory, dependency locks and golden fixtures support distribution compatibility. Inline Spec diagrams are Markdown publication inputs and do not require a renderer Skill or diagram-rendering branch in the instruction build.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Use build, prompt-resolver and package-validation tests for byte-identical repeat rendering, both integrations, include errors, stale-source detection and owned-output cleanup. Consumer installation and source-worktree cases verify that the same build can serve its two using Modules without writing another worktree’s projections.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
