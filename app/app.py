# app.py
import logging
import sys
# Ensure unicodedata is available early (required by idna/requests)
import unicodedata  # noqa: F401
from config import setup_logger, APP_NAME
from ui import run_app
from ui.messages import msg_info
from single_instance import enforce_single_instance

if __name__ == "__main__":
    # Initialize rotating file logger before anything else
    setup_logger()
    log = logging.getLogger("mdi.app")
    
    # Enforce single instance
    is_first, mutex_handle = enforce_single_instance()
    if not is_first:
        log.warning("Another instance is already running. Exiting.")
        msg_info(APP_NAME, "Another instance of MDI AutoLogin is already running.\n\nPlease use the existing instance from the system tray.")
        sys.exit(0)
    
    # Store mutex handle for cleanup (we'll release it in a try/finally)
    try:
        # No basicConfig here; setup_logger already attaches handlers.
        run_app()
    finally:
        # Release mutex on exit
        if mutex_handle:
            from single_instance import _release_mutex
            _release_mutex(mutex_handle)
            log.debug("Single-instance mutex released")
