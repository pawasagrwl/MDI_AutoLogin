# net.py
import platform
import re
import subprocess
import time
import logging
from typing import Any, Dict, List, Tuple

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
log = logging.getLogger("mdi.net")

_session = requests.Session()
_session.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AutoLogin",
        "Accept": "*/*",
        "Connection": "close",
    }
)

_PROBE_URL = "http://clients3.google.com/generate_204"
SYSTEM = platform.system()

if SYSTEM == "Windows":
    _si = subprocess.STARTUPINFO()
    _si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    _si.wShowWindow = subprocess.SW_HIDE
    _NO_WINDOW = subprocess.CREATE_NO_WINDOW
else:
    _si = None
    _NO_WINDOW = 0


def _run_cmd(cmd: List[str]) -> str:
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            startupinfo=_si,
            creationflags=_NO_WINDOW,
        ).stdout
    except Exception:
        return ""


def _probe():
    return _session.get(_PROBE_URL, timeout=3, verify=False, allow_redirects=True)


def _current_ssids_windows() -> List[str]:
    out = _run_cmd(["netsh", "wlan", "show", "interfaces"])
    blocks = re.split(r"\r?\n\s*Name\s*:\s*", out)
    ssids = []
    for block in blocks:
        if not block.strip():
            continue
        if not re.search(r"^\s*State\s*:\s*connected\b", block, re.I | re.M):
            continue
        m = re.search(r"^\s*SSID\s*:\s*(.+)$", block, re.I | re.M)
        if m:
            val = m.group(1).strip()
            if val and val.lower() != "not connected":
                ssids.append(val)
    return ssids


def _current_ssids_mac() -> List[str]:
    airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
    out = _run_cmd([airport, "-I"])
    m = re.search(r"^\s*SSID:\s*(.+)$", out, re.M)
    return [m.group(1).strip()] if m else []


def _current_ssids_linux() -> List[str]:
    out = _run_cmd(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"])
    ssids = []
    for line in out.splitlines():
        parts = line.split(":")
        if len(parts) == 2 and parts[0] == "yes" and parts[1]:
            ssids.append(parts[1])
    return ssids


def _current_ssids() -> List[str]:
    if SYSTEM == "Windows":
        return _current_ssids_windows()
    if SYSTEM == "Darwin":
        return _current_ssids_mac()
    return _current_ssids_linux()


def any_connected_ssid(ssid: str) -> bool:
    target = ssid.lower()
    for s in _current_ssids():
        if target in s.lower():
            return True
    return False


def _gateway_is_campus_windows() -> bool:
    out = _run_cmd(["ipconfig"])
    for gw in re.findall(r"Default Gateway[^\r\n]*:\s*([\d\.]+)", out, re.I):
        if gw.startswith("172.16."):
            return True
    return False


def _gateway_is_campus_mac() -> bool:
    out = _run_cmd(["netstat", "-rn"])
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "default" and parts[1].startswith("172.16."):
            return True
    return False


def _gateway_is_campus_linux() -> bool:
    out = _run_cmd(["ip", "route"])
    for line in out.splitlines():
        if line.startswith("default") and " via 172.16." in line:
            return True
    return False


def gateway_is_campus() -> bool:
    if SYSTEM == "Windows":
        return _gateway_is_campus_windows()
    if SYSTEM == "Darwin":
        return _gateway_is_campus_mac()
    return _gateway_is_campus_linux()


def target_network_available(cfg) -> bool:
    """
    True only when we can see the target SSID or the campus gateway.
    Prevents login attempts while Wi-Fi is off or on another network.
    """
    return any_connected_ssid(cfg["ssid"]) or gateway_is_campus()

def portal_intercept_present() -> bool:
    try:
        r = _probe()
        redirected = r.url != _PROBE_URL
        captive_markers = ("172.16." in r.url) or ("24online" in r.text.lower())
        return (r.status_code != 204) or redirected or captive_markers
    except Exception:
        return True


def connected_to_target(cfg) -> bool:
    return target_network_available(cfg) or portal_intercept_present()

def online_now() -> bool:
    try:
        r = _probe()
        return r.status_code == 204
    except Exception:
        return False


def send_login(cfg, username: str, password: str) -> bool:
    payload = {"mode": "191", "username": username, "password": password}
    try:
        r = _session.post(
            cfg["login_url"],
            data=payload,
            timeout=cfg["post_timeout"],
            verify=False,
            allow_redirects=True,
        )
        log.info("📨 Login POST sent (status %s).", r.status_code)
        return True
    except Exception as e:
        log.info("❌ Error sending login POST: %s", e)
        return False


def settle_until_online(max_s: float, step: float) -> bool:
    waited = 0.0
    while waited < max_s:
        if online_now():
            return True
        time.sleep(step)
        waited += step
    return False


def analyze_login_response(cfg, http_status: int, url: str, text: str) -> Tuple[str, str]:
    if 200 <= http_status < 400:
        patterns = cfg.get("login_error_patterns") or {}
        low = (text or "").lower()
        for code, rx in patterns.items():
            try:
                if re.search(rx, low, re.I | re.M):
                    return code, code.replace("_", " ").title()
            except re.error:
                pass
        if "success" in low or "logged in" in low:
            return "ok", "Login success"
        if "24online" in low or "172.16." in (url or ""):
            return "unknown", "Portal still intercepting"
        return "unknown", "Unrecognized response"
    else:
        return "unknown", f"HTTP {http_status}"


def login_with_diagnostics(cfg, username: str, password: str) -> Dict[str, Any]:
    payload = {"mode": "191", "username": username, "password": password}
    try:
        r = _session.post(
            cfg["login_url"],
            data=payload,
            timeout=cfg["post_timeout"],
            verify=False,
            allow_redirects=True,
        )
        code, text = analyze_login_response(cfg, r.status_code, r.url, r.text)
        ok = code == "ok"
        if code == "unknown":
            log.info("📝 Portal page (excerpt): %s | url=%s", _excerpt(r.text), r.url)
        return {"ok": ok, "http_status": r.status_code, "reason_code": code, "reason_text": text, "url": r.url}
    except Exception as e:
        log.info("❌ Error sending login POST: %s", e)
        return {"ok": False, "http_status": 0, "reason_code": "network_error", "reason_text": str(e), "url": ""}


def _excerpt(txt: str, n: int = 240) -> str:
    if not txt:
        return ""
    s = re.sub(r"\s+", " ", txt).strip()
    return (s[:n] + "…") if len(s) > n else s