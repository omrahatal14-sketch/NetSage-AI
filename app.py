"""
NetSage AI - Root Application Entrypoint
Launches the Flask backend server from the backend package.
"""

import sys
import os

# Set working directory to project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.app import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
