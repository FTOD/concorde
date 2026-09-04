---
id: feature.understanding.answer-workflow-questions
kind: feature
module: module.concorde.understanding
related_features:
  - feature.concorde.workflow
interfaces:
  provided:
    - interface.concorde.ask
  required: []
evidence_status: partial
---

# Feature Design: Answer Workflow Questions

## Outcome and Scope

A maintainer receives a concise, cited, read-only answer about Concorde concepts, paths, Tools,
Skills, Operations, interfaces, or current-project application using only the smallest relevant
maintained sources.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.understanding.ask-skill` | Supplies canonical ask guidance and stable navigation rules. |
| `entity.concorde.coding-agent` | Selects bounded sources, reasons over them, and returns citations without mutation. |
| `entity.concorde.specification` | Provides project-specific architecture/design evidence when the question requires it. |

## Interfaces

### `interface.concorde.ask` — Ask a grounded Concorde question

- **Consumer**: Maintainer or coding agent needing workflow/framework orientation.
- **Direction**: Natural-language input to read-only cited answer.
- **Entry points**: Leaf Skill `concorde-ask`.
- **Inputs**: One bounded question and optional project target.
- **Outputs**: Concise answer, direct source citations, and clearly identified uncertainty.
- **Obligations**: Use installed/current sources, disclose inference, and avoid unrelated/deeper reads or any write.
- **Failures**: Missing authority or unresolved ambiguity is reported rather than guessed as fact.
- **Compatibility**: Answers use current Profile 7 terms while historical names are labeled legacy.
- **Implementing entities**: `entity.understanding.ask-skill`, `entity.concorde.coding-agent`.

## Usage Scenarios

1. Ask where a feature/interface/entity belongs and receive the current rule plus canonical path examples.
2. Ask how the selected project applies a rule and receive citations to one bounded architecture/design.
3. Ask an underspecified question and receive a concise uncertainty statement instead of hidden broad reads.

## Related Features

- `feature.concorde.workflow` composes this feature as the read-only orientation surface available at
  any point in the lifecycle without changing lifecycle state.

## Requirements

- **FR-001**: Answers MUST prefer installed/canonical guidance and current project authorities over memory.
- **FR-002**: Each project-specific factual claim MUST cite the smallest source that supports it.
- **FR-003**: The Skill MUST make no file, selection, network-account, or workflow-state change.
- **FR-004**: Reading deeper architecture or code MUST be deliberate, necessary to the question, and disclosed.

## Edge Cases

- The question uses a removed earlier-profile term; answer maps it to Profile 7 and labels it historical.
- Available sources disagree; answer presents the conflict rather than selecting one silently.
