# runtime_hook.py
# PyInstaller runtime hook to ensure built-in modules are available
import sys

# Ensure unicodedata is available (required by idna)
try:
    import unicodedata
except ImportError:
    # If unicodedata is not available, this is a critical error
    # but we'll let it fail naturally so the user sees the real error
    pass

# Suppress PyInstaller temp directory cleanup warnings
import warnings
warnings.filterwarnings('ignore', category=UserWarning, message='.*Failed to remove temporary directory.*')

