# Query and Routing scenarios

These precise specifications belong directly to the [Query and Routing Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Context](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Query and Routing

### scenario.development.answer-question — Direct answer from selected Module contexts

- GIVEN a question with an optional target or focus routing hint
- WHEN `concorde-main` runs with `action: ask`
- THEN the host deterministically resolves the explicitly selected Modules' complete Spec contexts, indexes each selected Module's original documents once and grants them read-only to the answerer, and the answerer opens them on demand and returns a direct answer
- AND the response contains no authored project file changes

See [routing hints only steer selection](requirements.md#req.development.routing-hint-not-context) and
[routing hints never grant context](requirements.md#req.development.routing-hint-no-grant).

### scenario.development.answer-gap — Missing promise reported as a Spec gap

- GIVEN the answerer's selected complete Module contexts do not contain a promise the question needs
- WHEN the answerer would otherwise have to guess or consult an unselected source
- THEN the response reports a Spec gap naming the blocked question, the owning Module and the current context identity
- AND the answerer does not read implementation files or search code to supply the missing meaning

### scenario.development.discovery-limit — Discovery stops at its declared limit

- GIVEN repeated context expansion has not resolved the question
- WHEN a discovery worker's bounded expansion-step limit is reached
- THEN the host returns the `context_limit` outcome instead of expanding context further

The detailed contract is [Complete-context question and route](execution-reference.md#query-and-routing-query-and-routing-agent-graph).
