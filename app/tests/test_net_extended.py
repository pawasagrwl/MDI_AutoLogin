"""
Extended tests for net.py - Additional network and login functionality
"""
import pytest
from unittest.mock import patch, MagicMock
import time

from net import (
    online_now,
    send_login,
    settle_until_online,
    login_with_diagnostics,
    _probe,
    _run_cmd,
)


@patch("net._probe")
def test_online_now_true(mock_probe):
    """Test online_now when actually online"""
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.url = "http://clients3.google.com/generate_204"
    mock_probe.return_value = mock_response
    
    assert online_now() is True


@patch("net._probe")
def test_online_now_false_redirect(mock_probe):
    """Test online_now when redirected (captive portal)"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "http://172.16.16.16/login"
    mock_probe.return_value = mock_response
    
    assert online_now() is False


@patch("net._probe")
def test_online_now_false_exception(mock_probe):
    """Test online_now when probe raises exception"""
    mock_probe.side_effect = Exception("Network error")
    
    assert online_now() is False


@patch("net._session.post")
def test_send_login_success(mock_post):
    """Test successful login request"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "http://example.com/success"
    mock_response.text = "Login successful"
    mock_post.return_value = mock_response
    
    cfg = {
        "login_url": "http://example.com/login",
        "post_timeout": 8,
    }
    
    result = send_login(cfg, "test_user", "test_pass")
    assert result is True
    mock_post.assert_called_once()


@patch("net._session.post")
def test_send_login_failure(mock_post):
    """Test failed login request"""
    mock_post.side_effect = Exception("Connection error")
    
    cfg = {
        "login_url": "http://example.com/login",
        "post_timeout": 8,
    }
    
    result = send_login(cfg, "test_user", "test_pass")
    assert result is False


@patch("net.online_now")
def test_settle_until_online_immediate(mock_online):
    """Test settle_until_online when already online"""
    mock_online.return_value = True
    
    result = settle_until_online(max_s=10.0, step=0.5)
    assert result is True
    assert mock_online.call_count == 1


@patch("net.online_now")
@patch("time.sleep")
def test_settle_until_online_after_wait(mock_sleep, mock_online):
    """Test settle_until_online when comes online after waiting"""
    mock_online.side_effect = [False, False, True]
    
    result = settle_until_online(max_s=10.0, step=0.5)
    assert result is True
    assert mock_online.call_count == 3
    assert mock_sleep.call_count == 2  # Sleep between checks


@patch("net.online_now")
@patch("time.sleep")
def test_settle_until_online_timeout(mock_sleep, mock_online):
    """Test settle_until_online when timeout reached"""
    mock_online.return_value = False
    
    # With max_s=1.0 and step=0.5, should check 3 times (0, 0.5, 1.0)
    result = settle_until_online(max_s=1.0, step=0.5)
    assert result is False
    assert mock_online.call_count >= 2


@patch("net._session.post")
@patch("net.analyze_login_response")
def test_login_with_diagnostics_success(mock_analyze, mock_post):
    """Test login_with_diagnostics with successful login"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "http://example.com/success"
    mock_response.text = "Login successful"
    
    mock_post.return_value = mock_response
    mock_analyze.return_value = ("ok", "Login successful")
    
    cfg = {
        "login_url": "http://example.com/login",
        "post_timeout": 8,
        "login_error_patterns": {},
    }
    
    result = login_with_diagnostics(cfg, "test_user", "test_pass")
    
    assert result["ok"] is True
    assert result["reason_code"] == "ok"
    mock_post.assert_called_once()


@patch("net._session.post")
@patch("net.analyze_login_response")
def test_login_with_diagnostics_quota_exceeded(mock_analyze, mock_post):
    """Test login_with_diagnostics with quota exceeded error"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "http://example.com/login"
    mock_response.text = "Quota exceeded"
    
    mock_post.return_value = mock_response
    mock_analyze.return_value = ("quota_exceeded", "Quota exceeded")
    
    cfg = {
        "login_url": "http://example.com/login",
        "post_timeout": 8,
        "login_error_patterns": {},
    }
    
    result = login_with_diagnostics(cfg, "test_user", "test_pass")
    
    assert result["ok"] is False
    assert result["reason_code"] == "quota_exceeded"
    assert "quota" in result["reason_text"].lower()


@patch("net._session.post")
def test_login_with_diagnostics_connection_error(mock_post):
    """Test login_with_diagnostics when connection fails"""
    mock_post.side_effect = Exception("Connection error")
    
    cfg = {
        "login_url": "http://example.com/login",
        "post_timeout": 8,
        "login_error_patterns": {},
    }
    
    result = login_with_diagnostics(cfg, "test_user", "test_pass")
    
    assert result["ok"] is False
    assert result["reason_code"] == "network_error"  # Actual code returned


@patch("net._session.get")
def test_probe_success(mock_get):
    """Test _probe function"""
    mock_response = MagicMock()
    mock_get.return_value = mock_response
    
    result = _probe()
    assert result == mock_response
    mock_get.assert_called_once_with(
        "http://clients3.google.com/generate_204",
        timeout=3,
        verify=False,
        allow_redirects=True
    )


@patch("subprocess.run")
def test_run_cmd_success(mock_run):
    """Test _run_cmd with successful command"""
    mock_result = MagicMock()
    mock_result.stdout = "output text"
    mock_result.returncode = 0
    mock_run.return_value = mock_result
    
    result = _run_cmd(["test", "command"])
    assert result == "output text"
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_run_cmd_exception(mock_run):
    """Test _run_cmd when command raises exception"""
    mock_run.side_effect = Exception("Command failed")
    
    result = _run_cmd(["test", "command"])
    assert result == ""


@patch("net._current_ssids")
def test_any_connected_ssid_case_insensitive(mock_ssids):
    """Test that SSID matching is case insensitive"""
    mock_ssids.return_value = ["MDI-WiFi", "OtherNetwork"]
    
    from net import any_connected_ssid
    assert any_connected_ssid("mdi") is True
    assert any_connected_ssid("MDI") is True
    assert any_connected_ssid("Mdi") is True


@patch("net._current_ssids")
def test_any_connected_ssid_partial_match(mock_ssids):
    """Test that SSID matching works with partial matches"""
    mock_ssids.return_value = ["MDI-WiFi-5G", "OtherNetwork"]
    
    from net import any_connected_ssid
    assert any_connected_ssid("MDI") is True
    assert any_connected_ssid("MDI-WiFi") is True

