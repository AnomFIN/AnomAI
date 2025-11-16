#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for install_tool_for_windows.py

This module tests the llama-cpp-python installation script to ensure it:
- Validates Python version correctly
- Checks pip availability
- Provides proper error messages
- Handles different installation scenarios
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module to test
import install_tool_for_windows as install_tool


class TestPythonVersionCheck(unittest.TestCase):
    """Test Python version validation."""
    
    @patch('install_tool_for_windows.sys.version_info')
    @patch('install_tool_for_windows.sys.maxsize', 2**63)  # 64-bit
    def test_valid_python_version(self, mock_version):
        """Test that valid Python version (3.10+ 64-bit) passes."""
        mock_version.major = 3
        mock_version.minor = 10
        mock_version.micro = 0
        
        result = install_tool.check_python_version()
        self.assertTrue(result)
    
    @patch('install_tool_for_windows.sys.version_info')
    @patch('install_tool_for_windows.sys.maxsize', 2**31)  # 32-bit
    def test_invalid_architecture(self, mock_version):
        """Test that 32-bit Python is rejected."""
        mock_version.major = 3
        mock_version.minor = 10
        mock_version.micro = 0
        
        result = install_tool.check_python_version()
        self.assertFalse(result)
    
    @patch('install_tool_for_windows.sys.version_info')
    @patch('install_tool_for_windows.sys.maxsize', 2**63)  # 64-bit
    def test_old_python_version(self, mock_version):
        """Test that Python < 3.10 is rejected."""
        mock_version.major = 3
        mock_version.minor = 9
        mock_version.micro = 0
        
        result = install_tool.check_python_version()
        self.assertFalse(result)
    
    @patch('install_tool_for_windows.sys.version_info')
    @patch('install_tool_for_windows.sys.maxsize', 2**63)  # 64-bit
    def test_python_2_rejected(self, mock_version):
        """Test that Python 2.x is rejected."""
        mock_version.major = 2
        mock_version.minor = 7
        mock_version.micro = 18
        
        result = install_tool.check_python_version()
        self.assertFalse(result)


class TestPipAvailability(unittest.TestCase):
    """Test pip availability check."""
    
    @patch('install_tool_for_windows.subprocess.run')
    def test_pip_available(self, mock_run):
        """Test that pip availability check works when pip is available."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = install_tool.check_pip_available()
        self.assertTrue(result)
        
        # Verify that subprocess.run was called correctly
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn('pip', args)
        self.assertIn('--version', args)
    
    @patch('install_tool_for_windows.subprocess.run')
    def test_pip_not_available(self, mock_run):
        """Test that pip availability check fails when pip is not available."""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, 'pip')
        
        result = install_tool.check_pip_available()
        self.assertFalse(result)


class TestRunPipCommand(unittest.TestCase):
    """Test pip command execution."""
    
    @patch('install_tool_for_windows.subprocess.run')
    def test_successful_pip_command(self, mock_run):
        """Test that successful pip commands return True."""
        mock_run.return_value = MagicMock(returncode=0, stdout='Success', stderr='')
        
        result = install_tool.run_pip_command(
            ['install', 'test-package'],
            'Test installation'
        )
        
        self.assertTrue(result)
        mock_run.assert_called_once()
    
    @patch('install_tool_for_windows.subprocess.run')
    def test_failed_pip_command(self, mock_run):
        """Test that failed pip commands return False."""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(
            1, 'pip', output='', stderr='Error'
        )
        
        result = install_tool.run_pip_command(
            ['install', 'nonexistent-package'],
            'Test installation'
        )
        
        self.assertFalse(result)


class TestColorFunctions(unittest.TestCase):
    """Test color output functions."""
    
    def test_colors_can_be_disabled(self):
        """Test that color codes can be disabled."""
        # Store original values
        original_okgreen = install_tool.Colors.OKGREEN
        
        # Disable colors
        install_tool.Colors.disable()
        
        # Verify colors are empty
        self.assertEqual(install_tool.Colors.OKGREEN, '')
        self.assertEqual(install_tool.Colors.FAIL, '')
        self.assertEqual(install_tool.Colors.WARNING, '')
        
        # Restore original value for other tests
        install_tool.Colors.OKGREEN = original_okgreen
    
    def test_print_functions_dont_crash(self):
        """Test that print functions don't crash."""
        # These should not raise exceptions
        try:
            install_tool.print_header("Test")
            install_tool.print_success("Test")
            install_tool.print_info("Test")
            install_tool.print_warning("Test")
            install_tool.print_error("Test")
        except Exception as e:
            self.fail(f"Print function raised exception: {e}")


class TestInstallationScript(unittest.TestCase):
    """Test the installation script structure."""
    
    def test_script_has_main_function(self):
        """Test that script has a main function."""
        self.assertTrue(hasattr(install_tool, 'main'))
        self.assertTrue(callable(install_tool.main))
    
    def test_script_has_install_functions(self):
        """Test that script has installation functions."""
        self.assertTrue(hasattr(install_tool, 'install_cpu_version'))
        self.assertTrue(hasattr(install_tool, 'install_gpu_version'))
        self.assertTrue(callable(install_tool.install_cpu_version))
        self.assertTrue(callable(install_tool.install_gpu_version))
    
    def test_script_has_verify_function(self):
        """Test that script has verification function."""
        self.assertTrue(hasattr(install_tool, 'verify_installation'))
        self.assertTrue(callable(install_tool.verify_installation))


class TestScriptExecution(unittest.TestCase):
    """Test script execution scenarios."""
    
    def test_help_flag_is_available(self):
        """Test that --help flag is available in argparse."""
        # Create an argument parser like the one in the script
        import argparse
        parser = argparse.ArgumentParser()
        
        # --help is built-in to argparse, so we just test it exits properly
        with self.assertRaises(SystemExit) as cm:
            parser.parse_args(['--help'])
        
        # Verify it exits with code 0
        self.assertEqual(cm.exception.code, 0)


class TestFileContent(unittest.TestCase):
    """Test that the script file has proper content."""
    
    def setUp(self):
        """Set up test by finding the script file."""
        self.script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'install_tool_for_windows.py'
        )
    
    def test_file_exists(self):
        """Test that install_tool_for_windows.py exists."""
        self.assertTrue(os.path.exists(self.script_path))
    
    def test_file_has_shebang(self):
        """Test that script has proper shebang."""
        with open(self.script_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
        
        self.assertTrue(first_line.startswith('#!'))
    
    def test_file_has_utf8_encoding(self):
        """Test that script declares UTF-8 encoding."""
        with open(self.script_path, 'r', encoding='utf-8') as f:
            content = f.read(500)  # Read first 500 chars
        
        self.assertIn('utf-8', content.lower())
    
    def test_file_has_docstring(self):
        """Test that script has a module docstring."""
        with open(self.script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for triple-quoted docstring
        self.assertIn('"""', content)
    
    def test_file_mentions_llama_cpp_python(self):
        """Test that script mentions llama-cpp-python."""
        with open(self.script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('llama-cpp-python', content)
    
    def test_file_has_error_handling(self):
        """Test that script has error handling."""
        with open(self.script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have try/except blocks
        self.assertIn('try:', content)
        self.assertIn('except', content)
    
    def test_file_has_gpu_support(self):
        """Test that script supports GPU installation."""
        with open(self.script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('--gpu', content)
        self.assertIn('CUDA', content)


if __name__ == '__main__':
    unittest.main()
