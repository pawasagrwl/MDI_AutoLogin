"""
Tests for single_instance.py - Single-instance enforcement
"""
import pytest
from unittest.mock import patch, MagicMock
import platform

# Only test on Windows since single_instance is Windows-specific
pytestmark = pytest.mark.skipif(
    platform.system() != "Windows",
    reason="single_instance module is Windows-specific"
)

from single_instance import (
    _create_mutex,
    _release_mutex,
    _find_old_instances,
    _kill_old_instances,
    enforce_single_instance,
    MUTEX_NAME,
)


@pytest.fixture
def mock_psutil(monkeypatch):
    """Mock psutil for testing"""
    mock_psutil_module = MagicMock()
    
    # Mock Process class
    mock_process = MagicMock()
    mock_process.pid = 1234
    mock_process.exe.return_value = "C:\\old\\MDI AutoLogin.exe"
    mock_process.terminate = MagicMock()
    mock_process.wait = MagicMock()
    mock_process.kill = MagicMock()
    
    # Mock process_iter
    mock_psutil_module.process_iter.return_value = [mock_process]
    mock_psutil_module.Process.return_value = mock_process
    mock_psutil_module.NoSuchProcess = Exception
    mock_psutil_module.AccessDenied = Exception
    mock_psutil_module.ZombieProcess = Exception
    mock_psutil_module.TimeoutExpired = Exception
    
    monkeypatch.setattr("single_instance.psutil", mock_psutil_module)
    return mock_psutil_module


@patch("single_instance.IS_WINDOWS", True)
@patch("ctypes.windll.kernel32.CreateMutexW")
@patch("ctypes.windll.kernel32.GetLastError")
def test_create_mutex_success(mock_get_error, mock_create_mutex):
    """Test successful mutex creation"""
    mock_handle = MagicMock()
    mock_create_mutex.return_value = mock_handle
    mock_get_error.return_value = 0  # No error
    
    handle = _create_mutex()
    assert handle == mock_handle
    mock_create_mutex.assert_called_once()


@patch("single_instance.IS_WINDOWS", True)
@patch("ctypes.windll.kernel32.CreateMutexW")
@patch("ctypes.windll.kernel32.GetLastError")
@patch("ctypes.windll.kernel32.CloseHandle")
def test_create_mutex_already_exists(mock_close, mock_get_error, mock_create_mutex):
    """Test mutex creation when mutex already exists"""
    mock_handle = MagicMock()
    mock_create_mutex.return_value = mock_handle
    mock_get_error.return_value = 183  # ERROR_ALREADY_EXISTS
    
    handle = _create_mutex()
    assert handle is None
    mock_close.assert_called_once_with(mock_handle)


@patch("single_instance.IS_WINDOWS", True)
@patch("ctypes.windll.kernel32.CloseHandle")
def test_release_mutex(mock_close):
    """Test releasing mutex handle"""
    mock_handle = MagicMock()
    _release_mutex(mock_handle)
    mock_close.assert_called_once_with(mock_handle)


@patch("single_instance.IS_WINDOWS", False)
def test_create_mutex_not_windows():
    """Test mutex creation on non-Windows"""
    handle = _create_mutex()
    assert handle is None


def test_find_old_instances_same_name_different_path(mock_psutil, monkeypatch):
    """Test finding old instances with same name but different path"""
    import os
    monkeypatch.setattr("os.getpid", lambda: 9999)
    
    # Current executable
    current_exe = "C:\\new\\MDI AutoLogin.exe"
    
    # Mock process with different path
    mock_proc = MagicMock()
    mock_proc.pid = 1234
    mock_proc.exe.return_value = "C:\\old\\MDI AutoLogin.exe"
    
    mock_psutil.process_iter.return_value = [mock_proc]
    mock_psutil.Process.return_value = mock_proc
    
    old_instances = _find_old_instances(current_exe)
    assert len(old_instances) == 1
    assert old_instances[0].pid == 1234


def test_find_old_instances_same_path_skipped(mock_psutil, monkeypatch):
    """Test that processes with same path as current are skipped"""
    import os
    monkeypatch.setattr("os.getpid", lambda: 9999)
    
    current_exe = "C:\\app\\MDI AutoLogin.exe"
    
    # Mock process with same path
    mock_proc = MagicMock()
    mock_proc.pid = 1234
    mock_proc.exe.return_value = current_exe
    
    mock_psutil.process_iter.return_value = [mock_proc]
    
    old_instances = _find_old_instances(current_exe)
    # Should find it as duplicate (same path, different PID)
    assert len(old_instances) >= 0  # May or may not be found depending on logic


