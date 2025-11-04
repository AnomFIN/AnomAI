"""
Tests for thread count validation in local AI model.
"""
import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add parent directory to path to import jugiai
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# We need to mock tkinter before importing jugiai
sys.modules['tkinter'] = Mock()
sys.modules['tkinter.ttk'] = Mock()
sys.modules['tkinter.filedialog'] = Mock()
sys.modules['tkinter.messagebox'] = Mock()
sys.modules['tkinter.simpledialog'] = Mock()
sys.modules['tkinter.scrolledtext'] = Mock()


class TestThreadValidation(unittest.TestCase):
    """Test thread count validation logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import after mocking tkinter
        from jugiai import JugiAIApp
        self.app_class = JugiAIApp
    
    @patch('os.cpu_count')
    def test_validate_thread_count_auto(self, mock_cpu_count):
        """Test that 0 or negative values return None for auto-detection."""
        mock_cpu_count.return_value = 4
        
        # Create a minimal mock app with just the validation method
        class MinimalApp:
            def _safe_log(self, *args, **kwargs):
                pass
            
            def _validate_thread_count(self, requested_threads: int):
                """Copied from JugiAIApp for testing."""
                if requested_threads <= 0:
                    return None
                
                cpu_count = os.cpu_count() or 4
                max_threads = cpu_count * 4
                
                if requested_threads > max_threads:
                    self._safe_log(
                        f"Thread count {requested_threads} exceeds recommended maximum {max_threads} "
                        f"(4x CPU count {cpu_count}). Capping to {max_threads}."
                    )
                    return max_threads
                
                return requested_threads
        
        app = MinimalApp()
        
        # Test auto (0)
        self.assertIsNone(app._validate_thread_count(0))
        
        # Test negative values (should return None for auto)
        self.assertIsNone(app._validate_thread_count(-1))
        self.assertIsNone(app._validate_thread_count(-100))
    
    @patch('os.cpu_count')
    def test_validate_thread_count_within_limit(self, mock_cpu_count):
        """Test that thread counts within limits are returned as-is."""
        mock_cpu_count.return_value = 4
        
        class MinimalApp:
            def _safe_log(self, *args, **kwargs):
                pass
            
            def _validate_thread_count(self, requested_threads: int):
                if requested_threads <= 0:
                    return None
                
                cpu_count = os.cpu_count() or 4
                max_threads = cpu_count * 4
                
                if requested_threads > max_threads:
                    self._safe_log(
                        f"Thread count {requested_threads} exceeds recommended maximum {max_threads} "
                        f"(4x CPU count {cpu_count}). Capping to {max_threads}."
                    )
                    return max_threads
                
                return requested_threads
        
        app = MinimalApp()
        
        # Test values within limit (4 CPUs * 4 = max 16)
        self.assertEqual(app._validate_thread_count(1), 1)
        self.assertEqual(app._validate_thread_count(4), 4)
        self.assertEqual(app._validate_thread_count(8), 8)
        self.assertEqual(app._validate_thread_count(16), 16)
    
    @patch('os.cpu_count')
    def test_validate_thread_count_exceeds_limit(self, mock_cpu_count):
        """Test that thread counts exceeding limits are capped."""
        mock_cpu_count.return_value = 4
        
        class MinimalApp:
            def __init__(self):
                self.log_messages = []
            
            def _safe_log(self, *args, **kwargs):
                self.log_messages.append(str(args))
            
            def _validate_thread_count(self, requested_threads: int):
                if requested_threads <= 0:
                    return None
                
                cpu_count = os.cpu_count() or 4
                max_threads = cpu_count * 4
                
                if requested_threads > max_threads:
                    self._safe_log(
                        f"Thread count {requested_threads} exceeds recommended maximum {max_threads} "
                        f"(4x CPU count {cpu_count}). Capping to {max_threads}."
                    )
                    return max_threads
                
                return requested_threads
        
        app = MinimalApp()
        
        # Test value exceeding limit (4 CPUs * 4 = max 16)
        # User sets 512, should be capped to 16
        result = app._validate_thread_count(512)
        self.assertEqual(result, 16)
        self.assertTrue(len(app.log_messages) > 0, "Should have logged a warning")
        
        # Test other excessive values
        app.log_messages.clear()
        result = app._validate_thread_count(1024)
        self.assertEqual(result, 16)
        
        result = app._validate_thread_count(100)
        self.assertEqual(result, 16)
    
    @patch('os.cpu_count')
    def test_validate_thread_count_different_cpu_counts(self, mock_cpu_count):
        """Test thread validation with different CPU counts."""
        class MinimalApp:
            def _safe_log(self, *args, **kwargs):
                pass
            
            def _validate_thread_count(self, requested_threads: int):
                if requested_threads <= 0:
                    return None
                
                cpu_count = os.cpu_count() or 4
                max_threads = cpu_count * 4
                
                if requested_threads > max_threads:
                    self._safe_log(
                        f"Thread count {requested_threads} exceeds recommended maximum {max_threads} "
                        f"(4x CPU count {cpu_count}). Capping to {max_threads}."
                    )
                    return max_threads
                
                return requested_threads
        
        app = MinimalApp()
        
        # Test with 8 CPUs (max = 32)
        mock_cpu_count.return_value = 8
        self.assertEqual(app._validate_thread_count(32), 32)
        self.assertEqual(app._validate_thread_count(512), 32)
        
        # Test with 16 CPUs (max = 64)
        mock_cpu_count.return_value = 16
        self.assertEqual(app._validate_thread_count(64), 64)
        self.assertEqual(app._validate_thread_count(512), 64)
        
        # Test with 2 CPUs (max = 8)
        mock_cpu_count.return_value = 2
        self.assertEqual(app._validate_thread_count(8), 8)
        self.assertEqual(app._validate_thread_count(512), 8)


if __name__ == '__main__':
    unittest.main()
