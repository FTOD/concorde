# TL;DR: Atomic Feature

`feature.example.atomic` · specified at `module.example` · one minute.

## Purpose

Atomic Feature delivers its observable outcome for the fixture maintainer.

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

- [spec.md](spec.md) and [design.md](design.md).
