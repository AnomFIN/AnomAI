"""
Tests for thread count validation in local AI model.
"""
import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add parent directory to path to import jugiai
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _validate_thread_count_impl(requested_threads: int, log_callback=None):
    """
    Shared implementation of thread validation for testing.
    This mirrors the logic in JugiAIApp._validate_thread_count()
    """
    if requested_threads <= 0:
        return None
    
    cpu_count = os.cpu_count() or 4
    max_threads = cpu_count * 4
    
    if requested_threads > max_threads:
        if log_callback:
            log_callback(
                f"Thread count {requested_threads} exceeds recommended maximum {max_threads} "
                f"(4x CPU count {cpu_count}). Capping to {max_threads}."
            )
        return max_threads
    
    return requested_threads


class TestThreadValidation(unittest.TestCase):
    """Test thread count validation logic."""
    
    @patch('os.cpu_count')
    def test_validate_thread_count_auto(self, mock_cpu_count):
        """Test that 0 or negative values return None for auto-detection."""
        mock_cpu_count.return_value = 4
        
        # Test auto (0)
        self.assertIsNone(_validate_thread_count_impl(0))
        
        # Test negative values (should return None for auto)
        self.assertIsNone(_validate_thread_count_impl(-1))
        self.assertIsNone(_validate_thread_count_impl(-100))
    
    @patch('os.cpu_count')
    def test_validate_thread_count_within_limit(self, mock_cpu_count):
        """Test that thread counts within limits are returned as-is."""
        mock_cpu_count.return_value = 4
        
        # Test values within limit (4 CPUs * 4 = max 16)
        self.assertEqual(_validate_thread_count_impl(1), 1)
        self.assertEqual(_validate_thread_count_impl(4), 4)
        self.assertEqual(_validate_thread_count_impl(8), 8)
        self.assertEqual(_validate_thread_count_impl(16), 16)
    
    @patch('os.cpu_count')
    def test_validate_thread_count_exceeds_limit(self, mock_cpu_count):
        """Test that thread counts exceeding limits are capped."""
        mock_cpu_count.return_value = 4
        
        log_messages = []
        def log_callback(msg):
            log_messages.append(msg)
        
        # Test value exceeding limit (4 CPUs * 4 = max 16)
        # User sets 512, should be capped to 16
        result = _validate_thread_count_impl(512, log_callback)
        self.assertEqual(result, 16)
        self.assertTrue(len(log_messages) > 0, "Should have logged a warning")
        
        # Test other excessive values
        log_messages.clear()
        result = _validate_thread_count_impl(1024, log_callback)
        self.assertEqual(result, 16)
        
        result = _validate_thread_count_impl(100, log_callback)
        self.assertEqual(result, 16)
    
    @patch('os.cpu_count')
    def test_validate_thread_count_different_cpu_counts(self, mock_cpu_count):
        """Test thread validation with different CPU counts."""
        
        # Test with 8 CPUs (max = 32)
        mock_cpu_count.return_value = 8
        self.assertEqual(_validate_thread_count_impl(32), 32)
        self.assertEqual(_validate_thread_count_impl(512), 32)
        
        # Test with 16 CPUs (max = 64)
        mock_cpu_count.return_value = 16
        self.assertEqual(_validate_thread_count_impl(64), 64)
        self.assertEqual(_validate_thread_count_impl(512), 64)
        
        # Test with 2 CPUs (max = 8)
        mock_cpu_count.return_value = 2
        self.assertEqual(_validate_thread_count_impl(8), 8)
        self.assertEqual(_validate_thread_count_impl(512), 8)
    
    @patch('os.cpu_count')
    def test_validate_thread_count_invalid_input(self, mock_cpu_count):
        """Test handling of invalid thread count values."""
        mock_cpu_count.return_value = 4
        
        # Test that negative values are treated as auto-detect
        self.assertIsNone(_validate_thread_count_impl(-1))
        self.assertIsNone(_validate_thread_count_impl(-999))
        
        # Test zero is auto-detect
        self.assertIsNone(_validate_thread_count_impl(0))


if __name__ == '__main__':
    unittest.main()
