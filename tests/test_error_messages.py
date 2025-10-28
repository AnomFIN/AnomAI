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


class WindowsStoreGuardTests(unittest.TestCase):
    def test_should_redirect_detects_windows_store_path(self) -> None:
        env: dict[str, str] = {}
        executable = r"C:\\Users\\test\\AppData\\Local\\Microsoft\\WindowsApps\\python.exe"
        self.assertTrue(jugiai._should_redirect_windows_store(executable, env, "win32"))

    def test_should_redirect_respects_skip_flag_and_platform(self) -> None:
        env: dict[str, str] = {"JUGIAI_SKIP_STUB_GUARD": "1"}
        executable = r"C:\\Users\\test\\AppData\\Local\\Microsoft\\WindowsApps\\python.exe"
        self.assertFalse(jugiai._should_redirect_windows_store(executable, env, "win32"))
        self.assertFalse(jugiai._should_redirect_windows_store(executable, {}, "linux"))

    def test_guard_relaunches_via_py_and_exits(self) -> None:
        fake_sys = types.SimpleNamespace(
            executable=r"C:\\Users\\test\\AppData\\Local\\Microsoft\\WindowsApps\\python.exe",
            argv=["jugiai.py", "--demo"],
            platform="win32",
        )

        with patch.object(jugiai, "sys", fake_sys), patch.dict(
            jugiai.os.environ, {}, clear=True
        ), patch.object(jugiai.shutil, "which", return_value="py"), patch.object(
            jugiai.subprocess, "check_call", return_value=None
        ) as mocked_call:
            with self.assertRaises(SystemExit) as ctx:
                jugiai._guard_windows_store_stub()

        self.assertEqual(ctx.exception.code, 0)
        expected_env = {"JUGIAI_SKIP_STUB_GUARD": "1"}
        mocked_call.assert_called_once()
        args, kwargs = mocked_call.call_args
        self.assertIn("py", args[0][0])
        self.assertIn("-3", args[0])
        self.assertIn("--demo", args[0])
        self.assertEqual(kwargs["env"], expected_env)


if __name__ == "__main__":
    unittest.main()
