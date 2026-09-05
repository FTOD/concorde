"""Validate the distributable Profile 8 boundary without executing Operation entrypoints."""
import ast
import json
from pathlib import Path
from ..model import Finding
from .protocol_contracts import OPERATIONS, INTERNAL_SKILLS, dependencies
from .skill_assets import resolve_skill_prompt, render_capabilities
from .operation_data import json_schema


def validate_package(root: Path) -> list[Finding]:
    findings = []
    def fail(path, message):
        findings.append(Finding("CONCORDE-PACKAGE-008", "error", path, message,
                                "Reconcile the Profile 8 package inventory and projections."))
    try:
        manifest = json.loads((root / "concorde.json").read_text())
        for key, value in {"schema_version":3,"architecture_profile":8,"workspace_protocol":14,
                           "delivery_proposal":10,"skills":list(INTERNAL_SKILLS),"operations":list(OPERATIONS)}.items():
            if manifest.get(key) != value: fail("concorde.json", f"Invalid {key}; expected {value}")
        for folder, names in (("skills", INTERNAL_SKILLS), ("operations", OPERATIONS)):
            actual={p.name for p in (root/folder).iterdir() if p.is_dir() and p.name != "__pycache__"}
            if actual != set(names): fail(folder, "Canonical inventory differs from the manifest")
            for name in names:
                path=f"{folder}/{name}/SKILL.md"
                prompt=resolve_skill_prompt(root/path, "skill" if folder=="skills" else "operation", "")
                if prompt.exposure != ("internal" if folder=="skills" else "public"):
                    fail(path,"Only paired Operations are public")
                if folder=="operations":
                    source=(root/folder/name/"operation.py").read_text()
                    tree=ast.parse(source)
                    literals={t.id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                              for t in n.targets if isinstance(t,ast.Name) and t.id in {"OPERATION_NAME","OPERATION_CAPABILITIES"}}
                    if literals.get("OPERATION_NAME") != name or literals.get("OPERATION_CAPABILITIES") != dependencies(name):
                        fail(path,"Executable dependency declaration differs from the Operation registry")
                    if prompt.capabilities != dependencies(name): fail(path,"Skill dependency declaration differs from registry")
                    if "operation_service import" not in source or "operation_main" not in source:
                        fail(path,"Entry point must delegate to the trusted host")
        for integration in ("claude","codex"):
            if len(render_capabilities(root,integration)) != len(OPERATIONS):
                fail("concorde.json",f"{integration} must expose every paired Operation exactly once")
        names=[f"{op}-{suffix}" for op in OPERATIONS for suffix in ("request","response")]
        names += ["concorde-agent-stage-context","concorde-agent-stage-result"]
        if json.loads((root/"protocol/schemas.json").read_text()) != {name:json_schema(name) for name in names}:
            fail("protocol/schemas.json","Exported contracts differ from executable schemas")
    except (ValueError,OSError,KeyError,TypeError) as exc:
        fail("concorde.json",str(exc))
    return findings
