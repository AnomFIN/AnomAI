"""
Integration tests for repeat_penalty parameter verification.

Verifies that repeat_penalty configuration is properly structured for use with local models.
"""
import pathlib
import sys
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


class RepeatPenaltyConfigurationTests(unittest.TestCase):
    """Test that repeat_penalty configuration is properly set up."""
    
    def test_repeat_penalty_in_default_config(self):
        """Verify repeat_penalty is in DEFAULT_CONFIG."""
        self.assertIn("repeat_penalty", DEFAULT_CONFIG)
        self.assertIsInstance(DEFAULT_CONFIG["repeat_penalty"], (int, float))
        self.assertEqual(DEFAULT_CONFIG["repeat_penalty"], 1.1)
    
    def test_repeat_penalty_in_default_profile(self):
        """Verify repeat_penalty is in DEFAULT_PROFILE."""
        self.assertIn("repeat_penalty", DEFAULT_PROFILE)
        self.assertIsInstance(DEFAULT_PROFILE["repeat_penalty"], (int, float))
        self.assertEqual(DEFAULT_PROFILE["repeat_penalty"], 1.1)
    
    def test_repeat_penalty_has_sensible_default(self):
        """Verify repeat_penalty default value is sensible for local models."""
        # Default should be > 1.0 to reduce repetition
        self.assertGreater(DEFAULT_CONFIG["repeat_penalty"], 1.0)
        # But not too high to affect quality
        self.assertLessEqual(DEFAULT_CONFIG["repeat_penalty"], 1.5)
    
    def test_repeat_penalty_different_from_openai_defaults(self):
        """Verify repeat_penalty is distinct from OpenAI penalty parameters."""
        # OpenAI penalties default to 0.0
        self.assertEqual(DEFAULT_CONFIG["frequency_penalty"], 0.0)
        self.assertEqual(DEFAULT_CONFIG["presence_penalty"], 0.0)
        # repeat_penalty defaults to 1.1
        self.assertNotEqual(DEFAULT_CONFIG["repeat_penalty"], 0.0)
        self.assertEqual(DEFAULT_CONFIG["repeat_penalty"], 1.1)
    
    def test_config_with_custom_repeat_penalty(self):
        """Test that custom repeat_penalty values can be configured."""
        test_values = [1.0, 1.1, 1.2, 1.3, 1.5, 2.0]
        
        for value in test_values:
            config = {**DEFAULT_CONFIG, "repeat_penalty": value}
            self.assertEqual(config["repeat_penalty"], value)
            self.assertIn("repeat_penalty", config)
    
    def test_profile_with_repeat_penalty(self):
        """Test that profiles can include repeat_penalty."""
        profile = {
            **DEFAULT_PROFILE,
            "repeat_penalty": 1.4
        }
        
        self.assertIn("repeat_penalty", profile)
        self.assertEqual(profile["repeat_penalty"], 1.4)
        # Verify other profile keys are preserved
        self.assertIn("name", profile)
        self.assertIn("model", profile)
        self.assertIn("backend", profile)


if __name__ == "__main__":
    unittest.main()
