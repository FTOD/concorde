# Feature Abstract: Invoke

`feature.example.api.invoke` · specified at `module.example.api` · one minute.

## Purpose

Invoke delivers its observable outcome for the fixture maintainer.

## Functionality

The feature provides the behavior its specification defines and nothing else.

## Structure

```text
maintainer ──▶ providing module ──▶ boundary contract
```

## Logic

1. The maintainer invokes the feature.
2. The providing module realizes it through its contracts.

**Rules the implementation must keep**

- The realization stays within the specified behavior.

## Read Next

- [design.md](design.md) and [implementation.md](implementation.md).
