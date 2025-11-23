"""
Tests for ui/worker.py - Background worker logic
"""
import pytest
from unittest.mock import patch, MagicMock
import time

from ui.worker import AutoLoginWorker


@pytest.fixture
def mock_tray():
    """Mock tray app reference"""
    tray = MagicMock()
    tray.update_tooltip = MagicMock()
    return tray


@pytest.fixture
def worker(mock_tray, temp_config_dir, sample_config, mock_keyring):
    """Create a worker instance for testing"""
    with patch("ui.worker.load_config", return_value=sample_config):
        with patch("ui.worker.get_password", return_value="test_pass"):
            with patch("ui.worker.get_event_bus"):
                worker = AutoLoginWorker(mock_tray)
                return worker


def test_worker_initialization(worker, sample_config):
    """Test worker initializes correctly"""
    assert worker.cfg == sample_config
    assert worker.username == sample_config["username"]
    assert worker.password == "test_pass"
    assert worker.running is False
    assert worker.fail_count == 0


def test_worker_config_refresh(worker, temp_config_dir, sample_config):
    """Test worker refreshes config when file changes"""
    import time
    from config import CONFIG_PATH, save_config
    
    # Initial config
    assert worker.cfg["ssid"] == "MDI"
    
    # Modify config file
    new_config = sample_config.copy()
    new_config["ssid"] = "MDI-New"
    save_config(new_config)
    
    # Wait a tiny bit for mtime to change
    time.sleep(0.1)
    
    # Refresh should pick up new config
    worker._refresh_config_if_needed()
    assert worker.cfg["ssid"] == "MDI-New"


@patch("ui.worker.online_now")
@patch("ui.worker.portal_intercept_present")
def test_worker_log_state_online(mock_portal, mock_online, worker):
    """Test worker logs state correctly when online"""
    mock_online.return_value = True
    mock_portal.return_value = False
    
    worker._log_once_per_state(True, False)
    assert worker.last_online_state == "online"


@patch("ui.worker.online_now")
@patch("ui.worker.portal_intercept_present")
def test_worker_log_state_captive(mock_portal, mock_online, worker):
    """Test worker logs state correctly when captive"""
    mock_online.return_value = False
    mock_portal.return_value = True
    
    worker._log_once_per_state(False, True)
    assert worker.last_online_state == "captive"


def test_worker_backoff_fatal(worker, sample_config):
    """Test backoff logic for fatal errors"""
    worker._apply_backoff_and_cooldown(sample_config, fatal=True)
    assert worker.fail_count == 0
    assert worker.backoff_s is None
    assert worker.cooldown_until > time.time()


def test_worker_backoff_non_fatal(worker, sample_config):
    """Test backoff logic for non-fatal errors"""
    initial_fail = worker.fail_count
    worker._apply_backoff_and_cooldown(sample_config, fatal=False)
    assert worker.fail_count == initial_fail + 1
    assert worker.backoff_s is not None

