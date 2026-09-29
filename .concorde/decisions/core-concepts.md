# Decision log: core-concepts

Goal: Rename the root-owned Shared vocabulary topic to Core concepts (core-concepts.md), keeping stable document and concept identities. Clarify that Concorde root module.md explains overall concept relationships and collaboration, while Core concepts provides focused detailed explanations and glossary.json remains the sole definition source. Review and reduce duplicated architectural narrative without changing behavior or Protocol. Update all affected references, glossary explanation paths, ownership declarations and registry; validate, build the docsite to verify publication, and deliver.

## Main-agent decisions

- User approved the name Core concepts and asked that overall concept relationships belong in the root Module. Rename both topic files to core-concepts.md(.json); preserve document.concorde.vocabulary as the stable document identity, as required by Protocol A1. Keep concept identities and definitions unchanged.
- Root module.md already explains the work levels, delegation and error flow; avoid repeating those narratives in the topic. Keep detailed concept explanations there, linking to root Design/Usage as needed. Keep the task within module.concorde; the Harness phrase "shared vocabulary" links to the Context glossary entry, not the renamed page, so it does not require a separate Module change.

## Task-session decisions and preparation

- Preserve `document.concorde.vocabulary` and all 15 root concept identities and definitions; change only their explanation paths. Rename both document members and regenerate the registry through Concorde, so ownership and publication follow the renamed reading path.
- Keep root Usage/Design responsible for the overall work levels, flow and Module collaborations. Make the Core concepts introduction explicit about focused explanations and the glossary as the sole definition source; remove repeated overview prose and keep per-link error details in the concept explanation. This is editorial consolidation without changes to promises, behavior or Protocol.
- Follow the main agent’s recorded choice to leave the Harness wording alone: its lowercase “shared vocabulary” is a term link to the unchanged Context glossary entry, not a link to the renamed document. Historical evidence and the task goal also remain unchanged.
- Preparation probe returned exit 2 because `.venv`, `docsite/node_modules` and the guessed `.concorde/project.json` path were absent. Created dependencies using the prescribed commands; no source defect was indicated.
- `uv sync --locked --group dev` succeeded with a hardlink fallback warning; copying is sufficient. `npm --prefix docsite ci` succeeded with upstream deprecation notices and 31 audit findings (1 low, 25 moderate, 5 high). Dependency updates are outside this documentation task; retain the lockfile. Initial Concorde build succeeded.

## Verification before delivery

- Regenerated the registry with `registry --write`; only `module.concorde` changed. Concorde `build --check` and `spec-validation` pass on the final sources with zero findings. `git diff --check` and staged whitespace checks pass. Existing Spec Markdown layout is retained; no Python, TypeScript, JavaScript or Markdown under `docs/` changed.
- `npm --prefix docsite run build` succeeded and promoted the verified publication candidate. Docusaurus could not check for updates in the protected user config store; this optional update notification did not affect the build and no permission change is needed.
- Checked the published page title and route `/specs/concorde/core-concepts`, stable `document.concorde.vocabulary` anchor, all 15 concept anchors, root navigation and all 15 glossary explanation links. The old page is absent. A direct comparison confirms topic metadata is byte-for-byte unchanged, every concept definition and identity is unchanged, and only the root-owned explanation paths changed.
- Full required suite on the final sources: `.venv/bin/python -m pytest` — 642 passed, 4 skipped, 19.39 seconds. No new tests were added for the editorial change; structural validation and real publication cover the rename.
- Reviewed the staged diff: six changed files including the two-member document rename; Protocol, requirements, scenarios, contracts and implementation are untouched.

- First `task-validation` invocation was interrupted by the Bash tool's 300-second timeout. Run `r-20260928T163919-task_validation-c5b5a4b4` saved only `status.json`, at `run_configured_checks`, and returned no result or error chain. `task show` reports no workspace lock holder. The configured root check itself permits 300 seconds, so the outer limit was too short to obtain a complete result; retry in the foreground with 900 seconds to let the configured checks report their own outcomes. The untracked `.claude/agents` and `.claude/commands` are sandbox character-device placeholders, not project files.

- Retried task validation completed successfully: `r-20260928T164501-task_validation-f4542d92`, ready, all 23 configured checks passed, zero blocking findings, warnings or confirmations. It took about 321 seconds, explaining the earlier outer timeout. Use the same 900-second outer budget for Delivery, which repeats readiness itself.

- Delivery succeeded: run `r-20260928T165036-delivery-b910ce33`, commit `3bacd35e659419c2b2df72c5089599834dc620cc`, evidence `.concorde/evidence/core-concepts/1.json`. All 23 configured checks passed again; no blocking findings, warnings or confirmations. Delivery explicitly records that no code changed. The verified editorial commit is `fb79b1694bef1ce13e832e3a34e027b65020fcd9`. Final Git status has only the sandbox’s protected-file placeholders and no remaining project changes. Merge remains the main agent’s step.

## Main-agent delivery review

- Inspected delivered commit 3bacd35e659419c2b2df72c5089599834dc620cc, final source diff and evidence bundle. The six source/registry files match the approved documentation reorganization, and the additional file is the Delivery evidence bundle. All 23 configured checks passed with zero warnings; the interrupted initial validation is explicitly recorded as interrupted in the bundle and was superseded by successful validation and delivery. Primary worktree is clean and the final diff has no whitespace errors. Proceed with the prescribed checked merge.

## Closed: merged, 2026-09-28T17:04:22Z

- Checked merge succeeded at 6ed417a42f684ad5b16e0ea5f95e4c5bc24baa78. Both primary-worktree checks (build and spec-validation) passed, merge returned no warnings, and the task closed as merged with its worktree removed.
