"""
Tests for net.py - Network detection and login logic
"""
import pytest
from unittest.mock import patch, MagicMock

from net import (
    any_connected_ssid,
    gateway_is_campus,
    target_network_available,
    connected_to_target,
    analyze_login_response,
    portal_intercept_present,
)


@patch("net._current_ssids")
def test_any_connected_ssid_found(mock_ssids):
    """Test SSID detection when connected"""
    mock_ssids.return_value = ["MDI-WiFi", "OtherNetwork"]
    assert any_connected_ssid("MDI") is True
    assert any_connected_ssid("mdi") is True  # Case insensitive


@patch("net._current_ssids")
def test_any_connected_ssid_not_found(mock_ssids):
    """Test SSID detection when not connected"""
    mock_ssids.return_value = ["OtherNetwork"]
    assert any_connected_ssid("MDI") is False


@patch("net._current_ssids")
def test_any_connected_ssid_empty(mock_ssids):
    """Test SSID detection when no networks"""
    mock_ssids.return_value = []
    assert any_connected_ssid("MDI") is False


@patch("net.gateway_is_campus")
@patch("net.any_connected_ssid")
def test_target_network_available_ssid(mock_ssid, mock_gateway):
    """Test target network detection via SSID"""
    mock_ssid.return_value = True
    mock_gateway.return_value = False
    cfg = {"ssid": "MDI"}
    assert target_network_available(cfg) is True


@patch("net.gateway_is_campus")
@patch("net.any_connected_ssid")
def test_target_network_available_gateway(mock_ssid, mock_gateway):
    """Test target network detection via gateway"""
    mock_ssid.return_value = False
    mock_gateway.return_value = True
    cfg = {"ssid": "MDI"}
    assert target_network_available(cfg) is True


@patch("net.gateway_is_campus")
@patch("net.any_connected_ssid")
def test_target_network_available_neither(mock_ssid, mock_gateway):
    """Test target network detection when not available"""
    mock_ssid.return_value = False
    mock_gateway.return_value = False
    cfg = {"ssid": "MDI"}
    assert target_network_available(cfg) is False


@patch("net.portal_intercept_present")
@patch("net.target_network_available")
def test_connected_to_target(mock_target, mock_portal):
    """Test connected_to_target logic"""
    mock_target.return_value = True
    mock_portal.return_value = False
    cfg = {"ssid": "MDI"}
    assert connected_to_target(cfg) is True


def test_analyze_login_response_success():
    """Test login response analysis for success"""
    cfg = {"login_error_patterns": {}}
    code, _ = analyze_login_response(cfg, 200, "http://example.com", "login successful")
    assert code == "ok"


def test_analyze_login_response_quota_exceeded():
    """Test login response analysis for quota exceeded"""
    cfg = {
        "login_error_patterns": {
            "quota_exceeded": r"\bquota\b.*\bexceeded\b",
        }
    }
    code, _ = analyze_login_response(
        cfg, 200, "http://example.com", "Your data quota has been exceeded"
    )
    assert code == "quota_exceeded"


def test_analyze_login_response_bad_credentials():
    """Test login response analysis for bad credentials"""
    cfg = {
        "login_error_patterns": {
            "bad_credentials": "invalid.*credential",
        }
    }
    code, _ = analyze_login_response(
        cfg, 200, "http://example.com", "Invalid user credentials"
    )
    assert code == "bad_credentials"


def test_analyze_login_response_already_logged_in():
    """Test login response analysis for already logged in"""
    cfg = {
        "login_error_patterns": {
            "already_logged_in": "already.*logged.*in",
        }
    }
    code, _ = analyze_login_response(
        cfg, 200, "http://example.com", "You are already logged in"
    )
    assert code == "already_logged_in"


@patch("net._probe")
def test_portal_intercept_present_204(mock_probe):
    """Test portal detection when online (204)"""
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.url = "http://clients3.google.com/generate_204"
    mock_probe.return_value = mock_response
    assert portal_intercept_present() is False


@patch("net._probe")
def test_portal_intercept_present_redirect(mock_probe):
    """Test portal detection when redirected"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "http://172.16.16.16/login"
    mock_response.text = ""
    mock_probe.return_value = mock_response
    assert portal_intercept_present() is True


@patch("net._probe")
def test_portal_intercept_present_captive_marker(mock_probe):
    """Test portal detection when captive markers present"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "http://example.com"
    mock_response.text = "24online portal login"
    mock_probe.return_value = mock_response
    assert portal_intercept_present() is True

