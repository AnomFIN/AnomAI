import pathlib
import sys
import types
import unittest
from unittest.mock import patch

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import jugiai


class FormatLlamaImportErrorTests(unittest.TestCase):
    def test_includes_windows_store_hint_when_stub_detected(self) -> None:
        fake_exc = ImportError("No module named 'llama_cpp'")

        with patch("jugiai.importlib.util.find_spec", return_value=None), patch(
            "jugiai.importlib.metadata.distribution",
            side_effect=jugiai.importlib.metadata.PackageNotFoundError,
        ), patch.object(
            jugiai,
            "sys",
            types.SimpleNamespace(
                executable=r"C:\\Users\\test\\AppData\\Local\\Microsoft\\WindowsApps\\python.exe"
            ),
        ), patch("jugiai.os.path.exists", return_value=False):
            message = jugiai._format_llama_import_error(fake_exc)

        self.assertIn("Windows Storen stubi", message)
        self.assertIn("`py -3 jugiai.py`", message)
        self.assertIn("Suositeltu korjaus:", message)

    def test_mentions_venv_activation_when_available(self) -> None:
        fake_exc = ImportError("No module named 'llama_cpp'")

        with patch("jugiai.importlib.util.find_spec", return_value=None), patch(
            "jugiai.importlib.metadata.distribution",
            side_effect=jugiai.importlib.metadata.PackageNotFoundError,
        ), patch.object(
            jugiai,
            "sys",
            types.SimpleNamespace(executable=r"C:\\Python313\\python.exe"),
        ), patch("jugiai.os.path.exists", return_value=True):
            message = jugiai._format_llama_import_error(fake_exc)

        self.assertIn("Ympäristövinkit:", message)
        self.assertIn(r"\.venv\Scripts\activate", message)


if __name__ == "__main__":
    unittest.main()
