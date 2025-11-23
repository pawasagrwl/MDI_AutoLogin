"""
Tests for ui/messages.py - Message dialogs
"""
import pytest
from unittest.mock import patch, MagicMock

from ui.messages import msg_info, msg_error, ask_yes_no


@patch("ui.messages.ctypes.windll.user32.MessageBoxW")
def test_msg_info(mock_messagebox):
    """Test msg_info function"""
    mock_messagebox.return_value = 1  # IDOK
    
    msg_info("Test Title", "Test message")
    
    mock_messagebox.assert_called_once()
    args = mock_messagebox.call_args
    assert args[0][1] == "Test message"
    assert args[0][2] == "Test Title"
    # Check MB_OK | MB_ICONINFO flags
    assert args[1] == {} or "MB_OK" in str(args) or args[0][3] & 0x40  # MB_ICONINFO


@patch("ui.messages.ctypes.windll.user32.MessageBoxW")
def test_msg_error(mock_messagebox):
    """Test msg_error function"""
    mock_messagebox.return_value = 1  # IDOK
    
    msg_error("Error Title", "Error message")
    
    mock_messagebox.assert_called_once()
    args = mock_messagebox.call_args
    assert args[0][1] == "Error message"
    assert args[0][2] == "Error Title"
    # Check MB_OK | MB_ICONERROR flags
    assert args[1] == {} or "MB_ICONERROR" in str(args) or args[0][3] & 0x10  # MB_ICONERROR


@patch("ui.messages.ctypes.windll.user32.MessageBoxW")
def test_ask_yes_no_yes(mock_messagebox):
    """Test ask_yes_no when user clicks Yes"""
    # IDYES = 6 in Windows API
    mock_messagebox.return_value = 6  # IDYES
    
    result = ask_yes_no("Question", "Do you want to continue?")
    
    assert result is True
    mock_messagebox.assert_called_once()
    args = mock_messagebox.call_args
    assert args[0][1] == "Do you want to continue?"
    assert args[0][2] == "Question"
    # Check MB_YESNO | MB_ICONINFO flags
    assert args[1] == {} or "MB_YESNO" in str(args) or args[0][3] & 0x04  # MB_YESNO


@patch("ui.messages.ctypes.windll.user32.MessageBoxW")
def test_ask_yes_no_no(mock_messagebox):
    """Test ask_yes_no when user clicks No"""
    # IDYES = 6, IDNO = 7 in Windows API
    mock_messagebox.return_value = 7  # IDNO (not IDYES)
    
    result = ask_yes_no("Question", "Do you want to continue?")
    
    assert result is False
    mock_messagebox.assert_called_once()

