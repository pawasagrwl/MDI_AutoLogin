# runtime_hook.py
# PyInstaller runtime hook to ensure built-in modules are available
import os
import sys
import warnings

# Comprehensive runtime hook to ensure all critical modules are imported early
# This helps PyInstaller detect and include all necessary modules

# Core built-in modules
_import_safely = lambda m: __import__(m, fromlist=[''])

# Core modules
for module in ['unicodedata', 'hmac', 'hashlib', 'configparser', 'pkgutil', 
               'importlib', 'importlib.util', 'importlib.metadata']:
    try:
        _import_safely(module)
    except ImportError:
        pass

# HTTP/URL modules
for module in ['http', 'http.client', 'http.server', 'http.cookiejar',
               'urllib', 'urllib.request', 'urllib.parse', 'urllib.error']:
    try:
        _import_safely(module)
    except ImportError:
        pass

# Email modules
for module in ['email', 'email.message', 'email.policy', 'email.utils']:
    try:
        _import_safely(module)
    except ImportError:
        pass

# Encoding modules
for module in ['encodings', 'encodings.idna', 'encodings.utf_8', 
               'encodings.ascii', 'encodings.latin_1']:
    try:
        _import_safely(module)
    except ImportError:
        pass

# JSON and data
for module in ['json', 'json.encoder', 'json.decoder', 'csv', 'pickle']:
    try:
        _import_safely(module)
    except ImportError:
        pass

# Third-party packages
for module in ['certifi', 'urllib3', 'requests', 'keyring', 
               'jaraco.context', 'jaraco.classes', 'jaraco.functools',
               'backports.tarfile', 'psutil', 'pystray', 'PIL',
               'idna', 'charset_normalizer', 'importlib_metadata', 'zipp']:
    try:
        _import_safely(module)
    except ImportError:
        pass

# Clean up
del _import_safely

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

