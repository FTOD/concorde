"""Issue report and provenance values shared by tests that file Issues."""


def report(**changes):
    return {
        "report_key": "missing-retry",
        "type": "gap",
        "subtype": "missing-contract",
        "title": "Retry ownership is unspecified",
        "description": "The caller and service do not assign retries.",
        "impact": "Retry implementation cannot be selected.",
        "basis": "Neither admitted contract assigns retries.",
        "owner_target_id": "module.service",
        "evidence": [
            {"path": "specs/service/module.md", "description": "Failure behavior"}
        ],
        **changes,
    }


def source(**changes):
    return {
        "invocation_id": "worker-1",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.service",
        "context_id": "sha256:" + "a" * 64,
        "change_id": None,
        "head": None,
        **changes,
    }
