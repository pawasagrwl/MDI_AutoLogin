# runtime_hook.py
# PyInstaller runtime hook to ensure built-in modules are available
import os
import sys
import warnings

# Ensure critical modules are available early
try:
    import unicodedata
except ImportError:
    pass

# Ensure certifi is available (required by requests for SSL certificates)
try:
    import certifi
except ImportError:
    pass

# Ensure backports are available (used by various packages)
try:
    import backports.tarfile
except ImportError:
    pass

# Note: PyInstaller's "Failed to remove temporary directory" warning
# is shown as a Windows MessageBox by the bootloader (C code), not Python.
# This warning is harmless - it just means Windows couldn't delete the temp
# folder immediately (usually because a file is still locked).
# The temp folder will be cleaned up on next reboot or by Windows cleanup.
# 
# Unfortunately, we cannot suppress this MessageBox from Python code since
# it's shown by PyInstaller's bootloader after Python exits.
# 
# Options to reduce this warning:
# 1. Use --onedir instead of --onefile (but creates a folder instead of single exe)
# 2. Accept it as harmless (recommended - it doesn't affect functionality)
# 3. Set runtime_tmpdir to a specific location (may help in some cases)

# Suppress any Python-level warnings we can catch
warnings.filterwarnings('ignore', category=UserWarning, message='.*temporary.*')
warnings.filterwarnings('ignore', category=UserWarning, message='.*Failed to remove.*')

