# Decision log: git-status-smoke

Goal: Smoke test of a task session's network, not a real change; it will be abandoned. Do exactly this, naming no network hosts on any command: (1) run plain git status in the worktree; (2) run git -C references/pi status; (3) run curl -sS -o /dev/null -w '%{http_code}' https://github.com/; (4) send the main agent one message with each command's exact exit status and output, then stop. Change no file, do not deliver and do not escalate.
