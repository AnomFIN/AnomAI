"""
Tests for local model configuration parameters.

Ensures that new GGUF model parameters are properly handled in config.
"""
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Mock tkinter before importing jugiai
sys.modules['tkinter'] = mock.MagicMock()
sys.modules['tkinter.scrolledtext'] = mock.MagicMock()
sys.modules['tkinter.ttk'] = mock.MagicMock()
sys.modules['tkinter.filedialog'] = mock.MagicMock()
sys.modules['tkinter.messagebox'] = mock.MagicMock()
sys.modules['tkinter.simpledialog'] = mock.MagicMock()

from jugiai import DEFAULT_CONFIG


class LocalModelConfigTests(unittest.TestCase):
    """Test local model configuration parameters."""

    def test_default_config_includes_new_parameters(self):
        """Test that DEFAULT_CONFIG includes all new local model parameters."""
        expected_keys = [
            "local_n_ctx",
            "local_n_batch",
            "local_gpu_layers",
            "local_max_tokens",
            "local_seed",
            "local_rope_scale",
            "prefer_gpu",
        ]
        
        for key in expected_keys:
            self.assertIn(key, DEFAULT_CONFIG, f"Missing key: {key}")
    
    def test_default_values_are_sensible(self):
        """Test that default values for new parameters are sensible."""
        self.assertEqual(DEFAULT_CONFIG["local_n_ctx"], 4096)
        self.assertEqual(DEFAULT_CONFIG["local_n_batch"], 256)
        self.assertEqual(DEFAULT_CONFIG["local_gpu_layers"], -1)  # Auto
        self.assertIsNone(DEFAULT_CONFIG["local_max_tokens"])
        self.assertIsNone(DEFAULT_CONFIG["local_seed"])
        self.assertIsNone(DEFAULT_CONFIG["local_rope_scale"])
        self.assertTrue(DEFAULT_CONFIG["prefer_gpu"])
    
    def test_config_save_and_load_with_new_params(self):
        """Test that config with new parameters saves and loads correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
            config_data = {
                "api_key": "test-key",
                "backend": "local",
                "local_model_path": "/path/to/model.gguf",
                "local_threads": 4,
                "local_n_ctx": 8192,
                "local_n_batch": 512,
                "local_gpu_layers": 35,
                "local_max_tokens": 2048,
                "local_seed": 42,
                "local_rope_scale": 1.5,
                "prefer_gpu": False,
            }
            json.dump(config_data, f)
        
        try:
            # Load the config
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Verify all values are preserved
            self.assertEqual(loaded_config["local_n_ctx"], 8192)
            self.assertEqual(loaded_config["local_n_batch"], 512)
            self.assertEqual(loaded_config["local_gpu_layers"], 35)
            self.assertEqual(loaded_config["local_max_tokens"], 2048)
            self.assertEqual(loaded_config["local_seed"], 42)
            self.assertEqual(loaded_config["local_rope_scale"], 1.5)
            self.assertFalse(loaded_config["prefer_gpu"])
        finally:
            os.unlink(config_path)
    
    def test_config_merge_preserves_new_params(self):
        """Test that config merge preserves new parameters."""
        saved_config = {
            "local_n_ctx": 8192,
            "local_gpu_layers": 0,  # Force CPU
            "prefer_gpu": False,
        }
        
        # Merge like jugiai.py does: {**DEFAULT_CONFIG, **data}
        merged = {**DEFAULT_CONFIG, **saved_config}
        
        # Verify new values override defaults
        self.assertEqual(merged["local_n_ctx"], 8192)
        self.assertEqual(merged["local_gpu_layers"], 0)
        self.assertFalse(merged["prefer_gpu"])
        
        # Verify other defaults are still present
        self.assertEqual(merged["local_n_batch"], 256)  # Not overridden
        self.assertIsNone(merged["local_seed"])  # Not overridden
    
    def test_none_values_for_optional_params(self):
        """Test that None values for optional parameters are handled correctly."""
        config_data = {
            "local_max_tokens": None,
            "local_seed": None,
            "local_rope_scale": None,
        }
        
        # These should all be None by default
        for key, value in config_data.items():
            self.assertIsNone(value)
            self.assertIsNone(DEFAULT_CONFIG[key])
    
    def test_gpu_layers_auto_value(self):
        """Test that -1 for gpu_layers means auto-detect."""
        self.assertEqual(DEFAULT_CONFIG["local_gpu_layers"], -1)
        
        # -1 should be a valid value in config
        config_data = {"local_gpu_layers": -1}
        merged = {**DEFAULT_CONFIG, **config_data}
        self.assertEqual(merged["local_gpu_layers"], -1)
    
    def test_context_window_sizes(self):
        """Test various context window sizes."""
        test_cases = [
            2048,  # Small
            4096,  # Default
            8192,  # Large
            32768,  # Very large
        ]
        
        for n_ctx in test_cases:
            config_data = {"local_n_ctx": n_ctx}
            merged = {**DEFAULT_CONFIG, **config_data}
            self.assertEqual(merged["local_n_ctx"], n_ctx)


class LocalModelManagerTests(unittest.TestCase):
    """Test LocalModelManager class behavior."""
    
    def test_model_manager_import(self):
        """Test that LocalModelManager can be imported."""
        from jugiai import LocalModelManager, _local_model_manager
        
        self.assertIsNotNone(LocalModelManager)
        self.assertIsInstance(_local_model_manager, LocalModelManager)
    
    def test_model_manager_initial_state(self):
        """Test that model manager starts in unloaded state."""
        from jugiai import _local_model_manager
        
        # Fresh import should have no model loaded
        # Note: Can't fully reset global state, but can check attributes exist
        self.assertIsNone(_local_model_manager.llm)
        self.assertIsNone(_local_model_manager.model_path)
        self.assertEqual(_local_model_manager.loaded_params, {})


if __name__ == "__main__":
    unittest.main()
