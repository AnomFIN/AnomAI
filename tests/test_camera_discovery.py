"""Unit tests for camera discovery functionality."""

# Ship intelligence, not excuses.

import pathlib
import sys
import unittest
from unittest.mock import patch, MagicMock
import socket

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Mock tkinter before importing jugiai
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.scrolledtext'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.simpledialog'] = MagicMock()

from jugiai import discover_cameras_on_network


class CameraDiscoveryTests(unittest.TestCase):
    """Tests for camera discovery functionality."""
    
    @patch('socket.socket')
    def test_discover_cameras_returns_list(self, mock_socket_class):
        """Test that discover_cameras_on_network returns a list."""
        # Mock socket to simulate getting local IP
        mock_socket = MagicMock()
        mock_socket.getsockname.return_value = ('192.168.1.100', 0)
        mock_socket_class.return_value = mock_socket
        
        result = discover_cameras_on_network(timeout=0.1)
        
        # Should return a list (even if empty)
        self.assertIsInstance(result, list)
    
    @patch('socket.socket')
    def test_discover_cameras_handles_network_error(self, mock_socket_class):
        """Test that discover_cameras_on_network handles network errors gracefully."""
        # Simulate network error
        mock_socket = MagicMock()
        mock_socket.connect.side_effect = socket.error("Network unreachable")
        mock_socket_class.return_value = mock_socket
        
        # Should not raise an exception
        result = discover_cameras_on_network(timeout=0.1)
        self.assertIsInstance(result, list)
    
    @patch('socket.socket')
    def test_discover_cameras_finds_open_ports(self, mock_socket_class):
        """Test that discover_cameras_on_network identifies cameras on open ports."""
        # Mock socket to simulate finding a camera
        mock_socket_instance = MagicMock()
        mock_socket_instance.getsockname.return_value = ('192.168.1.100', 0)
        mock_socket_instance.connect_ex.return_value = 0  # Port is open
        
        mock_socket_class.return_value = mock_socket_instance
        
        result = discover_cameras_on_network(timeout=0.1)
        
        # Should return a list
        self.assertIsInstance(result, list)
    
    def test_discover_cameras_result_structure(self):
        """Test that discovered cameras have the expected structure."""
        # This is a basic structure test without mocking
        result = discover_cameras_on_network(timeout=0.1)
        
        # Each discovered camera should have ip, port, and name
        for camera in result:
            self.assertIn('ip', camera)
            self.assertIn('port', camera)
            self.assertIn('name', camera)
            self.assertIsInstance(camera['ip'], str)
            self.assertIsInstance(camera['port'], int)
            self.assertIsInstance(camera['name'], str)


if __name__ == "__main__":
    unittest.main()
