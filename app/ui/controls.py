# ui/controls.py
import sys, os, webbrowser, logging, time
import tkinter as tk
from tkinter import ttk
from .settings_window import SettingsWindow

from config import (
    APP_NAME, APP_VERSION, DEVELOPER_NAME, DEFAULT_SSID, LOG_PATH, CONFIG_PATH, SERVICE_NAME,
    load_config, save_config, get_password, set_password,
)
from net import (
    connected_to_target, online_now, portal_intercept_present,
    settle_until_online, login_with_diagnostics, target_network_available
)
from .theme import apply_theme, ui_bg
from .messages import msg_info, msg_error, ask_yes_no

log = logging.getLogger("mdi.ui")


class ToggleSwitch(tk.Canvas):
    def __init__(self, parent, state=False, command=None):
        self._bg = self._resolve_bg(parent)
        super().__init__(parent, width=50, height=24, highlightthickness=0, bg=self._bg)
        self.command = command
        self.state = bool(state)
        self.knob_pos = 24 if self.state else 2
        self._draw_base()
        self.bind("<Button-1>", self._on_click)

    def _draw_base(self):
        self.delete("all")
        color = "#4caf50" if self.state else "#b0b0b0"
        self.configure(bg=self._bg)
        self.body_left = self.create_oval(2, 2, 24, 22, fill=color, outline=color)
        self.body_right = self.create_oval(26, 2, 48, 22, fill=color, outline=color)
        self.body_rect = self.create_rectangle(13, 2, 37, 22, fill=color, outline=color)
        self.knob = self.create_oval(self.knob_pos, 2, self.knob_pos + 20, 22, fill="#ffffff", outline="#ffffff")

    def _animate(self, target):
        step = 2 if target > self.knob_pos else -2

        def _step():
            if (step > 0 and self.knob_pos >= target) or (step < 0 and self.knob_pos <= target):
                self.knob_pos = target
                self.coords(self.knob, self.knob_pos, 2, self.knob_pos + 20, 22)
                return
            self.knob_pos += step
            self.coords(self.knob, self.knob_pos, 2, self.knob_pos + 20, 22)
            self.after(10, _step)

        _step()

    def _on_click(self, _event):
        self.state = not self.state
        color = "#4caf50" if self.state else "#b0b0b0"
        for item in (self.body_left, self.body_rect, self.body_right):
            self.itemconfig(item, fill=color, outline=color)
        self._animate(24 if self.state else 2)
        if self.command:
            self.command(self.state)

    def set(self, state):
        state = bool(state)
        if self.state == state:
            return
        self.state = state
        self.knob_pos = 24 if self.state else 2
        self._draw_base()

    def _resolve_bg(self, widget):
        try:
            return widget.cget("background")
        except tk.TclError:
            try:
                style = ttk.Style()
                lookup = style.lookup(widget.winfo_class(), "background")
                if lookup:
                    return lookup
                return widget.master.cget("background")
            except Exception:
                return "#f0f0f0"


