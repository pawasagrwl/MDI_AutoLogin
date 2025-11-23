# single_instance.py
"""
Single-instance enforcement for MDI AutoLogin.
Prevents multiple instances from running and handles old version cleanup.
"""
import logging
import os
import platform
import sys
from pathlib import Path
from typing import Optional, Tuple

log = logging.getLogger("mdi.single_instance")

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

try:
    import psutil
except ImportError:
    psutil = None
    log.warning("psutil not available, old instance detection will be limited")


# Mutex name for single-instance enforcement
MUTEX_NAME = "Global\\MDI_AutoLogin_SingleInstance"


def _create_mutex() -> Optional[ctypes.wintypes.HANDLE]:
    """Create a named mutex. Returns handle if successful, None if already exists."""
    if not IS_WINDOWS:
        return None
    
    try:
        # Create mutex with current user permissions
        mutex = ctypes.windll.kernel32.CreateMutexW(
            None,  # Default security attributes
            False,  # Initially not owned
            MUTEX_NAME
        )
        
        if mutex:
            # Check if we got the mutex or if it already existed
            error = ctypes.windll.kernel32.GetLastError()
            if error == 183:  # ERROR_ALREADY_EXISTS
                # Mutex already exists, another instance is running
                ctypes.windll.kernel32.CloseHandle(mutex)
                return None
            return mutex
        return None
    except Exception as e:
        log.error("Failed to create mutex: %s", e)
        return None


def _release_mutex(mutex_handle: ctypes.wintypes.HANDLE):
    """Release the mutex handle."""
    if not IS_WINDOWS or not mutex_handle:
        return
    try:
        ctypes.windll.kernel32.CloseHandle(mutex_handle)
    except Exception as e:
        log.error("Failed to release mutex: %s", e)


def _find_old_instances(current_exe: str) -> list:
    """Find running instances of the app (including old versions).
    
    Returns list of Process objects for other instances.
    """
    if not psutil:
        return []
    
    current_exe_path = Path(current_exe).resolve()
    current_exe_name = current_exe_path.name.lower()
    current_pid = os.getpid()
    
    old_instances = []
    
    try:
        for proc in psutil.process_iter():
            try:
                proc_pid = proc.pid
                if proc_pid == current_pid:
                    continue  # Skip current process
                
                try:
                    exe_path = proc.exe()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    continue
                
                if not exe_path:
                    continue
                
                proc_exe_path = Path(exe_path).resolve()
                proc_exe_name = proc_exe_path.name.lower()
                
                # Check if it's the same executable name (could be old version in different location)
                if proc_exe_name == current_exe_name:
                    # If it's the same path, it's the same version (shouldn't happen due to mutex)
                    # If it's a different path, it's likely an old version
                    if proc_exe_path != current_exe_path:
                        log.info("Found old instance: PID %d, path: %s", proc_pid, exe_path)
                        old_instances.append(proc)
                    # Also catch same path instances (shouldn't happen, but just in case)
                    else:
                        log.warning("Found duplicate instance with same path: PID %d", proc_pid)
                        old_instances.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process disappeared or we can't access it
                continue
            except Exception as e:
                log.debug("Error checking process %d: %s", proc.pid, e)
                continue
    except Exception as e:
        log.error("Error finding old instances: %s", e)
    
    return old_instances


def _kill_old_instances(old_instances: list) -> int:
    """Kill old instances. Returns number of processes killed."""
    killed = 0
    for proc in old_instances:
        try:
            log.info("Terminating old instance: PID %d", proc.pid)
            proc.terminate()
            # Wait up to 3 seconds for graceful termination
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                log.warning("Force killing old instance: PID %d", proc.pid)
                proc.kill()
                proc.wait(timeout=1)
            killed += 1
        except psutil.NoSuchProcess:
            # Already dead
            pass
        except psutil.AccessDenied:
            log.warning("Access denied when trying to kill PID %d", proc.pid)
        except Exception as e:
            log.error("Error killing process %d: %s", proc.pid, e)
    
    return killed


def _bring_existing_to_front():
    """Try to bring the existing instance window to front."""
    if not IS_WINDOWS:
        return
    
    try:
        # Find window by class name or title
        # This is a simple approach - we could enhance it to find the actual tkinter window
        hwnd = ctypes.windll.user32.FindWindowW(None, None)  # This won't work well
        # For now, we'll just show a message - the user can manually bring it to front
        pass
    except Exception as e:
        log.debug("Could not bring window to front: %s", e)


def enforce_single_instance(current_exe: Optional[str] = None) -> Tuple[bool, Optional[object]]:
    """
    Enforce single instance of the application.
    
    Args:
        current_exe: Path to current executable (optional, will be auto-detected)
    
    Returns:
        Tuple of (is_first_instance: bool, mutex_handle: Optional[object])
        - If is_first_instance is False, another instance is already running
        - mutex_handle should be stored and released on exit
    """
    if current_exe is None:
        if getattr(sys, 'frozen', False):
            # PyInstaller bundle
            current_exe = sys.executable
        else:
            # Running from source
            current_exe = __file__  # This will be the .py file, but that's okay for detection
    
    # First, check for and kill old instances
    if psutil:
        old_instances = _find_old_instances(current_exe)
        if old_instances:
            log.info("Found %d old instance(s), terminating...", len(old_instances))
            killed = _kill_old_instances(old_instances)
            if killed > 0:
                log.info("Terminated %d old instance(s)", killed)
                # Give processes time to fully terminate
                import time
                time.sleep(0.5)
    
    # Now check for current instance using mutex
    mutex_handle = _create_mutex()
    
    if mutex_handle is None:
        # Another instance is already running
        log.warning("Another instance is already running")
        _bring_existing_to_front()
        return False, None
    
    log.debug("Single-instance mutex acquired")
    return True, mutex_handle

