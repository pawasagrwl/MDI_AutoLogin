# app.py
import logging
from config import setup_logger
from ui import run_app

if __name__ == "__main__":
    # Initialize rotating file logger before anything else
    setup_logger()
    # No basicConfig here; setup_logger already attaches handlers.
    run_app()