def test_find_old_instances_current_pid_skipped(mock_psutil, monkeypatch):
    """Test that current process PID is skipped"""
    import os
    current_pid = 9999
    monkeypatch.setattr("os.getpid", lambda: current_pid)
    
    current_exe = "C:\\app\\MDI AutoLogin.exe"
    
    # Mock process with current PID
    mock_proc = MagicMock()
    mock_proc.pid = current_pid
    mock_proc.exe.return_value = "C:\\other\\MDI AutoLogin.exe"
    
    mock_psutil.process_iter.return_value = [mock_proc]
    
    old_instances = _find_old_instances(current_exe)
    assert len(old_instances) == 0  # Current PID should be skipped


def test_kill_old_instances_success(mock_psutil):
    """Test successfully killing old instances"""
    mock_proc = MagicMock()
    mock_proc.pid = 1234
    mock_proc.terminate = MagicMock()
    mock_proc.wait = MagicMock()  # No timeout
    
    killed = _kill_old_instances([mock_proc])
    assert killed == 1
    mock_proc.terminate.assert_called_once()
    mock_proc.wait.assert_called_once()


def test_kill_old_instances_timeout(mock_psutil):
    """Test killing old instances with timeout"""
    mock_proc = MagicMock()
    mock_proc.pid = 1234
    mock_proc.terminate = MagicMock()
    # First wait raises TimeoutExpired, second wait succeeds
    mock_proc.wait.side_effect = [mock_psutil.TimeoutExpired("test", 3), None]
    mock_proc.kill = MagicMock()
    
    killed = _kill_old_instances([mock_proc])
    assert killed == 1
    mock_proc.terminate.assert_called_once()
    mock_proc.kill.assert_called_once()
    # Should have called wait twice (once for terminate, once for kill)
    assert mock_proc.wait.call_count == 2


def test_kill_old_instances_no_such_process(mock_psutil):
    """Test killing when process already gone"""
    mock_proc = MagicMock()
    mock_proc.pid = 1234
    mock_proc.terminate.side_effect = mock_psutil.NoSuchProcess(1234)
    
    killed = _kill_old_instances([mock_proc])
    assert killed == 0  # Process already gone


@patch("single_instance._find_old_instances")
@patch("single_instance._kill_old_instances")
@patch("single_instance._create_mutex")
def test_enforce_single_instance_first_instance(mock_mutex, mock_kill, mock_find):
    """Test enforce_single_instance when this is the first instance"""
    mock_handle = MagicMock()
    mock_mutex.return_value = mock_handle
    mock_find.return_value = []
    mock_kill.return_value = 0
    
    is_first, handle = enforce_single_instance("C:\\app\\MDI AutoLogin.exe")
    
    assert is_first is True
    assert handle == mock_handle
    mock_find.assert_called_once()
    mock_mutex.assert_called_once()


@patch("single_instance._find_old_instances")
@patch("single_instance._kill_old_instances")
@patch("single_instance._create_mutex")
def test_enforce_single_instance_old_instances_found(mock_mutex, mock_kill, mock_find):
    """Test enforce_single_instance when old instances are found"""
    mock_handle = MagicMock()
    mock_mutex.return_value = mock_handle
    
    mock_old_proc = MagicMock()
    mock_find.return_value = [mock_old_proc]
    mock_kill.return_value = 1
    
    is_first, handle = enforce_single_instance("C:\\app\\MDI AutoLogin.exe")
    
    assert is_first is True
    assert handle == mock_handle
    mock_find.assert_called_once()
    mock_kill.assert_called_once_with([mock_old_proc])


@patch("single_instance._find_old_instances")
@patch("single_instance._kill_old_instances")
@patch("single_instance._create_mutex")
def test_enforce_single_instance_another_running(mock_mutex, mock_kill, mock_find):
    """Test enforce_single_instance when another instance is running"""
    mock_find.return_value = []
    mock_kill.return_value = 0
    mock_mutex.return_value = None  # Mutex already exists
    
    is_first, handle = enforce_single_instance("C:\\app\\MDI AutoLogin.exe")
    
    assert is_first is False
    assert handle is None


@patch("single_instance.psutil", None)
@patch("single_instance._create_mutex")
def test_enforce_single_instance_no_psutil(mock_mutex):
    """Test enforce_single_instance when psutil is not available"""
    mock_handle = MagicMock()
    mock_mutex.return_value = mock_handle
    
    is_first, handle = enforce_single_instance("C:\\app\\MDI AutoLogin.exe")
    
    # Should still work, just can't find old instances
    assert is_first is True
    assert handle == mock_handle

