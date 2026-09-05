#!/usr/bin/env python3
"""Paired entry point for concorde-tasks."""
from pathlib import Path
import sys

OPERATION_NAME = 'concorde-tasks'
OPERATION_CAPABILITIES = ('concorde-task-author',)

def package_root():
    return Path(__file__).resolve().parents[2]

def _runtime():
    source = str(package_root() / "src")
    if source in sys.path:
        sys.path.remove(source)
    sys.path.insert(0, source)
    from concorde.capabilities.operation_service import run_operation, operation_main
    return run_operation, operation_main

def run(configuration, runtime_input, *, host_context):
    return _runtime()[0](OPERATION_NAME, configuration, runtime_input, host_context=host_context)

def main():
    return _runtime()[1](OPERATION_NAME, package_root())

if __name__ == "__main__":
    raise SystemExit(main())
