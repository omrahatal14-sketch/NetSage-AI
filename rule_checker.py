"""
NetSage AI - Root CLI Rule Checker Entrypoint
Delegates to backend.rule_checker
"""

import sys
import os

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.rule_checker import main

if __name__ == "__main__":
    main()
