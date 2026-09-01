# Compose Workflow Skills

`feature.skills.compose-workflow` · specified at `module.concorde.skills` · about three minutes.

## Purpose

Make the installed skill set the single, consistent interface for Concorde feature work.

## Functionality

- Composes Concorde guidance into the normal Spec Kit lifecycle skills.
- Adds init, context, validate, implementation-delivery, and ask skills.
- Resolves the selected feature before a phase assumes any file path.
- Names the durable or temporal files a phase may read and write.
- Invokes Scripts only for routing or deterministic operations.

## Structure

The preset supplies normal-phase command layers and templates. The extension supplies the five
Concorde-specific command definitions. Spec Kit materializes both through the active agent
integration. Installed skills are presentations; maintained package sources remain authoritative.
The parent [level view](../../../../diagrams/level-view.json) shows their place in the workflow.

## Logic

1. A maintainer invokes a skill.
2. The skill resolves the selected workspace when the phase is path-sensitive.
3. The skill reads durable intent and bounded context.
4. The coding agent authors the phase's permitted workspace files.
5. The skill presents every script finding and approval gate explicitly.

## Read Next

- [Feature design](design.md)
- [Skills module](../../module.md)
- [Root interaction model](../../../../../design.md)
