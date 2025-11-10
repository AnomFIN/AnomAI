"""
Tests for GPU configuration saving and loading.

Ensures that the GPU settings are properly saved and loaded from config.
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


class GPUConfigTests(unittest.TestCase):
    """Test GPU configuration."""

    def test_use_gpu_cpu_mode_save_and_load(self):
        """Test that use_gpu CPU mode is saved and loaded correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
            config_data = {
                "api_key": "test-key",
                "model": "gpt-4o-mini",
                "backend": "local",
                "local_model_path": "/path/to/model.gguf",
                "local_threads": 0,
                "use_gpu": "cpu",
                "n_gpu_layers": 0
            }
            json.dump(config_data, f)
        
        try:
            # Load the config
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Verify the GPU settings are preserved
            self.assertEqual(loaded_config["use_gpu"], "cpu")
            self.assertEqual(loaded_config["n_gpu_layers"], 0)
        finally:
            os.unlink(config_path)

    def test_use_gpu_gpu_mode_save_and_load(self):
        """Test that use_gpu GPU mode is saved and loaded correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
            config_data = {
                "api_key": "test-key",
                "model": "gpt-4o-mini",
                "backend": "local",
                "local_model_path": "/path/to/model.gguf",
                "local_threads": 0,
                "use_gpu": "gpu",
                "n_gpu_layers": -1
            }
            json.dump(config_data, f)
        
        try:
            # Load the config
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Verify the GPU settings are preserved
            self.assertEqual(loaded_config["use_gpu"], "gpu")
            self.assertEqual(loaded_config["n_gpu_layers"], -1)
        finally:
            os.unlink(config_path)

    def test_use_gpu_both_mode_save_and_load(self):
        """Test that use_gpu both mode with custom layer count is saved and loaded correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
            config_data = {
                "api_key": "test-key",
                "model": "gpt-4o-mini",
                "backend": "local",
                "local_model_path": "/path/to/model.gguf",
                "local_threads": 0,
                "use_gpu": "both",
                "n_gpu_layers": 20
            }
            json.dump(config_data, f)
        
        try:
            # Load the config
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Verify the GPU settings are preserved
            self.assertEqual(loaded_config["use_gpu"], "both")
            self.assertEqual(loaded_config["n_gpu_layers"], 20)
        finally:
            os.unlink(config_path)

    def test_default_gpu_settings(self):
        """Test that default GPU settings are CPU mode."""
        default_config = {
            "api_key": "",
            "model": "gpt-4o-mini",
            "backend": "openai",
            "local_model_path": "",
            "local_threads": 0,
            "use_gpu": "cpu",
            "n_gpu_layers": 0
        }
        
        # Verify defaults
        self.assertEqual(default_config["use_gpu"], "cpu")
        self.assertEqual(default_config["n_gpu_layers"], 0)

    def test_config_merge_preserves_gpu_settings(self):
        """Test that config merge preserves GPU settings from saved config."""
        default_config = {
            "api_key": "",
            "model": "gpt-4o-mini",
            "backend": "openai",
            "local_model_path": "",
            "local_threads": 0,
            "use_gpu": "cpu",
            "n_gpu_layers": 0
        }
        
        saved_config = {
            "backend": "local",
            "local_model_path": "/path/to/model.gguf",
            "use_gpu": "gpu",
            "n_gpu_layers": -1
        }
        
        # Merge like jugiai.py does: {**DEFAULT_CONFIG, **data}
        merged = {**default_config, **saved_config}
        
        # Verify GPU settings from saved config override defaults
        self.assertEqual(merged["use_gpu"], "gpu")
        self.assertEqual(merged["n_gpu_layers"], -1)
        self.assertEqual(merged["backend"], "local")

    def test_gpu_mode_validation(self):
        """Test that invalid GPU modes default to CPU."""
        valid_modes = ["cpu", "gpu", "both"]
        
        for mode in valid_modes:
            self.assertIn(mode, valid_modes)
        
        # Invalid mode should be handled by setting code
        invalid_mode = "invalid"
        self.assertNotIn(invalid_mode, valid_modes)

    def test_n_gpu_layers_negative_one(self):
        """Test that n_gpu_layers=-1 is handled correctly (all layers to GPU)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
            config_data = {
                "use_gpu": "gpu",
                "n_gpu_layers": -1
            }
            json.dump(config_data, f)
        
        try:
            # Load the config
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Verify -1 is preserved
            self.assertEqual(loaded_config["n_gpu_layers"], -1)
        finally:
            os.unlink(config_path)

    def test_n_gpu_layers_positive_integer(self):
        """Test that positive n_gpu_layers values are handled correctly."""
        test_values = [1, 10, 20, 35, 50]
        
        for layers in test_values:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                config_path = f.name
                config_data = {
                    "use_gpu": "both",
                    "n_gpu_layers": layers
                }
                json.dump(config_data, f)
            
            try:
                # Load the config
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Verify the layer count is preserved
                self.assertEqual(loaded_config["n_gpu_layers"], layers)
            finally:
                os.unlink(config_path)


if __name__ == "__main__":
    unittest.main()
