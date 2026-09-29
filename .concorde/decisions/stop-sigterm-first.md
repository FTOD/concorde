# Decision log: stop-sigterm-first

Goal: Stop a pi task-session round by sending SIGTERM to its pi process group first, so pi and sandbox-runtime clean up, and SIGKILL only after a short grace period

## Closed: merged, 2026-09-26T05:28:53Z
