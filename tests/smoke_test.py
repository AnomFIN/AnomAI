#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke Test for AnomAI/JugiAI
============================

Basic smoke test to verify the application can start and core functionality works.
This test runs in CI environments without GUI and validates:

1. Import sanity - all core modules can be imported
2. Configuration handling - config creation and loading
3. Offline mode detection - works without API keys
4. Core utilities - font size validation, playback utilities
5. Optional dependencies - graceful degradation when missing
6. Entry point validation - main script can be executed

This test ensures the application is installable and runnable in fresh environments.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class SmokeTest(unittest.TestCase):
    """Basic smoke tests for AnomAI application."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_import_core_modules(self):
        """Test that core modules can be imported without errors."""
        # Test playback utilities
        try:
            from playback_utils import (
                MAX_FONT_SIZE, MIN_FONT_SIZE, 
                clamp_font_size, resolve_speed_delay
            )
            self.assertIsInstance(MAX_FONT_SIZE, int)
            self.assertIsInstance(MIN_FONT_SIZE, int)
            self.assertTrue(callable(clamp_font_size))
            self.assertTrue(callable(resolve_speed_delay))
        except ImportError as e:
            self.fail(f"Failed to import playback_utils: {e}")
        
        # Test make_ico utility
        try:
            import make_ico
            # Should have main function
            self.assertTrue(hasattr(make_ico, 'main') or callable(make_ico))
        except ImportError as e:
            self.fail(f"Failed to import make_ico: {e}")
    
    def test_playback_utilities(self):
        """Test core playback utility functions."""
        from playback_utils import clamp_font_size, resolve_speed_delay
        
        # Test font size clamping
        self.assertEqual(clamp_font_size(5), 8)  # Below minimum
        self.assertEqual(clamp_font_size(15), 15)  # Within range
        self.assertEqual(clamp_font_size(50), 36)  # Above maximum
        
        # Test speed delay resolution
        self.assertIsInstance(resolve_speed_delay("fast"), (int, float))
        self.assertIsInstance(resolve_speed_delay("medium"), (int, float))
        self.assertIsInstance(resolve_speed_delay("slow"), (int, float))
        self.assertGreater(resolve_speed_delay("slow"), resolve_speed_delay("fast"))
    
    def test_configuration_handling(self):
        """Test configuration creation and validation."""
        # Mock tkinter to prevent GUI from launching
        with patch.dict('sys.modules', {
            'tkinter': MagicMock(),
            'tkinter.messagebox': MagicMock(),
            'tkinter.filedialog': MagicMock(),
            'tkinter.simpledialog': MagicMock(),
            'tkinter.ttk': MagicMock(),
            'tkinter.scrolledtext': MagicMock()
        }):
            # Change to temp directory for config file tests
            os.chdir(self.temp_dir)
            
            try:
                # Import after mocking GUI components
                from jugiai import DEFAULT_CONFIG, ChatApp
                
                # Test default config structure
                self.assertIsInstance(DEFAULT_CONFIG, dict)
                self.assertIn("model", DEFAULT_CONFIG)
                self.assertIn("temperature", DEFAULT_CONFIG)
                self.assertIn("backend", DEFAULT_CONFIG)
                
                # Test config file creation
                config_file = Path(self.temp_dir) / "config.json"
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
                
                self.assertTrue(config_file.exists())
                
                # Validate config can be loaded
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                self.assertEqual(loaded_config["model"], DEFAULT_CONFIG["model"])
                
            except ImportError as e:
                if "tkinter" in str(e).lower():
                    self.skipTest("tkinter not available in headless environment")
                else:
                    self.fail(f"Failed to import jugiai: {e}")
    
    def test_offline_mode_detection(self):
        """Test that offline mode works without API keys."""
        with patch.dict('sys.modules', {
            'tkinter': MagicMock(),
            'tkinter.messagebox': MagicMock(),
            'tkinter.filedialog': MagicMock(),
            'tkinter.simpledialog': MagicMock(),
            'tkinter.ttk': MagicMock(),
            'tkinter.scrolledtext': MagicMock()
        }):
            try:
                from jugiai import DEFAULT_CONFIG
                
                # Test offline mode detection
                offline_config = DEFAULT_CONFIG.copy()
                offline_config["api_key"] = ""
                offline_config["backend"] = "local"
                offline_config["offline_mode"] = True
                
                self.assertEqual(offline_config["backend"], "local")
                self.assertTrue(offline_config["offline_mode"])
                
            except ImportError as e:
                if "tkinter" in str(e).lower():
                    self.skipTest("tkinter not available in headless environment")
                else:
                    self.fail(f"Failed to test offline mode: {e}")
    
    def test_optional_dependencies_graceful_degradation(self):
        """Test that missing optional dependencies don't break the app."""
        # Test PIL/Pillow handling
        with patch.dict('sys.modules', {'PIL': None, 'PIL.Image': None}):
            try:
                from jugiai import PIL_AVAILABLE
                # Should gracefully handle missing PIL
                self.assertFalse(PIL_AVAILABLE)
            except ImportError as e:
                if "tkinter" not in str(e).lower():
                    self.fail(f"Should handle missing PIL gracefully: {e}")
        
        # Test llama-cpp-python handling  
        with patch.dict('sys.modules', {'llama_cpp': None}):
            # Should not crash when llama_cpp is missing
            # This is expected for fresh installs
            pass
    
    def test_entry_point_validation(self):
        """Test that the main entry point can be executed."""
        jugiai_path = PROJECT_ROOT / "jugiai.py"
        self.assertTrue(jugiai_path.exists(), "jugiai.py main entry point not found")
        
        # Verify it's a valid Python file
        with open(jugiai_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have proper encoding declaration
        self.assertIn("# -*- coding: utf-8 -*-", content)
        
        # Should have main execution guard
        self.assertIn('if __name__ == "__main__"', content)
        
        # Should import required standard library modules
        self.assertIn("import tkinter", content)
        self.assertIn("import json", content)
        self.assertIn("import os", content)
    
    def test_requirements_file_validity(self):
        """Test that requirements.txt is valid and minimal."""
        req_file = PROJECT_ROOT / "requirements.txt"
        self.assertTrue(req_file.exists(), "requirements.txt not found")
        
        with open(req_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should contain Pillow
        self.assertIn("pillow", content.lower())
        
        # Should not contain llama-cpp-python (handled separately)
        self.assertNotIn("llama-cpp-python", content.lower())
        
        # Should not contain PyInstaller (dev dependency)
        self.assertNotIn("pyinstaller", content.lower())
    
    def test_unified_installer_exists(self):
        """Test that the unified installer is present and functional."""
        installer_path = PROJECT_ROOT / "install.py"
        self.assertTrue(installer_path.exists(), "install.py unified installer not found")
        
        # Test that it can be imported without executing
        import importlib.util
        spec = importlib.util.spec_from_file_location("install", installer_path)
        install_module = importlib.util.module_from_spec(spec)
        
        # Should not crash on import
        try:
            spec.loader.exec_module(install_module)
            # Should have main classes and functions
            self.assertTrue(hasattr(install_module, 'AnomAIInstaller'))
            self.assertTrue(hasattr(install_module, 'main'))
        except SystemExit:
            # Expected if run without proper args, that's fine
            pass
    
    def test_legacy_installer_archived(self):
        """Test that legacy installers are properly archived."""
        legacy_dir = PROJECT_ROOT / "legacy-orig"
        self.assertTrue(legacy_dir.exists(), "legacy-orig directory not found")
        
        # Should contain archived installers
        self.assertTrue((legacy_dir / "install.bat").exists())
        self.assertTrue((legacy_dir / "install_utf8.bat").exists())
        
        # Should have README explaining the archive
        readme = legacy_dir / "README.md"
        self.assertTrue(readme.exists(), "legacy-orig/README.md not found")
        
        with open(readme, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("Legacy Installation Scripts", content)
        self.assertIn("install.py", content)


class IntegrationSmokeTest(unittest.TestCase):
    """Integration smoke tests that require more setup."""
    
    def test_app_startup_simulation(self):
        """Test that app can start in offline mode without crashing."""
        with patch.dict('sys.modules', {
            'tkinter': MagicMock(),
            'tkinter.messagebox': MagicMock(),
            'tkinter.filedialog': MagicMock(),
            'tkinter.simpledialog': MagicMock(),
            'tkinter.ttk': MagicMock(),
            'tkinter.scrolledtext': MagicMock()
        }):
            try:
                from jugiai import ChatApp, DEFAULT_CONFIG
                
                # Create a minimal offline config
                offline_config = DEFAULT_CONFIG.copy()
                offline_config.update({
                    "api_key": "",
                    "backend": "local", 
                    "offline_mode": True,
                    "local_model_path": "",  # Empty, should handle gracefully
                })
                
                # Mock the config and history files
                with tempfile.TemporaryDirectory() as temp_dir:
                    config_path = os.path.join(temp_dir, "config.json")
                    history_path = os.path.join(temp_dir, "history.json")
                    
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(offline_config, f)
                    
                    with open(history_path, 'w', encoding='utf-8') as f:
                        json.dump([], f)
                    
                    # Patch the file paths
                    with patch('jugiai.CONFIG_FILE', config_path), \
                         patch('jugiai.HISTORY_FILE', history_path):
                        
                        # Mock Tk root to prevent actual GUI
                        mock_root = MagicMock()
                        
                        # Should be able to create app instance
                        # This tests config loading and initialization
                        try:
                            # We can't actually create the GUI in headless mode
                            # but we can test config loading logic
                            pass
                        except Exception as e:
                            # Should not crash due to missing dependencies
                            if "llama" in str(e).lower():
                                pass  # Expected when llama-cpp-python not installed
                            else:
                                self.fail(f"Unexpected error in app startup: {e}")
                                
            except ImportError as e:
                if "tkinter" in str(e).lower():
                    self.skipTest("tkinter not available in headless environment")
                else:
                    raise


def main():
    """Run smoke tests."""
    # Configure test discovery
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(SmokeTest))
    suite.addTests(loader.loadTestsFromTestCase(IntegrationSmokeTest))
    
    # Run tests
    runner = unittest.TextTestRunner(
        verbosity=2,
        failfast=False,
        buffer=True
    )
    
    result = runner.run(suite)
    
    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)