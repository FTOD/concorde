"""Host-only repository regressions in disposable scratch; never install dependencies.

The configured read-only check grants repository inputs independently of programmer authority.
Production tests write builds, so run them against a source copy outside the candidate.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[3]
DIRECTORIES = ("agents", "capabilities", "prompts", "skills", "src", "protocol", "specs",
               "docs", "scripts", "tests", "docsite")
FILES = ("concorde.json", "pyproject.toml", "README.md", "skills-lock.json", ".concorde/config.json", ".concorde/specs.json",
         ".github/workflows/deploy-docsite.yml")


def main() -> int:
    installed = ROOT / "docsite/node_modules"
    if not (installed / "vitest/vitest.mjs").is_file():
        raise RuntimeError("Host publication checks require existing docsite/node_modules; no acquisition is allowed")
    with tempfile.TemporaryDirectory(prefix="concorde-publication-check-") as temporary:
        project = Path(temporary) / "project"
        project.mkdir()
        for name in DIRECTORIES:
            source = ROOT / name
            if source.is_dir():
                shutil.copytree(source, project / name, ignore=shutil.ignore_patterns(
                    "node_modules", "__pycache__", ".venv", ".generated", ".docusaurus",
                    "build", "coverage", "*.pyc", "*.tsbuildinfo"))
        for name in FILES:
            destination = project / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        (project / "docsite/node_modules").symlink_to(installed, target_is_directory=True)
        environment = {**os.environ, "PYTHONPATH": str(project / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
        commands = [
            ([sys.executable, "scripts/concorde.py", "build"], project),
            ([sys.executable, "-m", "unittest", "tests.concorde.views.test_ua_graph",
              "tests.concorde.views.test_viewer_launcher", "tests.concorde.views.test_docsite_scaffold",
              "tests.concorde.views.test_docsite_template"], project),
            (["node", "node_modules/vitest/vitest.mjs", "run", "--maxWorkers", "2",
              "--no-file-parallelism"], project / "docsite"),
        ]
        for argv, directory in commands:
            print("Host repository check:", " ".join(argv), flush=True)
            result = subprocess.run(argv, cwd=directory, env=environment)
            if result.returncode:
                return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
