# Decision log: specify-new-documents

Goal: When a specify worker needs new Spec documents of its bound Modules, the Operation creates them (empty, registered in the owner's metadata and the registry) and relaunches the worker once to fill them, instead of ending blocked and leaving the main agent to create them by hand.

## Closed: merged, 2026-09-27T16:31:01Z
