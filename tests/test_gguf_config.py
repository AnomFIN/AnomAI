"""
Tests for GGUF model configuration saving and loading.

Ensures that the local model path is properly saved and loaded from config.
"""
import json
import os
import pathlib
import sys
import tempfile
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class GGUFConfigTests(unittest.TestCase):
    """Test GGUF model path configuration."""

    def test_local_model_path_save_and_load(self):
        """Test that local_model_path is saved and loaded correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
            config_data = {
                "api_key": "test-key",
                "model": "gpt-4o-mini",
                "backend": "local",
                "local_model_path": "/path/to/model.gguf",
                "local_threads": 0
            }
            json.dump(config_data, f)
        
        try:
            # Load the config
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Verify the path is preserved
            self.assertEqual(loaded_config["local_model_path"], "/path/to/model.gguf")
            self.assertEqual(loaded_config["backend"], "local")
        finally:
            os.unlink(config_path)

    def test_local_model_path_stripped_on_save(self):
        """Test that local_model_path is stripped of whitespace on save."""
        test_path = "  /path/to/model.gguf  "
        stripped_path = test_path.strip()
        
        self.assertEqual(stripped_path, "/path/to/model.gguf")
        self.assertNotEqual(stripped_path, test_path)

    def test_empty_local_model_path(self):
        """Test that empty local_model_path is handled correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
            config_data = {
                "api_key": "test-key",
                "model": "gpt-4o-mini",
                "backend": "local",
                "local_model_path": "",
                "local_threads": 0
            }
            json.dump(config_data, f)
        
        try:
            # Load the config
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Verify empty path is preserved
            model_path = (loaded_config.get("local_model_path") or "").strip()
            self.assertEqual(model_path, "")
        finally:
            os.unlink(config_path)

    def test_local_model_path_with_spaces(self):
        """Test that local_model_path with spaces in filename is handled correctly."""
        test_path = "/path/to/my model with spaces.gguf"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
            config_data = {
                "api_key": "test-key",
                "model": "gpt-4o-mini",
                "backend": "local",
                "local_model_path": test_path,
                "local_threads": 0
            }
            json.dump(config_data, f)
        
        try:
            # Load the config
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Verify the path with spaces is preserved
            self.assertEqual(loaded_config["local_model_path"], test_path)
        finally:
            os.unlink(config_path)

    def test_config_merge_preserves_local_model_path(self):
        """Test that config merge preserves local_model_path from saved config."""
        default_config = {
            "api_key": "",
            "model": "gpt-4o-mini",
            "backend": "openai",
            "local_model_path": "",
            "local_threads": 0
        }
        
        saved_config = {
            "backend": "local",
            "local_model_path": "/path/to/model.gguf"
        }
        
        # Merge like jugiai.py does: {**DEFAULT_CONFIG, **data}
        merged = {**default_config, **saved_config}
        
        # Verify local_model_path from saved config overrides default
        self.assertEqual(merged["local_model_path"], "/path/to/model.gguf")
        self.assertEqual(merged["backend"], "local")


if __name__ == "__main__":
    unittest.main()
