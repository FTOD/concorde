from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPOSITORY_ROOT / "src"
FIXTURES_ROOT = REPOSITORY_ROOT / "tests" / "concorde" / "fixtures"
