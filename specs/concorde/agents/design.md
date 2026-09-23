# Agents in depth

This topic explains the reasons behind how Agents are defined and what their definitions do and do
not guarantee. The [entry](module.md) defines the terms; [Agent definitions](definitions.md) gives
every field and value.

## One definition, many uses

An Agent's identity and its limits are stated once, and every other part of Concorde derives from
that statement instead of keeping its own copy. Task context turns a definition into the Agent
binding of one call, Agent execution's launch preflight allows exactly the tools the definition
lists, the build renders the instructions it names, and model selection keys its per-Agent
overrides by its name. A launch with more tools than the definition, or a proposal with fields the
definition does not allow, is refused rather than tolerated, so a capability cannot quietly give an
Agent more than its definition says. Editing instructions or a definition changes the digest that
Task context binds into every call, so a call prepared before the edit is refused as stale.

## What the definitions declare, and what is not enforced

The definitions declare the most an Agent may use, and the Harness enforces part of it:

- The tool list is enforced at launch. An Agent without `edit`, `write` or `bash` cannot change a
  file through Pi's tools, which is why only the programmer, whose definition writes
  implementation, has them, and why the code reviewer checks code through `run_checks` inside the
  read-only check boundary instead of a shell.
- Which files an Agent reads or writes with those tools is not enforced. File scope, network and
  credential limits are written into its instructions. A reader's file tools accept any path the
  developer's user can read, and the programmer's `bash` reaches any path and could run Concorde's
  launcher.
- The result is enforced: whatever an Agent claims, the Host checks and its provider accepts.

Agents are fresh and terminal on purpose. A fresh conversation cannot carry a previous step's
assumptions forward as if they were evidence, and an Agent without delegation cannot widen its own
grant by handing work to another agent.

## Why hooks are named, not imported

Each definition names its provider's Agent hook by an entry-point string rather than importing it.
The Harness can then run any Agent without importing any provider, and a provider can change how
its Agent's results are prepared and accepted without touching this Module or the Harness. The
instructions an Agent follows and the rules its result is checked against therefore live with
different owners on purpose: the instructions here, the acceptance with the provider.

## An example

`concorde-plan` first runs the context assessor on "add retries to the client". If the client
Module's Spec never says which failures may be retried, the assessor reports that gap and the
planner does not run. Neither Agent looks at code to guess the policy. The developer settles it in
the Spec and calls the capability again, which starts fresh Agents.
