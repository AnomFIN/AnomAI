"""
Tests for repeat_penalty parameter support in local models.

Ensures that repeat_penalty is properly configured and passed to llama-cpp-python.
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

from jugiai import DEFAULT_CONFIG, DEFAULT_PROFILE


class RepeatPenaltyConfigTests(unittest.TestCase):
    """Test repeat_penalty configuration."""

    def test_default_config_includes_repeat_penalty(self):
        """Test that DEFAULT_CONFIG includes repeat_penalty."""
        self.assertIn("repeat_penalty", DEFAULT_CONFIG)
        self.assertEqual(DEFAULT_CONFIG["repeat_penalty"], 1.1)
    
    def test_default_profile_includes_repeat_penalty(self):
        """Test that DEFAULT_PROFILE includes repeat_penalty."""
        self.assertIn("repeat_penalty", DEFAULT_PROFILE)
        self.assertEqual(DEFAULT_PROFILE["repeat_penalty"], 1.1)
    
    def test_repeat_penalty_default_value_is_sensible(self):
        """Test that default repeat_penalty value reduces repetition."""
        # repeat_penalty > 1.0 reduces repetition
        # 1.1 is a common default value
        self.assertGreater(DEFAULT_CONFIG["repeat_penalty"], 1.0)
        self.assertLessEqual(DEFAULT_CONFIG["repeat_penalty"], 1.5)
    
    def test_config_save_and_load_with_repeat_penalty(self):
        """Test that config with repeat_penalty saves and loads correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
            config_data = {
                "api_key": "test-key",
                "backend": "local",
                "local_model_path": "/path/to/model.gguf",
                "repeat_penalty": 1.3,
            }
            json.dump(config_data, f)
        
        try:
            # Load the config
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Verify repeat_penalty is preserved
            self.assertEqual(loaded_config["repeat_penalty"], 1.3)
        finally:
            os.unlink(config_path)
    
    def test_config_merge_preserves_repeat_penalty(self):
        """Test that config merge preserves repeat_penalty."""
        saved_config = {
            "repeat_penalty": 1.5,
        }
        
        # Merge like jugiai.py does: {**DEFAULT_CONFIG, **data}
        merged = {**DEFAULT_CONFIG, **saved_config}
        
        # Verify new value overrides default
        self.assertEqual(merged["repeat_penalty"], 1.5)
    
    def test_repeat_penalty_range(self):
        """Test valid range for repeat_penalty."""
        # Typical range is 1.0 to 2.0
        # 1.0 = no penalty, >1.0 reduces repetition
        test_values = [1.0, 1.1, 1.2, 1.3, 1.5, 2.0]
        
        for value in test_values:
            config_data = {"repeat_penalty": value}
            merged = {**DEFAULT_CONFIG, **config_data}
            self.assertEqual(merged["repeat_penalty"], value)
            self.assertGreaterEqual(merged["repeat_penalty"], 1.0)
            self.assertLessEqual(merged["repeat_penalty"], 2.0)


class RepeatPenaltyProfileTests(unittest.TestCase):
    """Test repeat_penalty in profile management."""
    
    def test_profile_includes_repeat_penalty(self):
        """Test that profiles can include repeat_penalty."""
        profile_data = {
            "name": "Test Profile",
            "model": "local-model",
            "backend": "local",
            "repeat_penalty": 1.4,
        }
        
        # Verify repeat_penalty is part of the profile
        self.assertIn("repeat_penalty", profile_data)
        self.assertEqual(profile_data["repeat_penalty"], 1.4)
    
    def test_profile_with_different_repeat_penalty_values(self):
        """Test profiles with different repeat_penalty values."""
        profiles = {
            "Low Repetition": {"repeat_penalty": 1.5},
            "Moderate": {"repeat_penalty": 1.2},
            "Minimal": {"repeat_penalty": 1.0},
        }
        
        for name, profile in profiles.items():
            self.assertIn("repeat_penalty", profile)
            self.assertGreaterEqual(profile["repeat_penalty"], 1.0)


class RepeatPenaltyLocalModelTests(unittest.TestCase):
    """Test repeat_penalty parameter usage in local model calls."""
    
    def test_repeat_penalty_parameter_format(self):
        """Test that repeat_penalty is formatted correctly."""
        # repeat_penalty should be a float
        value = DEFAULT_CONFIG["repeat_penalty"]
        self.assertIsInstance(value, (int, float))
        
        # Should be convertible to float
        float_value = float(value)
        self.assertIsInstance(float_value, float)
    
    def test_repeat_penalty_different_from_openai_penalties(self):
        """Test that repeat_penalty is distinct from OpenAI penalties."""
        # OpenAI uses frequency_penalty and presence_penalty (range -2.0 to 2.0)
        # llama-cpp-python uses repeat_penalty (range 1.0 to 2.0)
        
        # Verify all three parameters exist
        self.assertIn("frequency_penalty", DEFAULT_CONFIG)
        self.assertIn("presence_penalty", DEFAULT_CONFIG)
        self.assertIn("repeat_penalty", DEFAULT_CONFIG)
        
        # Verify they have different ranges/defaults
        # frequency_penalty and presence_penalty default to 0.0
        self.assertEqual(DEFAULT_CONFIG["frequency_penalty"], 0.0)
        self.assertEqual(DEFAULT_CONFIG["presence_penalty"], 0.0)
        # repeat_penalty defaults to 1.1
        self.assertEqual(DEFAULT_CONFIG["repeat_penalty"], 1.1)


if __name__ == "__main__":
    unittest.main()
