# Specification Graph scenarios

These precise specifications belong directly to the [Specification Graph Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Evidence](../module.md#terminology) | Defined in Concorde Framework. |
| [Review coverage](../review/module.md#terminology) | Defined in Review. |
| [Ready](../module.md#terminology) | Defined in Concorde Framework. |

## Specification Graph

### scenario.specify-loop.independent — Author and review a Spec independently

- GIVEN a developer supplies a Spec-writing or Spec-revision task and constraints
- WHEN concorde-specify-loop routes the owning Module and runs the selected Spec stages
- THEN only owned Spec replacements are accepted and independent reviews cover the complete contract and affected consumers
- AND successful stages return completed with artifact references, without planning, implementation, code checks, code review requirements or readiness
- AND specify=false skips authoring while run_reviews=false records a Spec review skip only where no requirement already exists
- AND a required review with blocking findings, gaps, incomplete coverage or failed execution stops with inspectable progress
- AND repeating the same intent resumes accepted authoring and current reviews, including when concorde-dev-loop calls specify-loop before continuing development

The detailed contract is [Independent Spec completion](execution-reference.md#specify-loop-specification-graph).
