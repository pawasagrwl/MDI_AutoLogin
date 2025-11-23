"""
Tests for ui/theme.py - Theme application
"""
import pytest
from unittest.mock import patch, MagicMock
import tkinter as tk

from ui.theme import apply_theme, ui_bg, _sanitize_color


def test_sanitize_color_valid():
    """Test _sanitize_color with valid color"""
    result = _sanitize_color("#ffffff")
    assert result == "#ffffff"


def test_sanitize_color_empty():
    """Test _sanitize_color with empty string"""
    result = _sanitize_color("")
    assert result == "SystemButtonFace"


def test_sanitize_color_none():
    """Test _sanitize_color with None"""
    result = _sanitize_color(None)
    assert result == "SystemButtonFace"


def test_sanitize_color_dash_prefix():
    """Test _sanitize_color with dash prefix (invalid)"""
    result = _sanitize_color("-invalid")
    assert result == "SystemButtonFace"


def test_ui_bg_with_style():
    """Test ui_bg when style lookup works"""
    root = tk.Tk()
    root.withdraw()  # Hide window
    
    try:
        bg = ui_bg(root)
        # Should return a valid color string
        assert isinstance(bg, str)
        assert len(bg) > 0
    finally:
        root.destroy()


def test_ui_bg_fallback():
    """Test ui_bg fallback to root background"""
    try:
        root = tk.Tk()
        root.withdraw()
        root.configure(bg="#123456")
        
        try:
            with patch("ui.theme.ttk.Style") as mock_style:
                mock_style_instance = MagicMock()
                mock_style_instance.lookup.return_value = None
                mock_style.return_value = mock_style_instance
                
                bg = ui_bg(root)
                # Should fall back to root background or default
                assert isinstance(bg, str)
        finally:
            root.destroy()
    except tk.TclError:
        # Skip test if tkinter is not properly installed
        pytest.skip("tkinter not properly installed")


def test_apply_theme_dark_mode():
    """Test apply_theme with dark mode"""
    root = tk.Tk()
    root.withdraw()
    
    try:
        apply_theme(root, dark=True)
        
        # Check that theme was applied
        style = root.tk.call("ttk::style", "theme", "use")
        # Should use "clam" theme
        assert style is not None
        
        # Check background was set
        bg = root.cget("bg")
        assert bg == "#121212"  # Dark mode background
    finally:
        root.destroy()


def test_apply_theme_light_mode():
    """Test apply_theme with light mode"""
    root = tk.Tk()
    root.withdraw()
    
    try:
        apply_theme(root, dark=False)
        
        # Check that theme was applied
        bg = root.cget("bg")
        assert bg == "#f6f6f6"  # Light mode background
    finally:
        root.destroy()


def test_apply_theme_handles_exception():
    """Test apply_theme handles exceptions gracefully"""
    try:
        root = tk.Tk()
        root.withdraw()
        
        try:
            # Mock theme_use to raise exception
            with patch("ui.theme.ttk.Style") as mock_style:
                mock_style_instance = MagicMock()
                mock_style_instance.theme_use.side_effect = Exception("Theme error")
                mock_style.return_value = mock_style_instance
                
                # Should not raise exception
                apply_theme(root, dark=True)
                # If we get here, exception was handled
                assert True
        finally:
            root.destroy()
    except tk.TclError:
        # Skip test if tkinter is not properly installed
        pytest.skip("tkinter not properly installed")

