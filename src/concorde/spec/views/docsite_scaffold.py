"""Preview-first scaffold of the packaged docsite adapter into an initialized project."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from ..errors import system_cause
from ..model import Finding, ToolResult
from ..repository import SpecError, SpecRepository
from ..typed_data import TypedDataError, checked_path, safe_path
from .creation import create_files
from .docsite_template import (
    TEMPLATE_ROOT,
    WORKFLOW_TEMPLATE,
    DocsiteTemplateError,
    adapter_files,
    template_digest,
    verify_package_root,
    workflow_template,
)

PROPOSAL_VERSION = 2
SITE_IDENTITY_PATH = f"{TEMPLATE_ROOT}/site.json"
WORKFLOW_SOURCE = f"{TEMPLATE_ROOT}/{WORKFLOW_TEMPLATE}"
WORKFLOW_TARGET = ".github/workflows/deploy-docsite.yml"

_IDENTITY_FIELDS = frozenset(
    ("schema_version", "title", "url", "baseUrl", "organizationName", "projectName")
)
_PROPOSAL_FIELDS = frozenset(
    (
        "proposal_version",
        "template_root",
        "template_digest",
        "identity",
        "github_pages",
        "files",
        "conflicts",
    )
)
_SSH_GITHUB = re.compile(r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>.+?)(?:\.git)?$")
_HTTPS_GITHUB = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>.+?)(?:\.git)?/?$"
)
_GITHUB_REPOSITORY = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)$"
)


def _default_package_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "project"


def _entry_module_title(project_root: Path) -> str | None:
    """The root Module's title (the Module no other Module contains), or None when uninitialized."""
    try:
        repository = SpecRepository(project_root)
        return repository.modules[repository.root_module].title
    except (SpecError, TypedDataError, OSError, ValueError, KeyError):
        return None


def _absolute_http_url(value: str) -> bool:
    """An absolute http(s) URL with a host and no whitespace."""
    if not value or any(character.isspace() for character in value):
        return False
    try:
        parts = urlsplit(value)
        return parts.scheme.lower() in {"http", "https"} and bool(parts.hostname)
    except ValueError:
        return False


def _git(root: Path, *arguments: str) -> str | None:
    """Git's answer in ``root``, read from no environment override, or None when it fails."""
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            text=True,
            timeout=10,
            env=environment,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout.strip() if completed.returncode == 0 else None


def _origin_repository(root: Path) -> str | None:
    """The ``origin`` remote of the repository whose working tree ``root`` is, primary or linked."""
    if not (root / ".git").exists():
        return None
    top = _git(root, "rev-parse", "--show-toplevel")
    if top is None or Path(top).resolve() != root.resolve():
        return None
    url = _git(root, "config", "--get", "remote.origin.url")
    if not url:
        return None
    match = _SSH_GITHUB.match(url) or _HTTPS_GITHUB.match(url)
    if match:
        return f"https://github.com/{match.group('owner')}/{match.group('repo')}"
    if _absolute_http_url(url):
        return url
    return None


def _template_invalid(error: DocsiteTemplateError) -> ToolResult:
    finding = Finding(
        "CONCORDE-DOCSITE-002",
        "error",
        TEMPLATE_ROOT,
        f"The docsite package template is missing or invalid: {error}",
        "Install or reinstall Concorde so the docsite/ package template root is present.",
    )
    return ToolResult("docsite", ".", "invalid", findings=(finding,), error=error)


