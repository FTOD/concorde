# Review scenarios

These precise specifications belong directly to the [Review Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term                                       | Meaning / definition           |
| ------------------------------------------ | ------------------------------ |
| [Spec](../module.md#terminology)           | Defined in Concorde Framework. |
| [Issue](../module.md#terminology)          | Defined in Concorde Framework. |
| [Host](../module.md#terminology)           | Defined in Concorde Framework. |
| [Worker](../module.md#terminology)         | Defined in Concorde Framework. |
| [Pi integration](../module.md#terminology) | Defined in Concorde Framework. |
| [Module](../module.md#terminology)         | Defined in Concorde Framework. |
| [Review coverage](module.md#terminology)   | Defined in Review.             |

## Review

### scenario.review.standalone — Public review without a development change

- GIVEN an initialized project without a managed development change or preexisting Issue record
- AND a task with an explicit Module target, optional same-owner scenario focus and no review-mode selector
- WHEN the user invokes `concorde-spec-review` or `concorde-code-review` through the Pi `concorde` tool and invokes the exact returned native workflow call
- THEN the host validates the caller selection and a fresh reviewer receives its complete contract and, for `concorde-code-review`, only its admitted implementation files and scoped changes
- AND native write/edit/shell/delegation tools are absent while file/network/credential restrictions remain prompt-level policy
- AND the host returns typed review coverage, findings, gaps and completion status, persisting the review report without creating a development change or changing project Specs or implementation
- AND an unmanaged Git checkout uses HEAD as the scoped change baseline

The detailed contract is [Independent current review](execution-reference.md#review-independent-review-operation).

### scenario.review.terminology-consistency — Compare local restatements with canonical meaning

- GIVEN an admitted Spec collection with imported terminology rows and their complete canonical defining units
- WHEN `concorde-spec-review` assesses that collection
- THEN every local restatement is checked for semantic consistency with its direct canonical definition, including unchanged and referenced reading documents
- AND different wording is allowed without requiring text equality
- AND additions, omissions, contradictions or consumer-specific behavior that change shared meaning are reported with local and canonical locations
- AND coverage identifies checked term/source pairs or explicitly states that no imported restatements exist
- AND missing, ambiguous or unassessed comparisons are reported as gaps or incomplete coverage, never silently counted as consistent

### scenario.review.separate-entries — Review authority follows the selected Operation

- GIVEN an initialized project and a standalone review task
- WHEN a caller selects a public review Operation
- THEN `concorde-spec-review` selects only the Spec reviewer and `concorde-code-review` selects only the code reviewer
- AND a request containing review_mode is rejected rather than changing that Operation's authority
- AND the retired `concorde-review` entry is rejected without an alias or implicit migration

### scenario.review.consumer-currentness — Owner and consumer evidence stay independently current

- GIVEN a managed target with required Spec review and direct consumers of its complete paired contract
- WHEN review evidence is checked after direct source, metadata, registration or intent changes
- THEN each owner and consumer needs its own current complete-context review under its accepted intent
- AND missing, corrupt, skipped, incomplete, empty-coverage, blocking or unrelated evidence cannot satisfy the requirement
- AND same-scope unresolved contract blockers prevent cached evidence reuse while unrelated work does not clear or inherit those dependencies
- AND an explicitly selected review runs fresh bounded reviewers and preserves historical reports rather than reusing a deleted workflow's completion

### scenario.review.explicit-components — Code-free parents aggregate only current component evidence

- GIVEN a code-free Module with accepted tasks and separately completed explicit component work
- WHEN the caller selects code review for that Module
- THEN each recorded component with implementation files receives a fresh read-only reviewer under its derived task and constraints
- AND the parent aggregates only typed reports without starting component development or receiving component code
- AND readiness checks the exact current component review scope, coverage, intent and artifact bytes without requiring a fictional local code review
- AND changed inputs, corrupt reports or unrelated intent invalidate reuse while fresh review does not fabricate implementation completion

### scenario.review.native-scope — Fresh native scopes reconcile complete typed evidence

- GIVEN a deterministically selected owner/component/shared-consumer scope
- WHEN its authored native workflow runs fresh scoped reviewers and fixed Host aggregation
- THEN clean/advisory/blocking/incomplete results preserve their distinct meaning and genuine immutable receipts
- AND wrong context/mode/receipt/coverage, stale inputs or missing/failed reviewers cannot accept a partial scope
- AND shared consumers retain separate complete contexts and code-free parents aggregate applicable components
- AND a scope of more than thirty-two reviewers uses the same two Host grants without a new business cap
- AND required review and primary-authoritative evidence remain intact without a public Graph/RPC fallback
