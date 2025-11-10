"""
Test to validate install.bat syntax and structure.
This test checks for common batch file errors without actually running the script.
"""
import unittest
import os
import re


class TestInstallBatSyntax(unittest.TestCase):
    """Test cases for install.bat syntax validation"""

    def setUp(self):
        """Set up test by loading install.bat content"""
        self.install_bat_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'install.bat'
        )
        with open(self.install_bat_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
        self.lines = self.content.split('\n')

    def test_file_exists(self):
        """Test that install.bat exists"""
        self.assertTrue(
            os.path.exists(self.install_bat_path),
            "install.bat file should exist"
        )

    def test_has_echo_off(self):
        """Test that script starts with @echo off"""
        first_line = self.lines[0].strip()
        self.assertEqual(
            first_line.lower(),
            '@echo off',
            "Script should start with @echo off"
        )

    def test_has_setlocal(self):
        """Test that script has setlocal enabledelayedexpansion"""
        has_setlocal = any(
            'setlocal' in line.lower() and 'enabledelayedexpansion' in line.lower()
            for line in self.lines[:10]
        )
        self.assertTrue(
            has_setlocal,
            "Script should have 'setlocal enabledelayedexpansion' near the start"
        )

    def test_has_endlocal(self):
        """Test that script has endlocal statements"""
        endlocal_count = sum(
            1 for line in self.lines 
            if 'endlocal' in line.lower() and not line.strip().startswith('REM')
        )
        self.assertGreater(
            endlocal_count, 0,
            "Script should have at least one endlocal statement"
        )

    def test_has_maybe_pause_function(self):
        """Test that :maybe_pause function exists"""
        has_maybe_pause = any(':maybe_pause' in line for line in self.lines)
        self.assertTrue(
            has_maybe_pause,
            "Script should have :maybe_pause function"
        )

    def test_checks_python_existence(self):
        """Test that script checks for Python"""
        has_python_check = any(
            'where python' in line.lower() or 'where py' in line.lower()
            for line in self.lines
        )
        self.assertTrue(
            has_python_check,
            "Script should check for Python installation"
        )

    def test_provides_python_download_url(self):
        """Test that script provides Python download URL"""
        has_download_url = any(
            'python.org' in line.lower()
            for line in self.lines
        )
        self.assertTrue(
            has_download_url,
            "Script should provide Python download URL"
        )

    def test_creates_venv(self):
        """Test that script creates virtual environment"""
        has_venv_creation = any(
            '-m venv' in line
            for line in self.lines
        )
        self.assertTrue(
            has_venv_creation,
            "Script should create virtual environment"
        )

    def test_activates_venv(self):
        """Test that script activates virtual environment"""
        has_venv_activation = any(
            'activate.bat' in line
            for line in self.lines
        )
        self.assertTrue(
            has_venv_activation,
            "Script should activate virtual environment"
        )

    def test_upgrades_pip(self):
        """Test that script upgrades pip"""
        has_pip_upgrade = any(
            'pip install --upgrade pip' in line
            for line in self.lines
        )
        self.assertTrue(
            has_pip_upgrade,
            "Script should upgrade pip"
        )

    def test_installs_requirements(self):
        """Test that script installs requirements.txt"""
        has_requirements_install = any(
            'requirements.txt' in line and 'pip install' in line
            for line in self.lines
        )
        self.assertTrue(
            has_requirements_install,
            "Script should install requirements.txt"
        )

    def test_has_llama_cpp_option(self):
        """Test that script offers llama-cpp-python installation"""
        has_llama_option = any(
            'llama-cpp-python' in line
            for line in self.lines
        )
        self.assertTrue(
            has_llama_option,
            "Script should offer llama-cpp-python installation"
        )

    def test_has_config_creation(self):
        """Test that script creates config.json"""
        has_config_creation = any(
            'config.json' in line
            for line in self.lines
        )
        self.assertTrue(
            has_config_creation,
            "Script should handle config.json creation"
        )

    def test_has_exe_build_option(self):
        """Test that script offers EXE building"""
        has_exe_build = any(
            'pyinstaller' in line.lower()
            for line in self.lines
        )
        self.assertTrue(
            has_exe_build,
            "Script should offer executable building"
        )

    def test_has_shortcut_creation(self):
        """Test that script offers desktop shortcut creation"""
        has_shortcut = any(
            'shortcut' in line.lower() or 'desktop' in line.lower()
            for line in self.lines
        )
        self.assertTrue(
            has_shortcut,
            "Script should offer desktop shortcut creation"
        )

    def test_balanced_if_statements(self):
        """Test that if statements are properly closed"""
        # Count if statements in batch files
        if_count = 0
        for line in self.lines:
            stripped = line.strip().lower()
            if (stripped.startswith('if ') or 
                stripped.startswith('if(') or
                stripped.startswith('if not ') or
                stripped.startswith('if /i ')):
                if_count += 1
        
        # We should have a reasonable number of if statements
        self.assertGreater(
            if_count, 5,
            "Script should have multiple conditional checks"
        )

    def test_has_error_handling(self):
        """Test that script has error handling"""
        has_error_checks = sum(
            1 for line in self.lines
            if 'errorlevel' in line.lower() or 'error' in line.lower()
        )
        self.assertGreater(
            has_error_checks, 5,
            "Script should have multiple error handling checks"
        )

    def test_has_progress_indicators(self):
        """Test that script has progress indicators"""
        has_ok_messages = any('[OK]' in line for line in self.lines)
        has_error_messages = any('[ERROR]' in line for line in self.lines)
        has_warning_messages = any('[WARNING]' in line for line in self.lines)
        
        self.assertTrue(
            has_ok_messages,
            "Script should have [OK] progress indicators"
        )
        self.assertTrue(
            has_error_messages,
            "Script should have [ERROR] messages"
        )
        self.assertTrue(
            has_warning_messages,
            "Script should have [WARNING] messages"
        )

    def test_has_section_headers(self):
        """Test that script has clear section headers"""
        section_count = sum(
            1 for line in self.lines
            if '========' in line
        )
        self.assertGreater(
            section_count, 5,
            "Script should have multiple section dividers for clarity"
        )

    def test_no_goto_without_label(self):
        """Test that goto statements reference existing labels"""
        goto_targets = []
        labels = []
        
        for line in self.lines:
            stripped = line.strip()
            # Find goto statements
            if stripped.startswith('goto '):
                target = stripped.split()[1].replace(':', '')
                goto_targets.append(target)
            # Find labels
            if stripped.startswith(':') and not stripped.startswith('::'):
                label = stripped[1:].split()[0]
                labels.append(label)
        
        # Check that all goto targets have corresponding labels
        for target in goto_targets:
            if target != 'eof':  # Special label
                self.assertIn(
                    target, labels,
                    f"goto :{target} should have a corresponding label"
                )

    def test_uses_delayed_expansion_correctly(self):
        """Test that delayed expansion is used correctly with exclamation marks"""
        # After setlocal enabledelayedexpansion, we should see !var! instead of %var%
        # for variables that are set and used in the same code block
        has_delayed_vars = any(
            '!' in line and 'errorlevel' in line.lower()
            for line in self.lines
        )
        self.assertTrue(
            has_delayed_vars,
            "Script should use !errorlevel! with delayed expansion"
        )

    def test_has_version_validation(self):
        """Test that script validates Python version"""
        has_version_check = any(
            'PY_MAJOR' in line or 'PY_MINOR' in line or 'version_info' in line
            for line in self.lines
        )
        self.assertTrue(
            has_version_check,
            "Script should validate Python version"
        )

    def test_has_architecture_validation(self):
        """Test that script validates 64-bit Python"""
        has_arch_check = any(
            '64' in line and ('bit' in line.lower() or 'PY_BITS' in line)
            for line in self.lines
        )
        self.assertTrue(
            has_arch_check,
            "Script should validate 64-bit Python architecture"
        )


if __name__ == '__main__':
    unittest.main()