# ----- Control Panel -----
class ControlPanel:
    def __init__(self, parent_root, tray_app):
        self.tray_app = tray_app
        self.root = tk.Toplevel(parent_root)
        self.root.title(f"{APP_NAME} v{APP_VERSION} — Control Panel")
        self.root.geometry("820x500")
        self.root.minsize(700, 420)

        self.cfg = load_config()
        apply_theme(self.root, self.cfg.get("dark_mode", False))

        # Disclaimer notice at the top
        disclaimer_frame = ttk.Frame(self.root, padding=(12, 8, 12, 8))
        disclaimer_frame.pack(fill="x", pady=(0, 4))
        disclaimer_text = (
            "⚠️ DISCLAIMER: The developer is not responsible for any consequences of using this app. "
            "While this app uses no external resources from your PC and the source code is open, "
            "you are solely responsible for using and sharing this application."
        )
        disclaimer_label = tk.Label(
            disclaimer_frame,
            text=disclaimer_text,
            font=("Segoe UI", 8),
            fg="#d32f2f" if not self.cfg.get("dark_mode", False) else "#ff6b6b",
            bg=self.root.cget("background"),
            wraplength=780,
            justify="left",
            anchor="w"
        )
        disclaimer_label.pack(fill="x", anchor="w")

        top = ttk.Frame(self.root, padding=(12,10,12,6)); top.pack(fill="x")
        left = ttk.Frame(top); left.pack(side="left", fill="x", expand=True)

        # Single compact status row (badges)
        self.badges = ttk.Frame(left); self.badges.pack(side="top", fill="x", expand=True)
        self.lbl_net   = tk.Label(self.badges, font=("Segoe UI", 9), padx=8, pady=3, bd=0, relief="flat")
        self.lbl_user  = tk.Label(self.badges, font=("Segoe UI", 9), padx=8, pady=3, bd=0, relief="flat")
        self.lbl_auto  = tk.Label(self.badges, font=("Segoe UI", 9), padx=8, pady=3, bd=0, relief="flat")  # NEW
        self.lbl_state = tk.Label(self.badges, font=("Segoe UI", 9), padx=8, pady=3, bd=0, relief="flat")

        self.lbl_net.pack(side="left", padx=(0,6))
        self.lbl_user.pack(side="left", padx=(0,6))
        self.lbl_auto.pack(side="left", padx=(0,6))   # NEW
        self.lbl_state.pack(side="left", padx=(0,6))

        # # Legacy status line (kept)
        # self.status_label = tk.Label(left,
        #                              text=self._status_text(),
        #                              font=("Segoe UI", 9),
        #                              padx=10, pady=4,
        #                              bd=0, relief="flat",
        #                              anchor="w", justify="left")
        # self.status_label.pack(side="left", padx=(0,8))

        top_right = tk.Frame(top, bg=self.root.cget("background"))
        top_right.pack(side="right", padx=(12, 0))
        ttk.Label(top_right, text="Dark mode").pack(side="left", padx=(0, 6))
        self.dark_switch = ToggleSwitch(top_right, state=self.cfg.get("dark_mode", False), command=self._on_dark_switch)
        self.dark_switch.pack(side="left", padx=(0, 12))
        ttk.Button(top_right, text="Quit", command=self._quit_app).pack(side="left")

        row = ttk.Frame(self.root, padding=(12,0,12,8)); row.pack(fill="x")
        self.btn_toggle = ttk.Button(row, text=self._toggle_text(), command=self._toggle_autologin)
        self.btn_toggle.pack(side="left", padx=(0,8))
        ttk.Button(row, text="Manual login now", command=self._manual_login).pack(side="left", padx=(0,8))
        ttk.Button(row, text="Settings…", command=self._open_settings).pack(side="left", padx=(0,8))

        util = ttk.Frame(row)
        util.pack(side="right")

        ttk.Button(util, text="Open log", command=self._open_log).pack(side="right")

        self.reset_menu = tk.Menu(self.root, tearoff=0)
        self.reset_menu.add_command(label="Reset log", command=self.tray_app.reset_log_file)
        self.reset_menu.add_command(label="Reset settings", command=self.tray_app.reset_settings)
        self.reset_menu.add_command(label="Reset app", command=self.tray_app.reset_app)
        self.reset_button = ttk.Menubutton(util, text="Reset ▾", direction="below")
        self.reset_button.pack(side="right", padx=(0, 10))
        self.reset_button["menu"] = self.reset_menu

        mid = ttk.Frame(self.root, padding=(12,4,12,12)); mid.pack(fill="both", expand=True)
        self.txt = tk.Text(mid, wrap="none", undo=False, font=("Consolas", 10), borderwidth=1, relief="solid")
        if self.cfg.get("dark_mode", False):
            self.txt.configure(bg="#0f0f0f", fg="#eaeaea", insertbackground="#eaeaea")
        else:
            self.txt.configure(bg="white", fg="#111111", insertbackground="black")
        self.scroll_y = ttk.Scrollbar(mid, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=self.scroll_y.set)
        self.txt.pack(side="left", fill="both", expand=True)
        self.scroll_y.pack(side="right", fill="y")

        # Footer with attribution
        footer = ttk.Frame(self.root, padding=(12, 4, 12, 8))
        footer.pack(fill="x", side="bottom")
        footer_label = tk.Label(
            footer,
            text=f"Made by {DEVELOPER_NAME}",
            font=("Segoe UI", 8),
            fg="#666666" if not self.cfg.get("dark_mode", False) else "#999999",
            bg=self.root.cget("background")
        )
        footer_label.pack(side="left", anchor="w")

        self._refresh_status()
        self._refresh_log()
        self._log_timer = None
        self._schedule_log_refresh()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---- helpers / UI reactions ----
    def _status_text(self):
        running = self.tray_app.worker is not None and self.tray_app.worker.running
        return f"SSID: {self.cfg.get('ssid', DEFAULT_SSID)}   |   Username: {self.cfg.get('username','') or '(not set)'}   |   Auto-login: {'Running' if running else 'Stopped'}"
    def _toggle_text(self):
        running = self.tray_app.worker is not None and self.tray_app.worker.running
        return "Stop auto-login" if running else "Start auto-login"

    def _set_status_color(self, color: str, text: str = None):
        # Directly colors the State badge; text ignored here (legacy compat)
        try:
            bg = color
            fg = "#ffffff"
            if bg.lower() in ("#ffa000", "#999999", "systembuttonface"):
                fg = "#000000"
            self.lbl_state.configure(bg=bg, fg=fg)
        except Exception:
            pass


    def _set_badge(self, label: tk.Label, text: str, bg: str):
        try:
            fg = "#ffffff"
            if bg.lower() in ("#ffa000", "#ffffaa", "#e0e0e0", "systembuttonface"):
                fg = "#000000"
            label.configure(text=text, bg=bg, fg=fg)
        except Exception:
            pass

    # ---- button handlers ----
    def _toggle_autologin(self):
        if self.tray_app.worker and self.tray_app.worker.running:
            self.tray_app.stop_worker()
        else:
            self.tray_app.start_worker()
        self._refresh_status()

    def _manual_login(self):
        cfg = load_config()
        user = cfg.get("username", ""); pwd = get_password(user)
        if not user or not pwd:
            msg_info(APP_NAME, "Set username/password in Settings first.")
            return
        if online_now():
            self._set_status_color("#28a745")
            msg_info(APP_NAME, "Already online.")
            return
        if not target_network_available(cfg):
            self._set_status_color("#FFA000")
            msg_info(APP_NAME, f"Not on {cfg['ssid']} yet.")
            return
        diag = login_with_diagnostics(cfg, user, pwd)
        time.sleep(float(cfg.get("post_probe_delay_s", 1.5)))
        settled = settle_until_online(cfg["settle_max"], cfg["settle_step"])
        if settled or diag.get("ok"):
            self._set_status_color("#28a745" if settled else "#FFA000")
            msg_info(APP_NAME, "Login successful." + (" Online." if settled else " Waiting for portal…"))
        else:
            reason = diag.get("reason_code","unknown")
            text = diag.get("reason_text","Unknown")
            if reason == "already_logged_in":
                self._set_status_color("#28a745")
                msg_info(APP_NAME, "Portal reports you are already logged in.")
            elif reason in {"quota_exceeded","too_many_devices","account_expired","bad_credentials"}:
                self._set_status_color("#E53935")
                msg_error(APP_NAME, f"Login blocked: {text}")
            else:
                self._set_status_color("#FFA000")
                msg_info(APP_NAME, f"Login not finalized: {text}")
        self._refresh_log()

    def _open_settings(self):
        SettingsWindow(self.root, first_run=False)
        self.cfg = load_config()
        self._refresh_status()
        if self.cfg.get("dark_mode", False):
            self.txt.configure(bg="#0f0f0f", fg="#eaeaea", insertbackground="#eaeaea")
        else:
            self.txt.configure(bg="white", fg="#111111", insertbackground="black")
        self.dark_switch.set(self.cfg.get("dark_mode", False))

    def _open_log(self):
        try:
            webbrowser.open(LOG_PATH.as_uri())
        except Exception:
            os.startfile(str(LOG_PATH))

    def _on_dark_switch(self, state: bool):
        self.cfg["dark_mode"] = bool(state)
        save_config(self.cfg)
        apply_theme(self.root, self.cfg["dark_mode"])

        if self.cfg["dark_mode"]:
            self.txt.configure(bg="#0f0f0f", fg="#eaeaea", insertbackground="#eaeaea")
        else:
            self.txt.configure(bg="white", fg="#111111", insertbackground="black")
        self.dark_switch.set(self.cfg.get("dark_mode", False))

    def _quit_app(self):
        self.tray_app.stop_worker()
        self._cancel_log_refresh()
        try: self.root.destroy()
        except Exception: pass
        try: self.tray_app.icon.stop()
        except Exception: pass

    def _refresh_status(self):
        online = online_now()
        captive = portal_intercept_present() or connected_to_target(self.cfg)

        if online:
            color = "#28a745"; state = "Online"
        elif captive:
            color = "#FFA000"; state = "Captive portal"
        else:
            color = "#999999"; state = "Not connected"

        # Badges
        ssid = self.cfg.get('ssid', DEFAULT_SSID)
        user_txt = self.cfg.get('username','') or "(not set)"
        running = self.tray_app.worker is not None and self.tray_app.worker.running

        self._set_badge(self.lbl_net,   f"SSID: {ssid}", "#3b82f6" if (captive or online) else "#999999")
        self._set_badge(self.lbl_user,  f"User: {user_txt}", "#e0e0e0")
        self._set_badge(self.lbl_auto,  f"Auto-login: {'Running' if running else 'Stopped'}", "#10b981" if running else "#9e9e9e")
        self._set_badge(self.lbl_state, f"{state}", color)

        try:
            self.btn_toggle.config(text=self._toggle_text())
        except Exception:
            pass

    def _refresh_log(self):
        try:
            txt = LOG_PATH.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            txt = "(log not available yet)"
        lines = txt.splitlines()
        txt = "\n".join(lines[-400:])
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", txt)
        self.txt.see("end")

    def _schedule_log_refresh(self):
        self._log_timer = self.root.after(2000, self._on_log_tick)

    def _on_log_tick(self):
        try:
            self._refresh_log()
            self._refresh_status()
        finally:
            if self.root.winfo_exists():
                self._schedule_log_refresh()

    def _cancel_log_refresh(self):
        try:
            if self._log_timer:
                self.root.after_cancel(self._log_timer)
        except Exception:
            pass

    def _on_close(self):
        self._cancel_log_refresh()
        try: self.root.destroy()
        except Exception: pass
        