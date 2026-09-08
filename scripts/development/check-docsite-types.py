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
    # TypeScript imports the sidebar, not published pages or rendered diagram HTML.
    # Derive the real sidebar in a fresh checkout without requiring publication first.
    prepare = (
        "const {mkdirSync,writeFileSync}=require('node:fs');"
        "const {loadScopedRegistry}=require('./plugins/scoped-content/model.ts');"
        "const {scopedSidebar}=require('./plugins/scoped-content/materialize.ts');"
        "const sidebar=scopedSidebar(loadScopedRegistry('..'));"
        "mkdirSync('.generated',{recursive:true});"
        "writeFileSync('.generated/specs-sidebar.json',JSON.stringify(sidebar,null,2)+'\\n');"
    )
    subprocess.run(["node", "--import", "tsx", "-e", prepare], cwd=DOCSITE, check=True)
    return subprocess.run(["node", str(compiler), "--noEmit", "--project", str(DOCSITE / "tsconfig.json")],
                          cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
