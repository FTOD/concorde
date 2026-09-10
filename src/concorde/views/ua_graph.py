"""Deterministic Understand Anything graph export, derived only from the Spec registry.

The exporter never scans the project for undeclared content: every node, edge and layer it adds
comes from registered Module identities, their ``parent``/``uses`` relationships, their registered
documents and their entities' declared file listings. When an existing raw Understand Anything
graph is present it is treated as an overlay target: the exporter strips only the elements a prior
export of its own added (identified by the distinctive ``concorde-ua-graph`` tag on nodes -- chosen
to not collide with a real scan's own organic tags, such as one literally named "concorde" -- the
``layer:module.`` and ``layer:unlisted`` layer identities, and edges with a ``module:`` endpoint)
and replaces them with a freshly derived set, leaving every other element of the graph untouched.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..spec.model import Finding, ToolResult
from ..spec.repository import HEADING, SpecError, SpecRepository, SpecTarget, walk_lines
from ..spec.typed_data import TypedDataError, checked_path

GRAPH_PATHS = (".understand-anything/knowledge-graph.json", ".ua/knowledge-graph.json")
FILE_LIKE_TYPES = frozenset({"file", "config", "document", "pipeline", "resource", "schema"})
CONFIG_SUFFIXES = (".json", ".yml", ".yaml", ".toml")
MODULE_PREFIX = "module:"
CONCORDE_TAG = "concorde-ua-graph"
GRAPH_VERSION = "1.0.0"


class UaGraphError(ValueError):
    """The existing raw Understand Anything graph cannot be overlaid."""


def _purpose_summary(body: str) -> str:
    """The first prose paragraph of the module.md Purpose section (Required format section rules)."""
    lines = walk_lines(body)
    start = None
    level = None
    for index, (_number, kind, line) in enumerate(lines):
        if kind != "prose":
            continue
        match = HEADING.match(line)
        if match and match.group(2).strip() == "Purpose" and len(match.group(1)) <= 3:
            start, level = index + 1, len(match.group(1))
            break
    if start is None:
        return ""
    paragraph: list[str] = []
    for _number, kind, line in lines[start:]:
        if kind != "prose":
            continue
        match = HEADING.match(line)
        if match and len(match.group(1)) <= level:
            break
        if line.strip():
            paragraph.append(line.strip())
        elif paragraph:
            break
    return " ".join(paragraph)


def _first_sentence(text: str) -> str:
    if not text:
        return text
    index = text.find(". ")
    return text[: index + 1] if index != -1 else text


def _extension_prefix(path: str) -> str:
    if path.endswith(".md"):
        return "document:"
    if path.endswith(CONFIG_SUFFIXES):
        return "config:"
    return "file:"


def _edge(source: str, target: str, kind: str, weight: float, description: str | None = None) -> dict[str, Any]:
    edge: dict[str, Any] = {"source": source, "target": target, "type": kind, "direction": "forward", "weight": weight}
    if description is not None:
        edge["description"] = description
    return edge


def _index_by_path(nodes: list[dict]) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    for node in sorted(nodes, key=lambda item: item.get("id", "")):
        path = node.get("filePath")
        if isinstance(path, str) and path:
            index.setdefault(path, []).append(node)
    return index


def _match_id(index: dict[str, list[dict]], path: str, allowed_types: frozenset[str]) -> str | None:
    for node in index.get(path, ()):
        if node.get("type") in allowed_types:
            return node["id"]
    return None


def _resolve_document_node(path: str, document_id: str, *, overlay: bool, index: dict[str, list[dict]],
                            created: dict[str, dict]) -> str:
    if overlay:
        found = _match_id(index, path, frozenset({"document"}))
        if found is not None:
            return found
    node_id = f"document:{path}"
    created.setdefault(node_id, {
        "id": node_id, "type": "document", "name": Path(path).name, "filePath": path,
        "summary": document_id, "tags": [CONCORDE_TAG, "document"],
    })
    return node_id


def _resolve_file_node(path: str, *, overlay: bool, index: dict[str, list[dict]], created: dict[str, dict],
                        pending: bool) -> str:
    if overlay:
        found = _match_id(index, path, FILE_LIKE_TYPES)
        if found is not None:
            return found
    node_id = _extension_prefix(path) + path
    node_type = node_id.split(":", 1)[0]
    node = created.get(node_id)
    if node is None:
        tags = [CONCORDE_TAG, node_type] + (["pending"] if pending else [])
        created[node_id] = {
            "id": node_id, "type": node_type, "name": Path(path).name, "filePath": path,
            "summary": path, "tags": tags,
        }
    elif pending and "pending" not in node["tags"]:
        node["tags"].append("pending")
    return node_id


def _build_elements(repository: SpecRepository, *,
                     index: dict[str, list[dict]] | None) -> tuple[dict[str, dict], list[dict], dict[str, dict]]:
    overlay = index is not None
    index = index or {}
    targets = list(repository.targets.values())
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    purposes: dict[str, str] = {}

    for target in targets:
        purpose = _purpose_summary(repository.document(target.primary_document).body)
        purposes[target.id] = purpose
        nodes[f"module:{target.id}"] = {
            "id": f"module:{target.id}", "type": "module", "name": target.title, "summary": purpose,
            "tags": [CONCORDE_TAG, "module"], "complexity": "moderate",
        }

    for target in targets:
        if target.parent is not None:
            edges.append(_edge(f"module:{target.parent}", f"module:{target.id}", "contains", 1.0, "composes"))

    for target in targets:
        responsibilities = {dep["target_id"]: dep["responsibility"] for dep in repository.dependencies(target)}
        for peer in target.uses:
            edges.append(_edge(f"module:{target.id}", f"module:{peer}", "depends_on", 0.8,
                                responsibilities.get(peer, "uses")))

    doc_node_ids: dict[str, str] = {}
    for target in targets:
        for path in target.documents:
            if path not in doc_node_ids:
                document_id = repository.document(path).document_id
                doc_node_ids[path] = _resolve_document_node(path, document_id, overlay=overlay, index=index, created=nodes)
            edges.append(_edge(doc_node_ids[path], f"module:{target.id}", "documents", 0.7))

    file_node_ids: dict[str, str] = {}
    layer_members: dict[str, set[str]] = {}
    for target in targets:
        for path in repository.implementation_files(target):
            entity = repository.entity_for_path(target, path)
            if entity is None:
                continue
            pending = path in entity.pending
            if path not in file_node_ids:
                file_node_ids[path] = _resolve_file_node(path, overlay=overlay, index=index, created=nodes, pending=pending)
            node_id = file_node_ids[path]
            edges.append(_edge(f"module:{target.id}", node_id, "contains", 0.9, f"{entity.id}: {entity.title}"))
            listers = repository.listing_users(path)
            if listers and listers[0] == target.id:
                layer_members.setdefault(target.id, set()).add(node_id)

    for path, node_id in file_node_ids.items():
        listers = repository.listing_users(path)
        for other in listers[1:]:
            edges.append(_edge(node_id, f"module:{other}", "related", 0.5, f"also listed by {other}"))

    layers: dict[str, dict] = {}
    for target in targets:
        if not target.files:
            continue
        layers[f"layer:{target.id}"] = {
            "id": f"layer:{target.id}", "name": target.title,
            "description": _first_sentence(purposes[target.id]),
            "nodeIds": sorted(layer_members.get(target.id, ())),
        }

    if overlay:
        claimed = set(file_node_ids)
        unlisted: set[str] = set()
        for path in index:
            if path in claimed:
                continue
            match = _match_id(index, path, FILE_LIKE_TYPES)
            if match is not None:
                unlisted.add(match)
        # Omitted when empty so a fresh skeleton export is stable under an immediate overlay
        # re-derivation (for example the --check that naturally follows an export).
        if unlisted:
            layers["layer:unlisted"] = {
                "id": "layer:unlisted", "name": "Not listed by any Module",
                "description": "File-level nodes from the Understand Anything graph that no Module lists as an implementation file.",
                "nodeIds": sorted(unlisted),
            }

    return nodes, edges, layers


def _git_commit(root: Path) -> str:
    try:
        result = subprocess.run(("git", "-C", str(root), "rev-parse", "HEAD"),
                                 capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _serialize(version: str, project: dict, nodes, edges, layers, tour) -> dict:
    return {
        "version": version,
        "project": project,
        "nodes": sorted(nodes, key=lambda item: item["id"]),
        "edges": sorted(edges, key=lambda item: (item["source"], item["target"], item["type"])),
        "layers": sorted(layers, key=lambda item: item["id"]),
        "tour": tour,
    }


def _strip_concorde(graph: dict) -> dict:
    nodes = [node for node in graph["nodes"] if CONCORDE_TAG not in (node.get("tags") or [])]
    edges = [edge for edge in graph["edges"]
             if not (str(edge.get("source", "")).startswith(MODULE_PREFIX)
                     or str(edge.get("target", "")).startswith(MODULE_PREFIX))]
    layers = [layer for layer in graph["layers"]
              if not (str(layer.get("id", "")).startswith("layer:module.") or layer.get("id") == "layer:unlisted")]
    return {"version": graph["version"], "project": graph["project"], "nodes": nodes, "edges": edges,
            "layers": layers, "tour": graph["tour"]}


def _load_graph(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise UaGraphError(f"existing UA graph must be one real file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise UaGraphError(f"cannot read existing UA graph: {error}") from error
    if not isinstance(value, dict):
        raise UaGraphError("existing UA graph must be one JSON object")
    if not isinstance(value.get("version"), str):
        raise UaGraphError("existing UA graph requires a string version")
    if not isinstance(value.get("project"), dict):
        raise UaGraphError("existing UA graph requires an object project")
    if not isinstance(value.get("nodes"), list) or not isinstance(value.get("edges"), list):
        raise UaGraphError("existing UA graph requires array nodes and edges")
    layers = value.get("layers", [])
    tour = value.get("tour", [])
    if not isinstance(layers, list) or not isinstance(tour, list):
        raise UaGraphError("existing UA graph layers and tour must be arrays when present")
    return {**value, "layers": layers, "tour": tour}


def _derive_graph(repository: SpecRepository, root: Path, base: dict | None) -> dict:
    if base is None:
        nodes, edges, layers = _build_elements(repository, index=None)
        project = {
            "name": repository.project_id,
            "languages": [],
            "frameworks": [],
            "description": "Skeleton graph deterministically exported by Concorde from the project's explicit Spec registry.",
            "analyzedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "gitCommitHash": _git_commit(root),
        }
        return _serialize(GRAPH_VERSION, project, list(nodes.values()), edges, list(layers.values()), [])
    stripped = _strip_concorde(base)
    index = _index_by_path(stripped["nodes"])
    nodes, edges, layers = _build_elements(repository, index=index)
    merged_nodes = list(stripped["nodes"]) + list(nodes.values())
    merged_edges = list(stripped["edges"]) + edges
    merged_layers = list(stripped["layers"]) + list(layers.values())
    return _serialize(stripped["version"], stripped["project"], merged_nodes, merged_edges, merged_layers, stripped["tour"])


def _target_relative(root: Path) -> str:
    for candidate in GRAPH_PATHS:
        if checked_path(root, candidate).is_file():
            return candidate
    return GRAPH_PATHS[-1]


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".concorde-ua-graph-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def export_ua_graph(project_root: str | Path, *, check: bool = False) -> ToolResult:
    root = Path(project_root).resolve()
    try:
        repository = SpecRepository(root)
    except SpecError as error:
        finding = Finding("CONCORDE-UA-GRAPH-001", "error", ".concorde/config.json",
                           f"The project registry cannot be loaded: {error}",
                           "Fix the Spec registry so it loads, then retry.")
        return ToolResult("ua-graph", ".", "invalid", findings=(finding,))

    try:
        relative = _target_relative(root)
        target_path = checked_path(root, relative)
    except TypedDataError as error:
        finding = Finding("CONCORDE-UA-GRAPH-004", "error", GRAPH_PATHS[-1], str(error),
                           "Ensure the UA graph path and its parents are not symlinks.")
        return ToolResult("ua-graph", ".", "invalid", findings=(finding,))

    base = None
    if target_path.is_file():
        try:
            base = _load_graph(target_path)
        except UaGraphError as error:
            finding = Finding("CONCORDE-UA-GRAPH-002", "error", relative, str(error),
                               "Repair or remove the existing UA graph file, or point the viewer at a fresh export.")
            return ToolResult("ua-graph", relative, "invalid", findings=(finding,))

    try:
        graph = _derive_graph(repository, root, base)
    except SpecError as error:
        finding = Finding("CONCORDE-UA-GRAPH-001", "error", ".concorde/config.json",
                           f"The project registry cannot be loaded: {error}",
                           "Fix the Spec registry so it loads, then retry.")
        return ToolResult("ua-graph", ".", "invalid", findings=(finding,))
    payload = (json.dumps(graph, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

    if check:
        current = target_path.read_bytes() if target_path.is_file() else None
        if current == payload:
            return ToolResult("ua-graph", relative, "success", (relative,))
        finding = Finding("CONCORDE-UA-GRAPH-003", "warning", relative,
                           "The exported UA graph is stale relative to the current registry.",
                           "Run `python -m concorde ua-graph` without --check to refresh it.")
        return ToolResult("ua-graph", relative, "invalid", findings=(finding,))

    try:
        _atomic_write(target_path, payload)
    except OSError as error:
        finding = Finding("CONCORDE-UA-GRAPH-004", "error", relative, f"Writing the UA graph failed: {error}",
                           "Resolve the filesystem failure and retry.")
        return ToolResult("ua-graph", relative, "failed", findings=(finding,))
    return ToolResult("ua-graph", relative, "success", (relative,),
                       result={"nodes": len(graph["nodes"]), "edges": len(graph["edges"]), "layers": len(graph["layers"])})
