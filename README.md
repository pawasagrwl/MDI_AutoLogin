# MDI AutoLogin

A lightweight Windows tray application that automatically logs you into the **MDI Wi-Fi captive portal** with no manual steps. It runs in the background, auto-detects the network, and handles login instantly.

---

## ✨ Features

* 🔑 Automatic login when connected to MDI Wi-Fi
* 🔒 Secure credential storage (Windows Credential Manager)
* 🖥️ Tray icon with control panel (start/stop, manual login, settings, logs, reset)
* ⚙️ Auto-start with Windows and start minimized option
* 📡 Live connection status and real-time logs
* 🧠 Smart retry and backoff with error detection (quota, devices, credentials, expiry)
* 🌙 Light/Dark theme support

---

## 📦 Installation

1. Download the latest release `.exe` from [Releases](../../releases).
2. Run it. On first launch, configure SSID, username, and password.
3. It will start minimized and log you in automatically whenever MDI Wi-Fi is available.

---

## 🛠 Development

### Running from Source

```bash
pip install -r requirements.txt
cd app
python app.py
```

**Logs location:**
`C:\Users\<YourName>\AppData\Local\MDI_AutoLogin\mdi_autologin.log`

### Building Executable

```bash
cd build
build.bat
```

The executable will be created in `app/dist/MDI AutoLogin.exe`

For detailed build instructions, see [Build Guide](docs/BUILD_GUIDE.md).

### Running Tests

```bash
cd app
pytest tests/
```

Or use the test runner:
```bash
cd app/tests
run_tests.bat
```

Tests cover:
- Configuration loading/saving
- Network detection logic
- Login response analysis
- Worker state management
- Startup registration

---

## 📁 Project Structure

```
mdi_auto_login_app/
├── app/          # Source code
│   ├── app.py    # Entry point
│   ├── config.py # Configuration management
│   ├── net.py    # Network detection & login
│   ├── startup.py # Windows/macOS startup handling
│   └── ui/       # User interface components
├── build/        # Build scripts and configuration
├── docs/         # Additional documentation
```

---

## 📝 Notes

* Credentials are stored securely in Windows Credential Manager.
* If login fails due to quota, session, or device limit, the app retries intelligently.
* Use **Manual login now** or **Reset** from the control panel if needed.
* Kill all instances:
  ```bash
  taskkill /IM "MDI AutoLogin.exe" /F
  ```

---

## 📚 Additional Documentation

- **[Build Guide](docs/BUILD_GUIDE.md)** - Detailed build instructions and troubleshooting
- **[Roadmap](docs/ROADMAP.md)** - Future plans and improvements

---

## License

See LICENSE file for details.
