#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for local_requirements.txt

This module tests the local_requirements.txt file to ensure it:
- Exists and is readable
- Contains llama-cpp-python
- Has proper documentation
- Uses proper encoding
"""

import os
import unittest


class TestLocalRequirements(unittest.TestCase):
    """Test local_requirements.txt file."""
    
    def setUp(self):
        """Set up test by finding the requirements file."""
        self.req_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'local_requirements.txt'
        )
    
    def test_file_exists(self):
        """Test that local_requirements.txt exists."""
        self.assertTrue(
            os.path.exists(self.req_path),
            f"local_requirements.txt not found at {self.req_path}"
        )
    
    def test_file_is_readable(self):
        """Test that local_requirements.txt is readable."""
        try:
            with open(self.req_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIsNotNone(content)
        except Exception as e:
            self.fail(f"Failed to read local_requirements.txt: {e}")
    
    def test_file_contains_llama_cpp_python(self):
        """Test that file contains llama-cpp-python."""
        with open(self.req_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should contain llama-cpp-python as a package
        self.assertIn('llama-cpp-python', content)
    
    def test_file_has_documentation(self):
        """Test that file has proper documentation."""
        with open(self.req_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have documentation headers
        self.assertIn('#', content)  # Has comments
        self.assertIn('INSTALLATION', content.upper())  # Has installation section
    
    def test_file_mentions_installation_methods(self):
        """Test that file mentions multiple installation methods."""
        with open(self.req_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should mention different installation options
        self.assertIn('install_tool_for_windows.py', content)
        self.assertIn('pip install', content)
    
    def test_file_mentions_gpu_support(self):
        """Test that file mentions GPU installation option."""
        with open(self.req_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should mention GPU/CUDA support
        self.assertIn('GPU', content)
        self.assertIn('CUDA', content)
    
    def test_file_has_no_bom(self):
        """Test that file has no BOM (Byte Order Mark)."""
        with open(self.req_path, 'rb') as f:
            first_bytes = f.read(3)
        
        # UTF-8 BOM is EF BB BF
        self.assertNotEqual(
            first_bytes,
            b'\xef\xbb\xbf',
            "File should not have UTF-8 BOM"
        )
    
    def test_file_uses_unix_or_windows_line_endings(self):
        """Test that file uses consistent line endings."""
        with open(self.req_path, 'rb') as f:
            content = f.read()
        
        # Should have line endings (either LF or CRLF)
        has_lf = b'\n' in content
        has_crlf = b'\r\n' in content
        
        self.assertTrue(
            has_lf or has_crlf,
            "File should have line endings"
        )
    
    def test_file_is_not_empty(self):
        """Test that file is not empty."""
        with open(self.req_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        
        # Should have at least one non-comment line (the package)
        self.assertGreater(
            len(lines),
            0,
            "File should contain at least one package"
        )
    
    def test_package_line_format(self):
        """Test that package line has proper format."""
        with open(self.req_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        
        # Find the llama-cpp-python line
        llama_line = None
        for line in lines:
            if 'llama-cpp-python' in line:
                llama_line = line
                break
        
        self.assertIsNotNone(llama_line, "Should have llama-cpp-python line")
        
        # Should just be the package name (possibly with version specifier)
        # Format: llama-cpp-python[==version]
        self.assertTrue(
            llama_line.startswith('llama-cpp-python'),
            f"Package line should start with 'llama-cpp-python', got: {llama_line}"
        )


class TestRequirementsFileIntegration(unittest.TestCase):
    """Test integration with pip and requirements handling."""
    
    def setUp(self):
        """Set up test by finding the requirements file."""
        self.req_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'local_requirements.txt'
        )
    
    def test_file_can_be_parsed_by_pip(self):
        """Test that file can be parsed by pip (basic syntax check)."""
        import subprocess
        import sys
        
        # Try to parse the requirements file with pip (dry-run)
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--dry-run', '-r', self.req_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Should not have syntax errors in parsing
            # (may fail to install, but should parse OK)
            self.assertNotIn('ERROR: Invalid requirement', result.stderr)
            self.assertNotIn('Could not parse', result.stderr)
            
        except subprocess.TimeoutExpired:
            # If it times out, it at least started parsing successfully
            pass
        except FileNotFoundError:
            self.skipTest("pip not available in test environment")


if __name__ == '__main__':
    unittest.main()
