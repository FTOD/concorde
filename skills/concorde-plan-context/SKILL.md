---
name: concorde-plan-context
description: "Resolve and report the permission-bounded context for one selected planning attempt."
exposure: internal
effects:
  reads:
    - selected-feature
    - module-architecture
    - module-ancestry
    - related-summaries
    - required-feature-specs
    - owned-implementation
    - attempt
    - checklists
    - constitution
    - reflections
    - framework
    - templates
  writes: []
  network: false
  credentials: none
---

## User Input

```text
$ARGUMENTS
```

# Resolve Bounded Planning Context

This is the read-only first leaf of the paired `concorde-plan` Operation. The trusted host has
already resolved Workspace Protocol 13, required-interface ownership, concrete non-symlink paths,
and a deny-by-default native launch policy. Use only those launch paths and the original request.

## Context receipt

Read the complete selected feature, providing module architecture, bounded ancestry, optional
Constitution, selected attempt artifacts, providing-module implementation/test locators, and each
dependency feature specification admitted by an exact `interfaces.required` owner reason. Do not
open another feature body merely because it appears in `related_features`.

Return one compact context receipt containing:

- selected feature ID/path and providing architecture;
- ancestry architecture paths and canonical related-feature summaries supplied by the host;
- each admitted provider feature path with every required-interface reason;
- owned implementation/test locators and selected attempt/control paths;
- the host workspace/source digest and explicit denied dependency-internal categories; and
- any missing, ambiguous, unsafe, or contradictory authority that must stop authorship.

Never write a plan, reflection, source, architecture, feature, test, package, or generated file. A
missing provider, policy mismatch, unreadable declared path, symlink, or attempted undeclared read is
a named failure. The next leaf may rely on this receipt but may not widen it.
