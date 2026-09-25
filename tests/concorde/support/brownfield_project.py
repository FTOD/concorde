"""An existing codebase adopted by Concorde: installed, initialized and committed, never specified.

The root Module ``module.shop`` (entry ``specs/project/module.md``) binds every existing file, as
initialization leaves it: ``src/checkout/``, ``src/inventory/``, ``src/db.py``, ``tests/``,
``README.md``, ``pyproject.toml`` and ``.gitignore``. ``run`` runs ``concorde run`` in-process with
the fake ``claude`` of the worker tests, whose plan is taken from ``FAKE-PLAN: <json>`` in the brief.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from concorde.distribution.project_defaults import install_project_defaults
from concorde.operations.host import execute
from concorde.spec.initialize import apply_project_proposal, project_proposal
from concorde.tasks import store
from tests.concorde.support.paths import REPOSITORY_ROOT

FAKE = REPOSITORY_ROOT / "tests/concorde/harness/workers/fake_claude.py"

FILES = {
    "README.md": "# Shop\n\nA small shop.\n",
    "pyproject.toml": '[project]\nname = "shop"\n\n[tool.pytest.ini_options]\ntestpaths = ["tests"]\n',
    ".gitignore": (
        ".concorde/runs/\n.concorde/tasks/\n.concorde/worker-models.json\n"
        ".claude/worktrees/\n__pycache__/\n"
    ),
    "src/checkout/api.py": (
        "from inventory.stock import hold\n\n\ndef submit(basket):\n"
        "    hold(basket)\n    return {'order': 1}\n"
    ),
    "src/checkout/payment.py": (
        "def charge(card, amount, retry=True):\n"
        "    try:\n        return card.pay(amount)\n"
        "    except DeclinedError:\n        if retry:\n"
        "            return charge(card, amount, retry=False)\n        raise\n"
    ),
    "src/inventory/stock.py": "STOCK = {}\n\n\ndef hold(basket):\n    return True\n",
    "src/db.py": "def connect():\n    return None\n",
    "tests/test_checkout.py": "def test_submit():\n    assert True\n",
}


def git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    ).stdout


def commit(root: Path, message: str = "change") -> None:
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", message)


class BrownfieldProject:
    """A committed, initialized codebase whose root Module binds every existing file."""

    ENTRY = "specs/project/module.md"

    def __init__(self, test):
        directory = tempfile.TemporaryDirectory()
        test.addCleanup(directory.cleanup)
        self.base = Path(os.path.realpath(directory.name))
        self.root = self.base / "shop"
        self.home = self.base / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.root.mkdir()
        git(self.root, "init", "-q")
        for path, content in FILES.items():
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text(content)
        install_project_defaults(self.root, REPOSITORY_ROOT)
        proposal = project_proposal(self.root, REPOSITORY_ROOT, "Shop", "module.shop")
        apply_project_proposal(self.root, REPOSITORY_ROOT, proposal)
        commit(self.root, "adopt Concorde")
        self.fake = self.base / "claude"
        self.fake.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{FAKE}" "$@"\n')
        self.fake.chmod(0o755)

    def open_task(self, task_id: str = "adopt", modules=("module.shop",)) -> dict:
        return store.open_task(self.root, task_id, "describe the code", list(modules))

    def worktree(self, task_id: str = "adopt") -> Path:
        return Path(store.load_task(self.root, task_id)["worktree"])

    def run(self, *argv: str, cwd: Path | None = None) -> tuple[int, dict]:
        values = {"CONCORDE_CLAUDE": str(self.fake), "CONCORDE_CLIENT": "claude"}
        with (
            patch.dict(os.environ, values),
            patch("pathlib.Path.home", return_value=self.home),
        ):
            return execute(list(argv), cwd=cwd or self.root)

    def answers(self, *items: dict) -> str:
        path = self.base / f"answers-{len(list(self.base.glob('answers-*')))}.json"
        path.write_text(json.dumps({"answers": list(items)}))
        return str(path)

    @staticmethod
    def plan(rounds) -> str:
        """A ``--goal`` carrying the fake worker's plan."""
        return "FAKE-PLAN: " + json.dumps(rounds)


__all__ = ["BrownfieldProject", "commit", "git"]
