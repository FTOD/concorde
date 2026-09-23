"""The Operation declarations: one module per Operation, listed in ``OPERATIONS``.

The catalog loader (``concorde.operations.catalog``) imports exactly these modules and nothing
else; each module is bound by the Module that owns its Operation.
"""

OPERATIONS = (
    "context_solve",
    "plan",
    "tasks",
    "implement",
    "spec_review",
    "code_review",
    "issues",
    "validate",
    "deliver",
    "init",
    "configure",
)
