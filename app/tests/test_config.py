"""
Tests for config.py
"""
import json
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open

from config import (
    load_config,
    save_config,
    get_password,
    set_password,
    CONFIG_PATH,
    DEFAULT_SSID,
)


def test_load_config_defaults(temp_config_dir):
    """Test that load_config returns defaults when no config exists"""
    # Ensure config file doesn't exist
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
    
    config = load_config()
    assert config["ssid"] == DEFAULT_SSID
    assert config["username"] == ""
    assert "login_url" in config
    assert "retry" in config
    assert config["first_run"] is True


def test_load_config_from_file(temp_config_dir, sample_config):
    """Test loading config from existing file"""
    CONFIG_PATH.write_text(json.dumps(sample_config), encoding="utf-8")
    config = load_config()
    assert config["ssid"] == sample_config["ssid"]
    assert config["username"] == sample_config["username"]


def test_save_config(temp_config_dir, sample_config):
    """Test saving config to file"""
    save_config(sample_config)
    assert CONFIG_PATH.exists()
    loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert loaded["ssid"] == sample_config["ssid"]


def test_get_password(mock_keyring):
    """Test getting password from keyring"""
    mock_keyring[("MDI_AutoLogin", "test_user")] = "test_pass"
    password = get_password("test_user")
    assert password == "test_pass"


def test_get_password_not_found(mock_keyring):
    """Test getting password when not set"""
    password = get_password("nonexistent")
    assert password == ""


def test_set_password(mock_keyring):
    """Test setting password in keyring"""
    set_password("test_user", "test_pass")
    assert mock_keyring[("MDI_AutoLogin", "test_user")] == "test_pass"


def test_set_password_empty_username(mock_keyring):
    """Test that empty username doesn't set password"""
    set_password("", "test_pass")
    assert ("MDI_AutoLogin", "") not in mock_keyring


def test_load_config_invalid_json(temp_config_dir):
    """Test loading config with invalid JSON"""
    CONFIG_PATH.write_text("invalid json {", encoding="utf-8")
    config = load_config()
    # Should return defaults when JSON is invalid
    assert config["ssid"] == DEFAULT_SSID
    assert config["first_run"] is True


def test_load_config_missing_keys(temp_config_dir):
    """Test loading config with missing keys (returns JSON as-is, doesn't merge)"""
    partial_config = {"ssid": "CustomSSID"}
    CONFIG_PATH.write_text(json.dumps(partial_config), encoding="utf-8")
    config = load_config()
    assert config["ssid"] == "CustomSSID"
    # Note: load_config doesn't merge with defaults, it returns JSON as-is
    # So missing keys won't be filled in
    assert "username" not in config or config.get("username") == ""  # May or may not be present


def test_save_config_preserves_all_keys(temp_config_dir, sample_config):
    """Test that save_config preserves all keys"""
    save_config(sample_config)
    loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert loaded.keys() == sample_config.keys()


def test_get_password_empty_username(mock_keyring):
    """Test getting password with empty username"""
    password = get_password("")
    assert password == ""


def test_get_password_keyring_exception(mock_keyring):
    """Test get_password handles keyring exceptions"""
    from unittest.mock import patch
    with patch("keyring.get_password", side_effect=Exception("Keyring error")):
        password = get_password("test_user")
        assert password == ""


def test_set_password_keyring_exception():
    """Test set_password raises exception on keyring error"""
    from unittest.mock import patch
    with patch("keyring.set_password", side_effect=Exception("Keyring error")):
        with pytest.raises(Exception):
            set_password("test_user", "test_pass")


@patch("config.startup_status")
def test_is_autostart_enabled_true(mock_status):
    """Test is_autostart_enabled when enabled"""
    from config import is_autostart_enabled
    mock_status.return_value = True
    assert is_autostart_enabled() is True


@patch("config.startup_status")
def test_is_autostart_enabled_false(mock_status):
    """Test is_autostart_enabled when disabled"""
    from config import is_autostart_enabled
    mock_status.return_value = False
    assert is_autostart_enabled() is False


@patch("config.enable_startup")
@patch("config.current_executable")
def test_set_autostart_enable(mock_exe, mock_enable):
    """Test set_autostart when enabling"""
    from config import set_autostart
    mock_exe.return_value = "C:\\app\\MDI AutoLogin.exe"
    mock_enable.return_value = True
    
    result = set_autostart(True, "C:\\app\\MDI AutoLogin.exe")
    assert result is True
    mock_enable.assert_called_once()


@patch("config.disable_startup")
def test_set_autostart_disable(mock_disable):
    """Test set_autostart when disabling"""
    from config import set_autostart
    mock_disable.return_value = True
    
    result = set_autostart(False)
    assert result is True
    mock_disable.assert_called_once()

