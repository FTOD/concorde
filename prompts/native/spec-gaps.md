---
audience: worker
---

A Spec gap is a missing or conflicting promise of the Module that owns the behaviour you need.
Report it through report_issue, naming the missing promise, the step it blocks and the owning
Module, and continue only with work that does not depend on it. Never fill a gap from source code,
memory or a guess. A failed command or check, an explicit prohibition and a missing runtime value
whose failure behaviour the Spec defines are not Spec gaps.
