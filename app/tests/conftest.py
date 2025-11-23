"""
Pytest configuration and shared fixtures
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture
def temp_config_dir(monkeypatch):
    """Create a temporary directory for config files during tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
        yield tmp_path


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        "ssid": "MDI",
        "username": "test_user",
        "login_url": "https://172.16.16.16/24online/servlet/E24onlineHTTPClient",
        "base_interval": 5,
        "retry_wait": 3,
        "post_timeout": 8,
        "post_grace_s": 6,
        "post_probe_delay_s": 1.5,
        "settle_max": 10,
        "settle_step": 0.5,
        "first_run": False,
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
            "quota_exceeded": r"\b(quota|data\s*quota|usage\s*quota)\b",
            "too_many_devices": r"\b(max(?:imum)?|too\s*many|simultaneous)\b",
            "bad_credentials": "(invalid|incorrect).*?(user|id|credential|password)",
            "account_expired": "(expired|inactive|blocked)",
            "already_logged_in": "(already\\s*logged\\s*in|session\\s*exists)",
        },
    }


@pytest.fixture
def mock_keyring(monkeypatch):
    """Mock keyring for testing"""
    keyring_store = {}
    
    def get_password(service, username):
        return keyring_store.get((service, username), None)
    
    def set_password(service, username, password):
        keyring_store[(service, username)] = password
    
    def delete_password(service, username):
        keyring_store.pop((service, username), None)
    
    monkeypatch.setattr("keyring.get_password", get_password)
    monkeypatch.setattr("keyring.set_password", set_password)
    monkeypatch.setattr("keyring.delete_password", delete_password)
    
    return keyring_store

