# Decision log: installer-pi-runtime

Goal: Install the pi worker runtime by default, since workers run on pi by default: plain installs and updates place it (updates add it to installs that lack it) unless --without-pi-runtime; --pi only adds the pi main-session files, and --update --pi adds them to an existing install.

## Closed: merged, 2026-09-27T16:22:01Z
