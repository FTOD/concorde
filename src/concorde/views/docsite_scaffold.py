"""Preview-first scaffold of the packaged docsite adapter into an initialized project."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .docsite_template import (
    DocsiteTemplateError,
    TEMPLATE_ROOT,
    WORKFLOW_TEMPLATE,
    adapter_files,
    template_digest,
    verify_package_root,
    workflow_template,
)
from ..spec.typed_data import TypedDataError, checked_path, safe_path
from ..spec.model import Finding, ToolResult
from ..spec.changes import apply_files, file_change
from ..spec.repository import SpecError, SpecRepository

PROPOSAL_VERSION = 2
SITE_IDENTITY_PATH = f"{TEMPLATE_ROOT}/site.json"
WORKFLOW_SOURCE = f"{TEMPLATE_ROOT}/{WORKFLOW_TEMPLATE}"
WORKFLOW_TARGET = ".github/workflows/deploy-docsite.yml"

_ABSOLUTE_HTTP_URL = re.compile(r"^https?://\S+$")
_ORIGIN_SECTION = 'remote "origin"'
_SSH_GITHUB = re.compile(r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>.+?)(?:\.git)?$")
_HTTPS_GITHUB = re.compile(r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>.+?)(?:\.git)?/?$")
_GITHUB_REPOSITORY = re.compile(r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)$")


def _default_package_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "project"


def _entry_module_title(project_root: Path) -> str | None:
    """The registered entry Module's title, or None when the project is not initialized."""
    try:
        repository = SpecRepository(project_root)
        return repository.targets[repository.entry_target].title
    except (SpecError, TypedDataError, OSError, ValueError, KeyError):
        return None


def _origin_repository(root: Path) -> str | None:
    git_dir = root / ".git"
    if not git_dir.is_dir() or git_dir.is_symlink():
        return None
    config_path = git_dir / "config"
    if not config_path.is_file() or config_path.is_symlink():
        return None
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError:
        return None
    section: str | None = None
    url: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].strip()
            continue
        if section == _ORIGIN_SECTION and "=" in stripped:
            key, _, value = stripped.partition("=")
            if key.strip() == "url":
                url = value.strip()
    if not url:
        return None
    match = _SSH_GITHUB.match(url) or _HTTPS_GITHUB.match(url)
    if match:
        return f"https://github.com/{match.group('owner')}/{match.group('repo')}"
    if _ABSOLUTE_HTTP_URL.match(url):
        return url
    return None


def _validate_identity_inputs(title: str | None, repository: str | None, url: str | None, base_url: str | None) -> list[str]:
    errors: list[str] = []
    if title is not None and not title.strip():
        errors.append("--title must be non-empty")
    if repository is not None and not _ABSOLUTE_HTTP_URL.match(repository):
        errors.append("--repository must be an absolute http(s):// URL")
    if url is not None and not _ABSOLUTE_HTTP_URL.match(url):
        errors.append("--url must be an absolute http(s):// URL")
    if base_url is not None and not (base_url.startswith("/") and base_url.endswith("/")):
        errors.append("--base-url must start and end with '/'")
    return errors


def _resolve_identity(
    title: str,
    repository: str | None,
    url_override: str | None,
    base_url_override: str | None,
) -> tuple[dict[str, Any], Finding | None]:
    github = _GITHUB_REPOSITORY.match(repository) if repository else None
    identity_finding: Finding | None = None
    if github:
        owner, repo = github.group("owner"), github.group("repo")
        default_url = f"https://{owner}.github.io"
        default_base_url = "/" if repo == f"{owner}.github.io" else f"/{repo}/"
        organization_name = owner
        project_name = repo
    else:
        default_url = "https://localhost"
        default_base_url = "/"
        organization_name = project_name = _slug(title)
        identity_finding = Finding(
            "CONCORDE-DOCSITE-009",
            "info",
            SITE_IDENTITY_PATH,
            "Identity defaults could not be derived from a GitHub origin remote.",
            "Edit docsite/site.json to set the final url, baseUrl, organizationName, and projectName, "
            "or pass --repository/--url/--base-url explicitly.",
        )
    identity: dict[str, Any] = {
        "baseUrl": base_url_override if base_url_override is not None else default_base_url,
        "organizationName": organization_name,
        "projectName": project_name,
        "schema_version": 1,
        "title": title,
        "url": url_override if url_override is not None else default_url,
    }
    if repository:
        identity["repository"] = repository
    return identity, identity_finding


