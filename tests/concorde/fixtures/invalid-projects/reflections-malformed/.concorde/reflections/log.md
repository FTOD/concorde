# Reflections: Example

### R-001 · Missing effect

- **Phase**: plan
- **Date**: 2026-08-28
- **Feature**: feature.example.deliver
- **Kind**: specification
- **Concerns**: feature.example.deliver
- **Expected**: A field set.
- **Observed**: The Effect field was omitted.
- **Action**: Continued.
- **Improvement**: Add the field.
- **Status**: open

### R-001 · Duplicate identifier

- **Phase**: implement
- **Date**: 2026-08-28
- **Feature**: feature.example.deliver
- **Kind**: tooling
- **Concerns**: specs/example/architecture.md
- **Expected**: Unique identifiers.
- **Observed**: R-001 reused.
- **Effect**: assumed
- **Action**: Continued.
- **Improvement**: Renumber.
- **Status**: open

### R-002 · Invalid kind

- **Phase**: implement
- **Date**: 2026-08-28
- **Feature**: feature.example.deliver
- **Kind**: bug
- **Concerns**: contract.example.workflow
- **Expected**: A fixed vocabulary.
- **Observed**: A free-text kind.
- **Effect**: worked-around
- **Action**: Continued.
- **Improvement**: Use a fixed kind.
- **Status**: open

### R-003 · Unknown feature

- **Phase**: analyze
- **Date**: 2026-08-28
- **Feature**: feature.example.missing
- **Kind**: architecture
- **Concerns**: module.example.api
- **Expected**: Attribution to a known feature.
- **Observed**: Attributed to a feature that does not exist.
- **Effect**: deferred
- **Action**: Continued.
- **Improvement**: Attribute correctly.
- **Status**: resolved
- **Note**: Fixed in the fixture narrative.
