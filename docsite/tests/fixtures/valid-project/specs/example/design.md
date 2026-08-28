# Design Reference: Example

## Implementation Notes

The fixture module is realized by its feature specifications alone; no runtime code accompanies it.

## Design Rationale

Fixture modules stay minimal so tests exercise Concorde publication behavior, not domain detail.

## Alternatives Considered

A richer fixture hierarchy was rejected because it would duplicate the real Concorde tree.

## Decision Log

- Keep one leaf module with a summary and a design reference.
