---
audience: worker
---

## The project's architecture review

This panel reviews the architecture of the whole project once. It has architects and a chair. It
has no reviewers. The reviewed Module is the whole project: every Module is a reviewed Module.

As an `architect`, judge every Module's place among the others by the architecture quality
criteria above. Start at the root Module's entry document. Follow the Modules' relations as far as
the question needs. Look for these problems first:

- A responsibility two Modules both claim, or one no Module claims.
- A dependency a Module relies on but does not declare, or one that points the wrong way.
- A consumer that knows a provider's internals.
- Two Modules that say different things about the same promise.

Leave the Module quality of single documents to the Modules' own Spec panels.

Every Module's documents can carry a blocking finding here. Set a finding's `module` to the Module
whose document it cites. Name in `related` every other Module the problem concerns.

As the `chair`, audit, merge and reject as above. Every Module's documents are the reviewed
Module's own documents in this review.
