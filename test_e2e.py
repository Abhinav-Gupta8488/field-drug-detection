"""
End-to-End Automated Verification Test
Tests that static frontend, sample images, color correction, classification,
and tamper verification are all fully operational.
"""

import sys
import os
import io
import json
import base64
from fastapi.testclient import TestClient

backend_dir = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_dir)

from main import app

client = TestClient(app)

def run_tests():
    print("[1] Testing API Health...")
    r = client.get("/api/health")
    assert r.status_code == 200, f"Healthcheck failed: {r.status_code}"
    print("    PASSED:", r.json())

    print("[2] Testing Sample Cases...")
    r = client.get("/api/sample-cases")
    assert r.status_code == 200
    cases = r.json().get("cases", [])
    assert len(cases) == 6, f"Expected 6 cases, got {len(cases)}"
    print(f"    PASSED: {len(cases)} sample cases verified.")

    print("[3] Testing Static Mobile App HTML Delivery...")
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    print("    PASSED: Mobile web frontend served at root '/'")

    print("[4] Testing Full Pipeline Analysis (Case 2: Scott on Cocaine)...")
    img_resp = client.get("/api/sample-image/case_02_scott_cocaine.jpg")
    assert img_resp.status_code == 200
    img_bytes = img_resp.content

    data = {
        "reagent_type": "SCOTT",
        "latitude": 34.052234,
        "longitude": -118.243685,
        "altitude": 85.0,
        "accuracy": 4.1,
        "location_description": "Port of Los Angeles Container Inspection",
        "officer_badge": "PORT-CUSTOMS-412",
        "agency": "Maritime Interdiction Unit",
        "kit_batch_lot": "LOT-SC-2026-B1",
        "ref_card_roi": json.dumps([60, 150, 220, 140]),
        "vial_roi": json.dumps([400, 185, 120, 135])
    }
    files = {"image": ("test_capture.jpg", img_bytes, "image/jpeg")}

    res = client.post("/api/analyze", data=data, files=files)
    assert res.status_code == 200, f"Analyze failed: {res.text}"
    result = res.json()
    
    top = result["classification"]["top_match"]
    print(f"    Match Result: {top['substance']} ({top['confidence_percent']}%)")
    print(f"    Measured HSV: H={result['hsv_metrics']['hue']} deg, S={result['hsv_metrics']['saturation']}%, V={result['hsv_metrics']['value']}%")
    print(f"    Optical Gains: Blue={result['calibration_metrics']['channel_gains']['blue_gain']}, Red={result['calibration_metrics']['channel_gains']['red_gain']}")
    print(f"    Raw SHA-256:  {result['manifest']['cryptographic_components']['raw_image_sha256']}")
    print(f"    Merkle Root:  {result['manifest']['chain_of_custody_hash']}")

    print("[5] Testing Tamper Verification...")
    manifest = result["manifest"]
    v_res = client.post("/api/verify", data={"manifest_json": json.dumps(manifest)})
    assert v_res.status_code == 200
    v_json = v_res.json()
    assert v_json["is_authentic"] is True
    print("    PASSED: Original manifest authentic check.")

    # Tampering test
    tampered = json.loads(json.dumps(manifest))
    tampered["evidence_data"]["gps"]["latitude"] += 0.005
    v_tampered = client.post("/api/verify", data={"manifest_json": json.dumps(tampered)})
    assert v_tampered.status_code == 200
    vt_json = v_tampered.json()
    assert vt_json["is_authentic"] is False
    print("    PASSED: GPS coordinate alteration (+0.005 deg) was correctly detected as TAMPERED!")

    print("\n================ ALL 5 END-TO-END TESTS PASSED ================")

if __name__ == "__main__":
    run_tests()
