"""
Tests for startup.py - Windows/macOS startup registration
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

from startup import (
    is_admin,
    current_executable,
    startup_status,
)


@patch("startup.IS_WINDOWS", True)
@patch("startup.IS_MAC", False)
def test_is_admin_windows():
    """Test admin check on Windows"""
    with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=1):
        assert is_admin() is True
    with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=0):
        assert is_admin() is False


@patch("startup.IS_WINDOWS", False)
@patch("startup.IS_MAC", True)
def test_is_admin_mac():
    """Test admin check on macOS (always True)"""
    # On macOS, is_admin always returns True
    assert is_admin() is True


def test_current_executable_not_frozen(monkeypatch):
    """Test current_executable when not frozen"""
    monkeypatch.setattr(sys, "executable", "C:\\Python\\python.exe")
    # Don't set sys.frozen - getattr will return False
    if hasattr(sys, "frozen"):
        monkeypatch.delattr(sys, "frozen", raising=False)
    
    monkeypatch.setattr(sys, "argv", ["app.py"])
    with patch("startup.os.path.abspath", return_value="C:\\app\\app.py"):
        exe = current_executable()
        assert exe == "C:\\app\\app.py"


def test_current_executable_frozen(monkeypatch):
    """Test current_executable when frozen (PyInstaller)"""
    monkeypatch.setattr(sys, "executable", "C:\\app\\MDI AutoLogin.exe")
    # sys.frozen is added dynamically by PyInstaller
    # Patch getattr in startup module to return True for sys.frozen
    import startup
    original_getattr = getattr
    
    def mock_getattr(obj, name, default=None):
        if obj is sys and name == "frozen":
            return True
        return original_getattr(obj, name, default)
    
    with patch("startup.getattr", side_effect=mock_getattr):
        exe = current_executable()
        assert exe == "C:\\app\\MDI AutoLogin.exe"

