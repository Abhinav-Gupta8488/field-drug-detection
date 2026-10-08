"""
Test script to verify color correction, HSV classification, and SHA-256 tamper evidence.
"""

import os
import cv2
import json
from color_correction import run_full_color_calibration
from reagent_classifier import extract_hsv_features, classify_drug_reaction
from tamper_evidence import generate_tamper_evident_record, verify_tamper_evident_record


def test_marquis_mdma():
    img_path = os.path.join(os.path.dirname(__file__), "sample_data", "case_01_marquis_mdma.jpg")
    img = cv2.imread(img_path)
    assert img is not None, "Failed to load sample image"
    
    with open(img_path, "rb") as f:
        raw_bytes = f.read()
        
    ref_card_roi = [60, 150, 220, 140]
    vial_roi = [400, 185, 120, 135]
    
    # 1. Color correction
    corrected_img, vial_crop, calib_metrics = run_full_color_calibration(
        img, ref_card_roi=ref_card_roi, vial_roi=vial_roi
    )
    
    # Encode calibrated image
    _, calib_enc = cv2.imencode(".jpg", corrected_img)
    calib_bytes = calib_enc.tobytes()
    
    # 2. HSV Feature Extraction & Reagent Classification
    hsv_feat = extract_hsv_features(vial_crop)
    classification = classify_drug_reaction("MARQUIS", hsv_feat)
    
    # 3. Cryptographic Tamper-Evident Record
    gps = {
        "latitude": 37.774929,
        "longitude": -122.419416,
        "altitude": 16.2,
        "accuracy": 3.8,
        "location_description": "Tenderloin Field Checkpoint, SF"
    }
    
    manifest = generate_tamper_evident_record(
        raw_image_bytes=raw_bytes,
        calibrated_image_bytes=calib_bytes,
        gps_data=gps,
        classification_result=classification,
        operator_metadata={
            "officer_badge": "SFPD-NARCO-902",
            "agency": "Narcotics Task Force",
            "kit_batch_lot": "LOT-MQ-2026-X4",
            "reagent_type": "MARQUIS"
        }
    )
    
    # 4. Verify authentic record
    verif = verify_tamper_evident_record(manifest, raw_image_bytes=raw_bytes, calibrated_image_bytes=calib_bytes)
    assert verif["is_authentic"] is True, f"Verification failed: {verif}"
    
    # 5. Test tampering detection (simulate altering GPS latitude by 0.0001 deg)
    tampered_manifest = json.loads(json.dumps(manifest))
    tampered_manifest["evidence_data"]["gps"]["latitude"] += 0.0001
    tampered_verif = verify_tamper_evident_record(tampered_manifest, raw_image_bytes=raw_bytes, calibrated_image_bytes=calib_bytes)
    assert tampered_verif["is_authentic"] is False, "Tampering was NOT detected!"
    assert len(tampered_verif["discrepancies"]) > 0
    
    print("\n--- TEST PIPELINE SUCCESSFUL ---")
    print(f"Top Match: {classification['top_match']['substance']} ({classification['top_match']['confidence_percent']}%)")
    print(f"Measured HSV: H={hsv_feat['hue']} deg, S={hsv_feat['saturation']}%, V={hsv_feat['value']}%")
    print(f"Calibration Method: {calib_metrics['method']}")
    print(f"Raw Image SHA-256: {manifest['cryptographic_components']['raw_image_sha256']}")
    print(f"GPS Canonical Hash: {manifest['cryptographic_components']['gps_metadata_sha256']}")
    print(f"Chain-of-Custody Root: {manifest['chain_of_custody_hash']}")
    print(f"Tamper Detection Verification: PASSED (Altered GPS correctly triggered: {tampered_verif['discrepancies'][0]['error']})")


if __name__ == "__main__":
    test_marquis_mdma()
