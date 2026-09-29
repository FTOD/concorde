# Decision log: pi-run-result-in-turn

Goal: In the pi run view, never leave a finished Concorde run's result waiting for the end of the turn: return the result of a run that has already finished from concorde_run itself, and deliver a result that arrives while the main agent is still in a turn into that turn (steer) instead of as a follow-up, so bg_wait answering 'nothing to wait for' never precedes a pending result

## Closed: merged, 2026-09-25T08:23:24Z
