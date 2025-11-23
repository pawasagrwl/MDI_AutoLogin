# app/startup.py
import logging
import os
import platform
import plistlib
import subprocess
import sys
from pathlib import Path
from typing import Optional

LOG = logging.getLogger("mdi.startup")

IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"

TASK_NAME = "MDI AutoLogin"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
LAUNCH_AGENT_ID = "com.mdi.autologin"
LAUNCH_AGENT_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCH_AGENT_ID}.plist"

if IS_WINDOWS:
    import winreg  # type: ignore[attr-defined]


# near the top
import ctypes


def is_admin() -> bool:
    if not IS_WINDOWS:
        return True
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin(resume_target: Optional[str] = None, flag: str = "--elevate-autostart"):
    if not IS_WINDOWS:
        return False
    if getattr(sys, "frozen", False):
        target = current_executable()
        params = flag
    else:
        target = sys.executable
        params = f'"{current_executable()}" {flag}'
    if resume_target:
        params = f'{params} "{resume_target}"'
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", target, params, None, 1)
    return rc > 32

def current_executable() -> str:
    """Return the absolute path that should be registered for startup."""
    return sys.executable if getattr(sys, "frozen", False) else os.path.abspath(sys.argv[0])


def _schtasks(*args: str) -> subprocess.CompletedProcess[str]:
    if not IS_WINDOWS:
        raise RuntimeError("schtasks is only available on Windows")
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.run(
        ["schtasks", *args],
        capture_output=True,
        text=True,
        check=False,
        creationflags=creationflags,
    )


def _register_task(exe_path: str) -> bool:
    """
    Creates a scheduled task optimized for earliest possible startup.
    
    Configuration:
    - ONLOGON: Triggers immediately when user logs in (before most startup apps)
    - HIGHEST privileges: Runs with highest available privileges for early execution
    - DELAY 0000:00: No delay, starts immediately
    - Interactive: Can show UI (tray icon)
    - No password: Uses current user credentials
    
    This is the earliest possible startup method for user-facing apps.
    Task Scheduler runs ONLOGON tasks before Run key entries and Startup folder.
    """
    try:
        result = _schtasks(
            "/Create",
            "/F",  # Force (overwrite if exists)
            "/TN", TASK_NAME,
            "/TR", f'"{exe_path}"',  # Task to run
            "/SC", "ONLOGON",  # Trigger: when user logs in (earliest user-facing trigger)
            "/RL", "HIGHEST",  # Run level: highest privileges (runs before normal tasks)
            "/DELAY", "0000:00",  # No delay - start immediately
            "/IT",  # Interactive task (allows UI/tray icon)
            "/NP",  # No password (uses current user's credentials)
        )
    except Exception as exc:
        LOG.exception("Failed to create scheduled task: %s", exc)
        return False

    if result.returncode != 0:
        LOG.warning("Scheduled task could not be created (code %s). Run the app as Administrator to allow early-start, falling back to Run key.", result.returncode)
        return False

    LOG.info("Scheduled task registered for %s", exe_path)
    return True


def _delete_task() -> bool:
    try:
        result = _schtasks("/Delete", "/F", "/TN", TASK_NAME)
        if result.returncode == 0:
            return True
        LOG.warning("Failed to delete scheduled task (code %s): %s", result.returncode, result.stderr.strip())
        return False
    except Exception as exc:
        LOG.exception("Failed to delete scheduled task: %s", exc)
        return False


def _task_exists() -> bool:
    try:
        return _schtasks("/Query", "/TN", TASK_NAME).returncode == 0
    except Exception:
        return False


def _set_run_key(exe_path: str):
    if not IS_WINDOWS:
        return
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, TASK_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
        LOG.info("Run-key fallback registered.")
    except OSError as exc:
        LOG.warning("Unable to set Run key: %s", exc)


def _delete_run_key() -> bool:
    if not IS_WINDOWS:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, TASK_NAME)
        return True
    except OSError:
        return False


def _run_key_exists() -> bool:
    if not IS_WINDOWS:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, TASK_NAME)
            return True
    except OSError:
        return False


def _write_launch_agent(exe_path: str):
    LAUNCH_AGENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plist = {
        "Label": LAUNCH_AGENT_ID,
        "ProgramArguments": [exe_path],
        "RunAtLoad": True,
        "KeepAlive": False,
        "ProcessType": "Background",
    }
    with LAUNCH_AGENT_PATH.open("wb") as fh:
        plistlib.dump(plist, fh)
    LOG.info("LaunchAgent plist written to %s", LAUNCH_AGENT_PATH)


def _remove_launch_agent():
    try:
        LAUNCH_AGENT_PATH.unlink()
    except FileNotFoundError:
        pass


def enable_startup(exe_path: Optional[str] = None, prefer_task: bool = True) -> bool:
    exe_path = exe_path or current_executable()
    if IS_WINDOWS:
        if prefer_task and _register_task(exe_path):
            _delete_run_key()
            return True
        _set_run_key(exe_path)
        return True

    if IS_MAC:
        _write_launch_agent(exe_path)
        return True

    return False


def disable_startup() -> bool:
    if IS_WINDOWS:
        task_removed = True
        if _task_exists():
            task_removed = _delete_task()
        run_removed = True
        if _run_key_exists():
            run_removed = _delete_run_key()
        return task_removed and run_removed
    elif IS_MAC:
        _remove_launch_agent()
        return True
    return False


def startup_status() -> bool:
    if IS_WINDOWS:
        return _task_exists() or _run_key_exists()
    if IS_MAC:
        return LAUNCH_AGENT_PATH.exists()
    return False
    
def _resume_target_for(flag: str) -> Optional[str]:
    try:
        idx = sys.argv.index(flag)
        if len(sys.argv) > idx + 1 and not sys.argv[idx + 1].startswith("--"):
            return sys.argv[idx + 1]
    except ValueError:
        pass
    return None


if "--elevate-autostart" in sys.argv:
    resume_target = _resume_target_for("--elevate-autostart")
    success = enable_startup(current_executable(), prefer_task=True)
    if success:
        LOG.info("Startup registered from elevated helper.")
        if resume_target:
            ctypes.windll.shell32.ShellExecuteW(None, "open", resume_target, "", None, 1)
    else:
        LOG.error("Elevated helper could not register startup.")
    sys.exit(0)

if "--disable-autostart" in sys.argv:
    resume_target = _resume_target_for("--disable-autostart")
    success = disable_startup()
    if success:
        LOG.info("Startup disabled from elevated helper.")
        if resume_target:
            ctypes.windll.shell32.ShellExecuteW(None, "open", resume_target, "", None, 1)
    else:
        LOG.error("Elevated helper could not disable startup.")
    sys.exit(0)