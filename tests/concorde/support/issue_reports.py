"""Issue report and provenance values shared by tests that file Issues, and the Git repository
whose primary worktree keeps them."""

import subprocess
from pathlib import Path


def git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    ).stdout


def git_project(root: Path) -> Path:
    """Make ``root`` the primary worktree of a new repository with one commit on ``main``,
    where Issue writes commit their records."""
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "t")
    git(root, "config", "user.email", "t@t")
    git(root, "config", "commit.gpgsign", "false")
    git(root, "commit", "-q", "--allow-empty", "-m", "start")
    return root


def report(**changes):
    return {
        "report_key": "missing-retry",
        "tier": "decision-needed",
        "severity": "high",
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
