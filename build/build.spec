# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for MDI AutoLogin
# Simplified and stable configuration

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Collect Tcl/Tk data files for tkinter
tcl_tk_data = []
try:
    # Try to find Tcl/Tk in Python installation
    python_dir = os.path.dirname(sys.executable)
    tcl_dir = os.path.join(python_dir, 'tcl')
    tk_dir = os.path.join(python_dir, 'tk')
    
    if os.path.exists(tcl_dir):
        tcl_tk_data.append((tcl_dir, 'tcl'))
    if os.path.exists(tk_dir):
        tcl_tk_data.append((tk_dir, 'tk'))
except Exception:
    # If we can't find them, PyInstaller might auto-detect
    pass

# Runtime hook path - try multiple methods to find it
# The runtime hook is in the same directory as this spec file (build/)
runtime_hook_path = None
# Try relative to current working directory (when run from app/)
if os.path.exists('../build/runtime_hook.py'):
    runtime_hook_path = os.path.abspath('../build/runtime_hook.py')
# Try in build/ subdirectory (when run from root)
elif os.path.exists('build/runtime_hook.py'):
    runtime_hook_path = os.path.abspath('build/runtime_hook.py')
# Try same directory as spec (when spec knows its location)
elif 'SPECPATH' in globals():
    spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
    hook_path = os.path.join(spec_dir, 'runtime_hook.py')
    if os.path.exists(hook_path):
        runtime_hook_path = hook_path

runtime_hooks = [runtime_hook_path] if runtime_hook_path and os.path.exists(runtime_hook_path) else []

a = Analysis(
    ['../app/app.py'],
    pathex=['../app'],
    binaries=[],
    datas=tcl_tk_data + collect_data_files('certifi'),  # Include certifi's certificate bundle
    hiddenimports=[
        # Built-in modules that PyInstaller sometimes misses
        'unicodedata',
        'hmac',  # Required by urllib3 (used by requests)
        'http',  # Required by urllib.request (used by jaraco.context)
        'http.client',
        'http.server',
        'http.cookiejar',
        'urllib',  # Standard library urllib (not urllib3)
        'urllib.request',
        'urllib.parse',
        'urllib.error',
        'urllib.response',
        'email',  # Sometimes required by urllib
        'email.message',
        'email.policy',
        'encodings',  # Required for text encoding
        'encodings.idna',
        'encodings.utf_8',
        'encodings.ascii',
        'encodings.latin_1',
        'pkgutil',  # Used for package discovery
        # Pystray dependencies
        'pystray._win32',
        'pystray._darwin',
        'six',
        # Keyring and Windows backend
        'keyring',
        'keyring.backends',
        'keyring.backends.Windows',
        'keyring.backends.Windows.WinVaultKeyring',
        'keyring.backends.macOS',
        # Jaraco packages (used by keyring)
        'jaraco',
        'jaraco.classes',
        'jaraco.context',
        'jaraco.functools',
        # PIL/Pillow for pystray icon handling
        'PIL._tkinter_finder',
        # Requests dependencies - collect all submodules to ensure everything is included
        'certifi',  # Required by requests for SSL certificates
        'urllib3',  # Required by requests
        'urllib3.util',  # Required by urllib3
        'urllib3.util.ssl_',  # Required by urllib3
        'urllib3.packages',  # Required by urllib3
        'urllib3.packages.ssl_match_hostname',  # Required by urllib3
        'charset_normalizer',  # Required by requests
        'idna',
        'idna.core',
        'idna.idnadata',
        # Backports (used by various packages)
        'backports',
        'backports.tarfile',
        # Single-instance enforcement
        'psutil',  # Required for detecting and killing old instances
        # Additional common dependencies that might be missed
        'importlib_metadata',  # Used by various packages
        'zipp',  # Used by importlib_metadata
    ] + collect_submodules('idna') + collect_submodules('certifi') + collect_submodules('urllib3') + collect_submodules('backports') + collect_submodules('jaraco'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=[
        'pytest',
        'test',
        'tests',
        'unittest',
        'pydoc',
        'doctest',
        'pdb',
        'tkinter.test',
        'pydoc_data',
        'distutils',
        'setuptools',
        'pip',
        'wheel',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True,  # Set to True to avoid base_library.zip extraction issues
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MDI AutoLogin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,  # Use system temp, but cleanup warnings are harmless
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version=None,
)
