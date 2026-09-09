```concorde-document
{
  "id": "document.implementation.build",
  "targets": [
    "implementation.build"
  ],
  "main_visible": false
}
```

# Build implementation

`implementation.build` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.distribution`.

## Responsibility

Realize the `@include` prompt resolver, deterministic rendering of Agent instructions, Skills, Protocol assets, schemas, documentation inventories and the Studio graph configuration, the build manifest with its freshness check, and package validation.

## Bound files

- `agents/__init__.py`
- `capabilities/__init__.py`
- `concorde.json`
- `pyproject.toml`
- `src/concorde/host/build.py`
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
- `tests/concorde/support/build_fixture.py`
- `uv.lock`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/host/build.py` | Renders every output, writes owned projections, compares without writing, recomputes the Protocol manifest and verifies freshness. |
| `src/concorde/host/prompt_resolver.py` | Resolves `@include` graphs for Skills, Agent Specs and rule roots and reports unreachable prompts. |
| `src/concorde/host/package_validation.py` | Validates prompts, capability modules, Agents, exported contracts, Spec alignment and build outputs with stable `CONCORDE-*` rule ids. |
| `capabilities/__init__.py`, `agents/__init__.py` | The capability and Agent inventories the build and validator read. |
| `concorde.json`, `pyproject.toml`, `uv.lock` | Package manifest, development dependencies and lock. |
| `tests/concorde/fixtures/build/golden/` Skill projections, `tests/concorde/support/build_fixture.py`, build and validation unit suites | Expected rendered bytes and validator cases. |

## Implementation interfaces, dependencies and constraints

`build(project_root, integration)` renders into a `BuildResult`; `write_build` writes only owned generated locations; `check_build` renders into a temporary directory; `verify_fresh` compares recorded source digests; `load_agent` returns a rendered body with its binding. Package validation attributes its findings to `module.distribution`, requires exactly one registered `concorde-capabilities` block and one `concorde-agents` block across all Module documents, and requires the Development interfaces document to describe every exported type identity and host error code. Dependencies are the Agent model, typed contracts and front matter parsing. Generated assets under `generated/`, `.claude/skills/` and `.agents/skills/` are derived outputs and never authoring sources.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Build fixtures must show that a changed authored responsibility alters the expected rendered bytes without admitting unrelated instructions; validator cases must cover unreachable prompts, unknown identifiers, inventory drift, Harness widening, schema export drift, Spec-alignment block mismatches and stale outputs.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
