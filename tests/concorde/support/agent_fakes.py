"""Fake ``claude`` and ``pi`` programs for listing the models workers may use.

``fake_agents`` writes both into a directory and returns the variables that make the worker model
configuration and ``configure_workers`` run them instead of the installed programs.
"""

from __future__ import annotations

import os
from pathlib import Path

FAKE_PI = """#!/usr/bin/env python3
import sys
arguments = sys.argv[1:]
if arguments == ["--version"]:
    print("0.87.1")
elif arguments == ["--help"]:
    print("  --thinking <level>             Set thinking level: off, minimal, low, medium, high, xhigh, max")
elif arguments == ["--no-extensions", "--list-models"]:
    print("provider      model            context  max-out  thinking  images")
    print("anthropic     claude-sonnet-5  1M       128K     yes       yes   ")
    print("local-openai  plain-7          200K     64K      no        no    ")
else:
    sys.exit(3)
"""
FAKE_CLAUDE = """#!/usr/bin/env python3
import sys
arguments = sys.argv[1:]
if arguments == ["--version"]:
    print("2.1.281 (Claude Code)")
elif arguments == ["--help"]:
    print("  --effort <level>                      Effort level for the current session")
    print("                                        (low, medium, high, xhigh, max)")
else:
    sys.exit(3)
"""


def fake_agents(directory: Path, home: Path) -> dict:
    """An environment whose ``pi`` and ``claude`` are fakes and whose home is ``home``."""
    directory.mkdir(parents=True, exist_ok=True)
    for name, text in (("pi", FAKE_PI), ("claude", FAKE_CLAUDE)):
        (directory / name).write_text(text)
        (directory / name).chmod(0o755)
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "CONCORDE_PI": str(directory / "pi"),
        "CONCORDE_CLAUDE": str(directory / "claude"),
    }
