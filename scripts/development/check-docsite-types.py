#!/usr/bin/env python3
"""Run the source checkout's type check, including in a fresh delivery worktree."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCSITE = ROOT / "docsite"


def main() -> int:
    # All preparation happens in an external temporary copy. Configured checks see the actual
    # project read-only, including its ignored caches and generated documentation directories.
    with tempfile.TemporaryDirectory(prefix="concorde-docsite-types-") as directory:
        docsite = Path(directory) / "docsite"
        shutil.copytree(DOCSITE, docsite, ignore=shutil.ignore_patterns(
            "node_modules", ".generated", ".docusaurus", "build", "coverage", "*.tsbuildinfo"))
        return check_copy(docsite)


def check_copy(docsite: Path) -> int:
    # Dependency identity participates in the configured check's input digest too.
    identity = hashlib.sha256(
        (DOCSITE / "package.json").read_bytes() + b"\0" + (DOCSITE / "package-lock.json").read_bytes()
    ).hexdigest()
    marker = DOCSITE / "node_modules/.concorde-typecheck-dependencies"
    installed = DOCSITE / "node_modules"
    if (installed / "typescript/bin/tsc").is_file() and marker.is_file() and marker.read_text() == identity:
        (docsite / "node_modules").symlink_to(installed, target_is_directory=True)
    else:
        subprocess.run(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
                       cwd=docsite, check=True)
    compiler = docsite / "node_modules/typescript/bin/tsc"
    # TypeScript imports the sidebar, not published pages or rendered diagram HTML.
    # Derive the real sidebar in a fresh checkout without requiring publication first.
    prepare = (
        "const {mkdirSync,writeFileSync}=require('node:fs');"
        "const {loadScopedRegistry}=require('./plugins/scoped-content/model.ts');"
        "const {scopedSidebar}=require('./plugins/scoped-content/materialize.ts');"
        "const sidebar=scopedSidebar(loadScopedRegistry(process.argv[1]));"
        "mkdirSync('.generated',{recursive:true});"
        "writeFileSync('.generated/specs-sidebar.json',JSON.stringify(sidebar,null,2)+'\\n');"
    )
    subprocess.run(["node", "--import", "tsx", "-e", prepare, str(ROOT)], cwd=docsite, check=True)
    return subprocess.run(["node", str(compiler), "--noEmit", "--project", str(docsite / "tsconfig.json")],
                          cwd=docsite).returncode


if __name__ == "__main__":
    raise SystemExit(main())
