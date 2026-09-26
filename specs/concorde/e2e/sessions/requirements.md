# Headless sessions requirements

The Module-wide obligations of [Headless sessions](module.md). The [scenarios](scenarios.md) show
them in concrete situations.

### req.headless-sessions.conditions-in-tool — Testing conditions are told by the tool

Every round of a headless session SHALL be started with the headless note appended to its system
prompt and its tools granted on the command line.

The headless note is the tool's; no part of it is added to the main-session guidance, which stays
what users get.

### req.headless-sessions.wake — A run left behind wakes the session once

When a round ends with an Operation run of the session still running, or stopped by the round's
end, the driver SHALL wait for it to finish and resume the same session with a wake message naming
it.

Each run is named in one wake message only, so a session is never woken twice for one run.

### req.headless-sessions.logs-kept — Every round is kept

The driver SHALL keep each round's output and standard error and the session's record in the
session directory, including for a session that ends with a failed round.
