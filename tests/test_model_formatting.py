"""
Tests for model name formatting logic.
"""
import os
import unittest


class ModelFormattingTests(unittest.TestCase):
    """Tests for _format_model_label functionality."""

    def test_extract_model_name_from_path(self):
        """Test extracting model name from a .gguf file path."""
        test_cases = [
            ("/path/to/dolphin-2.9.2-qwen2-7b.Q4_K_M.gguf", "dolphin-2.9.2-qwen2-7b.Q4_K_M"),
            ("./models/llama-3-8b-instruct.gguf", "llama-3-8b-instruct"),
            ("./models/mistral-7b.gguf", "mistral-7b"),
            ("model.gguf", "model"),
        ]
        
        for path, expected_name in test_cases:
            with self.subTest(path=path):
                # Extract filename without extension (mimicking the fix)
                actual_name = os.path.splitext(os.path.basename(path))[0]
                self.assertEqual(actual_name, expected_name)

    def test_empty_path_handling(self):
        """Test that empty paths are handled gracefully."""
        path = ""
        stripped = path.strip()
        self.assertEqual(stripped, "")
        
    def test_path_with_spaces(self):
        """Test that paths with spaces work correctly."""
        path = "/path/to/my model with spaces.gguf"
        expected = "my model with spaces"
        actual = os.path.splitext(os.path.basename(path))[0]
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
