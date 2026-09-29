# Decision log: worker-sandbox-tmpdir

Goal: Hand sandboxed commands of pi workers their own writable TMPDIR (CLAUDE_CODE_TMPDIR, which sandbox-runtime passes to commands instead of a /tmp/claude that may not exist), and ignore pi-lens's .pi-lens-probe-home/ in this project's .gitignore

## Closed: merged, 2026-09-26T05:12:42Z
