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


class DeliveryTerminologyContractTests(unittest.TestCase):
    def test_active_sources_contain_no_legacy_term(self) -> None:
        matches: list[str] = []
        for path in sorted(REPOSITORY_ROOT.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(REPOSITORY_ROOT)
            if (
                relative == HISTORICAL_LOG
                or relative.parts[:2] == (".claude", "worktrees")
                or any(part in EXCLUDED_PARTS for part in relative.parts)
            ):
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

    def test_superseded_command_vocabulary_is_absent(self) -> None:
        legacy_tokens = (
            "feature" + "-accept",
            "feature" + ".accept",
            "feature" + " accept",
            "feature_" + "acceptance",
        )
        matches: list[str] = []
        for path in sorted(REPOSITORY_ROOT.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(REPOSITORY_ROOT)
            if (
                relative == HISTORICAL_LOG
                or relative.parts[:2] == (".claude", "worktrees")
                or any(part in EXCLUDED_PARTS for part in relative.parts)
            ):
                continue
            try:
                text = path.read_text(encoding="utf-8").lower()
            except UnicodeDecodeError:
                continue
            for token in legacy_tokens:
                if token in text:
                    matches.append(f"{relative.as_posix()}:{token}")
        self.assertEqual(matches, [])

        self.assertFalse(
            (REPOSITORY_ROOT / ".agents/skills" / ("speckit-concorde-feature" + "-accept")).exists()
        )
        self.assertFalse(
            (
                REPOSITORY_ROOT
                / ("extensions/concorde/commands/speckit.concorde.feature" + ".accept.md")
            ).exists()
        )
        self.assertFalse(
            (
                REPOSITORY_ROOT
                / ("extensions/concorde/runtime/concorde/feature_" + "acceptance.py")
            ).exists()
        )

    def test_delivery_is_the_only_current_milestone_command(self) -> None:
        current = (
            REPOSITORY_ROOT / "extensions/concorde/commands/speckit.concorde.deliver.md",
            REPOSITORY_ROOT / ".agents/skills/speckit-concorde-deliver/SKILL.md",
            REPOSITORY_ROOT / "extensions/concorde/runtime/concorde/delivery.py",
        )
        superseded = (
            REPOSITORY_ROOT / "extensions/concorde/commands/speckit.concorde.impl.accept.md",
            REPOSITORY_ROOT / ".agents/skills/speckit-concorde-impl-accept/SKILL.md",
            REPOSITORY_ROOT / "extensions/concorde/runtime/concorde/implementation_acceptance.py",
        )
        for path in current:
            self.assertTrue(path.is_file(), path.as_posix())
        for path in superseded:
            self.assertFalse(path.exists(), path.as_posix())

    def test_superseded_delivery_interface_tokens_are_absent(self) -> None:
        stale_tokens = (
            "speckit-concorde-impl-accept",
            "speckit.concorde.impl-accept",
            "speckit.concorde.impl.accept",
            "impl accept",
            "impl.accept",
            "concorde-accept-",
        )
        allowed = {
            SELECTED_ROOT / "implementation.md",
            Path("tests/concorde/contract/test_delivery_terminology.py"),
        }
        matches: list[str] = []
        for path in sorted(REPOSITORY_ROOT.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(REPOSITORY_ROOT)
            if (
                relative in allowed
                or relative.parts[: len((SELECTED_ROOT / "attempt").parts)] == (SELECTED_ROOT / "attempt").parts
                or relative == HISTORICAL_LOG
                or relative.parts[:3] == (".concorde", "reflections", "plans")
                or relative.parts[:3] == (".concorde", "reflections", "worktrees")
                or relative.parts[:2] == (".claude", "worktrees")
                or any(part in EXCLUDED_PARTS for part in relative.parts)
            ):
                continue
            try:
                text = path.read_text(encoding="utf-8").lower()
            except UnicodeDecodeError:
                continue
            for token in stale_tokens:
                if token in text:
                    matches.append(f"{relative.as_posix()}:{token}")
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
