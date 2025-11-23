# Development Checklist

Use this checklist whenever you make code changes or add new features to ensure nothing is missed.

## 🔧 Code Changes

- [ ] **Code Review**
  - [ ] Code follows existing style and patterns
  - [ ] No hardcoded values (use config/constants)
  - [ ] Error handling is appropriate
  - [ ] Logging is added where needed

- [ ] **Testing**
  - [ ] Test the new feature/change manually
  - [ ] Test existing features still work (regression testing)
  - [ ] Test edge cases and error scenarios
  - [ ] Test on clean system (if possible)
  - [ ] Run unit tests (if applicable): `pytest app/tests/`

- [ ] **UI/UX**
  - [ ] UI changes work in both light and dark mode
  - [ ] Text is readable and properly formatted
  - [ ] Buttons/controls are accessible and functional
  - [ ] No UI elements overlap or are cut off
  - [ ] Window sizes are appropriate

## 📦 Build & Distribution

- [ ] **Update Version**
  - [ ] Update `APP_VERSION` in `app/config.py`
  - [ ] Update version in `build/build.spec` (if needed)
  - [ ] Consider if this is a major/minor/patch release

- [ ] **Build Locally**
  - [ ] Run `build/build.bat` to create executable
  - [ ] Verify build completes without errors
  - [ ] Test the built `.exe` file:
    - [ ] App starts correctly
    - [ ] New feature works in the built version
    - [ ] Existing features still work
    - [ ] No runtime errors or missing modules
    - [ ] Single-instance enforcement works
    - [ ] Auto-start functionality works (if changed)

- [ ] **Dependencies**
  - [ ] Check if new dependencies were added
  - [ ] Update `app/requirements.txt` if needed
  - [ ] Update `build/requirements-build.txt` if needed
  - [ ] Add to `hiddenimports` in `build/build.spec` if PyInstaller misses it

## 📝 Documentation

- [ ] **Code Documentation**
  - [ ] Add docstrings to new functions/classes
  - [ ] Update comments for complex logic
  - [ ] Update README.md if user-facing features changed

- [ ] **User Documentation**
  - [ ] Update README.md with new features/changes
  - [ ] Update any relevant docs in `docs/` folder
  - [ ] Add screenshots if UI changed significantly

## 🔍 Pre-Release Checks

- [ ] **Git & Version Control**
  - [ ] All changes are committed
  - [ ] Commit messages are clear and descriptive
  - [ ] No sensitive data (passwords, API keys) in code
  - [ ] `.gitignore` is up to date

- [ ] **Release Notes**
  - [ ] Prepare release notes/changelog
  - [ ] List new features
  - [ ] List bug fixes
  - [ ] List breaking changes (if any)
  - [ ] Note any known issues

- [ ] **Final Testing**
  - [ ] Test on a different machine (if possible)
  - [ ] Test with fresh install (no existing config)
  - [ ] Test upgrade from previous version
  - [ ] Verify auto-start works after upgrade
  - [ ] Check that old instances are properly terminated

## 🚀 Release Process

- [ ] **GitHub Release**
  - [ ] Push all commits to repository
  - [ ] Create and push version tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
  - [ ] Or use release script: `release.bat` or `release.ps1`
  - [ ] Verify GitHub Actions build succeeds
  - [ ] Download and test the GitHub Actions build
  - [ ] Verify release notes are correct on GitHub

- [ ] **Post-Release**
  - [ ] Monitor for any issues reported by users
  - [ ] Update roadmap if needed
  - [ ] Archive/backup the release build locally

## 🐛 Common Issues to Check

- [ ] **PyInstaller Issues**
  - [ ] No `ModuleNotFoundError` in built executable
  - [ ] Tkinter/Tcl files are included
  - [ ] All required DLLs are bundled
  - [ ] Executable runs without Python installed

- [ ] **Windows-Specific**
  - [ ] UAC elevation works correctly
  - [ ] Scheduled Task creation/removal works
  - [ ] Registry operations work (if applicable)
  - [ ] Credential storage (keyring) works

- [ ] **Functionality**
  - [ ] Auto-login still works
  - [ ] Manual login works
  - [ ] Settings save/load correctly
  - [ ] Log file is created and updated
  - [ ] Tray icon appears and works
  - [ ] Control panel opens/closes correctly

## 📋 Feature-Specific Checks

### If Adding New UI Elements
- [ ] Works in both light and dark themes
- [ ] Properly sized and positioned
- [ ] Accessible via keyboard (if applicable)
- [ ] Tooltips/help text added (if needed)

### If Changing Network/Login Logic
- [ ] Test on actual MDI network
- [ ] Test error handling (no network, wrong credentials, etc.)
- [ ] Test retry logic
- [ ] Test with different network conditions

### If Changing Auto-Start
- [ ] Test enabling auto-start
- [ ] Test disabling auto-start
- [ ] Test with admin privileges
- [ ] Test without admin privileges (fallback)
- [ ] Verify Scheduled Task is created correctly
- [ ] Verify it runs on Windows startup

### If Adding New Dependencies
- [ ] Add to `app/requirements.txt`
- [ ] Add to `build/requirements-build.txt`
- [ ] Add to `hiddenimports` in `build/build.spec` if needed
- [ ] Test that it works in built executable
- [ ] Check license compatibility

## 🎯 Quick Checklist (Minimal)

For small changes, at minimum:
- [ ] Test the change works
- [ ] Test existing features still work
- [ ] Build and test the `.exe`
- [ ] Update version if needed
- [ ] Commit and push

---

**Note:** This checklist is comprehensive. For small bug fixes, you may not need to check every item. Use your judgment, but always test the built executable before releasing.

