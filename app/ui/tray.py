# ui/tray.py
import threading, logging, os, webbrowser, time
import tkinter as tk
from PIL import Image, ImageDraw
import pystray

from config import APP_NAME, LOG_PATH, CONFIG_PATH, SERVICE_NAME, load_config, get_password
from net import (
    target_network_available,
    settle_until_online,
    login_with_diagnostics,
    online_now,
)
from .controls import ControlPanel
from .settings_window import SettingsWindow
from .messages import ask_yes_no, msg_info, msg_error
from .worker import AutoLoginWorker
import keyring

log = logging.getLogger("mdi.ui")

class TrayApp:
    def __init__(self, tk_root):
        self.tk_root = tk_root
        self.panel = None
        self.icon = pystray.Icon("mdi_tray")
        self.worker = None
        self.icon.icon = self._build_icon()
        self.icon.title = APP_NAME
        self.update_tooltip(False)
        self.icon.menu = pystray.Menu(
            pystray.MenuItem("Open Control Panel", self.open_control_panel, default=True),
            pystray.MenuItem("Start auto-login", self.start_worker),
            pystray.MenuItem("Stop auto-login", self.stop_worker),
            pystray.MenuItem("Manual login now", self.manual_login),
            pystray.MenuItem("Settings…", self.open_settings),
            pystray.MenuItem("Open log", self.open_log),
            pystray.MenuItem("Reset log", lambda _: self.reset_log_file()),
            pystray.MenuItem("Reset settings", lambda _: self.reset_settings()),
            pystray.MenuItem("Reset app", lambda _: self.reset_app()),
            pystray.MenuItem("Quit", self.quit)
        )

    def _build_icon(self):
        img = Image.new("RGBA", (24, 24), (0,0,0,0))
        d = ImageDraw.Draw(img)
        d.arc([2,10,22,22], 200, 340, fill=(255,255,255,255), width=2)
        d.arc([5,12,19,22], 200, 340, fill=(255,255,255,255), width=2)
        d.arc([8,14,16,22], 200, 340, fill=(0,180,255,255), width=2)
        d.ellipse([10,18,14,22], fill=(0,180,255,255))
        return img

    def update_tooltip(self, running: bool):
        self.icon.title = f"{APP_NAME} — {'Running' if running else 'Idle'}"

    # UI actions on Tk thread
    def open_control_panel(self, _=None):
        def _show_panel():
            if getattr(self, "panel", None) and self.panel.root.winfo_exists():
                try:
                    self.panel.root.deiconify()
                    self.panel.root.lift()
                    self.panel.root.focus_force()
                except Exception:
                    pass
                return
            self.panel = ControlPanel(self.tk_root, self)
        self.tk_root.after(0, _show_panel)

    def start_worker(self, _=None):
        if self.worker and self.worker.running:
            return
        self.worker = AutoLoginWorker(self)
        self.worker.start()
        log.info("▶️ Auto-login started.")
        self.update_tooltip(True)

    def stop_worker(self, _=None):
        if self.worker:
            self.worker.stop()
            self.worker.join(timeout=2.0)
            self.worker = None
        log.info("⏹️ Auto-login stopped.")
        self.update_tooltip(False)

    def manual_login(self, _=None):
        cfg = load_config()
        user = cfg.get("username",""); pwd = get_password(user)
        if not user or not pwd:
            msg_info(APP_NAME, "Please set username/password in Settings first.")
            return
        if online_now():
            msg_info(APP_NAME, "Already online.")
            return
        if not target_network_available(cfg):
            msg_info(APP_NAME, f"Not on {cfg['ssid']} yet.")
            return

        diag = login_with_diagnostics(cfg, user, pwd)
        time.sleep(float(cfg.get("post_probe_delay_s", 1.5)))
        settled = settle_until_online(cfg["settle_max"], cfg["settle_step"])
        if settled or diag.get("ok"):
            msg_info(APP_NAME, "Login successful." + (" Online." if settled else " Waiting for portal…"))
            return

        reason = diag.get("reason_code", "unknown")
        text = diag.get("reason_text", "Unknown")
        if reason == "already_logged_in":
            msg_info(APP_NAME, "Portal reports you are already logged in.")
        else:
            msg_error(APP_NAME, f"Login failed: {text}")

    def open_settings(self, _=None):
        def _open():
            SettingsWindow(self.tk_root, first_run=False)
        self.tk_root.after(0, _open)

    def open_log(self, _=None):
        try:
            webbrowser.open(LOG_PATH.as_uri())
        except Exception:
            os.startfile(str(LOG_PATH))

    def _confirm(self, title: str, text: str) -> bool:
        return ask_yes_no(title, text)

    def reset_log_file(self):
        if not self._confirm(APP_NAME, "Clear the log file?"):
            return
        try:
            LOG_PATH.write_text("", encoding="utf-8")
            log.info("🗑️ Log file cleared.")
            msg_info(APP_NAME, "Log file cleared.")
        except Exception as e:
            log.exception("Failed to clear log")
            msg_error(APP_NAME, f"Could not clear log: {e}")

    def reset_settings(self):
        if not self._confirm(APP_NAME, "Reset settings to defaults? This will remove saved username and settings."):
            return
        try:
            try:
                if CONFIG_PATH.exists(): CONFIG_PATH.unlink()
            except Exception:
                pass
            try:
                cfg = load_config()
                if cfg.get("username"):
                    keyring.delete_password(SERVICE_NAME, cfg.get("username"))
            except Exception:
                pass
            from config import save_config  # import local to avoid confusion
            save_config(load_config())
            log.info("⚙️ Settings reset to defaults.")
            msg_info(APP_NAME, "Settings reset to defaults.")
        except Exception as e:
            log.exception("Failed to reset settings")
            msg_error(APP_NAME, f"Could not reset settings: {e}")

    def reset_app(self):
        if not self._confirm(APP_NAME, "Reset app (clear settings, log, and stored credentials)?"):
            return
        try:
            self.stop_worker()
            try:
                if CONFIG_PATH.exists(): CONFIG_PATH.unlink()
                if LOG_PATH.exists(): LOG_PATH.unlink()
            except Exception:
                pass
            try:
                cfg = load_config()
                if cfg.get("username"):
                    keyring.delete_password(SERVICE_NAME, cfg.get("username"))
            except Exception:
                pass
            from config import save_config
            save_config(load_config())
            log.info("🔄 App reset performed.")
            msg_info(APP_NAME, "App reset complete. Restart the app to apply changes.")
        except Exception as e:
            log.exception("Failed to reset app")
            msg_error(APP_NAME, f"Could not reset app: {e}")

    def quit(self, _=None):
        self.stop_worker()
        try:
            self.icon.stop()
        except Exception:
            pass
        def _stop_tk():
            try: self.tk_root.quit()
            except Exception: pass
        self.tk_root.after(0, _stop_tk)

    def run(self):
        cfg = load_config()
        first = cfg.get("first_run", True) or not cfg.get("username")

        if first:
            win = SettingsWindow(self.tk_root, first_run=True)
            self.tk_root.wait_window(win.root)
            # Re-read config because first run may have updated flags
            cfg = load_config()
            # Show the Control Panel once on literal first run
            self.open_control_panel()
        else:
            # Respect minimize-on-start preference
            if not cfg.get("minimize_on_start", True):
                self.open_control_panel()

        # Start tray icon thread
        t = threading.Thread(target=self.icon.run, daemon=True)
        t.start()

        try:
            cfg = load_config()
            if cfg.get("auto_start_on_launch", True):
                self.start_worker()
        except Exception:
            log.exception("Failed to start auto-login at launch.")

# Entrypoint kept identical to old ui.py API
def run_app():
    root = tk.Tk()
    root.withdraw()
    app = TrayApp(root)
    try:
        app.run()
        root.mainloop()
    finally:
        try: app.icon.stop()
        except Exception:
            pass
