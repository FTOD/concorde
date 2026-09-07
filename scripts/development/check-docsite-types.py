#!/usr/bin/env python3
"""Run the source checkout's type check, including in a fresh delivery worktree."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCSITE = ROOT / "docsite"


def main() -> int:
    # Dependency identity participates in the configured check's input digest too.
    identity = hashlib.sha256(
        (DOCSITE / "package.json").read_bytes() + b"\0" + (DOCSITE / "package-lock.json").read_bytes()
    ).hexdigest()
    marker = DOCSITE / "node_modules/.concorde-typecheck-dependencies"
    compiler = DOCSITE / "node_modules/typescript/bin/tsc"
    if not compiler.is_file() or not marker.is_file() or marker.read_text() != identity:
        subprocess.run(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
                       cwd=DOCSITE, check=True)
        marker.write_text(identity)
    # Generate the Profile 8 sidebar that sidebars.specs.ts imports.
    prepare = (
        "const {loadScopedRegistry}=require('./plugins/scoped-content/model.ts');"
        "const {materializeScoped}=require('./plugins/scoped-content/materialize.ts');"
        "materializeScoped(loadScopedRegistry('..')).catch(error=>{console.error(error);process.exitCode=1;});"
    )
    subprocess.run(["node", "--import", "tsx", "-e", prepare], cwd=DOCSITE, check=True)
    return subprocess.run(["node", str(compiler), "--noEmit", "--project", str(DOCSITE / "tsconfig.json")],
                          cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
