# app/net_events.py
import logging
import platform
import threading
from typing import Callable, List, Optional

log = logging.getLogger("mdi.net.events")
SYSTEM = platform.system()

_subscriber_bus = None
_bus_lock = threading.Lock()


class NetworkEventBus:
    """Simple pub/sub bus that wakes listeners when Wi-Fi state changes."""

    def __init__(self):
        self._subs: List[Callable[[str], None]] = []
        self._lock = threading.Lock()
        self._watcher = _create_watcher(self)
        if self._watcher:
            self._watcher.start()

    def subscribe(self, callback: Callable[[str], None]) -> Callable[[], None]:
        with self._lock:
            self._subs.append(callback)

        def _unsubscribe():
            with self._lock:
                if callback in self._subs:
                    self._subs.remove(callback)

        return _unsubscribe

    def publish(self, reason: str):
        with self._lock:
            targets = list(self._subs)
        for cb in targets:
            try:
                cb(reason)
            except Exception:
                log.exception("Network event subscriber failed")

    def poke(self, reason: str = "manual"):
        self.publish(reason)

    def shutdown(self):
        if self._watcher:
            self._watcher.stop()
            self._watcher = None


def _create_watcher(bus: NetworkEventBus):
    if SYSTEM == "Windows":
        return _WindowsWifiWatcher(bus)
    return None


def get_event_bus() -> NetworkEventBus:
    global _subscriber_bus
    if _subscriber_bus is None:
        with _bus_lock:
            if _subscriber_bus is None:
                _subscriber_bus = NetworkEventBus()
    return _subscriber_bus


# ---------- Windows Native Wi-Fi notifications ----------
if SYSTEM == "Windows":
    import ctypes
    from ctypes import POINTER, WINFUNCTYPE, Structure, c_byte, c_void_p
    from ctypes import wintypes

    wlanapi = ctypes.WinDLL("wlanapi.dll")
    WLAN_NOTIFICATION_SOURCE_NONE = 0x00000000
    WLAN_NOTIFICATION_SOURCE_ACM = 0x00000008
    WLAN_NOTIFICATION_ACM_CONNECTION_COMPLETE = 7
    WLAN_NOTIFICATION_ACM_DISCONNECTED = 10

    class GUID(Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", c_byte * 8),
        ]

    class WLAN_NOTIFICATION_DATA(Structure):
        _fields_ = [
            ("NotificationSource", wintypes.DWORD),
            ("NotificationCode", wintypes.DWORD),
            ("InterfaceGuid", GUID),
            ("dwDataSize", wintypes.DWORD),
            ("pData", c_void_p),
        ]

    WLAN_NOTIFICATION_CALLBACK = WINFUNCTYPE(None, POINTER(WLAN_NOTIFICATION_DATA), c_void_p)


class _WindowsWifiWatcher(threading.Thread):
    def __init__(self, bus: NetworkEventBus):
        super().__init__(name="wifi-events", daemon=True)
        self.bus = bus
        self._stop = threading.Event()
        self._callback = None
        self._handle = wintypes.HANDLE()

    def run(self):
        if SYSTEM != "Windows":
            return

        negotiated = wintypes.DWORD()
        rc = wlanapi.WlanOpenHandle(2, None, ctypes.byref(negotiated), ctypes.byref(self._handle))
        if rc != 0:
            log.warning("WlanOpenHandle failed (rc=%s)", rc)
            return

        self._callback = WLAN_NOTIFICATION_CALLBACK(self._handle_notification)
        rc = wlanapi.WlanRegisterNotification(
            self._handle,
            WLAN_NOTIFICATION_SOURCE_ACM,
            False,
            self._callback,
            None,
            None,
            None,
        )
        if rc != 0:
            log.warning("WlanRegisterNotification failed (rc=%s)", rc)
            wlanapi.WlanCloseHandle(self._handle, None)
            return

        log.info("Wi-Fi watcher started.")
        try:
            while not self._stop.wait(0.5):
                pass
        finally:
            wlanapi.WlanRegisterNotification(
                self._handle,
                WLAN_NOTIFICATION_SOURCE_NONE,
                False,
                None,
                None,
                None,
                None,
            )
            wlanapi.WlanCloseHandle(self._handle, None)
            log.info("Wi-Fi watcher stopped.")

    def stop(self):
        self._stop.set()

    def _handle_notification(self, data_ptr, _context):
        if not data_ptr:
            return
        data = data_ptr.contents
        if data.NotificationCode == WLAN_NOTIFICATION_ACM_CONNECTION_COMPLETE:
            self.bus.publish("connected")
        elif data.NotificationCode == WLAN_NOTIFICATION_ACM_DISCONNECTED:
            self.bus.publish("disconnected")