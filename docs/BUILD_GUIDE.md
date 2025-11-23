# Building MDI AutoLogin for Distribution

This guide explains how to build a standalone Windows executable that runs on any PC without Python installed and minimizes antivirus false positives.

## Prerequisites

1. **Python 3.11+** installed
2. **All dependencies** installed: `pip install -r requirements.txt`
3. **PyInstaller** installed: `pip install pyinstaller`

## Quick Build

1. Open a terminal in the `app` directory
2. Run: `build.bat` (or `pyinstaller build.spec` manually)
3. Find the executable in `dist\MDI AutoLogin.exe`

## Optimizations Applied

### 1. **Excluded Unnecessary Modules**
The spec file excludes large libraries you don't need (matplotlib, numpy, winrt, etc.) to:
- Reduce executable size
- Speed up startup time
- Reduce AV false positive risk

### 2. **Hidden Imports**
Added explicit imports for Windows-specific modules that PyInstaller might miss:
- `pystray._win32` (tray icon)
- `keyring.backends.Windows` (credential storage)
- Various `win32*` modules (Windows API calls)

### 3. **UPX Compression Disabled**
UPX compression can trigger antivirus false positives. The spec file has `upx=False` to avoid this.

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

- [ ] Build executable using `build.spec`
- [ ] Test on clean Windows machine
- [ ] Code sign the executable (if possible)
- [ ] Scan with VirusTotal
- [ ] Test Windows Defender SmartScreen behavior
- [ ] Create installer (optional, using NSIS/Inno Setup)
- [ ] Document installation instructions

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

## File Structure After Build

```
app/
├── build/          (temporary build files)
├── dist/
│   └── MDI AutoLogin.exe  (your final executable)
├── build.spec      (PyInstaller configuration)
└── build.bat       (build script)
```

## Notes

- The executable is **portable** - no installation needed
- First run creates config/log files in `%LOCALAPPDATA%\MDI_AutoLogin\`
- Users can run it from anywhere (USB drive, network share, etc.)

