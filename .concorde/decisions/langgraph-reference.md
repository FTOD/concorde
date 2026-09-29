# Decision log: langgraph-reference

Goal: Vendor LangGraph (the locked version) as an external reference under references/langgraph and declare it as an external include of the Modules that use LangGraph

## 2026-09-28 — decisions taken without the developer

1. **Two submodules instead of one.** The langchain-ai/langgraph repository at 1.2.12 no longer
   carries its documentation (`docs/` holds only `llms.txt` and redirects); the pages live in
   langchain-ai/docs. Options: source only; source plus the docs repository as a second
   submodule; the docs repository only. Chose source plus docs (`references/langgraph`,
   `references/langgraph-docs`), because readers need both the Graph API documentation and the
   exact code behind it.
2. **Pins.** `references/langgraph` at tag 1.2.12 (49cce0ca), the release `uv.lock` locks and the
   newest LangGraph tag; the vendored `libs/langgraph/langgraph/` is byte-identical to the
   installed package (`diff -rq` empty). The docs repository has no release tags, so it is pinned
   at its head 264fdf88 (2026-09-25), the first state after the 1.2.12 release (2026-09-21).
3. **Sparse scope.** langgraph: LICENSE, README, `docs/llms.txt`, `libs/langgraph/README.md`,
   `libs/langgraph/langgraph/`; checkpoint, prebuilt, SDKs, CLI, tests and notebooks left out
   (spec_panel uses none of them, and the checkpoint lib's version is locked separately).
   langgraph-docs: LICENSE, README, `src/oss/langgraph/`. Media excluded like every reference.
   About 1.3 MB and 1.2 MB checked out.
4. **Which Modules include them.** Only `module.spec-review`: `spec_review/panel.py` is the one
   source that uses LangGraph's API. Operations mentions it without using it, and Distribution
   only installs it and checks the import, so neither gets the include.
5. **Development page.** Its submodule list lacked swe-bench as well as the new references; the
   sentence now names every vendored submodule and says both LangGraph references move with the
   lock. This lies within `module.concorde`, which owns the page and `.gitmodules`.

## Results

All `ok`: registry --write (regenerated module.spec-review), build, build --check (no
differences), spec-validation (0 errors, 0 warnings), pytest on spec model, checks, grants and
spec_review (89 passed). The review-spec grant for module.spec-review now lists both references
as `ro`.

## Closed: merged, 2026-09-27T19:26:54Z
