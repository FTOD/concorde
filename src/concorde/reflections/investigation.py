"""Validate and persist typed investigation results on the trusted parent side."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from ..capabilities.operation_data import OperationDataError, checked_path, validate_typed, verify_artifacts
from .reflections import parse_reflection_document


def _replace_sections(text: str, replacements: dict[str, str]) -> str:
    lines = text.splitlines(keepends=True)
    headers = []
    fence = None
    for index, line in enumerate(lines):
        match = re.match(r"^\s*(```+|~~~+)", line)
        if match:
            token = match.group(1)[0]
            fence = None if fence == token else token if fence is None else fence
        if fence is None and (match := re.match(r"^## (.+?)\s*$", line)):
            headers.append((index, match.group(1)))
    for position in reversed(range(len(headers))):
        begin, name = headers[position]
        if name in replacements:
            end = headers[position + 1][0] if position + 1 < len(headers) else len(lines)
            lines[begin + 1:end] = ["\n", replacements[name].strip() + "\n\n"]
    return "".join(lines)


def _triage_text(original: str, finding: dict) -> str:
    text = _replace_sections(original, {
        "Triage Analysis": finding["analysis"],
        "Proposed Resolution": finding["resolution"],
        "Intervention Rationale": finding["intervention_rationale"],
    })
    lines = text.splitlines(keepends=True)
    end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    updates = {"triage": "complete", "human_intervention": finding["human_intervention"]}
    for key, value in updates.items():
        found = next((index for index in range(1, end) if re.match(rf"^{key}:", lines[index])), None)
        if found is None:
            lines.insert(end, f"{key}: {value}\n")
            end += 1
        else:
            lines[found] = f"{key}: {value}\n"
    return "".join(lines)


def _plan_text(entry, finding: dict, task: dict, verified_on: str, status: str) -> str:
    metadata = {
        "id": entry.identifier, "title": entry.title, "route": finding["route"], "status": status,
        "recorded_under": entry.feature, "implement_in": task["feature_path"], "implement_in_id": entry.feature,
        "touches_docsite": any(path == "docsite" or path.startswith("docsite/") for path in finding["files"]),
        "effort": finding["effort"], "files": finding["files"],
        "verified": verified_on, "verified_commit": finding["verified_commit"],
    }
    front = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items())
    return (f"---\n{front}\n---\n\n## Problem\n\n{finding['analysis']}\n\n"
            f"## Verification\n\n{finding['verification']}\n\n"
            f"## Change\n\n{finding['steps']}\n\n## Validation\n\n{finding['validation']}\n\n"
            f"## Risks and out of scope\n\n{finding['risks']}\n")


def _write_plan(project: Path, relative: str, original: bytes | None, content: str) -> None:
    path = checked_path(project, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    observed = path.read_bytes() if path.exists() else None
    if observed != original:
        raise OperationDataError("stale_reference", "/domain_output", "reflection plan changed during investigation")
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
    try:
        observed = checked_path(project, relative).read_bytes() if path.exists() else None
        if observed != original:
            raise OperationDataError("stale_reference", "/domain_output", "reflection plan changed during persistence")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def apply_investigation(project: Path, queue, runtime_input: dict, domain_output: dict,
                        entries: dict, *, concorde_project: bool) -> list[dict]:
    output = validate_typed(domain_output, "concorde-reflection-investigation-result", "/domain_output")
    data = runtime_input["data"]
    task = data["task"]["data"]
    identifiers = task["reflection_ids"]
    findings = output["data"]["findings"]
    if [item["reflection_id"] for item in findings] != identifiers:
        raise OperationDataError("incompatible_handoff", "/domain_output/data/findings", "investigation must return exactly the selected IDs in order")
    if queue._captured_head(project) != data["head"]:
        raise OperationDataError("workspace_mismatch", "/domain_output", "Git HEAD changed during investigation")
    verify_artifacts(project, runtime_input, "/input")
    config = queue.load_config(project)
    plans = queue._load_plans(project, config)
    prepared = []
    for finding in findings:
        identifier = finding["reflection_id"]
        entry = entries[identifier]
        if entry.status != "open":
            raise OperationDataError("incompatible_handoff", "/domain_output", "investigation cannot alter a closed reflection")
        if finding["verified_commit"] != data["head"]:
            raise OperationDataError("workspace_mismatch", "/domain_output", "investigator verification does not match its admitted HEAD")
        if concorde_project and finding["protocol_change"]:
            raise OperationDataError("incompatible_handoff", "/domain_output", "normative Protocol changes require feature.concorde.evolve-protocol")
        if finding["observed_state"] == "not-reproduced" and (finding["route"] != "dismiss" or finding["human_intervention"] != "required"):
            raise OperationDataError("incompatible_handoff", "/domain_output", "a non-reproduced problem requires a maintainer dismissal decision")
        if finding["route"] == "fast-loop" and finding["effort"] != "small":
            raise OperationDataError("incompatible_handoff", "/domain_output", "fast-loop requires a small verified change")
        for key in ("verification", "analysis", "resolution", "intervention_rationale", "steps", "validation", "risks"):
            if re.search(r"^#{1,2}\s", finding[key], re.M):
                raise OperationDataError("invalid_field", f"/domain_output/{key}", "section text cannot introduce document-level headings")
        for relative in finding["files"]:
            checked_path(project, relative, "/domain_output/data/findings/files")
        source = checked_path(project, entry.path)
        original = source.read_bytes()
        text = _triage_text(original.decode("utf-8"), finding)
        # Parse at the intended bucket path so every shape/content check applies
        # before the first write. Relocation itself remains the queue Tool's job.
        bucket = "needs-comments" if finding["human_intervention"] == "required" else "planned"
        updated, problems = parse_reflection_document(text, f".concorde/reflections/{bucket}/{identifier}.md")
        if problems or updated is None:
            raise OperationDataError("invalid_field", "/domain_output", "invalid triage completion: " + "; ".join(item.message for item in problems))
        for key in ("Status", "Note", "User Comments", "Context", "Expected", "Observed", "Impact", "Evidence", "Occurrences"):
            if updated.fields.get(key) != entry.fields.get(key):
                raise OperationDataError("incompatible_handoff", "/domain_output", f"investigation changed preserved field: {key}")
        status = ("stale" if finding["observed_state"] == "not-reproduced" else
                  "hold" if finding["human_intervention"] == "required" else "proposed")
        old_plan = plans.get(identifier)
        plan_path = f"{config['plans_dir']}/{identifier}.md"
        old_bytes = checked_path(project, plan_path).read_bytes() if old_plan else None
        if status == "proposed" and task["action"] == "implement" and finding["observed_state"] == "reproduced":
            previously_approved = bool(old_plan and old_plan["status"] == "approved"
                                       and old_plan["route"] == finding["route"]
                                       and old_plan["files"] == finding["files"]
                                       and old_plan["implement_in_id"] == entry.feature
                                       and f"## Change\n\n{finding['steps']}\n" in old_bytes.decode("utf-8")
                                       and f"## Validation\n\n{finding['validation']}\n" in old_bytes.decode("utf-8"))
            if not config["require_approval"] or previously_approved:
                status = "approved"
        plan_text = _plan_text(entry, finding, task, data["verified_on"], status)
        prepared.append((identifier, source, original, text, plan_path, old_bytes, plan_text, status))
    for identifier, source, original, text, plan_path, old_bytes, plan_text, status in prepared:
        if queue._captured_head(project) != data["head"]:
            raise OperationDataError("workspace_mismatch", "/domain_output", "Git HEAD changed before persistence")
        _write_plan(project, plan_path, old_bytes, plan_text)
        queue._atomic_file_replace(project, source, original, text.encode("utf-8"), "triage completion")
        queue.relocate(project, [identifier])
        report = queue.validate_entry(project, identifier)
        if report.get("status") != "valid":
            raise OperationDataError("incompatible_handoff", "/domain_output", f"persisted triage completion failed validation: {identifier}")
    if task["action"] == "implement":
        if any(item["observed_state"] != "reproduced" for item in findings):
            raise OperationDataError("incompatible_handoff", "/domain_output", "problem no longer reproduces; downstream implementation stopped")
        if any(item["human_intervention"] == "required" for item in findings):
            raise OperationDataError("incompatible_handoff", "/domain_output", "selected reflection requires maintainer comments")
        if any(item["route"] != task["route"] for item in findings):
            raise OperationDataError("incompatible_handoff", "/domain_output", "verified resolution route differs from the requested route")
        if any(item[-1] != "approved" for item in prepared):
            raise OperationDataError("incompatible_handoff", "/domain_output", "project requires explicit approval of this resolution plan")
    return findings
