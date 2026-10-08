"""
Start Script for Field Drug Testing Mobile Application
Runs both the OpenCV processing engine and the Mobile Web Interface on port 8000.
"""

import os
import sys
import socket
import uvicorn


def get_local_ip():
    """Gets the local LAN IP for accessing from a physical mobile device."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 8000

    print("=" * 65)
    print(" NARCO-SCAN FIELD MOBILE PROTOTYPE SYSTEM")
    print("=" * 65)
    print(" OpenCV Color Calibration & Reference Card Correction: ACTIVE")
    print(" HSV Range Colorimetric Reagent Classifier: ACTIVE")
    print(" SHA-256 Tamper-Evident Geolocation Chain-of-Custody: ACTIVE")
    print("-" * 65)
    print(f" -> Local Desktop Access:  http://localhost:{port}")
    print(f" -> Mobile Phone Wi-Fi:    http://{local_ip}:{port}")
    print("=" * 65)

    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    sys.path.insert(0, backend_dir)
    
    from main import app
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
