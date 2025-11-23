# ui/settings_window.py
import logging
import os
import sys
import tkinter as tk
from tkinter import ttk

from config import (
    APP_NAME,
    APP_VERSION,
    DEVELOPER_NAME,
    DEFAULT_SSID,
    get_password,
    is_autostart_enabled,
    load_config,
    save_config,
    set_autostart,
    set_password,
)
import startup
from .messages import ask_yes_no, msg_error, msg_info
from .theme import apply_theme

log = logging.getLogger("mdi.settings")


class SettingsWindow:
    def __init__(self, parent_root, first_run=False):
        self.first_run = first_run
        self.root = tk.Toplevel(parent_root)
        self.root.title(f"{APP_NAME} v{APP_VERSION} — {'Welcome' if first_run else 'Settings'}")
        self.root.geometry("420x400")
        self.root.resizable(False, False)

        cfg = load_config()
        apply_theme(self.root, cfg.get("dark_mode", False))

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
            fg="#d32f2f" if not cfg.get("dark_mode", False) else "#ff6b6b",
            bg=self.root.cget("background"),
            wraplength=380,
            justify="left",
            anchor="w"
        )
        disclaimer_label.pack(fill="x", anchor="w")

        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill="both", expand=True)
        frm.grid_columnconfigure(1, weight=1)

        ttk.Label(frm, text="Wi-Fi SSID:").grid(row=0, column=0, sticky="w")
        self.ent_ssid = ttk.Entry(frm, width=38)
        self.ent_ssid.insert(0, cfg.get("ssid", DEFAULT_SSID))
        self.ent_ssid.grid(row=0, column=1, sticky="we")

        ttk.Label(frm, text="Login URL:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.ent_url = ttk.Entry(frm, width=38)
        self.ent_url.insert(0, cfg.get("login_url", "https://172.16.16.16/24online/servlet/E24onlineHTTPClient"))
        self.ent_url.grid(row=1, column=1, sticky="we", pady=(8, 0))

        ttk.Label(frm, text="Username:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.ent_user = ttk.Entry(frm, width=38)
        self.ent_user.insert(0, cfg.get("username", ""))
        self.ent_user.grid(row=2, column=1, sticky="we", pady=(8, 0))

        ttk.Label(frm, text="Password:").grid(row=3, column=0, sticky="w", pady=(8, 0))
        row = ttk.Frame(frm)
        row.grid(row=3, column=1, sticky="we", pady=(8, 0))
        self.ent_pwd = ttk.Entry(row, width=30, show="•")
        self.ent_pwd.insert(0, get_password(cfg.get("username", "")))
        self.ent_pwd.pack(side="left", fill="x", expand=True)
        self._pw_visible = False

        def toggle_pw():
            self._pw_visible = not self._pw_visible
            self.ent_pwd.configure(show="" if self._pw_visible else "•")
            btn_toggle.config(text="Hide" if self._pw_visible else "Show")

        btn_toggle = ttk.Button(row, text="Show", width=6, command=toggle_pw)
        btn_toggle.pack(side="left", padx=(6, 0))

        self._dim_entry(self.ent_ssid)
        self._dim_entry(self.ent_url)

        autostart_default = cfg.get("auto_start_on_launch", True) or is_autostart_enabled()
        self.auto_start_var = tk.BooleanVar(value=autostart_default)
        chk_autostart = ttk.Checkbutton(frm, text="Start auto-login with Windows/macOS", variable=self.auto_start_var)
        chk_autostart.grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.minimize_on_start_var = tk.BooleanVar(value=cfg.get("minimize_on_start", True))
        chk_minimize = ttk.Checkbutton(frm, text="Start minimized to tray", variable=self.minimize_on_start_var)
        chk_minimize.grid(row=6, column=0, columnspan=2, sticky="w", pady=(6, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=7, column=0, columnspan=2, pady=12)
        ttk.Button(btns, text="Save", command=self.on_save).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Cancel", command=self.on_cancel).pack(side="left")

        # Footer with attribution
        footer = ttk.Frame(self.root, padding=(12, 4, 12, 8))
        footer.pack(fill="x", side="bottom")
        footer_label = tk.Label(
            footer,
            text=f"Made by {DEVELOPER_NAME}",
            font=("Segoe UI", 8),
            fg="#666666" if not cfg.get("dark_mode", False) else "#999999",
            bg=self.root.cget("background")
        )
        footer_label.pack(side="left", anchor="w")

    def on_cancel(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    # Faux-disabled styling helpers
    def _dim_style_name(self) -> str:
        dark = load_config().get("dark_mode", False)
        return "DimDark.TEntry" if dark else "DimLight.TEntry"

    def _ensure_dim_styles(self):
        style = ttk.Style(self.root)
        style.configure("DimLight.TEntry", foreground="#777777", fieldbackground="#eeeeee")
        style.configure("DimDark.TEntry", foreground="#9aa0a6", fieldbackground="#1a1a1a")

    def _dim_entry(self, entry: ttk.Entry):
        self._ensure_dim_styles()
        entry._initial_text = entry.get()
        entry._is_dimmed = True
        try:
            entry.configure(style=self._dim_style_name())
        except tk.TclError:
            pass

        def _activate(_):
            if getattr(entry, "_is_dimmed", False):
                entry._is_dimmed = False
                try:
                    entry.configure(style="TEntry")
                except tk.TclError:
                    pass
                entry.after(0, lambda: (entry.focus_set(), entry.selection_range(0, "end")))

        def _maybe_redim(_):
            text = entry.get()
            if text == getattr(entry, "_initial_text", "") or not text.strip():
                entry._is_dimmed = True
                try:
                    entry.configure(style=self._dim_style_name())
                except tk.TclError:
                    pass

        entry.bind("<FocusIn>", _activate, add="+")
        entry.bind("<Button-1>", _activate, add="+")
        entry.bind("<FocusOut>", _maybe_redim, add="+")
        self._dimmed_entries = getattr(self, "_dimmed_entries", [])
        self._dimmed_entries.append(entry)

    def on_save(self):
        ssid = self.ent_ssid.get().strip() or DEFAULT_SSID
        user = self.ent_user.get().strip()
        pwd = self.ent_pwd.get()
        url = self.ent_url.get().strip() or "https://172.16.16.16/24online/servlet/E24online/servlet/E24onlineHTTPClient"

        if not user or not pwd:
            msg_error(APP_NAME, "Please enter username and password.")
            return

        cfg = load_config()
        cfg.update(
            {
                "ssid": ssid,
                "username": user,
                "login_url": url,
                "first_run": False,
                "auto_start_on_launch": bool(self.auto_start_var.get()),
                "minimize_on_start": bool(self.minimize_on_start_var.get()),
            }
        )

        save_config(cfg)
        set_password(user, pwd)
        exe = startup.current_executable()
        resume_target = exe if getattr(sys, "frozen", False) else None

        if cfg["auto_start_on_launch"]:
            prompt = (
                "Administrator permission is required to update the Start-with-Windows task.\n\n"
                "After you click Yes, Windows will show a UAC prompt—choose Yes there as well."
            )
            if not startup.is_admin():
                if ask_yes_no(APP_NAME, prompt):
                    if startup.relaunch_as_admin(resume_target=resume_target):
                        self.on_cancel()
                        return
                    else:
                        msg_error(APP_NAME, "Could not request elevation. Start-with-Windows will fall back to the Run key.")
                        set_autostart(True, exe)
                else:
                    set_autostart(True, exe)
            else:
                # Already admin - try to create Scheduled Task first
                if not startup.enable_startup(exe, prefer_task=True):
                    # If task creation failed, fall back to Run key
                    if not set_autostart(True, exe):
                        msg_error(APP_NAME, "Could not enable start with Windows.")
        else:
            # Disable autostart - try to remove both task and Run key
            prompt = (
                "Administrator permission is required to fully remove the Start-with-Windows task.\n\n"
                "After you click Yes, Windows will show a UAC prompt—choose Yes there as well."
            )
            if not startup.is_admin():
                # Try to remove Run key first (doesn't need admin)
                from startup import disable_startup
                disable_startup()
                # Check if task exists by trying to query it
                import subprocess
                try:
                    result = subprocess.run(['schtasks', '/Query', '/TN', 'MDI AutoLogin'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        # Task exists, need admin to remove it
                        if ask_yes_no(APP_NAME, prompt):
                            if startup.relaunch_as_admin(resume_target=resume_target, flag="--disable-autostart"):
                                self.on_cancel()
                                return
                        # User declined or elevation failed - keep checkbox enabled
                        cfg["auto_start_on_launch"] = True
                        save_config(cfg)
                        self.auto_start_var.set(True)
                except Exception:
                    pass  # Couldn't check, assume it's removed
            else:
                # Already admin - can remove both
                if not startup.disable_startup():
                    msg_error(APP_NAME, "Could not disable start with Windows.")
                    cfg["auto_start_on_launch"] = True
                    save_config(cfg)
                    self.auto_start_var.set(True)

        log.info("💾 Settings saved.")
        msg_info(APP_NAME, "Settings saved.")
        self.on_cancel()