# ui/theme.py
import tkinter as tk
from tkinter import ttk

def _sanitize_color(c: str) -> str:
    if not c or str(c).startswith("-"):
        return "SystemButtonFace"
    return str(c)

def ui_bg(root: tk.Misc) -> str:
    st = ttk.Style(root)
    return _sanitize_color(st.lookup('TFrame', 'background') or root.cget('bg'))

def apply_theme(root: tk.Misc, dark: bool):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    if dark:
        bg = "#121212"; fg = "#eaeaea"
        btn_bg = "#1e1e1e"; btn_active = "#2a2a2a"; btn_fg = fg
        entry_bg = "#1a1a1a"; entry_fg = fg
    else:
        bg = "#f6f6f6"; fg = "#111111"
        btn_bg = "#ffffff"; btn_active = "#e8e8e8"; btn_fg = "#111111"
        entry_bg = "#ffffff"; entry_fg = "#111111"

    style.configure(".", background=bg, foreground=fg)
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background=btn_bg, foreground=btn_fg, padding=(10,6))
    style.map("TButton", background=[("active", btn_active), ("pressed", btn_active)])
    style.configure("TEntry", fieldbackground=entry_bg, foreground=entry_fg)
    style.configure("TCheckbutton", background=bg, foreground=fg)
    try:
        root.configure(bg=bg)
    except Exception:
        pass
