# Decision log: review-distribution

Goal: Fix the spec review findings of Distribution

## Brief (main agent, 2026-09-30)

The developer asked for a spec review after `project-model-names` merged and said: fix the small
problems yourselves, and ask the developer only at the end about what needs their decision.

The unbound `spec_review` run `r-20260929T203136-spec_review-a3b63738` examined main at 14e573aa
and ended `changes_required`. Its result, with every finding's evidence and suggestion, is
`/home/zhenyu/concorde/.concorde/unbound/r-20260929T203136-spec_review-a3b63738/result.json`
(read-only for you); this task covers the findings of module.distribution.

### What to do

- Fix every finding of these Modules, blocking and advisory, except those named below as the
  developer's. Typical fixes: split a requirement that holds several obligations into atomic
  requirements, one SHALL each; split a scenario that mixes situations into scenarios of one
  situation each; correct examples, diagrams and wording that contradict the provider's Spec or the
  code. When a scenario identity changes, update the tests whose verification declarations name it.
  Keep what the Modules promise unchanged unless the finding shows the promise is wrong; when the
  code and the Spec disagree, decide which is right from the other Specs and the developer's earlier
  decisions, and record the decision here.
- Findings that say a provider's contracts were not supplied: check whether the Module's
  declarations omit that contract and add it if so; otherwise report it as a possible spec_review
  defect with evidence. Do not change module.spec-review.
- A finding you judge wrong: do not change the Spec; record why here and in your report.
- Anything else you find that needs the developer (it changes a promise's meaning, the design, or an
  earlier developer decision): leave it unchanged and report it with options and a recommendation.
  Do not escalate and stop: deliver the rest and put every such question in your final report.

### Specific to this task

Leave f.6 (a run started between update's idle check and the end of the framework replacement) UNCHANGED in behaviour: the fix needs an exclusion shared with Execution's run admission, which the developer decides. Analyse the code, confirm whether the race is real, and give options (e.g. a framework lock that update holds and every run takes shared at start; or narrowing the promise) with your recommendation. For f.5, state the outcome, possible partial state and retry behaviour of filesystem failures and interruptions honestly (a small, documentation-level fix unless the code is wrong). For f.7 (provider contracts not supplied) check the declarations as described in the common brief.

### Process

Create what Git ignores (`uv sync --locked --group dev`, `npm --prefix docsite ci`, `build`). Format,
`build --check`, `spec-validation`, `registry --write` if a module block changes, the relevant tests
and once the full pytest suite on the final input. Then run `python3 scripts/concorde.py run
spec_review` once in the task worktree (bound; it reviews this task's Modules and updates their
review memory) and handle its findings the same way, without looping further. Then `task-validation`
and `delivery`, and report to the main agent with SendMessage: what you fixed, the findings you
judged wrong, and the open questions for the developer with options and recommendations.

## Task session (2026-09-30)

Analysis of the findings of `r-20260929T203136-spec_review-a3b63738` for module.distribution:

- f.1: `cli.py` routes `trace` to Tracing before the envelope; the entry already lists it among the
  exceptions. Fix the requirement: add `trace` to req.distribution.one-envelope's exceptions.
- f.2: the test verifying scenario.distribution.install installs into an uninitialized Git project
  and asserts no configuration, registry or `specs/` is created. The scenario's "project with Specs"
  is the error, not the promise: it becomes a project not yet initialized; the binding in an
  initialized project stays with scenario.distribution.install-later-files-bound.
- f.3: `build.py`'s `PROMPT_ROOT_DIRECTORIES` includes `prompts/development`, so every file directly
  in it is a root. The entry's list (and the code comment in `build.py`) omit it; both are corrected.
- f.4: split req.distribution.installer-project-mcp into registration, keeping the rest of the file
  and the pre-write refusal (`installer-mcp-checked`), one SHALL each. No test names requirements.
- f.5: the code does not catch an `OSError` of its own writes: a failed write after the first write
  ends the installer with a Python traceback, no error link. Decision (within Distribution, follows
  the error-chain rule and req.distribution.installer-error-links): the installer and update refuse
  such a failure with `install_failed` (reason `environment`), naming the OS error; the entry states
  the partial state (receipt written last, so it still describes the previous install; an update's
  rebinding and mark not written), that nothing is rolled back, and that running the same command
  again completes it, with `install-concorde.py <project> --update` when the command itself no
  longer runs. New requirement and scenario for it.
- f.6: left unchanged as the brief says; analysis goes to the report.
- f.7: Spec core's contracts document defines no contract node, so no `relies_on` can select the
  envelope. Decision: Distribution `includes` the document `document.spec.contracts` with a reason,
  and its `uses` of Spec core, Tracing and Execution also list the promises the entry links to
  (req.spec.init-explicit-envelope, req.spec.installation-follows-record, contract.tracing.error,
  concept.run-lock).
- f.8: the update section is split into what update does, the unvalidated state and the open tasks,
  with an illustrative state view.

### Bound spec_review `r-20260929T205731-spec_review-02c77a16` (changes_required, 3 blocking)

- f.1 (blocking): the same race as the earlier f.6, left unchanged for the developer.
- f.2 (blocking): valid. The receipt is now written through `install.json.partial` and
  `os.replace`, so a failure leaves the previous or the new receipt; the entry, the requirement and
  the update paragraph distinguish a stop before, at and after the receipt; a new scenario
  (`update-mark-failed`) and its test cover a failure after the receipt.
- f.3 (blocking): valid; the binding requirement and step 9 now use Spec core's selection (receipt
  files outside `.concorde/`, not amended). No change of behaviour: the code already did this.
- f.4 (advisory): valid; req.distribution.unvalidated-reported promises CONCORDE-UPDATE-001 only
  when validation finds another error, which is what the code does.
- f.5 (advisory): valid; the uses-spec paragraph is limited to the commands that print the
  envelope and says how the installer treats Spec core refusals.
- As the brief says, the review is not run again.

### Delivery

Full suite on the final input: 790 passed, 4 skipped. `task-validation`
`r-20260929T210247-task_validation-ac8b8f67` ready; `delivery` `r-20260929T210316-delivery-50f6198f`
delivered as 4b2fd8631ec5 (it carries the review memory `.concorde/reviews/spec/module.distribution.json`).

Open for the developer: the race between the installer's idle check and new runs (first review's
f.6, bound review's f.1), left unchanged; options in the report to the main agent.

## Closed: merged, 2026-09-29T21:04:24Z
