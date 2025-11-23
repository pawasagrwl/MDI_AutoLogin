# Building MDI AutoLogin for Distribution

This guide explains how to build a standalone Windows executable that runs on any PC without Python installed and minimizes antivirus false positives.

## Prerequisites

1. **Python 3.11+** installed
2. **Build dependencies** installed: `pip install -r build/requirements-build.txt`
3. **PyInstaller** installed (included in requirements-build.txt)

## Quick Build (Local)

### Option 1: Using Build Script (Recommended)

1. Open a terminal in the `build` directory
2. Run: `build.bat`
3. Find the executable in `app\dist\MDI AutoLogin.exe`

### Option 2: Manual Build

1. Open a terminal in the `app` directory
2. Run: `pyinstaller ..\build\build.spec --workpath=build --distpath=dist --clean`
3. Find the executable in `dist\MDI AutoLogin.exe`

## Automated Build (GitHub Actions)

The repository includes a GitHub Actions workflow that automatically builds the EXE:

### Automatic Build on Tag Push

When you push a tag starting with `v` (e.g., `v1.0.0`):

```bash
git tag v1.0.0
git push origin v1.0.0
```

This will:
- Automatically build the EXE
- Create a GitHub Release
- Attach the EXE to the release

### Manual Build via GitHub Actions

1. Go to your repository on GitHub
2. Click on **Actions** tab
3. Select **Build Windows EXE** workflow
4. Click **Run workflow**
5. Optionally specify a version (e.g., `v1.0.0`)
6. Wait for build to complete
7. Download the EXE from the artifacts section

**Note:** The GitHub Actions build uses the same `build/build.spec` file, ensuring consistent builds across environments.

For more details, see [GitHub Actions Workflows](../.github/workflows/README.md).

## Build Configuration

The build uses `build/build.spec` which includes:

### 1. **Excluded Unnecessary Modules**
The spec file excludes large libraries you don't need (matplotlib, numpy, winrt, etc.) to:
- Reduce executable size
- Speed up startup time
- Reduce AV false positive risk

### 2. **Hidden Imports**
Added explicit imports for modules that PyInstaller might miss:
- `unicodedata` (required by idna/requests)
- `pystray._win32` (tray icon backend)
- `keyring.backends.Windows` (credential storage)
- `idna` and submodules (for requests)
- `six` (required by pystray)

### 3. **Tcl/Tk Data Files**
Automatically includes Tcl/Tk data files for tkinter GUI support.

### 4. **UPX Compression Disabled**
UPX compression can trigger antivirus false positives. The spec file has `upx=False` to avoid this.

### 5. **No Archive Mode**
Uses `noarchive=True` to avoid `base_library.zip` extraction issues. This may show a harmless temp directory cleanup warning on exit (does not affect functionality).

## Reducing Antivirus False Positives

### Best Solution: Code Signing

**Code signing is the most effective way to prevent AV false positives.**

1. **Get a Code Signing Certificate:**
   - Purchase from: DigiCert, Sectigo, GlobalSign, or similar
   - Cost: ~$200-400/year
   - Required for: Professional distribution

2. **Sign the Executable:**
   ```batch
   signtool sign /f your_certificate.pfx /p your_password /t http://timestamp.digicert.com "dist\MDI AutoLogin.exe"
   ```

3. **Verify Signature:**
   ```batch
   signtool verify /pa "dist\MDI AutoLogin.exe"
   ```

### Alternative: Free Options

1. **Windows Defender SmartScreen:**
   - First-time users may see "Unknown publisher" warning
   - After enough users run it, Windows learns it's safe
   - Not ideal for initial distribution

2. **VirusTotal Submission:**
   - Upload your exe to https://www.virustotal.com
   - If flagged, submit for review to major AV vendors
   - Helps build reputation over time

3. **Add to Windows Defender Exclusions:**
   - Users can manually add your exe to Windows Defender exclusions
   - Not practical for distribution

## Testing on Clean Windows

Before distributing:

1. **Test on a clean Windows VM:**
   - Windows 10/11 without Python installed
   - Fresh Windows Defender (default settings)
   - No other antivirus software

2. **Check for:**
   - Executable runs without errors
   - No missing DLL errors
   - Tray icon appears
   - Auto-login works
   - Settings save correctly

## Distribution Checklist

- [ ] Build executable using `build/build.spec` (locally or via GitHub Actions)
- [ ] Test on clean Windows machine
- [ ] Code sign the executable (if possible)
- [ ] Scan with VirusTotal
- [ ] Test Windows Defender SmartScreen behavior
- [ ] Create installer (optional, using NSIS/Inno Setup)
- [ ] Document installation instructions
- [ ] Create GitHub Release with tag (if using automated builds)

## Troubleshooting

### "Failed to execute script"
- Check if all hidden imports are included
- Verify no missing DLLs
- Run with `console=True` temporarily to see errors

### Large executable size
- Review excluded modules in spec file
- Remove unused dependencies from `requirements.txt`

### AV false positives
- Code sign the executable
- Submit to VirusTotal for review
- Contact AV vendors if needed

## File Structure

### Project Structure
```
mdi_auto_login_app/
├── app/                    # Application source code
│   ├── app.py             # Main entry point
│   ├── dist/              # Build output (after build)
│   └── ...
├── build/                  # Build configuration
│   ├── build.spec         # PyInstaller configuration
│   ├── build.bat          # Local build script
│   ├── requirements-build.txt  # Build dependencies
│   └── runtime_hook.py   # Runtime hook for PyInstaller
└── .github/
    └── workflows/
        └── build.yml      # GitHub Actions workflow
```

### After Local Build
```
app/
├── build/          (temporary build files - can be deleted)
├── dist/
│   └── MDI AutoLogin.exe  (your final executable)
└── ...
```

## Notes

- The executable is **portable** - no installation needed
- First run creates config/log files in `%LOCALAPPDATA%\MDI_AutoLogin\`
- Users can run it from anywhere (USB drive, network share, etc.)
- **Temp directory warning:** When closing the app, you may see a harmless "Failed to remove temporary directory" warning. This is a known PyInstaller behavior with `noarchive=True` and doesn't affect functionality - Windows will clean up automatically.

