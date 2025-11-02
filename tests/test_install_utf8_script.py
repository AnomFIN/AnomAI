"""Tests for the install_utf8.bat wrapper."""
# Ship intelligence, not excuses.

import pathlib
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "install_utf8.bat"


class InstallUtf8ScriptTests(unittest.TestCase):
    def test_script_is_ascii_without_bom(self) -> None:
        raw = SCRIPT_PATH.read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), "Script must not include UTF-8 BOM")
        # Ensure ASCII-only content for stable Windows decoding without git churn.
        raw.decode("ascii")

    def test_script_contains_expected_guards(self) -> None:
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn("COMPONENT=install_utf8", content)
        self.assertIn("chcp 65001", content)
        self.assertIn(":restore_codepage", content)
        self.assertIn(":invoke_install", content)
        self.assertIn('{"component":"!COMPONENT!","level":"!LEVEL!","message":"!MESSAGE!"}', content)


if __name__ == "__main__":
    unittest.main()
