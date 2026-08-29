from __future__ import annotations

import unittest
from pathlib import Path
import re


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
LEGACY_TERM = "har" + "den"
EXCLUDED_PARTS = {
    ".git",
    ".docusaurus",
    "build",
    "generated",
    ".generated",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    ".cache",
    ".specify-dev",
    "coverage",
    "dist",
}
HISTORICAL_LOG = Path("specs/concorde/reflections.md")
SELECTED_ROOT = Path(
    "specs/concorde/features/001-concorde-workflow/subfeatures/009-accept-milestone"
)
SELECTED_IMPLEMENTATION = SELECTED_ROOT / "implementation.md"
LEGACY_PATTERN = re.compile(rf"\b{LEGACY_TERM}(?:s|ed|ing)?\b", re.IGNORECASE)
ALLOWED_UNRELATED_PHRASES = {
    f"security {LEGACY_TERM}ing",
    f"spec-{LEGACY_TERM}ing",
}


class AcceptanceTerminologyContractTests(unittest.TestCase):
    def test_active_sources_contain_no_legacy_term(self) -> None:
        matches: list[str] = []
        for path in sorted(REPOSITORY_ROOT.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(REPOSITORY_ROOT)
            if relative == HISTORICAL_LOG or any(part in EXCLUDED_PARTS for part in relative.parts):
                continue
            if relative == SELECTED_IMPLEMENTATION and (REPOSITORY_ROOT / SELECTED_ROOT / "attempt").is_dir():
                # The lifecycle preserves the old placeholder byte-for-byte until this attempt is
                # explicitly accepted; the exemption disappears with the attempt directory.
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for number, line in enumerate(text.splitlines(), start=1):
                lowered = line.lower()
                if LEGACY_PATTERN.search(line) and not any(phrase in lowered for phrase in ALLOWED_UNRELATED_PHRASES):
                    matches.append(f"{relative.as_posix()}:{number}")
        self.assertEqual(matches, [])

    def test_legacy_command_surface_is_absent(self) -> None:
        legacy_skill = REPOSITORY_ROOT / ".agents/skills" / f"speckit-concorde-feature-{LEGACY_TERM}"
        legacy_command = (
            REPOSITORY_ROOT
            / "extensions/concorde/commands"
            / f"speckit.concorde.feature.{LEGACY_TERM}.md"
        )
        self.assertFalse(legacy_skill.exists())
        self.assertFalse(legacy_command.exists())


if __name__ == "__main__":
    unittest.main()