def _validate_identity_inputs(
    title: str | None, repository: str | None, url: str | None, base_url: str | None
) -> list[str]:
    errors: list[str] = []
    if title is not None and not title.strip():
        errors.append("--title must be non-empty")
    if repository is not None and not _absolute_http_url(repository):
        errors.append("--repository must be an absolute http(s):// URL")
    if url is not None and not _absolute_http_url(url):
        errors.append("--url must be an absolute http(s):// URL")
    if base_url is not None and not (
        base_url.startswith("/") and base_url.endswith("/")
    ):
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
        "baseUrl": base_url_override
        if base_url_override is not None
        else default_base_url,
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
    entries: list[dict[str, Any]] = [
        {"path": path, "content": content, "source": path}
        for path, content in adapter.items()
    ]
    identity_bytes = (json.dumps(identity, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    entries.append(
        {"path": SITE_IDENTITY_PATH, "content": identity_bytes, "source": None}
    )
    if github_pages:
        entries.append(
            {
                "path": WORKFLOW_TARGET,
                "content": workflow_template(package),
                "source": WORKFLOW_SOURCE,
            }
        )
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
        prerequisites.append(
            {
                "name": "node",
                "status": "missing",
                "detail": "Node.js was not found on PATH.",
            }
        )
    else:
        try:
            result = subprocess.run(
                [node, "--version"], capture_output=True, text=True, timeout=5
            )
            version = result.stdout.strip() or result.stderr.strip()
            match = re.match(r"v?(\d+)", version)
            major = int(match.group(1)) if match else 0
            if not match or major < 20:
                prerequisites.append(
                    {
                        "name": "node",
                        "status": "outdated",
                        "detail": f"Node.js {version or 'unknown'} was found; Node.js 20 or newer is required.",
                    }
                )
            else:
                prerequisites.append(
                    {"name": "node", "status": "present", "detail": version}
                )
        except (OSError, subprocess.SubprocessError) as error:
            prerequisites.append(
                {
                    "name": "node",
                    "status": "missing",
                    "detail": f"Node.js version check failed: {error}",
                }
            )
    npm = shutil.which("npm")
    if npm is None:
        prerequisites.append(
            {"name": "npm", "status": "missing", "detail": "npm was not found on PATH."}
        )
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
    package = (
        Path(package_root).resolve()
        if package_root is not None
        else _default_package_root()
    )

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
        return _template_invalid(error)

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
    resolved_repository = (
        repository if repository is not None else _origin_repository(root)
    )
    identity, identity_finding = _resolve_identity(
        resolved_title, resolved_repository, url, base_url
    )

    try:
        adapter = adapter_files(package)
        entries = _proposal_entries(package, adapter, identity, github_pages)
    except DocsiteTemplateError as error:
        return _template_invalid(error)
    files = [
        _file_entry(entry["path"], entry["content"], entry["source"])
        for entry in entries
    ]
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
        (root / entry["path"]).is_file()
        and (root / entry["path"]).read_bytes() == entry["content"]
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
    return ToolResult(
        "docsite", ".", "proposal", findings=tuple(findings), result=result
    )


def _load_accepted(
    root: Path, package: Path, proposal_path: str
) -> tuple[dict[str, bytes], dict[str, Any], bool, str]:
    path = checked_path(root, safe_path(proposal_path))

    def refused(message: str, field: str = "", code: str = "invalid_proposal", **more):
        return SpecError(message, code, field, path=proposal_path, **more)

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise refused(
            f"the accepted docsite proposal {proposal_path} cannot be read as JSON",
            causes=[system_cause(error, path=proposal_path)],
        ) from error
    if not isinstance(value, dict):
        raise refused(
            f"the accepted docsite proposal is a JSON {type(value).__name__}, not an object"
        )
    for wrapper in ("result", "proposal"):
        if wrapper not in value:
            continue
        if wrapper == "result":
            value = value["result"]
            if not isinstance(value, dict) or "proposal" not in value:
                raise refused(
                    "the accepted docsite proposal's result must be an object holding "
                    f"proposal, not {value!r}"[:200],
                    "/result",
                )
        value = value["proposal"]
        break
    if not isinstance(value, dict) or value.get("proposal_version") != PROPOSAL_VERSION:
        found = value.get("proposal_version") if isinstance(value, dict) else None
        raise refused(
            f"the proposal has proposal_version {found!r}, but this package applies "
            f"version {PROPOSAL_VERSION}; regenerate with docsite --propose",
            "/proposal_version",
            remediation="regenerate the proposal with docsite --propose and apply that",
        )
    if set(value) != _PROPOSAL_FIELDS:
        raise refused(
            f"the proposal has fields {sorted(value)}; a scaffold proposal has exactly "
            f"{sorted(_PROPOSAL_FIELDS)}",
        )
    files = value.get("files")
    if not isinstance(files, list) or not files:
        raise refused(
            f"the proposal's files must be a non-empty list, not {files!r}"[:200],
            "/files",
        )
    identity = value.get("identity")
    problem = _identity_problem(identity)
    if problem is not None:
        raise refused(f"the proposal's identity {problem}"[:300], "/identity")
    conflicts = value.get("conflicts")
    if not isinstance(conflicts, list) or not all(
        isinstance(item, dict)
        and set(item) == {"path", "reason"}
        and all(isinstance(item[key], str) for key in item)
        for item in conflicts
    ):
        raise refused(
            "the proposal's conflicts must be a list of {path, reason} records of text, "
            f"not {conflicts!r}"[:200],
            "/conflicts",
        )
    github_pages = value.get("github_pages")
    if not isinstance(github_pages, bool):
        raise refused(
            f"the proposal's github_pages must be a boolean, not {github_pages!r}",
            "/github_pages",
        )
    if value.get("template_root") != TEMPLATE_ROOT:
        raise refused(
            f"the proposal's template_root is {value.get('template_root')!r}, not "
            f"{TEMPLATE_ROOT!r}",
            "/template_root",
        )

    adapter = adapter_files(package)
    actual_digest = template_digest(adapter)
    if actual_digest != value.get("template_digest"):
        raise refused(
            f"package bytes are stale relative to the accepted proposal template digest: "
            f"the proposal was made for {value.get('template_digest')}, the package at "
            f"{package} now has {actual_digest}",
            "/template_digest",
            code="stale_proposal",
        )

    # Reconstruct the sole permitted inventory before touching any destination.
    # Equality also enforces ordering, uniqueness, closed entry shapes, mappings,
    # identity serialization and the current content hashes.
    entries = _proposal_entries(package, adapter, identity, github_pages)
    expected = [
        _file_entry(entry["path"], entry["content"], entry["source"])
        for entry in entries
    ]
    if files != expected:
        raise refused(
            "the proposal's files differ from the exact scaffold inventory and content "
            "hashes: " + _files_difference(files, expected),
            "/files",
        )
    resolved = {entry["path"]: entry["content"] for entry in entries}
    return resolved, identity, github_pages, actual_digest


def _identity_problem(identity: Any) -> str | None:
    """Why ``identity`` is not a site identity a scaffold proposes, or None when it is."""
    if not isinstance(identity, dict):
        return f"must be an object, not {identity!r}"
    fields = set(identity)
    if not _IDENTITY_FIELDS <= fields or fields - _IDENTITY_FIELDS - {"repository"}:
        return (
            f"has fields {sorted(fields)}; it has exactly {sorted(_IDENTITY_FIELDS)} "
            "and optionally repository"
        )
    if identity["schema_version"] != 1 or isinstance(identity["schema_version"], bool):
        return f"has schema_version {identity['schema_version']!r}, not 1"
    for key in ("title", "organizationName", "projectName"):
        if not isinstance(identity[key], str) or not identity[key].strip():
            return f"has {key} {identity[key]!r}, not nonempty text"
    for key in ("url", "repository"):
        if key in identity and not (
            isinstance(identity[key], str) and _absolute_http_url(identity[key])
        ):
            return f"has {key} {identity[key]!r}, not an absolute http(s) URL"
    base_url = identity["baseUrl"]
    if not (
        isinstance(base_url, str)
        and base_url.startswith("/")
        and base_url.endswith("/")
    ):
        return f"has baseUrl {base_url!r}, which does not start and end with '/'"
    return None


def _files_difference(files: list[Any], expected: list[dict[str, Any]]) -> str:
    """Every differing path of a proposal's files, and any repeated or misordered path."""
    given_paths = [
        item.get("path") if isinstance(item, dict) else None for item in files
    ]
    given: dict[Any, list[Any]] = {}
    for path, item in zip(given_paths, files):
        given.setdefault(path if isinstance(path, str) else repr(path), []).append(item)
    wanted = {item["path"]: item for item in expected}
    differing = sorted(
        path
        for path in given.keys() | wanted.keys()
        if given.get(path) != [wanted.get(path)]
    )
    parts = []
    if differing:
        parts.append(f"{len(differing)} differing entr(y/ies): " + ", ".join(differing))
    repeated = sorted(path for path, items in given.items() if len(items) > 1)
    if repeated:
        parts.append("repeated paths: " + ", ".join(repeated))
    if not parts:
        parts.append("the entries are not sorted by path")
    return "; ".join(parts)


def apply_docsite(
    project_root: str | Path,
    proposal_path: str,
    *,
    package_root: str | Path | None = None,
) -> ToolResult:
    root = Path(project_root).resolve()
    package = (
        Path(package_root).resolve()
        if package_root is not None
        else _default_package_root()
    )
    if _entry_module_title(root) is None:
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
        resolved, identity, github_pages, digest = _load_accepted(
            root, package, proposal_path
        )
    except DocsiteTemplateError as error:
        return _template_invalid(error)
    except (OSError, KeyError, TypeError, ValueError) as error:
        failure = (
            error
            if isinstance(error, SpecError)
            else SpecError(
                f"the accepted proposal {proposal_path} cannot be applied",
                "invalid_proposal",
                path=proposal_path,
                causes=[system_cause(error)],
            )
        )
        finding = Finding(
            "CONCORDE-DOCSITE-004",
            "error",
            SITE_IDENTITY_PATH,
            f"Accepted proposal is invalid: {failure}",
            "Save the exact proposal JSON produced by the propose Tool at a safe project-relative path and retry, "
            "or run the propose Tool again if the package changed.",
        )
        return ToolResult("docsite", ".", "invalid", findings=(finding,), error=failure)

    states = {
        relative: "missing"
        if not (target := root / relative).exists() and not target.is_symlink()
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
            result={
                "identity": identity,
                "template_digest": digest,
                "github_pages": github_pages,
            },
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
            result={
                "conflicts": [
                    path for path, state in sorted(states.items()) if state != "missing"
                ]
            },
        )
    try:
        # Every destination was found absent. Each file is created only where nothing exists
        # yet, so a file another process creates meanwhile is never replaced.
        created = create_files(root, resolved)
    except (OSError, SpecError, TypedDataError) as error:
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
        result={
            "created": created,
            "identity": identity,
            "template_digest": digest,
            "github_pages": github_pages,
        },
    )
