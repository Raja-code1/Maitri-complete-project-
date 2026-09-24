"""
MAITRI Cockpit & API Server Launcher
Run this file directly: python run_app.py
"""

import os
import sys
import uvicorn

# Ensure repository root is in sys.path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

if __name__ == "__main__":
    print("\n" + "=" * 75)
    print("  MAITRI COCKPIT HUD & JARVIS VOICE COMPANION — LAUNCHING")
    print("  Bharatiya Antariksh Station (BAS) | ISRO Standalone Edge System")
    print("=" * 75)
    print("  [WEB] Local Access  : http://localhost:8000")
    print("  [WEB] Network Access: http://0.0.0.0:8000  (team on same Wi-Fi)")
    print("  [DOC] API Swagger   : http://localhost:8000/docs")
    print("  Press Ctrl+C to stop the server")
    print("-" * 75 + "\n")

    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=False)
