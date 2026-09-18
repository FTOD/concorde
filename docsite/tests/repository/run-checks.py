"""Host-only repository regressions with dependency preparation in disposable scratch.

The configured read-only check grants repository inputs independently of programmer authority.
Install the copied lockfile's dependencies and run builds against a source copy outside
the candidate; all dependency preparation and generated outputs stay in scratch.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DIRECTORIES = (
    "operations",
    "prompts",
    "skills",
    "src",
    "protocol",
    "specs",
    "pi",
    "docs",
    "scripts",
    "tests",
    "docsite",
    "reference",
    "templates",
)
FILES = (
    "concorde.json",
    "pyproject.toml",
    "README.md",
    "uv.lock",
    ".concorde/config.json",
    ".concorde/specs.json",
    ".github/workflows/deploy-docsite.yml",
)


def uncopied_listing_roots() -> list[str]:
    """Registry listing entries whose top-level name this copy would leave out.

    The copied project is validated, so every non-pending entry must exist in it. Deriving the
    complaint from the registry keeps a new listing root from silently emptying these checks.
    A source whose registry cannot be read carries no listing to compare, as in the preparation
    fixtures that drive this script over stub inputs.
    """
    try:
        registry = json.loads(
            (ROOT / ".concorde/specs.json").read_text(encoding="utf-8")
        )
        listed = {
            entry.split("/")[0]
            for target in registry["targets"]
            for entry in target["files"]
        }
    except (
        OSError,
        UnicodeDecodeError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
    ):
        return []
    return sorted(listed - set(DIRECTORIES) - {name.split("/")[0] for name in FILES})


def main() -> int:
    missing = uncopied_listing_roots()
    if missing:
        print(
            "Registry lists implementation roots this check does not copy:",
            ", ".join(missing),
            flush=True,
        )
        return 1
    with tempfile.TemporaryDirectory(prefix="concorde-publication-check-") as temporary:
        project = Path(temporary) / "project"
        project.mkdir()
        disposable = shutil.ignore_patterns(
            "node_modules",
            "__pycache__",
            ".venv",
            ".generated",
            ".docusaurus",
            "coverage",
            "*.pyc",
            "*.tsbuildinfo",
        )
        for name in DIRECTORIES:
            source = ROOT / name
            if source.is_dir():

                def ignore(directory, names, source=source):
                    # Generated output sits directly under a copied directory; a listed fixture
                    # deeper in the tree may legitimately be named build or coverage.
                    top = {"build", "coverage"} if Path(directory) == source else set()
                    return disposable(directory, names) | (top & set(names))

                shutil.copytree(source, project / name, ignore=ignore)
        for name in FILES:
            destination = project / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        environment = {
            **os.environ,
            "PYTHONPATH": str(project / "src"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "CONCORDE_PYTHON": sys.executable,
        }
        commands = [
            (
                ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
                project / "docsite",
            ),
            ([sys.executable, "scripts/concorde.py", "build"], project),
            (
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "tests.concorde.views.test_docsite_scaffold",
                    "tests.concorde.views.test_docsite_template",
                    "tests.concorde.views.test_scaffold_creation",
                    "tests.concorde.views.test_repository_checks",
                ],
                project,
            ),
            (
                [
                    "node",
                    "node_modules/vitest/vitest.mjs",
                    "run",
                    "--maxWorkers",
                    "2",
                    "--no-file-parallelism",
                ],
                project / "docsite",
            ),
        ]
        for argv, directory in commands:
            print("Host repository check:", " ".join(argv), flush=True)
            result = subprocess.run(argv, cwd=directory, env=environment)
            if result.returncode:
                return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
