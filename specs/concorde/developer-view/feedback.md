```concorde-document
{
  "id": "document.developer-view.feedback",
  "targets": [
    "domain.developer-view"
  ],
  "main_visible": true
}
```

# Developer feedback

Feedback starts with a developer's question, observation, correction or change request. It can
refer to a docsite page, diagram relationship, code graph entity, Agent Graph result or source file.
The developer explains the concern and intended outcome through the existing agent conversation.

## From observation to work

A question can be answered without changing files. A proposed correction is clarified into the
intended behavior and constraints before it becomes a development task. Once the request is clear
and authorized, it proceeds directly through the appropriate Framework Graph or capability; an extra report
or journal file is not a prerequisite.

Main routes from admitted Domain and Service responsibilities. The request retains the developer's
intent and constraints. Spec changes, implementation work and reviews follow their existing target
contexts and permissions. A view's link, selected node or copied graph excerpt does not grant wider
reads or permission to modify project files.

## Feedback as a Graph input

The accepted request or decision is human feedback to the selected Agent Graph or Agent Loop. It
identifies the relevant task, result revision and intended change. A clarification can revise the
task; an acceptance can enable the exact transition it authorizes; rejection or cancellation can
select revision, waiting or termination. The orchestration host re-admits affected context and
permissions before continuing. AI review findings remain attributed AI feedback and cannot stand
in for a required human decision.

## Outcomes and limits

An answer explains the relevant source and remaining uncertainty. A change request produces the
normal orchestration outcome: a verified candidate or a concrete blocker with preserved progress. The
developer can then inspect the updated view and continue the conversation.

Concorde currently accepts feedback through the developer conversation and existing typed capability
requests. These integrations do not define a Concorde comment store or an annotation-import
contract, and launching an external viewer does not add one. Diagram edits are not silently
applied to Specs. Layout and detail preferences are advisory unless they expose a concrete missing or
contradictory promise needed by the task.
