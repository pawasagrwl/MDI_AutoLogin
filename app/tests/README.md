# Test Suite for MDI AutoLogin

## Running Tests

### Quick Run
```bash
cd app
pytest tests/
```

### With Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

### Windows Batch Script
```bash
cd app/tests
run_tests.bat
```

## Test Structure

- `test_config.py` - Configuration management tests
- `test_net.py` - Network detection and login logic tests
- `test_startup.py` - Startup registration tests
- `test_worker.py` - Background worker tests
- `conftest.py` - Shared fixtures and configuration

## Writing New Tests

1. Create test file: `test_<module>.py`
2. Import the module you're testing
3. Use fixtures from `conftest.py` for common setup
4. Mock external dependencies (network, keyring, etc.)
5. Test both success and failure cases

## Example Test

```python
def test_my_function(mock_keyring):
    """Test description"""
    # Setup
    mock_keyring[("service", "user")] = "pass"
    
    # Execute
    result = my_function("user")
    
    # Assert
    assert result == "expected"
```

## Test Coverage Goals

- ✅ Config loading/saving
- ✅ Network detection
- ✅ Login response parsing
- ✅ Worker state management
- ⏳ UI components (needs more work)
- ⏳ Integration tests (end-to-end)