def _proposal_entries(
    package: Path,
    adapter: dict[str, bytes],
    identity: dict[str, Any],
    github_pages: bool,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = [{"path": path, "content": content, "source": path} for path, content in adapter.items()]
    identity_bytes = (json.dumps(identity, indent=2, sort_keys=True) + "\n").encode("utf-8")
    entries.append({"path": SITE_IDENTITY_PATH, "content": identity_bytes, "source": None})
    if github_pages:
        entries.append({"path": WORKFLOW_TARGET, "content": workflow_template(package), "source": WORKFLOW_SOURCE})
    return sorted(entries, key=lambda entry: entry["path"])


def _file_entry(path: str, content: bytes, source: str | None) -> dict[str, Any]:
    digest = "sha256:" + hashlib.sha256(content).hexdigest()
    if source is not None:
        return {"path": path, "sha256": digest, "source": source}
    return {"path": path, "sha256": digest, "content": content.decode("utf-8")}


def _detect_prerequisites(root: Path) -> list[dict[str, Any]]:
    prerequisites: list[dict[str, Any]] = []
    node = shutil.which("node")
    if node is None:
        prerequisites.append({"name": "node", "status": "missing", "detail": "Node.js was not found on PATH."})
    else:
        try:
            result = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=5)
            version = result.stdout.strip() or result.stderr.strip()
            match = re.match(r"v?(\d+)", version)
            major = int(match.group(1)) if match else 0
            if not match or major < 20:
                prerequisites.append(
                    {"name": "node", "status": "outdated", "detail": f"Node.js {version or 'unknown'} was found; Node.js 20 or newer is required."}
                )
            else:
                prerequisites.append({"name": "node", "status": "present", "detail": version})
        except (OSError, subprocess.SubprocessError) as error:
            prerequisites.append({"name": "node", "status": "missing", "detail": f"Node.js version check failed: {error}"})
    npm = shutil.which("npm")
    if npm is None:
        prerequisites.append({"name": "npm", "status": "missing", "detail": "npm was not found on PATH."})
    else:
        prerequisites.append({"name": "npm", "status": "present", "detail": npm})
    return prerequisites


