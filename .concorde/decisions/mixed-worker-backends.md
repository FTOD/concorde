# Decision log: mixed-worker-backends

Goal: Let the worker backend (claude or pi) be configured per worktree in worker-models.json (default, per Operation, per role) independently of the main session's program, falling back to the main session's program; configured only through the config file; refused with a detailed reason when the chosen program is not installed

## Closed: merged, 2026-09-25T19:04:56Z
