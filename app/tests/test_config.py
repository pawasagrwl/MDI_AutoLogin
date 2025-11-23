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

