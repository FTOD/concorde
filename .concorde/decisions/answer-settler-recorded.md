# Decision log: answer-settler-recorded

Goal: Record who settled each answered survey decision (main agent or developer) instead of always 'developer', and tell developers of a develop install to start nothing until concorde update ends

## Brief (main agent, 2026-09-30)

Two small follow-ups to tasks merged today. Both carry out the developer's decisions; the details
below are the main agent's decisions.

### 1. Who settled an answered decision (module.adoption, module.workflows)

The developer decided on 2026-09-30 (task decision-point-authority, merged at ae868d2f) that the
main agent settles the pending decision points of an interactive workflow that its authority
covers, and puts the rest to the developer. Adoption still records every answered survey decision
as `decided_by: developer`, in req.adoption (the `--answers` requirement, requirements.md:79),
contract.adoption.answers and the decomposition contract's semantics. The worker prompts
`prompts/workers/survey.md` and `code-to-spec.md` say the same, and Workflows' result contract
mirrors the enum `worker|developer`. So a decision the main agent settled would be recorded as the
developer's. Decision by the main agent: make the record accurate.
- Each answer in the `--answers` input names who gave it, `main-agent` or `developer`; the field is
  required, with no compatibility default (rapid-iteration rule).
- A decision that follows an answer is recorded with `decided_by` equal to that answer's settler.
  The enum becomes `worker|main-agent|developer` wherever it appears: the Adoption contracts,
  Workflows' result contract and its Markdown rendering, the worker prompts, the host's validation
  that the output follows every answer, and the tests.
- Bump each changed contract's version. Update the main-session and task-session guidance only
  where they describe the answers' shape. Adjust the field and value names if the contracts'
  conventions suggest better ones, and record the choice here.

### 2. Dogfooding sentence (module.dogfooding)

The developer decided on 2026-09-30 (task update-idle-promise, merged at ae834778) that
`concorde install`/`update` refuses only runs whose runner holds its run lock at the check, and
that the developer must not start Concorde while an install or update runs. In
`prompts/dogfooding/skill.md`, "Take the fix" (around line 124), add that nothing should be
started until the update ends. Align Dogfooding's Spec if it states the same step.

### Process

`uv sync --locked --group dev`, `npm --prefix docsite ci`, `build`; format, `build --check`,
`spec-validation`, the relevant tests and the full pytest suite once on the final input;
task-validation and delivery; report with SendMessage.

## Task session decisions (2026-09-30)

- **Field name `answered_by`, values `main-agent` and `developer`.** The answer names who settled it
  in `answered_by`, parallel to the decision's `decided_by`; the values are the ones
  `concorde task escalate --by` and the Tasks contracts already use (`main-agent`), so no new
  spelling. `decided_by` becomes `worker|main-agent|developer`. Required, no default.
- **Contract versions bumped:** `contract.adoption.decomposition` 4→5 and
  `contract.adoption.spec-description` 2→3 (their `decided_by` enum), `contract.adoption.answers`
  2→3 (new required field; semantics now say "the answers" rather than "the developer's answers"),
  `contract.workflows.step-request` 4→5 (its answer items carry `answered_by`; it has
  `additionalProperties: false`, so without it the step would refuse the new field) and
  `contract.workflows.result` 6→7 (`decided_by` enum). The Markdown rendering of the report prints
  `decided_by` as is, so it shows `main-agent` without change.
- **Host check:** `answer_problems` now requires `decided_by == answered_by` for a decision answer;
  the failure detail says who answered ("but the main-agent answered …").
- **Adoption wording:** module.md's "The developer's answers" and "seek the developer's answers" now
  name answers settled by the main agent within its authority or by the developer; the worker
  briefs' header "The developer's answers" became "The answers to earlier decisions and questions",
  and `invalid_answers`' explanation "answers are settled above the task". Scenario
  `scenario.adoption.survey-answers` now uses a main-agent answer and adds that crediting the
  developer fails; `scenario.adoption.invalid-answers` adds an answer that does not say who gave it.
  Workflows' `scenario.workflows.interactive-resume` adds that the result lists the decision as
  decided by whoever gave the answer.
- **Guidance:** task-session guidance gives the answer shape with `answered_by`, taken from the main
  agent's answer. In the main-session skill, the interactive-workflow bullet now tells the main
  agent to say for each answer whether it or the developer settled it: without that the task
  session cannot fill the required field. This is one clause where the skill describes answering
  the session, not a change of the main agent's role.
- **Dogfooding:** `prompts/dogfooding/skill.md` "Take the fix" adds "Start nothing until the update
  ends, no run, task session or other `concorde` command in any worktree of the project: its check
  does not stop what starts after it, and that may find Concorde half replaced." Dogfooding's
  module.md "Taking the fix" states the same with a link to Distribution's busy check, and
  `scenario.dogfooding.guidance` and its test cover it.

## Closed: merged, 2026-09-30T04:09:37Z
