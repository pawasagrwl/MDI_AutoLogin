# config.py
import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from startup import (
    current_executable,
    enable_startup,
    disable_startup,
    startup_status,
)

import keyring
import platform

# Explicitly set keyring backend for Windows to ensure it works in PyInstaller bundles
if platform.system() == "Windows":
    try:
        from keyring.backends.Windows import WinVaultKeyring
        keyring.set_keyring(WinVaultKeyring())
    except ImportError:
        # Backend not available, will use default
        pass
    except Exception:
        # Other error, will use default
        pass

APP_NAME = "MDI AutoLogin"
SERVICE_NAME = "MDI_AutoLogin"
DEFAULT_SSID = "MDI"

def app_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
    p = Path(base) / SERVICE_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p

CONFIG_PATH = app_dir() / "config.json"
LOG_PATH = app_dir() / "mdi_autologin.log"

def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "ssid": DEFAULT_SSID,
        "username": "",
        "login_url": "https://172.16.16.16/24online/servlet/E24onlineHTTPClient",
        "base_interval": 5,
        "retry_wait": 3,
        "post_timeout": 8,
        "post_grace_s": 6,
        "post_probe_delay_s": 1.5,
        "settle_max": 10,
        "settle_step": 0.5,
        "first_run": True,
        "auto_start_on_launch": True,
        "minimize_on_start": True,
        "dark_mode": False,
        "retry": {
            "max_consecutive": 3,
            "backoff_initial_s": 2,
            "backoff_max_s": 10,
            "cooldown_on_fatal_s": 10,
        },
        "login_error_patterns": {
            "quota_exceeded": r"\b(quota|data\s*quota|usage\s*quota)\b(?:(?!\bnot\b|\bremaining\b).){0,80}\b(exceed(?:ed)?|exhaust(?:ed)?|over(?:\s*limit)?)\b",
            "too_many_devices": r"\b(max(?:imum)?|too\s*many|simultaneous)\b.{0,40}\b(login|device|session)s?\b",
            "bad_credentials": "(invalid|incorrect).*?(user|id|credential|password)|authentication\\s*failed",
            "account_expired": "(expired|inactive|blocked)",
            "already_logged_in": "(already\\s*logged\\s*in|session\\s*exists)",
            "idle_timeout": "(idle\\s*time(?:out)?|session\\s*timed\\s*out)",
        },
    }

def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def get_password(username: str) -> str:
    if not username:
        return ""
    try:
        return keyring.get_password(SERVICE_NAME, username) or ""
    except Exception as e:
        log = logging.getLogger("mdi.config")
        log.error("Failed to get password from keyring: %s", e)
        return ""

def set_password(username: str, password: str):
    if not username:
        return
    try:
        keyring.set_password(SERVICE_NAME, username, password)
    except Exception as e:
        log = logging.getLogger("mdi.config")
        log.error("Failed to set password in keyring: %s", e)
        raise

def is_autostart_enabled() -> bool:
    return startup_status()

def set_autostart(enable: bool, exe_path: str = "") -> bool:
    exe = exe_path or current_executable()
    if enable:
        return enable_startup(exe)
    return disable_startup()

def setup_logger():
    lg = logging.getLogger("mdi")
    lg.setLevel(logging.INFO)
    if not any(isinstance(h, RotatingFileHandler) for h in lg.handlers):
        fh = RotatingFileHandler(LOG_PATH, maxBytes=512 * 1024, backupCount=3, encoding="utf-8", delay=True)
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        lg.addHandler(fh)
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in lg.handlers):
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        lg.addHandler(sh)
    lg.info("Log file: %s", LOG_PATH)
    return lg