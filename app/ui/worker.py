# ui/worker.py
import logging
import random
import threading
import time

from config import CONFIG_PATH, get_password, load_config
from net import (
    connected_to_target,
    login_with_diagnostics,
    online_now,
    portal_intercept_present,
    settle_until_online,
    target_network_available,  # new import
)
from net_events import get_event_bus

log = logging.getLogger("mdi.ui")


class AutoLoginWorker(threading.Thread):
    def __init__(self, tray_ref):
        super().__init__(daemon=True)
        self.tray_ref = tray_ref
        self.stop_event = threading.Event()
        self.wake_event = threading.Event()

        self.running = False
        self.last_online_state = None
        self.fail_count = 0
        self.cooldown_until = 0.0
        self.backoff_s = None
        self.last_post_ts = 0.0
        self._credentials_warned = False  # Only warn once about missing credentials

        self.cfg = load_config()
        self._cfg_mtime = self._config_mtime()
        self.username = self.cfg.get("username", "")
        self.password = get_password(self.username)
        self._net_bus = get_event_bus()
        self._unsubscribe = self._net_bus.subscribe(self._on_network_event)

    def _config_mtime(self) -> float:
        try:
            return CONFIG_PATH.stat().st_mtime
        except FileNotFoundError:
            return 0.0

    def _refresh_config_if_needed(self):
        mtime = self._config_mtime()
        if mtime != self._cfg_mtime:
            self.cfg = load_config()
            self._cfg_mtime = mtime
            self.username = self.cfg.get("username", "")
            self.password = get_password(self.username)
            # Reset warning flag if credentials are now available
            if self.username and self.password:
                self._credentials_warned = False

    def _log_once_per_state(self, now_online: bool, captive: bool):
        state = "online" if now_online else ("captive" if captive else "offline")
        if state != self.last_online_state:
            self.last_online_state = state
            if state == "online":
                log.info("✅ Online.")
            elif state == "captive":
                log.info("🛂 Captive portal detected.")
            else:
                log.info("📶 Not connected to target network yet.")

    def _apply_backoff_and_cooldown(self, cfg, fatal=False):
        retry_cfg = cfg.get("retry", {})
        if fatal:
            cooldown = float(retry_cfg.get("cooldown_on_fatal_s", 10))
            self.cooldown_until = time.time() + cooldown
            self.backoff_s = None
            self.fail_count = 0
            log.info("⏸️ Fatal portal response; pausing retries for %ss.", int(cooldown))
            return

        self.fail_count += 1
        if self.backoff_s is None:
            self.backoff_s = float(retry_cfg.get("backoff_initial_s", 2))
        else:
            self.backoff_s = min(self.backoff_s * 2, float(retry_cfg.get("backoff_max_s", 10)))

        max_consec = int(retry_cfg.get("max_consecutive", 3))
        if self.fail_count >= max_consec:
            cd = float(retry_cfg.get("backoff_max_s", 10))
            self.cooldown_until = time.time() + cd
            self.fail_count = 0
            self.backoff_s = None
            log.info("🧊 Too many consecutive failures; cooling down for %ss.", int(cd))

    def _wait_with_event(self, seconds: float):
        if seconds <= 0:
            return
        end = time.time() + seconds
        while not self.stop_event.is_set() and time.time() < end:
            remainder = end - time.time()
            wait_for = max(0.2, min(5.0, remainder))
            if self.wake_event.wait(wait_for):
                self.wake_event.clear()
                break

    def _on_network_event(self, reason: str):
        log.debug("Network event: %s", reason)
        self.backoff_s = None
        self.cooldown_until = 0.0
        self.wake_event.set()

    def run(self):
        self.tray_ref.update_tooltip(True)
        self.running = True

        while not self.stop_event.is_set():
            try:
                self._refresh_config_if_needed()
                cfg = self.cfg
                now = time.time()

                if self.cooldown_until and now < self.cooldown_until:
                    self._log_once_per_state(online_now(), portal_intercept_present())
                    self._wait_with_event(3.0)
                    continue

                on = online_now()
                capt = portal_intercept_present()
                on_target = target_network_available(cfg)

                self._log_once_per_state(on, capt if on_target else False)

                if capt and on_target and not on:
                    if not self.username or not self.password:
                        self.password = get_password(self.username)
                    if not self.username or not self.password:
                        # Only log once to avoid spam
                        if not self._credentials_warned:
                            log.warning("⚠️ No credentials configured. Please set username and password in Settings.")
                            self._credentials_warned = True
                        # Don't attempt login without credentials
                        self._wait_with_event(float(cfg.get("base_interval", 5)))
                        continue
                    else:
                        # Reset warning flag if credentials are now available
                        self._credentials_warned = False
                        if time.time() - self.last_post_ts >= float(cfg.get("post_grace_s", 6)):
                            self.last_post_ts = time.time()
                            diag = login_with_diagnostics(cfg, self.username, self.password)
                            self._wait_with_event(float(cfg.get("post_probe_delay_s", 1.5)))
                            settled = settle_until_online(cfg["settle_max"], cfg["settle_step"])
                            if settled:
                                log.info("🌐 Online confirmed after login.")
                                self.fail_count = 0
                                self.backoff_s = None
                                self.last_post_ts = time.time()
                                continue

                            reason = diag.get("reason_code", "unknown")
                            text = diag.get("reason_text", "Unknown")
                            log.info("🚫 Login not established: %s (%s)", reason, text)
                            if reason in {"quota_exceeded", "too_many_devices", "account_expired", "bad_credentials"}:
                                self._apply_backoff_and_cooldown(cfg, fatal=True)
                            else:
                                self._apply_backoff_and_cooldown(cfg, fatal=False)
                else:
                    self.fail_count = 0
                    self.backoff_s = None

            except Exception as e:
                log.info("⚠️ Worker loop error: %s", e)

            sleep_t = self.backoff_s if self.backoff_s else max(1.0, self.cfg["base_interval"] + random.uniform(-1, 1))
            self._wait_with_event(sleep_t)

        self.running = False
        if self._unsubscribe:
            self._unsubscribe()
        self.tray_ref.update_tooltip(False)

    def stop(self):
        self.stop_event.set()
        self.wake_event.set()