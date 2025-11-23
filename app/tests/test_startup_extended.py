"""
Extended tests for startup.py - Startup management functions
"""
import pytest
from unittest.mock import patch, MagicMock
import platform

# Import internal functions for testing
import startup
from startup import (
    enable_startup,
    disable_startup,
    startup_status,
)


@pytest.fixture
def mock_windows(monkeypatch):
    """Mock Windows environment"""
    monkeypatch.setattr("startup.IS_WINDOWS", True)
    monkeypatch.setattr("startup.IS_MAC", False)


@pytest.fixture
def mock_mac(monkeypatch):
    """Mock macOS environment"""
    monkeypatch.setattr("startup.IS_WINDOWS", False)
    monkeypatch.setattr("startup.IS_MAC", True)


@patch("startup._schtasks")
def test_register_task_success(mock_schtasks, mock_windows):
    """Test successful task registration"""
    mock_schtasks.return_value = MagicMock(returncode=0)
    
    result = startup._register_task("C:\\app\\MDI AutoLogin.exe")
    assert result is True
    mock_schtasks.assert_called_once()


@patch("startup._schtasks")
def test_register_task_failure(mock_schtasks, mock_windows):
    """Test task registration failure"""
    mock_schtasks.return_value = MagicMock(returncode=1)
    
    result = startup._register_task("C:\\app\\MDI AutoLogin.exe")
    assert result is False


@patch("startup._schtasks")
def test_delete_task_success(mock_schtasks, mock_windows):
    """Test successful task deletion"""
    mock_schtasks.return_value = MagicMock(returncode=0)
    
    result = startup._delete_task()
    assert result is True
    mock_schtasks.assert_called_once()


@patch("startup._schtasks")
def test_delete_task_not_found(mock_schtasks, mock_windows):
    """Test task deletion when task doesn't exist"""
    mock_schtasks.return_value = MagicMock(returncode=1, stderr=MagicMock(strip=MagicMock(return_value="")))
    
    result = startup._delete_task()
    # Returns False when deletion fails (not idempotent)
    assert result is False


@patch("startup._schtasks")
def test_task_exists_true(mock_schtasks, mock_windows):
    """Test _task_exists when task exists"""
    mock_schtasks.return_value = MagicMock(returncode=0)
    
    result = startup._task_exists()
    assert result is True


@patch("startup._schtasks")
def test_task_exists_false(mock_schtasks, mock_windows):
    """Test _task_exists when task doesn't exist"""
    mock_schtasks.return_value = MagicMock(returncode=1)
    
    result = startup._task_exists()
    assert result is False


@patch("startup.winreg")
def test_set_run_key_success(mock_winreg, mock_windows):
    """Test setting Run key"""
    mock_key = MagicMock()
    mock_winreg.OpenKey.return_value.__enter__ = MagicMock(return_value=mock_key)
    mock_winreg.OpenKey.return_value.__exit__ = MagicMock(return_value=False)
    
    startup._set_run_key("C:\\app\\MDI AutoLogin.exe")
    
    mock_winreg.OpenKey.assert_called_once()
    mock_winreg.SetValueEx.assert_called_once()


@patch("startup.winreg")
def test_delete_run_key_success(mock_winreg, mock_windows):
    """Test deleting Run key"""
    mock_key = MagicMock()
    mock_winreg.OpenKey.return_value.__enter__ = MagicMock(return_value=mock_key)
    mock_winreg.OpenKey.return_value.__exit__ = MagicMock(return_value=False)
    
    result = startup._delete_run_key()
    assert result is True
    mock_winreg.DeleteValue.assert_called_once()


@patch("startup.winreg")
def test_delete_run_key_not_found(mock_winreg, mock_windows):
    """Test deleting Run key when it doesn't exist"""
    mock_winreg.OpenKey.side_effect = OSError()  # OSError, not FileNotFoundError
    
    result = startup._delete_run_key()
    # Returns False when deletion fails (not idempotent)
    assert result is False


@patch("startup.winreg")
def test_run_key_exists_true(mock_winreg, mock_windows):
    """Test _run_key_exists when key exists"""
    mock_key = MagicMock()
    mock_winreg.OpenKey.return_value.__enter__ = MagicMock(return_value=mock_key)
    mock_winreg.OpenKey.return_value.__exit__ = MagicMock(return_value=False)
    mock_winreg.QueryValueEx.return_value = ("C:\\app\\MDI AutoLogin.exe",)
    
    result = startup._run_key_exists()
    assert result is True


@patch("startup.winreg")
def test_run_key_exists_false(mock_winreg, mock_windows):
    """Test _run_key_exists when key doesn't exist"""
    mock_winreg.OpenKey.side_effect = FileNotFoundError()
    
    result = startup._run_key_exists()
    assert result is False


@patch("startup._register_task")
@patch("startup._task_exists")
@patch("startup.current_executable")
def test_enable_startup_with_task(mock_exe, mock_exists, mock_register, mock_windows):
    """Test enable_startup when task registration succeeds"""
    mock_exe.return_value = "C:\\app\\MDI AutoLogin.exe"
    mock_exists.return_value = False
    mock_register.return_value = True
    
    result = enable_startup("C:\\app\\MDI AutoLogin.exe", prefer_task=True)
    assert result is True
    mock_register.assert_called_once()


@patch("startup._set_run_key")
@patch("startup._register_task")
@patch("startup._task_exists")
@patch("startup.current_executable")
def test_enable_startup_fallback_to_run_key(mock_exe, mock_exists, mock_register, mock_set_key, mock_windows):
    """Test enable_startup falls back to Run key when task fails"""
    mock_exe.return_value = "C:\\app\\MDI AutoLogin.exe"
    mock_exists.return_value = False
    mock_register.return_value = False  # Task registration fails
    mock_set_key.return_value = None
    
    result = enable_startup("C:\\app\\MDI AutoLogin.exe", prefer_task=True)
    # Should still return True (fallback to Run key)
    assert result is True
    mock_register.assert_called_once()
    mock_set_key.assert_called_once()


@patch("startup._delete_task")
@patch("startup._delete_run_key")
@patch("startup._task_exists")
@patch("startup._run_key_exists")
def test_disable_startup_success(mock_run_key_exists, mock_task_exists, mock_delete_key, mock_delete_task, mock_windows):
    """Test disable_startup"""
    mock_task_exists.return_value = True
    mock_run_key_exists.return_value = True
    mock_delete_task.return_value = True
    mock_delete_key.return_value = True
    
    result = disable_startup()
    assert result is True
    mock_delete_task.assert_called_once()
    mock_delete_key.assert_called_once()


@patch("startup._task_exists")
@patch("startup._run_key_exists")
def test_startup_status_task_exists(mock_run_key, mock_task, mock_windows):
    """Test startup_status when task exists"""
    mock_task.return_value = True
    mock_run_key.return_value = False
    
    result = startup_status()
    assert result is True


@patch("startup._task_exists")
@patch("startup._run_key_exists")
def test_startup_status_run_key_exists(mock_run_key, mock_task, mock_windows):
    """Test startup_status when Run key exists"""
    mock_task.return_value = False
    mock_run_key.return_value = True
    
    result = startup_status()
    assert result is True


@patch("startup._task_exists")
@patch("startup._run_key_exists")
def test_startup_status_none(mock_run_key, mock_task, mock_windows):
    """Test startup_status when neither exists"""
    mock_task.return_value = False
    mock_run_key.return_value = False
    
    result = startup_status()
    assert result is False

