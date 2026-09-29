# Decision log: entry-stubs

Goal: Make the initialize and scaffold entry stubs follow Protocol 15.1's recommended order instead of Purpose/Usage/Design, and restructure the Spec core and Scaffold entries the same way

## Brief (main agent, 2026-09-30)

### Why
The developer found Module entries hard to read: a mandatory Purpose / Usage / Design skeleton put
entry-point walk-throughs first and split "what the system is" from "why", burying the core ideas;
sequence diagrams felt heavy. Task `entry-structure` (merged as `090c764b`) changed the Spec
Protocol to 15.1.0 accordingly and rewrote the root entry `specs/concorde/module.md` as the model
to follow. The developer then asked that **every** Module entry be restructured the same way; this
task does the entries of the Modules it is bound to.

### The rules (read `protocol/module.md` "The entry" and `protocol/migration.md` "Version 15.1")
- No section is required; the whole entry is the design. Follow the recommended order:
  1. **Purpose** — short plain prose.
  2. **Core concepts** — the Module's own terms explained at their glossary anchors
     (`<a id="concept.…">`), other Modules' terms linked. Omit the heading when the Module owns no
     concept worth explaining.
  3. **Overview** — diagrams of the main structure, functions and flows, each with short prose.
  4. **Details** — headings of your choice: parts, collaborations with children and providers (at
     the `contains`/`uses` meaning anchors), entry points and commands, errors, design reasons.
- Command-level walk-throughs belong to the Module that owns the commands (so they stay in your
  Module if it owns them), but after the concepts and overview, never as the opening.
- Every process is a **workflow diagram** by default (lanes per participant when useful); a
  sequence diagram only when the interleaving of messages is itself the point. Convert any
  `shape: sequence_diagram` in your entries unless that exception clearly applies (log why).
- Render every D2 diagram you add or change and look at it before keeping it.
- The reader requirements of `protocol/module.md` still hold.

### Task-specific: the stubs
`entry-structure` left the generated stubs on the old skeleton:
- `src/concorde/spec/initialize.py` `initial_module_text` writes `## Purpose / ## Usage / ## Design`.
- The scaffold stub, `req.scaffold.stub-unspecified` ("SHALL say in its Usage and Design
  sections"), and `parent_reading`, which appends children under the root stub's `## Design`.
Change both so a generated entry follows the recommended order (e.g. Purpose, then a section
stating what is not yet specified, then where children are listed), keeping an honest statement of
what is unknown. Changing only one would make the scaffold add a second section, so change them
together, consistently. This DOES change promises of Spec core and Scaffold (the stub wording and
`req.scaffold.stub-unspecified`); that is in scope — update their requirements, scenarios and tests.
The spec-review sample finding texts like "Usage names the retry limit…" belong to Spec review and
stay. Then restructure the two entries themselves (`spec-tooling/spec/module.md`,
`execution/commands/scaffold/module.md`) under the rules above without other changes of meaning.

### Constraints
- Apart from the stub change above, this is a reorganization: no other promise, requirement, scenario,
  contract or behaviour changes. Tighten prose and remove repetition where it is safe; when you find
  a real error or gap, do not fix it here — log it and report it.
- Keep **every anchor id** stable (`concept.…`, `realization.…`, `contains-…`, `uses-…` and any
  heading slug that other documents link to — grep `specs/` for `<entry path>#` before renaming a
  heading). If a heading must be renamed, add an explicit `<a id="old-slug"></a>`.
- Edit only the documents and code of your bound Modules. Do not change `specs/concorde/glossary.json`
  definitions. Several restructuring tasks run in parallel on disjoint Modules.
- Run `python3 scripts/concorde.py build` and `spec-validation`, then `task-validation` and
  `delivery` in the task worktree, and report to the main agent with a one-paragraph summary per
  entry (new structure, diagrams converted, anything logged).

## Task session decisions (2026-09-30)

- **Stub layout.** Both generated stubs now read Purpose → `## Not yet specified` → `## Parts`
  (a scaffolded child adds `## Collaborations` after Parts for its proposed `uses`). "Not yet
  specified" stands where the recommended order puts core concepts and overview, and says the core
  concepts, behaviour and design are unknown (the root stub keeps its glossary sentence there).
  Parts holds the realizations and is where the scaffold appends the children's `contains`
  paragraphs (`parent_reading` now looks for `## Parts`, falling back to appending one). Reason:
  the recommended order, one section per question, honest unknowns before parts.
- **Wording kept on purpose.** The sentence "How <title> is used is not specified yet: …" is kept
  verbatim in the child stub, because Adoption's and the root's acceptance tests (other Modules)
  replace that exact sentence to simulate `code_to_spec`; changing it would silently weaken those
  tests. No file of another Module was edited.
- **Promises changed (in scope per brief).** `req.scaffold.stub-unspecified` now names the Not yet
  specified section after Purpose and the following Parts/Collaborations sections;
  `scenario.scaffold.creates` says the children's paragraphs land at the end of the parent's Parts;
  Spec core's initialization contract (which still said "the three required sections", stale
  since 15.1) now names Purpose / Not yet specified / Parts; `scenario.spec.propose-initialization`
  gains "its sections are Purpose, Not yet specified and Parts, in that order".
  `req.spec.init-honest-stub` unchanged (still true). Tests assert the section order.
