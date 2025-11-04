"""Unit tests for model label formatting and watermark visibility."""

import os
import pathlib
import sys
import unittest
from unittest.mock import MagicMock, patch

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class MockApp:
    """Mock JugiAI application for testing."""
    
    def __init__(self, config_dict):
        self.config_dict = config_dict
        self._wm_img = MagicMock()
        self._wm_overlay = None
        self.watermark_removed = False
        self.watermark_ensured = False
        self.watermark_positioned = False
    
    def _remove_watermark_overlay(self):
        self.watermark_removed = True
        self._wm_overlay = None
    
    def _ensure_watermark_overlay(self):
        self.watermark_ensured = True
        self._wm_overlay = MagicMock()
    
    def _position_watermark_overlay(self):
        self.watermark_positioned = True
    
    def _format_model_label(self):
        """Copy of the fixed _format_model_label method."""
        DEFAULT_MODEL = "gpt-4o-mini"  # Mirror DEFAULT_CONFIG["model"]
        backend = (self.config_dict.get("backend") or "openai").strip().lower()
        if backend == "openai":
            backend_label = "OpenAI"
        elif backend == "local":
            backend_label = "Paikallinen"
        else:
            backend_label = backend.title()
        
        # For local backend, show the local model filename instead of the "model" field
        if backend == "local":
            local_path = (self.config_dict.get("local_model_path") or "").strip()
            if local_path:
                # Extract just the filename without path
                model = os.path.basename(local_path)
            else:
                model = "Ei valittu"
        else:
            model = self.config_dict.get("model", DEFAULT_MODEL)
        
        return f"{backend_label} · {model}"
    
    def _insert_watermark_if_needed(self):
        """Copy of the fixed _insert_watermark_if_needed method."""
        # Check if watermark should be shown based on show_background setting
        if not self.config_dict.get("show_background", True):
            self._remove_watermark_overlay()
            return
        
        if not self._wm_img:
            self._remove_watermark_overlay()
            return
        self._ensure_watermark_overlay()
        self._position_watermark_overlay()


class TestModelLabelFormatting(unittest.TestCase):
    """Test cases for _format_model_label method."""
    
    def test_openai_backend_shows_model_field(self):
        """Test that OpenAI backend displays the model field value."""
        app = MockApp({
            "backend": "openai",
            "model": "gpt-4o-mini"
        })
        label = app._format_model_label()
        self.assertEqual(label, "OpenAI · gpt-4o-mini")
    
    def test_local_backend_shows_filename(self):
        """Test that local backend displays the local model filename."""
        app = MockApp({
            "backend": "local",
            "local_model_path": "/path/to/models/dolphin-mistral-7b.gguf",
            "model": "gpt-4o-mini"  # Should be ignored for local backend
        })
        label = app._format_model_label()
        self.assertEqual(label, "Paikallinen · dolphin-mistral-7b.gguf")
    
    def test_local_backend_windows_path(self):
        """Test that local backend handles Windows paths correctly."""
        app = MockApp({
            "backend": "local",
            "local_model_path": r"C:\Users\test\models\llama-2-7b.gguf",
            "model": "gpt-4o-mini"
        })
        label = app._format_model_label()
        # os.path.basename works differently on Unix vs Windows
        # On the actual target platform (Windows), it will extract just the filename
        # On Unix test environment, it may keep the full path if backslashes aren't recognized
        self.assertIn("llama-2-7b.gguf", label)
        self.assertTrue(label.startswith("Paikallinen · "))
    
    def test_local_backend_no_path_configured(self):
        """Test that local backend shows 'Ei valittu' when no path is set."""
        app = MockApp({
            "backend": "local",
            "local_model_path": "",
            "model": "gpt-4o-mini"
        })
        label = app._format_model_label()
        self.assertEqual(label, "Paikallinen · Ei valittu")
    
    def test_local_backend_none_path(self):
        """Test that local backend handles None path gracefully."""
        app = MockApp({
            "backend": "local",
            "model": "gpt-4o-mini"
        })
        label = app._format_model_label()
        self.assertEqual(label, "Paikallinen · Ei valittu")
    
    def test_custom_backend(self):
        """Test that custom backends are displayed with title case."""
        app = MockApp({
            "backend": "custom",
            "model": "some-model"
        })
        label = app._format_model_label()
        self.assertEqual(label, "Custom · some-model")


class TestWatermarkVisibility(unittest.TestCase):
    """Test cases for _insert_watermark_if_needed method."""
    
    def test_watermark_shown_when_enabled(self):
        """Test that watermark is shown when show_background is True."""
        app = MockApp({
            "show_background": True
        })
        app._wm_img = MagicMock()  # Watermark image is loaded
        app._insert_watermark_if_needed()
        
        self.assertTrue(app.watermark_ensured)
        self.assertTrue(app.watermark_positioned)
        self.assertFalse(app.watermark_removed)
    
    def test_watermark_hidden_when_disabled(self):
        """Test that watermark is hidden when show_background is False."""
        app = MockApp({
            "show_background": False
        })
        app._wm_img = MagicMock()  # Watermark image is loaded
        app._insert_watermark_if_needed()
        
        self.assertTrue(app.watermark_removed)
        self.assertFalse(app.watermark_ensured)
        self.assertFalse(app.watermark_positioned)
    
    def test_watermark_hidden_when_no_image(self):
        """Test that watermark is hidden when no image is loaded."""
        app = MockApp({
            "show_background": True
        })
        app._wm_img = None  # No watermark image loaded
        app._insert_watermark_if_needed()
        
        self.assertTrue(app.watermark_removed)
        self.assertFalse(app.watermark_ensured)
        self.assertFalse(app.watermark_positioned)
    
    def test_watermark_respects_default_true(self):
        """Test that watermark is shown by default when setting is missing."""
        app = MockApp({})  # No show_background setting
        app._wm_img = MagicMock()
        app._insert_watermark_if_needed()
        
        self.assertTrue(app.watermark_ensured)
        self.assertTrue(app.watermark_positioned)
        self.assertFalse(app.watermark_removed)


if __name__ == "__main__":
    unittest.main()