def _prerequisite_findings(prerequisites: list[dict[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []
    for item in prerequisites:
        if item["status"] not in {"missing", "outdated"}:
            continue
        findings.append(
            Finding(
                "CONCORDE-DOCSITE-007",
                "warning",
                f"{TEMPLATE_ROOT}/",
                f"{item['name']} is {item['status']}: {item['detail']}",
                "Install Node.js 20+ and npm, then retry.",
            )
        )
    return findings


def propose_docsite(
    project_root: str | Path,
    *,
    title: str | None = None,
    repository: str | None = None,
    url: str | None = None,
    base_url: str | None = None,
    github_pages: bool = False,
    package_root: str | Path | None = None,
) -> ToolResult:
    root = Path(project_root).resolve()
    package = Path(package_root).resolve() if package_root is not None else _default_package_root()

    entry_title = _entry_module_title(root)
    if entry_title is None:
        finding = Finding(
            "CONCORDE-DOCSITE-001",
            "error",
            ".concorde/config.json",
            "The project has no configured Spec entry target.",
            "Propose and apply project initialization first.",
        )
        return ToolResult("docsite", ".", "invalid", findings=(finding,))

    try:
        verify_package_root(package)
    except DocsiteTemplateError as error:
        finding = Finding(
            "CONCORDE-DOCSITE-002",
            "error",
            TEMPLATE_ROOT,
            f"The docsite package template is missing or invalid: {error}",
            "Install or reinstall Concorde so the docsite/ package template root is present.",
        )
        return ToolResult("docsite", ".", "invalid", findings=(finding,))

    errors = _validate_identity_inputs(title, repository, url, base_url)
    if errors:
        finding = Finding(
            "CONCORDE-DOCSITE-003",
            "error",
            SITE_IDENTITY_PATH,
            "; ".join(errors),
            "Pass a non-empty --title, absolute http(s):// --repository/--url, and a --base-url that starts and ends with '/'.",
        )
        return ToolResult("docsite", ".", "invalid", findings=(finding,))

    resolved_title = title if title is not None else (entry_title.strip() or root.name)
    resolved_repository = repository if repository is not None else _origin_repository(root)
    identity, identity_finding = _resolve_identity(resolved_title, resolved_repository, url, base_url)

    adapter = adapter_files(package)
    entries = _proposal_entries(package, adapter, identity, github_pages)
    files = [_file_entry(entry["path"], entry["content"], entry["source"]) for entry in entries]
    conflicts = [
        {"path": entry["path"], "reason": "target already exists"}
        for entry in entries
        if (root / entry["path"]).exists() or (root / entry["path"]).is_symlink()
    ]
    proposal = {
        "proposal_version": PROPOSAL_VERSION,
        "template_root": TEMPLATE_ROOT,
        "template_digest": template_digest(adapter),
        "identity": identity,
        "github_pages": github_pages,
        "files": files,
        "conflicts": conflicts,
    }

    prerequisites = _detect_prerequisites(root)
    findings = _prerequisite_findings(prerequisites)
    if identity_finding is not None:
        findings.append(identity_finding)

    result = {"proposal": proposal, "prerequisites": prerequisites}
    exact = [
        (root / entry["path"]).is_file() and (root / entry["path"]).read_bytes() == entry["content"]
        for entry in entries
    ]
    if all(exact):
        return ToolResult(
            "docsite",
            ".",
            "unchanged",
            tuple(sorted(entry["path"] for entry in entries)),
            findings=tuple(findings),
            result=result,
        )
    return ToolResult("docsite", ".", "proposal", findings=tuple(findings), result=result)


def _load_accepted(root: Path, package: Path, proposal_path: str) -> tuple[dict[str, bytes], dict[str, Any], bool, str]:
    path = checked_path(root, safe_path(proposal_path))
    value = json.loads(path.read_text(encoding="utf-8"))
    value = value.get("result", {}).get("proposal", value.get("proposal", value))
    if not isinstance(value, dict) or value.get("proposal_version") != PROPOSAL_VERSION:
        raise ValueError("unsupported or missing proposal_version; regenerate with docsite --propose (proposal version 2)")
    files = value.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("proposal files must be a non-empty list")
    identity = value.get("identity")
    if not isinstance(identity, dict):
        raise ValueError("proposal identity must be an object")
    github_pages = value.get("github_pages")
    if not isinstance(github_pages, bool):
        raise ValueError("proposal github_pages must be a boolean")
    if value.get("template_root") != TEMPLATE_ROOT:
        raise ValueError("proposal template_root must be docsite")

    adapter = adapter_files(package)
    actual_digest = template_digest(adapter)
    if actual_digest != value.get("template_digest"):
        raise ValueError("package bytes are stale relative to the accepted proposal template digest")

    # Reconstruct the sole permitted inventory before touching any destination.
    # Equality also enforces ordering, uniqueness, closed entry shapes, mappings,
    # identity serialization and the current content hashes.
    entries = _proposal_entries(package, adapter, identity, github_pages)
    expected = [_file_entry(entry["path"], entry["content"], entry["source"])
                for entry in entries]
    if files != expected:
        raise ValueError("proposal files must match the complete exact scaffold inventory and content hashes")
    resolved = {entry["path"]: entry["content"] for entry in entries}
    return resolved, identity, github_pages, actual_digest


def apply_docsite(
    project_root: str | Path,
    proposal_path: str,
    *,
    package_root: str | Path | None = None,
) -> ToolResult:
    root = Path(project_root).resolve()
    package = Path(package_root).resolve() if package_root is not None else _default_package_root()
    try:
        resolved, identity, github_pages, digest = _load_accepted(root, package, proposal_path)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, DocsiteTemplateError) as error:
        finding = Finding(
            "CONCORDE-DOCSITE-004",
            "error",
            SITE_IDENTITY_PATH,
            f"Accepted proposal is invalid: {error}",
            "Save the exact proposal JSON produced by the propose Tool at a safe project-relative path and retry, "
            "or run the propose Tool again if the package changed.",
        )
        return ToolResult("docsite", ".", "invalid", findings=(finding,))

    states = {
        relative: "missing"
        if not (target := root / relative).exists()
        else "exact"
        if target.is_file() and target.read_bytes() == content
        else "changed"
        for relative, content in resolved.items()
    }
    if all(state == "exact" for state in states.values()):
        return ToolResult(
            "docsite",
            ".",
            "unchanged",
            tuple(sorted(resolved)),
            result={"identity": identity, "template_digest": digest, "github_pages": github_pages},
        )
    if any(state != "missing" for state in states.values()):
        findings = tuple(
            Finding(
                "CONCORDE-DOCSITE-005",
                "error",
                path,
                f"Target is {state}; exact accepted content cannot be promoted.",
                "Move or reconcile the existing target, then accept a fresh proposal.",
            )
            for path, state in sorted(states.items())
            if state != "missing"
        )
        return ToolResult(
            "docsite",
            ".",
            "conflict",
            findings=findings,
            result={"conflicts": [path for path, state in sorted(states.items()) if state != "missing"]},
        )
    try:
        changes = [file_change(root, path, content.decode("utf-8")) for path, content in sorted(resolved.items())]
        created = apply_files(root, changes, set(resolved))
    except (OSError, SpecError, TypedDataError, UnicodeError) as error:
        finding = Finding(
            "CONCORDE-DOCSITE-006",
            "error",
            SITE_IDENTITY_PATH,
            f"Staged promotion failed: {error}",
            "Resolve the filesystem failure and retry the accepted proposal.",
        )
        return ToolResult("docsite", ".", "failed", findings=(finding,))
    return ToolResult(
        "docsite",
        ".",
        "success",
        tuple(created),
        result={"created": created, "identity": identity, "template_digest": digest, "github_pages": github_pages},
    )