- **Spec core entry.** Purpose; Core concepts (five subsections at the existing concept anchors:
  loaded Specs, structural checks, boundary sets and impact, grants, typed values and file
  transactions); Overview (the checked parts diagram, unchanged, plus a new illustrative workflow
  "how a Spec change reaches a worker"); Entry points (command list, then the worked example);
  Parts (component view and realization list, anchors unchanged); Why it is built this way
  (loading, boundaries and grants with the grant-order workflow, validation, typed values and file
  transactions, initialization with its workflow, Protocol text, its place among the Modules). No
  sequence diagram existed. Grant facts that had been split between Usage and Design (glossary
  writable, shared-file refusal, installed files) are merged under "Boundaries and grants".
- **Scaffold entry.** Purpose; no Core concepts heading (Scaffold owns no concept); Overview with
  two new illustrative diagrams (survey → proposal → scaffold → code_to_spec workflow; before/after
  of the parent's bindings); Running the command; What it writes; Results and errors; Why a
  deterministic command; Narrowing the parent; The Scaffold command (realization, step table,
  files); The Modules it relies on (`uses-*` anchors unchanged). No sequence diagram existed.
  "stated in the Design above" now links to #narrowing-the-parent. No heading slug of either
  entry was linked from elsewhere (grepped), so no compatibility anchors were needed.
- **Logged, not fixed.** Spec core's entry still says the grant does not mark pending entries and
  "whether it should is not settled" — an open design question carried over unchanged.
- **Non-ok result: task-validation `r-20260929T181245-task_validation-43578159` blocked.** The only
  blocking item is `check.views.repository-regressions` (module.views, exit 1):
  `docsite/tests/repository/fresh-project-scaffold.test.ts:284-290` expects the fresh project's
  rendered root page to contain `id="usage"` and `id="design"` in that order, which the new stub
  (Purpose / Not yet specified / Parts) no longer has. Every other check passed; the full pytest
  suite passes (788 passed, 4 skipped). The file is bound by module.views, outside this task's
  Modules, so it is escalated rather than edited. Proposed fix: expect `id="not-yet-specified"`
  before `id="parts"` instead (and drop the duplicated pair of assertions).

## Escalated to the main agent, 2026-09-29T18:19:08Z

- **task-session** task session (task entry-stubs): `views_test_asserts_old_stub`
  task-validation is blocked only by check.views.repository-regressions: docsite/tests/repository/fresh-project-scaffold.test.ts lines 284-290 assert that a freshly initialized project's rendered root page has id="usage" before id="design". The task's in-scope change of the initial stub (now Purpose / Not yet specified / Parts, per the brief) removes those headings, so the assertion must follow. The fix is mechanical: expect id="not-yet-specified" before id="parts" (and drop the duplicated usage/design pair). Everything else is done and verified: build, spec-validation success with no finding, full pytest 788 passed, both entries restructured and committed (56b764cb, c0f548ba).
  Not handled here (scope): The test file is bound by module.views, which is not among this task's Modules (module.spec, module.scaffold); the brief says to edit only the bound Modules' documents and code, and parallel restructuring tasks may be editing module.views.
  Options: Add module.views to this task (or authorize this one test edit) and I update the assertion here, then deliver; Fix the Views test in a separate task merged before this one
  Recommendation: Authorize the one-line test edit in this task: it is a direct consequence of the stub change the brief asked for, and delivering without it would leave main with a failing check
  Caused by:
  - **command** Command task-validation r-20260929T181245-task_validation-43578159 (workspace entry-stubs): `not_deliverable`
    workspace entry-stubs is not deliverable: 1 blocking finding(s), each a cause below; delivery, which decides the same readiness again, refuses the workspace until they are repaired (readiness in /home/zhenyu/concorde/.concorde/tasks/entry-stubs/workspace/runs/r-20260929T181245-task_validation-43578159/readiness.json)
    Not handled here (decision): task-validation only decides readiness and never repairs; each finding needs a Spec change (specify) or a code change (implement), which the task level chooses
    Evidence (blocking): check.views.repository-regressions module.views check failed (exit 1); log /home/zhenyu/concorde/.concorde/tasks/entry-stubs/workspace/runs/r-20260929T181245-task_validation-43578159/checks/check.views.repository-regressions/output.log
    Options: repair each blocking finding in the workspace and run task-validation again; run specify for a Spec finding, implement for a code or check finding
    Recommendation: repair the first blocking finding: check check.views.repository-regressions: module.views check failed (exit 1); log /home/zhenyu/concorde/.concorde/tasks/entry-stubs/workspace/runs/r-20260929T181245-task_validation-43578159/checks/check.views.repository-regressions/output.log
    Caused by:
    - **check** check.views.repository-regressions: `check_failed`
      the configured check check.views.repository-regressions of module.views failed with exit code 1; its log /home/zhenyu/concorde/.concorde/tasks/entry-stubs/workspace/runs/r-20260929T181245-task_validation-43578159/checks/check.views.repository-regressions/output.log ends with:
      | itle="Direct link to Not yet specified" translate="no">​</a></h2>[39m
      | [31m+ <p>The project&#x27;s core concepts are not specified yet. This Module declares the project&#x27;s[39m
      | [31m+ glossary, where every term of the project will be defined once; no term has been defined[39m
      | [31m+ yet.</p>[39m
      | [31m+ <p>How the project is used is not specified yet: its entry points, inputs, results, effects,[39m
      | [31m+ errors and repeat behaviour are unknown. Do not infer them from existing code.</p>[39m
      | [31m+ <p>The project&#x27;s decomposition, state, control flow and design reasons are not specified yet.</p>[39m
      | [31m+ <h2 class="anchor anchorTargetStickyNavbar_P4mg" id="parts">Parts<a href="#parts" class="hash-link" aria-label="Direct link to Parts" title="Direct link to Parts" translate="no">​</a></h2>[39m
      | [31m+ <p>The project&#x27;s parts and their collaborations are not specified yet. This Module contains,[39m
      | [31m+ uses and includes nothing, and no requirement or scenario has been written.</p>[39m
      | [31m+ <p>No realization binds implementation files yet.</p></div></article><nav class="docusaurus-mt-lg pagination-nav" aria-label="Docs pages"><a class="pagination-nav__link pagination-nav__link--next" href="/specs/project/glossary"><div class="pagination-nav__sublabel">Next</div><div class="pagination-nav__label">Glossary</div></a></nav></div></div><div class="col col--3"><div class="tableOfContents_ktwR thin-scrollbar theme-doc-toc-desktop"><ul class="table-of-contents table-of-contents__left-border"><li><a href="#purpose" class="table-of-contents__link toc-highlight">Purpose</a></li><li><a href="#not-yet-specified" class="table-of-contents__link toc-highlight">Not yet specified</a></li><li><a href="#parts" class="table-of-contents__link toc-highlight">Parts</a></li></ul></div></div></div></div></main></div></div></div><footer class="theme-layout-footer footer footer--dark"><div class="container container-fluid"><div class="footer__bottom text--center"><div class="footer__copyright">Atlas project documentation · 2026</div></div></div></footer></div>[39m
      | [31m+ </body>[39m
      | [31m+ </html>[39m
      | 
      | [36m [2m❯[22m tests/repository/fresh-project-scaffold.test.ts:[2m284:22[22m[39m
      |     [90m282|[39m     [34mexpect[39m(mainPage)[33m.[39mnot[33m.[39m[34mtoContain[39m([32m'id="requirements"'[39m)[33m;[39m
      |     [90m283|[39m     [34mexpect[39m(mainPage)[33m.[39mnot[33m.[39m[34mtoContain[39m([32m'id="scenarios"'[39m)[33m;[39m
      |     [90m284|[39m     [34mexpect[39m(mainPage)[33m.[39m[34mtoContain[39m([32m'id="usage"'[39m)[33m;[39m
      |     [90m   |[39m                      [31m^[39m
      |     [90m285|[39m     [34mexpect[39m(mainPage)[33m.[39m[34mtoContain[39m([32m'id="design"'[39m)[33m;[39m
      |     [90m286|[39m     [34mexpect[39m(mainPage)[33m.[39m[34mtoContain[39m([32m'id="usage"'[39m)[33m;[39m
      | 
      | [31m[2m⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/1]⎯[22m[39m
      Not handled here (capability): a configured check only measures the code it runs against
      Evidence (log): /home/zhenyu/concorde/.concorde/tasks/entry-stubs/workspace/runs/r-20260929T181245-task_validation-43578159/checks/check.views.repository-regressions/output.log sha256:d01ccaa800ee2b71ed65a426b954114939fb9060091be77dc00dc88f746a0591

```json
{
  "level": "task-session",
  "actor": "task session (task entry-stubs)",
  "code": "views_test_asserts_old_stub",
  "detail": "task-validation is blocked only by check.views.repository-regressions: docsite/tests/repository/fresh-project-scaffold.test.ts lines 284-290 assert that a freshly initialized project's rendered root page has id=\"usage\" before id=\"design\". The task's in-scope change of the initial stub (now Purpose / Not yet specified / Parts, per the brief) removes those headings, so the assertion must follow. The fix is mechanical: expect id=\"not-yet-specified\" before id=\"parts\" (and drop the duplicated usage/design pair). Everything else is done and verified: build, spec-validation success with no finding, full pytest 788 passed, both entries restructured and committed (56b764cb, c0f548ba).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "scope",
    "explanation": "The test file is bound by module.views, which is not among this task's Modules (module.spec, module.scaffold); the brief says to edit only the bound Modules' documents and code, and parallel restructuring tasks may be editing module.views."
  },
  "options": [
    "Add module.views to this task (or authorize this one test edit) and I update the assertion here, then deliver",
    "Fix the Views test in a separate task merged before this one"
  ],
  "recommendation": "Authorize the one-line test edit in this task: it is a direct consequence of the stub change the brief asked for, and delivering without it would leave main with a failing check",
  "causes": [
    {
      "level": "command",
      "actor": "Command task-validation r-20260929T181245-task_validation-43578159 (workspace entry-stubs)",
      "code": "not_deliverable",
      "detail": "workspace entry-stubs is not deliverable: 1 blocking finding(s), each a cause below; delivery, which decides the same readiness again, refuses the workspace until they are repaired (readiness in /home/zhenyu/concorde/.concorde/tasks/entry-stubs/workspace/runs/r-20260929T181245-task_validation-43578159/readiness.json)",
      "evidence": [
        {
          "kind": "blocking",
          "ref": "check.views.repository-regressions",
          "detail": "module.views check failed (exit 1); log /home/zhenyu/concorde/.concorde/tasks/entry-stubs/workspace/runs/r-20260929T181245-task_validation-43578159/checks/check.views.repository-regressions/output.log"
        }
      ],
      "attempts": [],
      "unhandled": {
        "reason": "decision",
        "explanation": "task-validation only decides readiness and never repairs; each finding needs a Spec change (specify) or a code change (implement), which the task level chooses"
      },
      "options": [
        "repair each blocking finding in the workspace and run task-validation again",
        "run specify for a Spec finding, implement for a code or check finding"
      ],
      "recommendation": "repair the first blocking finding: check check.views.repository-regressions: module.views check failed (exit 1); log /home/zhenyu/concorde/.concorde/tasks/entry-stubs/workspace/runs/r-20260929T181245-task_validation-43578159/checks/check.views.repository-regressions/output.log",
      "causes": [
        {
          "level": "check",
          "actor": "check.views.repository-regressions",
          "code": "check_failed",
          "detail": "the configured check check.views.repository-regressions of module.views failed with exit code 1; its log /home/zhenyu/concorde/.concorde/tasks/entry-stubs/workspace/runs/r-20260929T181245-task_validation-43578159/checks/check.views.repository-regressions/output.log ends with:\nitle=\"Direct link to Not yet specified\" translate=\"no\">​</a></h2>\u001b[39m\n\u001b[31m+ <p>The project&#x27;s core concepts are not specified yet. This Module declares the project&#x27;s\u001b[39m\n\u001b[31m+ glossary, where every term of the project will be defined once; no term has been defined\u001b[39m\n\u001b[31m+ yet.</p>\u001b[39m\n\u001b[31m+ <p>How the project is used is not specified yet: its entry points, inputs, results, effects,\u001b[39m\n\u001b[31m+ errors and repeat behaviour are unknown. Do not infer them from existing code.</p>\u001b[39m\n\u001b[31m+ <p>The project&#x27;s decomposition, state, control flow and design reasons are not specified yet.</p>\u001b[39m\n\u001b[31m+ <h2 class=\"anchor anchorTargetStickyNavbar_P4mg\" id=\"parts\">Parts<a href=\"#parts\" class=\"hash-link\" aria-label=\"Direct link to Parts\" title=\"Direct link to Parts\" translate=\"no\">​</a></h2>\u001b[39m\n\u001b[31m+ <p>The project&#x27;s parts and their collaborations are not specified yet. This Module contains,\u001b[39m\n\u001b[31m+ uses and includes nothing, and no requirement or scenario has been written.</p>\u001b[39m\n\u001b[31m+ <p>No realization binds implementation files yet.</p></div></article><nav class=\"docusaurus-mt-lg pagination-nav\" aria-label=\"Docs pages\"><a class=\"pagination-nav__link pagination-nav__link--next\" href=\"/specs/project/glossary\"><div class=\"pagination-nav__sublabel\">Next</div><div class=\"pagination-nav__label\">Glossary</div></a></nav></div></div><div class=\"col col--3\"><div class=\"tableOfContents_ktwR thin-scrollbar theme-doc-toc-desktop\"><ul class=\"table-of-contents table-of-contents__left-border\"><li><a href=\"#purpose\" class=\"table-of-contents__link toc-highlight\">Purpose</a></li><li><a href=\"#not-yet-specified\" class=\"table-of-contents__link toc-highlight\">Not yet specified</a></li><li><a href=\"#parts\" class=\"table-of-contents__link toc-highlight\">Parts</a></li></ul></div></div></div></div></main></div></div></div><footer class=\"theme-layout-footer footer footer--dark\"><div class=\"container container-fluid\"><div class=\"footer__bottom text--center\"><div class=\"footer__copyright\">Atlas project documentation · 2026</div></div></div></footer></div>\u001b[39m\n\u001b[31m+ </body>\u001b[39m\n\u001b[31m+ </html>\u001b[39m\n\n\u001b[36m \u001b[2m❯\u001b[22m tests/repository/fresh-project-scaffold.test.ts:\u001b[2m284:22\u001b[22m\u001b[39m\n    \u001b[90m282|\u001b[39m     \u001b[34mexpect\u001b[39m(mainPage)\u001b[33m.\u001b[39mnot\u001b[33m.\u001b[39m\u001b[34mtoContain\u001b[39m(\u001b[32m'id=\"requirements\"'\u001b[39m)\u001b[33m;\u001b[39m\n    \u001b[90m283|\u001b[39m     \u001b[34mexpect\u001b[39m(mainPage)\u001b[33m.\u001b[39mnot\u001b[33m.\u001b[39m\u001b[34mtoContain\u001b[39m(\u001b[32m'id=\"scenarios\"'\u001b[39m)\u001b[33m;\u001b[39m\n    \u001b[90m284|\u001b[39m     \u001b[34mexpect\u001b[39m(mainPage)\u001b[33m.\u001b[39m\u001b[34mtoContain\u001b[39m(\u001b[32m'id=\"usage\"'\u001b[39m)\u001b[33m;\u001b[39m\n    \u001b[90m   |\u001b[39m                      \u001b[31m^\u001b[39m\n    \u001b[90m285|\u001b[39m     \u001b[34mexpect\u001b[39m(mainPage)\u001b[33m.\u001b[39m\u001b[34mtoContain\u001b[39m(\u001b[32m'id=\"design\"'\u001b[39m)\u001b[33m;\u001b[39m\n    \u001b[90m286|\u001b[39m     \u001b[34mexpect\u001b[39m(mainPage)\u001b[33m.\u001b[39m\u001b[34mtoContain\u001b[39m(\u001b[32m'id=\"usage\"'\u001b[39m)\u001b[33m;\u001b[39m\n\n\u001b[31m\u001b[2m⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/1]⎯\u001b[22m\u001b[39m",
          "evidence": [
            {
              "kind": "log",
              "ref": "/home/zhenyu/concorde/.concorde/tasks/entry-stubs/workspace/runs/r-20260929T181245-task_validation-43578159/checks/check.views.repository-regressions/output.log",
              "detail": "sha256:d01ccaa800ee2b71ed65a426b954114939fb9060091be77dc00dc88f746a0591"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "capability",
            "explanation": "a configured check only measures the code it runs against"
          },
          "options": [],
          "recommendation": "",
          "causes": []
        }
      ]
    }
  ]
}
```

## Main agent's answer to escalation #1 (2026-09-30)

Decided without the developer (ordinary scope): option 1. This task may edit the one assertion in
`docsite/tests/repository/fresh-project-scaffold.test.ts` (module.views) that expects the old stub
headings, since it follows directly from the stub change. `restructure-spec-tooling` holds
module.views in parallel but edits entry documents, not this test; a merge conflict, if any, is
resolved later. Also accepted the session's other decisions (heading names, keeping the
"How <title> is used is not specified yet" sentence verbatim for other Modules' tests).
- **Escalation #1 applied.** Per the main agent's answer, `fresh-project-scaffold.test.ts` now
  expects `purpose` < `not-yet-specified` < `parts` (duplicate usage/design pair dropped); the
  Views repository regression check passes locally (259 tests). No other module.views file edited.

## Closed: merged, 2026-09-29T18:34:30Z
