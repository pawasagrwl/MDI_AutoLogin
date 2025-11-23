"""
Smoke tests - Basic functionality checks
Run these first to verify the test setup works
"""
import pytest

def test_imports():
    """Test that all main modules can be imported"""
    import config
    import net
    import startup
    from ui import worker
    assert True  # If we get here, imports worked

def test_pytest_works():
    """Basic pytest sanity check"""
    assert 1 + 1 == 2

def test_fixtures_work(temp_config_dir, sample_config, mock_keyring):
    """Test that fixtures are working"""
    assert temp_config_dir.exists()
    assert sample_config["ssid"] == "MDI"
    assert isinstance(mock_keyring, dict)

