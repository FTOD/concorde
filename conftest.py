"""pytest entry for the Concorde suite.

This rootdir conftest is loaded for every invocation, whatever paths or option values follow
``pytest``, so the local evidence plugin can register its command-line options before argument
parsing. It makes ``.venv/bin/python -m pytest`` record test reasons, measured input identity and
nested runtime diagnostics without extra flags. The tests themselves remain ``unittest.TestCase``
classes under ``tests/concorde``; pytest-xdist only schedules them across worker processes.
"""

pytest_plugins = ["tests.concorde.support.pytest_timing"]


def pytest_sessionstart(session):
    """Register every owner's typed values once per test process, as the launcher does."""
    from concorde.operations.catalog import register_types

    register_types()
