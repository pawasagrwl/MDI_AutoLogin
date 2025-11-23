"""
Tests for startup.py - Windows/macOS startup registration
"""
import pytest
from unittest.mock import patch, MagicMock
import platform

from startup import (
    is_admin,
    current_executable,
    startup_status,
)


@patch("platform.system")
def test_is_admin_windows(mock_system):
    """Test admin check on Windows"""
    mock_system.return_value = "Windows"
    with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=1):
        assert is_admin() is True
    with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=0):
        assert is_admin() is False


@patch("platform.system")
def test_is_admin_mac(mock_system):
    """Test admin check on macOS (always True)"""
    mock_system.return_value = "Darwin"
    assert is_admin() is True


@patch("sys.executable", "C:\\Python\\python.exe")
@patch("sys.frozen", False)
@patch("os.path.abspath")
def test_current_executable_not_frozen(mock_abspath):
    """Test current_executable when not frozen"""
    mock_abspath.return_value = "C:\\app\\app.py"
    exe = current_executable()
    assert exe == "C:\\app\\app.py"


@patch("sys.executable", "C:\\app\\MDI AutoLogin.exe")
@patch("sys.frozen", True)
def test_current_executable_frozen():
    """Test current_executable when frozen (PyInstaller)"""
    exe = current_executable()
    assert exe == "C:\\app\\MDI AutoLogin.exe"

