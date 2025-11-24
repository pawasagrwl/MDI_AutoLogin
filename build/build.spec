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
        # ===== COMPREHENSIVE BUILT-IN MODULES =====
        # Core built-in modules that PyInstaller commonly misses
        'unicodedata',
        'hmac',
        'hashlib',
        'configparser',
        'pkgutil',
        'importlib',
        'importlib.util',
        'importlib.metadata',
        'importlib_metadata',
        
        # HTTP/URL modules
        'http',
        'http.client',
        'http.server',
        'http.cookiejar',
        'http.cookies',
        'urllib',
        'urllib.request',
        'urllib.parse',
        'urllib.error',
        'urllib.response',
        'urllib.robotparser',
        
        # Email modules
        'email',
        'email.message',
        'email.policy',
        'email.utils',
        'email.encoders',
        'email.mime',
        'email.mime.text',
        'email.mime.multipart',
        
        # Encoding modules
        'encodings',
        'encodings.idna',
        'encodings.utf_8',
        'encodings.ascii',
        'encodings.latin_1',
        'encodings.cp1252',
        'encodings.utf_16',
        'encodings.utf_32',
        
        # XML/HTML parsing
        'xml',
        'xml.parsers',
        'xml.parsers.expat',
        'xml.sax',
        'xml.sax.handler',
        'html',
        'html.parser',
        
        # JSON and data formats
        'json',
        'json.encoder',
        'json.decoder',
        'csv',
        'pickle',
        'pickletools',
        
        # Compression
        'gzip',
        'zipfile',
        'tarfile',
        'bz2',
        'lzma',
        
        # Cryptography
        'secrets',
        'base64',
        'binascii',
        
        # Date/time
        'datetime',
        'calendar',
        'time',
        
        # Threading/multiprocessing
        'threading',
        'queue',
        'multiprocessing',
        'concurrent',
        'concurrent.futures',
        
        # Path and file operations
        'pathlib',
        'os.path',
        'shutil',
        'tempfile',
        'glob',
        'fnmatch',
        
        # Logging
        'logging',
        'logging.handlers',
        'logging.config',
        
        # Regular expressions
        're',
        
        # Collections and data structures
        'collections',
        'collections.abc',
        'collections.ordered_dict',
        'collections.deque',
        'collections.defaultdict',
        'collections.namedtuple',
        'collections.Counter',
        'collections.ChainMap',
        'itertools',
        'functools',
        'operator',
        
        # String operations
        'string',
        'textwrap',
        'difflib',
        
        # Type hints
        'typing',
        'typing_extensions',
        
        # ===== THIRD-PARTY PACKAGES =====
        # Pystray
        'pystray',
        'pystray._win32',
        'pystray._darwin',
        'pystray._base',
        'six',
        'six.moves',
        
        # Keyring and Windows backend
        'keyring',
        'keyring.backends',
        'keyring.backends.Windows',
        'keyring.backends.Windows.WinVaultKeyring',
        'keyring.backends.windows',
        'keyring.backends.windows.WinVaultKeyring',
        'keyring.backends.macOS',
        'keyring.util',
        
        # Jaraco packages (used by keyring)
        'jaraco',
        'jaraco.classes',
        'jaraco.context',
        'jaraco.functools',
        'jaraco.text',
        
        # PIL/Pillow
        'PIL',
        'PIL._tkinter_finder',
        'PIL.Image',
        'PIL.ImageDraw',
        
        # Requests and HTTP libraries
        'requests',
        'requests.adapters',
        'requests.auth',
        'requests.cookies',
        'requests.models',
        'requests.sessions',
        'requests.structures',
        'requests.utils',
        'requests.compat',
        'requests.packages',
        'requests.packages.urllib3',
        
        # Certifi (SSL certificates)
        'certifi',
        'certifi.core',
        
        # Urllib3
        'urllib3',
        'urllib3.util',
        'urllib3.util.ssl_',
        'urllib3.util.retry',
        'urllib3.util.connection',
        'urllib3.util.request',
        'urllib3.util.response',
        'urllib3.util.url',
        'urllib3.packages',
        'urllib3.packages.ssl_match_hostname',
        'urllib3.contrib',
        'urllib3.contrib.pyopenssl',
        'urllib3.contrib.socks',
        'urllib3.poolmanager',
        'urllib3.connectionpool',
        'urllib3.exceptions',
        
        # Charset normalizer
        'charset_normalizer',
        'charset_normalizer.api',
        'charset_normalizer.legacy',
        'charset_normalizer.models',
        'charset_normalizer.utils',
        
        # IDNA
        'idna',
        'idna.core',
        'idna.idnadata',
        'idna.package_data',
        'idna.intranges',
        'idna.uts46data',
        
        # Backports
        'backports',
        'backports.tarfile',
        
        # Single-instance enforcement
        'psutil',
        'psutil._common',
        'psutil._compat',
        'psutil._psplatform',
        'psutil._pswindows',
        
        # Additional metadata
        'zipp',
        'packaging',
        'packaging.version',
        'packaging.specifiers',
        'packaging.requirements',
        
        # Date utilities
        'dateutil',
        'python_dateutil',
        
        # More utilities
        'more_itertools',
    ] + (
        # Collect ALL submodules for major packages to ensure nothing is missed
        collect_submodules('idna') +
        collect_submodules('certifi') +
        collect_submodules('urllib3') +
        collect_submodules('backports') +
        collect_submodules('jaraco') +
        collect_submodules('keyring') +
        collect_submodules('requests') +
        collect_submodules('charset_normalizer') +
        collect_submodules('pystray') +
        collect_submodules('PIL') +
        collect_submodules('psutil') +
        collect_submodules('importlib_metadata') +
        collect_submodules('zipp') +
        collect_submodules('packaging')
    ),
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
