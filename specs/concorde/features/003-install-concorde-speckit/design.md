# Feature Design: Install Concorde with Spec Kit

**Design status**: Accepted implementation baseline.

## Realization Overview

The distribution module publishes a bundle that composes the Concorde preset and extension through
Spec Kit's native component system, including permanent feature-design creation and approval-gated hardening.

## Module and Feature Collaboration

Distribution packages reviewed Integration command/template surfaces and the Architecture Core runtime; the active agent integration materializes skills or slash commands.

## Scenario Realization

A maintainer previews and installs the bundle, Spec Kit resolves components, then clean-project commands execute only installed artifacts.

## Durable Implementation Decisions

Normal lifecycle overrides and the permanent design template live in the preset. Concorde-specific
runtime capabilities—including digest-bound `feature.harden` proposal/apply behavior—live in the
extension; agent syntax is presentation only.

## Traceability and Evidence

Clean-install acceptance tests and package receipts trace the installed handoff.

## Known Limitations

Human first-use comprehension evidence remains pending.
