"""Package-level Script, Skill, and Operation capability rules."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Iterable

from ..frontmatter import FrontMatterError, parse_document
from ..model import Finding
from ..skill_assets import SKILL_NAME


def _finding(rule: str, source: str, message: str, remediation: str) -> Finding:
    return Finding(rule, "error", source, message, remediation, subject_id="module.concorde")


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _real_files(directory: Path) -> set[str]:
    result: set[str] = set()
    if not directory.is_dir() or directory.is_symlink():
        return result
    for path in directory.iterdir():
        if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}:
            continue
        result.add(path.name)
    return result


def _manifest(root: Path) -> dict[str, Any] | None:
    path = root / "concorde.json"
    if path.is_symlink() or not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _names(value: Any) -> tuple[str, ...] | None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and SKILL_NAME.fullmatch(item) for item in value
    ):
        return None
    return tuple(value)


def _literal(tree: ast.Module, name: str) -> Any:
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in statement.targets
        ):
            return ast.literal_eval(statement.value)
        if (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.target.id == name
            and statement.value is not None
        ):
            return ast.literal_eval(statement.value)
    raise ValueError(f"missing literal {name}")


def _operation_python(path: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
    declared = _literal(tree, "OPERATION_SKILLS")
    stages = _literal(tree, "OPERATION_STAGES")
    if not isinstance(declared, tuple) or not all(isinstance(item, str) for item in declared):
        raise ValueError("OPERATION_SKILLS must be a literal tuple of Skill names")
    if not isinstance(stages, tuple) or not stages:
        raise ValueError("OPERATION_STAGES must be a non-empty literal tuple")
    flattened: list[str] = []
    stage_names: list[str] = []
    for item in stages:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not isinstance(item[1], tuple)
            or not item[1]
            or not all(isinstance(skill, str) for skill in item[1])
        ):
            raise ValueError("every OPERATION_STAGES item must be (stage, non-empty Skill tuple)")
        stage_names.append(item[0])
        flattened.extend(item[1])
    if len(stage_names) != len(set(stage_names)):
        raise ValueError("OPERATION_STAGES names must be unique")
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    if "build_operation" not in names:
        raise ValueError("operation.py must build through the shared LangGraph operation runtime")
    return tuple(declared), tuple(flattened)


def capability_source_paths(project_root: str | Path) -> tuple[str, ...]:
    """Return current package capability sources that participate in self-validation digest."""

    root = Path(project_root)
    manifest = _manifest(root)
    if manifest is None or manifest.get("name") != "concorde":
        return ()
    paths: list[str] = ["concorde.json"]
    for directory_name in ("scripts", "skills", "operations"):
        directory = root / directory_name
        if not directory.is_dir() or directory.is_symlink():
            continue
        for path in sorted(directory.rglob("*")):
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            if path.is_file() and not path.is_symlink():
                paths.append(_relative(root, path))
    return tuple(sorted(set(paths)))


def validate_capabilities(package: Any) -> list[Finding]:
    """Validate canonical package capabilities without importing or executing Operation Python."""

    root = Path(package.project_root)
    manifest = _manifest(root)
    if manifest is None or manifest.get("name") != "concorde":
        return []
    findings: list[Finding] = []
    if manifest.get("schema_version") != 2:
        findings.append(_finding(
            "CONCORDE-CAPABILITY-MANIFEST-001",
            "concorde.json",
            "Concorde capability sources require Package Manifest 2.",
            "Declare schema_version 2 with skills, operations, and the canonical package roots.",
        ))
    skills = _names(manifest.get("skills"))
    operations = _names(manifest.get("operations"))
    if skills is None or operations is None:
        findings.append(_finding(
            "CONCORDE-CAPABILITY-MANIFEST-001",
            "concorde.json",
            "Manifest skills and operations must be unique safe-name lists.",
            "Declare safe lowercase hyphenated Skill and Operation inventories.",
        ))
        skills = skills or ()
        operations = operations or ()
    if len(skills) != len(set(skills)) or len(operations) != len(set(operations)):
        findings.append(_finding(
            "CONCORDE-CAPABILITY-ID-001",
            "concorde.json",
            "Capability inventories contain duplicate names.",
            "Keep every Skill and Operation name unique.",
        ))
    collisions = sorted(set(skills) & set(operations))
    folded = [name.casefold() for name in (*skills, *operations)]
    if collisions or len(folded) != len(set(folded)):
        findings.append(_finding(
            "CONCORDE-CAPABILITY-ID-001",
            "concorde.json",
            f"Skills and Operations must share one collision-free namespace: {collisions}",
            "Rename colliding capabilities and update their source/projection identity together.",
        ))

    expected_roots = ["agent-assets", "operations", "scripts", "skills", "src", "templates"]
    if manifest.get("package_roots") != expected_roots:
        findings.append(_finding(
            "CONCORDE-CAPABILITY-MANIFEST-001",
            "concorde.json",
            "Package roots do not match the structural capability model.",
            f"Declare package_roots exactly as {expected_roots}.",
        ))

    for legacy in ("commands", "examples"):
        if (root / legacy).exists():
            findings.append(_finding(
                "CONCORDE-CAPABILITY-LEGACY",
                legacy,
                f"Legacy capability root '{legacy}/' remains.",
                "Move leaf prompts to skills/ and maintained LangGraphs to paired operations/.",
            ))

    for kind, declared in (("skill", skills), ("operation", operations)):
        root_name = "skills" if kind == "skill" else "operations"
        capability_root = root / root_name
        if capability_root.is_symlink() or not capability_root.is_dir():
            findings.append(_finding(
                "CONCORDE-CAPABILITY-MANIFEST-001",
                root_name,
                f"Canonical {root_name}/ is missing or unsafe.",
                f"Create one real {root_name}/ directory matching the manifest inventory.",
            ))
            continue
        observed = sorted(
            path.name for path in capability_root.iterdir()
            if path.name != "__pycache__" and path.is_dir() and not path.is_symlink()
        )
        if observed != sorted(declared):
            findings.append(_finding(
                "CONCORDE-CAPABILITY-MANIFEST-001",
                root_name,
                f"Manifest {root_name} inventory differs from physical directories.",
                "Reconcile the manifest and exact canonical capability directories.",
            ))

    for name in skills:
        directory = root / "skills" / name
        source = f"skills/{name}"
        observed = _real_files(directory)
        if directory.is_symlink() or observed != {"SKILL.md"}:
            findings.append(_finding(
                "CONCORDE-SKILL-001",
                source,
                f"Leaf Skill must contain exactly one real SKILL.md; found {sorted(observed)}.",
                "Remove Python, graph, symlink, and extra entries from the leaf Skill directory.",
            ))
            continue
        try:
            metadata, body = parse_document(
                (directory / "SKILL.md").read_text(encoding="utf-8"),
                f"{source}/SKILL.md",
            )
        except (OSError, UnicodeError, FrontMatterError) as error:
            findings.append(_finding("CONCORDE-SKILL-001", source, str(error), "Repair the leaf SKILL.md front matter."))
            continue
        if metadata.get("name") != name or "operation" in metadata or "skills" in metadata:
            findings.append(_finding(
                "CONCORDE-SKILL-002",
                f"{source}/SKILL.md",
                "Leaf Skill identity or metadata declares Operation composition.",
                "Match the directory name and keep operation/skills metadata only in paired Operations.",
            ))
        if not body.strip():
            findings.append(_finding("CONCORDE-SKILL-001", source, "Leaf Skill prompt is empty.", "Author one complete leaf capability prompt."))

    skill_set = set(skills)
    for name in operations:
        directory = root / "operations" / name
        source = f"operations/{name}"
        observed = _real_files(directory)
        if directory.is_symlink() or observed != {"SKILL.md", "operation.py"}:
            findings.append(_finding(
                "CONCORDE-OPERATION-001",
                source,
                f"Operation must contain exactly operation.py and SKILL.md; found {sorted(observed)}.",
                "Create the exact real Python/Markdown pair and remove every extra entry.",
            ))
            continue
        skill_path = directory / "SKILL.md"
        python_path = directory / "operation.py"
        if skill_path.is_symlink() or python_path.is_symlink():
            findings.append(_finding("CONCORDE-OPERATION-001", source, "Operation pair may not use symlinks.", "Use two real colocated files."))
            continue
        try:
            metadata, body = parse_document(skill_path.read_text(encoding="utf-8"), _relative(root, skill_path))
        except (OSError, UnicodeError, FrontMatterError) as error:
            findings.append(_finding("CONCORDE-OPERATION-004", source, str(error), "Repair the paired Operation SKILL.md."))
            continue
        declared_skills = _names(metadata.get("skills"))
        if metadata.get("name") != name or metadata.get("operation") != "operation.py" or not body.strip():
            findings.append(_finding(
                "CONCORDE-OPERATION-004",
                _relative(root, skill_path),
                "Operation SKILL.md does not identify its name, paired graph, and complete prompt.",
                "Declare matching name, operation: operation.py, leaf skills, and a complete body.",
            ))
        if declared_skills is None or len(declared_skills) < 2 or set(declared_skills) - skill_set:
            findings.append(_finding(
                "CONCORDE-OPERATION-003",
                _relative(root, skill_path),
                "Operation must declare at least two existing leaf Skills.",
                "Declare two or more unique names from the manifest skills inventory.",
            ))
            declared_skills = declared_skills or ()
        try:
            python_skills, flattened = _operation_python(python_path)
            if tuple(declared_skills) != python_skills or python_skills != flattened:
                raise ValueError("Markdown, OPERATION_SKILLS, and flattened OPERATION_STAGES disagree")
        except (OSError, UnicodeError, SyntaxError, ValueError) as error:
            findings.append(_finding(
                "CONCORDE-OPERATION-002",
                _relative(root, python_path),
                f"Operation graph declaration is invalid: {error}",
                "Use literal matching OPERATION_SKILLS/OPERATION_STAGES and the shared LangGraph runtime.",
            ))

    scripts = root / "scripts"
    if scripts.is_dir() and not scripts.is_symlink():
        for path in sorted(scripts.rglob("*.py")):
            if "__pycache__" in path.parts or path.is_symlink():
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
            except (OSError, UnicodeError, SyntaxError):
                continue
            imports = {
                node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
            } | {
                alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
            }
            if any(value == "langgraph" or value.startswith("langgraph.") for value in imports):
                findings.append(_finding(
                    "CONCORDE-SCRIPT-001",
                    _relative(root, path),
                    "A basic Script imports LangGraph Operation topology.",
                    "Move multi-Skill graph control into an exact operations/<name>/ pair.",
                ))
    return findings
