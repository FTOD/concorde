```concorde-document
{
  "id": "document.workflow.reflections",
  "targets": [
    "domain.workflow"
  ],
  "main_visible": true
}
```

# Reflection orchestration

A Reflection retains a problem, its observed effects, evidence, investigation and developer
comments. Status queries report metadata. Explicitly captured task gaps become queue records;
capturing a report neither resolves its source gap nor approves a repair.

## Investigation, implementation and disposition

Reflection status is metadata-only. Investigation runs as read-only implementation with selected
record bytes and HEAD. The host preserves the original report and human comments, writes findings
and an evidence-bound plan, and enforces configured approval. Implementation gets a newly authored
behavior task through a standard loop. Human disposition remains required before closing a report;
merely observing that a problem no longer reproduces does not dismiss it.



The input selects a known report or recorded gap. Investigation produces attributed findings and
a proposed resolution with evidence; implementation produces a verified candidate through the
normal development loop. Closing a report is a separate human disposition. Failed investigation or
stale evidence keeps the report and progress for a later attempt. The original observation and
user comments are retained throughout. See the Reflections service contract for queue actions and
approval settings.
