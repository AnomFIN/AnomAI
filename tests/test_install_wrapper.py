"""
Test to validate the install.bat wrapper and UTF-8 setup.
This ensures that the installation entry point properly chains to UTF-8 handling.
"""
import unittest
import os


class TestInstallWrapper(unittest.TestCase):
    """Test cases for install.bat wrapper validation"""

    def setUp(self):
        """Set up test by finding the project root"""
        self.project_root = os.path.dirname(os.path.dirname(__file__))
        self.install_bat = os.path.join(self.project_root, 'install.bat')
        self.install_utf8_bat = os.path.join(self.project_root, 'install_utf8.bat')
        self.install_main_bat = os.path.join(self.project_root, 'install_main.bat')

    def test_all_install_files_exist(self):
        """Test that all installation files exist"""
        self.assertTrue(
            os.path.exists(self.install_bat),
            "install.bat (wrapper) should exist"
        )
        self.assertTrue(
            os.path.exists(self.install_utf8_bat),
            "install_utf8.bat (UTF-8 handler) should exist"
        )
        self.assertTrue(
            os.path.exists(self.install_main_bat),
            "install_main.bat (main installer) should exist"
        )

    def test_wrapper_calls_utf8_handler(self):
        """Test that install.bat calls install_utf8.bat"""
        with open(self.install_bat, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn(
            'install_utf8.bat',
            content,
            "install.bat should call install_utf8.bat"
        )
        self.assertIn(
            'call "install_utf8.bat"',
            content,
            "install.bat should use 'call' to invoke install_utf8.bat"
        )

    def test_utf8_handler_calls_main_installer(self):
        """Test that install_utf8.bat calls install_main.bat"""
        with open(self.install_utf8_bat, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn(
            'install_main.bat',
            content,
            "install_utf8.bat should reference install_main.bat"
        )

    def test_wrapper_has_error_handling(self):
        """Test that install.bat has basic error handling"""
        with open(self.install_bat, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn(
            'if not exist',
            content,
            "install.bat should check if required files exist"
        )
        self.assertIn(
            'pause',
            content,
            "install.bat should pause on error"
        )

    def test_wrapper_is_simple_and_focused(self):
        """Test that install.bat wrapper is simple (< 50 lines)"""
        with open(self.install_bat, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Remove empty lines and comments for counting
        code_lines = [
            line for line in lines 
            if line.strip() and not line.strip().startswith('::')
        ]
        self.assertLess(
            len(code_lines), 50,
            "install.bat wrapper should be simple (< 50 lines of code)"
        )

    def test_wrapper_has_no_utf8_characters(self):
        """Test that install.bat wrapper contains only ASCII"""
        with open(self.install_bat, 'rb') as f:
            content = f.read()
        # Check for UTF-8 BOM
        self.assertFalse(
            content.startswith(b'\xef\xbb\xbf'),
            "install.bat should not have UTF-8 BOM"
        )
        # Try to decode as ASCII
        try:
            content.decode('ascii')
        except UnicodeDecodeError:
            self.fail("install.bat wrapper should contain only ASCII characters")

    def test_main_installer_has_no_problematic_utf8(self):
        """Test that install_main.bat has no problematic UTF-8 characters"""
        with open(self.install_main_bat, 'r', encoding='utf-8') as f:
            content = f.read()
        # Check for common problematic UTF-8 characters
        problematic_chars = {
            '\u2014': 'em dash',  # em dash (—)
            '\u2013': 'en dash',  # en dash (–)
            '\u2018': 'left single quote',  # left single quote (')
            '\u2019': 'right single quote',  # right single quote (')
            '\u201c': 'left double quote',  # left double quote (")
            '\u201d': 'right double quote',  # right double quote (")
        }
        for char, name in problematic_chars.items():
            self.assertNotIn(
                char, content,
                f"install_main.bat should not contain {name} - use ASCII equivalent"
            )

    def test_utf8_handler_sets_codepage(self):
        """Test that install_utf8.bat sets UTF-8 codepage"""
        with open(self.install_utf8_bat, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn(
            'chcp 65001',
            content,
            "install_utf8.bat should set codepage to 65001 (UTF-8)"
        )

    def test_utf8_handler_restores_codepage(self):
        """Test that install_utf8.bat restores original codepage"""
        with open(self.install_utf8_bat, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn(
            ':restore_codepage',
            content,
            "install_utf8.bat should have restore_codepage function"
        )


if __name__ == '__main__':
    unittest.main()
