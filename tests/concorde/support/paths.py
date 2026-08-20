from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPOSITORY_ROOT / "extensions" / "concorde" / "runtime"
FIXTURES_ROOT = REPOSITORY_ROOT / "tests" / "concorde" / "fixtures"
VALID_PROJECT = FIXTURES_ROOT / "valid-project"
CONTEXT_PROJECT = FIXTURES_ROOT / "context-project"
INVALID_PROJECTS = FIXTURES_ROOT / "invalid-projects"
