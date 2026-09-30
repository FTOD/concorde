# Decision log: decision-point-authority

Goal: Let the main agent settle the pending decision points of an interactive workflow that its authority covers, passing the rest to the developer

## Brief (main agent, 2026-09-30)

The developer's decision (2026-09-30, answering review-main-session's question on spec review
r-20260929T203136 finding module.main-session f.4): **the main agent may settle the pending decision
points of an interactive workflow that its authority covers**, and puts the rest to the developer.
This is option B of that question. The developer rejected option A, "every decision point goes to the
developer".

Today the glossary's `concept.decision-point` ("…that the workflow treats as the developer's to
settle…") and Workflows' entry (module.workflows: interactive decision points are escalated "to the
main agent, which asks the developer") say every point is the developer's. Main session's Workflows
section, req.main-session.workflow-pause, the brownfield scenario and the skill already say the main
agent settles those its authority covers.

Do:
- Change the definition of `concept.decision-point` (owner module.workflows) and Workflows' entry, its
  requirements and scenarios, so that a point is settled above the task by the main agent under the
  escalation policy of the main-session guidance: the main agent decides those of ordinary scope and
  puts to the developer those with a major impact. Keep `concept.workflow-mode` coherent; interactive
  still means the workflow stops at each point so that it is settled above the task.
- Check that Main session's text, the skill `prompts/main-session/skill.md`, the task-session
  guidance and the brownfield guidance (open questions and survey decisions shown to the developer)
  agree. Brownfield's "show the developer the open questions, the decisions and the checks the survey
  proposed" may stay: showing is not asking. Keep that the proposed checks are configured only when
  the developer accepts them.
- Record every choice in this log. Leave a question you cannot settle from this brief unchanged, and
  report it.

Process: `uv sync --locked --group dev`, `npm --prefix docsite ci`, `build`; format, `build --check`,
`spec-validation`, the relevant tests and the full pytest suite once on the final input; `registry
--write` if a module block changes; task-validation and delivery; report with SendMessage.

## Task session (2026-09-30)

Decisions taken without the developer:

- Glossary `concept.decision-point` now reads: a decision or open question the workflow leaves to be
  settled above the task, by the main agent when its authority covers it and otherwise by the
  developer; the survey decisions counted are those "the worker took itself rather than following
  an answer" (was "rather than the developer"), since an answer may now come from the main agent.
  `concept.workflow-mode` already said "settled above the task, through the main agent" and is
  unchanged.
- Workflows' entry: a decision point is "not the worker's to settle but is settled above the task";
  Workflows itself does not say who settles it, and counts an answer the same whoever gave it. In
  Concorde the main agent settles those its authority covers and puts those with a major impact to
  the developer, as its guidance's decision policy says. I did not link Main session's entry from
  Workflows, to keep the Execution half free of a reference into Coordination. The interactive-mode
  bullet, the brownfield walk-through (`d.db-helper`) and the `answers` argument now say the main
  agent settles or puts to the developer.
- Two new requirements in Workflows: `req.workflows.answers-any-settler` (a step's answers settle the
  points they name whoever gave them; the step code already counts answered ids regardless of who
  answered) and `req.workflows.settler-open` (the workflow result assigns no pending point to the
  developer or anyone else). Scenario `interactive-resume` now starts from "an answer to
  `d.db-helper`, given by the main agent or by the developer".
- Code: the `awaiting_decision` link of `concorde workflow report` no longer says "the developer
  must settle" nor offers "ask the developer every pending point"; it says the points are to be
  settled above the task, by the main agent where its authority covers it and otherwise by the
  developer. The brownfield script's helper `needsDeveloper` is renamed `interactiveStop`.
- Main session's Workflows section: interactive suits a developer who wants the decision points
  settled before the workflow goes on, "by the main agent or by the developer" (was "who wants to
  settle the decision points"). Root Module: an open question is "for the main agent or the
  developer to settle" (was "for the developer").
- Checked and left unchanged, since they already agree: `prompts/main-session/skill.md` (Workflows
  and "Decide, and escalate only what matters"), `prompts/main-session/task-session.md`,
  `prompts/main-session/claude-md.md`, req.main-session.workflow-pause, scenario.main-session.brownfield,
  Task sessions' entry. Brownfield's "show the developer the open questions, the decisions and the
  checks the survey proposed" and the checks configured only when the developer accepts them stay.

Left open (outside the task's Modules, reported to the main agent):

- Adoption (module.adoption) still calls answers "the developer's answers" (contract
  `contract.adoption.answers` semantics, req on `--answers`) and requires an answered decision to be
  recorded `decided_by: developer`; the worker prompts `prompts/workers/survey.md` and
  `code-to-spec.md` say the same, and Workflows' result contract mirrors the enum
  `worker | developer`. When the main agent settles a survey decision, the record will say
  `developer`. Not changed here.

## Closed: merged, 2026-09-30T04:00:12Z
