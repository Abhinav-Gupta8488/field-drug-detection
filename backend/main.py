"""
FastAPI Server for Field Drug Testing Mobile Application
Provides OpenCV color correction, HSV chemical classification, and SHA-256 tamper-evident records.
"""

import os
import io
import json
import base64
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from typing import Optional, List, Dict, Any

from color_correction import run_full_color_calibration, STANDARD_REFERENCE_CARD
from reagent_classifier import (
    extract_hsv_features,
    classify_drug_reaction,
    REAGENT_PROFILES
)
from tamper_evidence import (
    generate_tamper_evident_record,
    verify_tamper_evident_record,
    compute_sha256_bytes,
    sanitize_for_json
)
import generate_samples


app = FastAPI(
    title="Field Narcotics Colorimetric Classifier API",
    description="Mobile field drug testing API with OpenCV calibration and SHA-256 tamper-evident records",
    version="1.0.0"
)

# Enable CORS for mobile web and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_data")
os.makedirs(SAMPLE_DIR, exist_ok=True)

# Generate samples if not already present
if not os.path.exists(os.path.join(SAMPLE_DIR, "case_01_marquis_mdma.jpg")):
    generate_samples.generate_all_sample_cases()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "field-drug-testing-backend", "opencv": cv2.__version__}


@app.get("/api/reagents")
def get_reagents():
    """Returns list of all available reagents and descriptions."""
    results = []
    for code, info in REAGENT_PROFILES.items():
        results.append({
            "code": code,
            "name": info["name"],
            "description": info["description"],
            "substances_detected": [r["substance"] for r in info["reactions"]],
        })
    return {"reagents": results}


@app.get("/api/sample-cases")
def get_sample_cases():
    """Returns pre-loaded realistic field test cases for rapid demonstration."""
    cases = [
        {
            "id": "case_01_marquis_mdma.jpg",
            "title": "MDMA (Ecstasy) Test",
            "reagent": "MARQUIS",
            "expected_substance": "MDMA / Ecstasy",
            "expected_schedule": "Schedule I",
            "lighting": "Warm Indoor Tungsten (~3000K, Yellow cast)",
            "reaction_color": "Dark Purple to Pitch Black",
            "gps": {
                "latitude": 37.774929,
                "longitude": -122.419416,
                "altitude": 16.2,
                "accuracy": 3.8,
                "location_description": "Tenderloin Field Interdiction Zone, San Francisco"
            },
            "ref_card_roi": [60, 150, 220, 140],
            "vial_roi": [400, 185, 120, 135]
        },
        {
            "id": "case_02_scott_cocaine.jpg",
            "title": "Cocaine HCl Cobalt Test",
            "reagent": "SCOTT",
            "expected_substance": "Cocaine Hydrochloride",
            "expected_schedule": "Schedule II",
            "lighting": "Outdoor Overcast / Cool Shade (~7000K, Blue cast)",
            "reaction_color": "Royal Turquoise Blue Precipitate",
            "gps": {
                "latitude": 34.052234,
                "longitude": -118.243685,
                "altitude": 85.0,
                "accuracy": 4.1,
                "location_description": "Port of Los Angeles Container Inspection"
            },
            "ref_card_roi": [60, 150, 220, 140],
            "vial_roi": [400, 185, 120, 135]
        },
        {
            "id": "case_03_ehrlich_lsd.jpg",
            "title": "LSD Blotter Indole Test",
            "reagent": "EHRLICH",
            "expected_substance": "LSD (Lysergic acid diethylamide)",
            "expected_schedule": "Schedule I",
            "lighting": "Commercial Fluorescent (~4000K, Green tint)",
            "reaction_color": "Vivid Purple to Magenta",
            "gps": {
                "latitude": 40.712776,
                "longitude": -74.005974,
                "altitude": 10.5,
                "accuracy": 2.9,
                "location_description": "Manhattan Transit Hub Security Point"
            },
            "ref_card_roi": [60, 150, 220, 140],
            "vial_roi": [400, 185, 120, 135]
        },
        {
            "id": "case_04_marquis_meth.jpg",
            "title": "Methamphetamine Test",
            "reagent": "MARQUIS",
            "expected_substance": "Amphetamine / Methamphetamine",
            "expected_schedule": "Schedule II",
            "lighting": "Night Field Sodium Lighting (~2700K)",
            "reaction_color": "Vivid Orange to Red-Brown",
            "gps": {
                "latitude": 32.715738,
                "longitude": -117.161085,
                "altitude": 22.0,
                "accuracy": 5.0,
                "location_description": "San Ysidro Border Checkpoint"
            },
            "ref_card_roi": [60, 150, 220, 140],
            "vial_roi": [400, 185, 120, 135]
        },
        {
            "id": "case_05_mecke_heroin.jpg",
            "title": "Heroin Opiate Screen",
            "reagent": "MECKE",
            "expected_substance": "Heroin / Morphine",
            "expected_schedule": "Schedule I / II",
            "lighting": "Standard Daylight D65 (~5500K)",
            "reaction_color": "Dark Forest Green to Teal",
            "gps": {
                "latitude": 47.606209,
                "longitude": -122.332071,
                "altitude": 45.0,
                "accuracy": 3.4,
                "location_description": "Seattle Harbor Interdiction Terminal"
            },
            "ref_card_roi": [60, 150, 220, 140],
            "vial_roi": [400, 185, 120, 135]
        },
        {
            "id": "case_06_marquis_sugar.jpg",
            "title": "Negative Control (Sugar)",
            "reagent": "MARQUIS",
            "expected_substance": "Negative / Sugar (Sucrose)",
            "expected_schedule": "Non-Controlled",
            "lighting": "Diffused Ambient Light",
            "reaction_color": "Pale Straw / No Reaction",
            "gps": {
                "latitude": 39.739236,
                "longitude": -104.990251,
                "altitude": 1600.0,
                "accuracy": 3.0,
                "location_description": "Denver Forensic Field Unit"
            },
            "ref_card_roi": [60, 150, 220, 140],
            "vial_roi": [400, 185, 120, 135]
        }
    ]
    return {"cases": cases}


@app.get("/api/sample-image/{filename}")
def get_sample_image(filename: str):
    """Serves sample image files."""
    filepath = os.path.join(SAMPLE_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Sample image not found")
    return FileResponse(filepath, media_type="image/jpeg")


@app.get("/api/reference-card-template")
def get_reference_card_template():
    """Returns downloadable / printable standard reference color card template."""
    filepath = os.path.join(SAMPLE_DIR, "forensic_reference_card_template.png")
    if not os.path.exists(filepath):
        generate_samples.generate_all_sample_cases()
    return FileResponse(filepath, media_type="image/png", filename="forensic_reference_card_template.png")


def create_annotated_preview(
    image: np.ndarray,
    ref_card_roi: Optional[List[int]],
    vial_roi: Optional[List[int]],
    top_match: Optional[Dict[str, Any]],
    hsv_metrics: Dict[str, Any]
) -> str:
    """Draws HUD targeting boxes, labels, and color swatches on the calibrated image."""
    annotated = image.copy()
    h, w = annotated.shape[:2]
    
    # Draw Reference Card ROI box (Cyan)
    if ref_card_roi and len(ref_card_roi) == 4:
        rx, ry, rw, rh = ref_card_roi
        cv2.rectangle(annotated, (rx, ry), (rx + rw, ry + rh), (255, 230, 0), 2)
        cv2.putText(annotated, "COLOR REF CARD", (rx, max(18, ry - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 230, 0), 2)
        
    # Draw Vial ROI box (Emerald Green)
    if vial_roi and len(vial_roi) == 4:
        vx, vy, vw, vh = vial_roi
        cv2.rectangle(annotated, (vx, vy), (vx + vw, vy + vh), (0, 235, 140), 2)
        cv2.putText(annotated, "REACTION VIAL", (vx, max(18, vy - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 235, 140), 2)
        
    # Add forensic HUD banner at the bottom
    overlay = annotated.copy()
    cv2.rectangle(overlay, (0, h - 55), (w, h), (15, 20, 25), -1)
    cv2.addWeighted(overlay, 0.82, annotated, 0.18, 0, annotated)
    
    # Draw measured color chip swatch
    chip_x, chip_y = 15, h - 45
    chip_w, chip_h = 32, 32
    rep_rgb = hsv_metrics.get("representative_rgb", [0, 0, 0])
    rep_bgr = (rep_rgb[2], rep_rgb[1], rep_rgb[0])
    cv2.rectangle(annotated, (chip_x, chip_y), (chip_x + chip_w, chip_y + chip_h), rep_bgr, -1)
    cv2.rectangle(annotated, (chip_x, chip_y), (chip_x + chip_w, chip_y + chip_h), (255, 255, 255), 1)
    
    # Text info
    substance_str = top_match.get("substance", "Presumptive Screen") if top_match else "Analyzed"
    conf_str = f"{top_match.get('confidence_percent', 0)}%" if top_match else ""
    hsv_str = f"H:{hsv_metrics.get('hue')} S:{hsv_metrics.get('saturation')}% V:{hsv_metrics.get('value')}%"
    
    cv2.putText(annotated, f"{substance_str} [{conf_str}]", (55, h - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(annotated, hsv_str, (55, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (160, 200, 220), 1)
    
    # Encode as JPEG and base64
    _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return base64.b64encode(buf.tobytes()).decode("utf-8")


@app.post("/api/analyze")
async def analyze_drug_test(
    image: UploadFile = File(...),
    reagent_type: str = Form("MARQUIS"),
    latitude: float = Form(0.0),
    longitude: float = Form(0.0),
    altitude: Optional[float] = Form(None),
    accuracy: Optional[float] = Form(5.0),
    location_description: Optional[str] = Form("Field Mobile Position"),
    officer_badge: Optional[str] = Form("OFFICER-721"),
    agency: Optional[str] = Form("Field Forensics Task Force"),
    kit_batch_lot: Optional[str] = Form("LOT-2026-M4"),
    ref_card_roi: Optional[str] = Form(None),
    vial_roi: Optional[str] = Form(None),
):
    """
    Core analysis endpoint:
    1. Ingests raw photo
    2. Applies OpenCV color correction using reference card
    3. Extracts HSV features and classifies reaction color
    4. Generates SHA-256 tamper-evident chain-of-custody manifest
    """
    raw_bytes = await image.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Empty image uploaded")
        
    # Decode image with OpenCV
    nparr = np.frombuffer(raw_bytes, np.uint8)
    cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if cv_img is None:
        raise HTTPException(status_code=400, detail="Unable to decode image format")
        
    # Parse ROI coordinates if provided as JSON
    parsed_ref_roi = None
    if ref_card_roi:
        try:
            parsed_ref_roi = json.loads(ref_card_roi)
        except Exception:
            parsed_ref_roi = None
            
    parsed_vial_roi = None
    if vial_roi:
        try:
            parsed_vial_roi = json.loads(vial_roi)
        except Exception:
            parsed_vial_roi = None
            
    # Step 1: Run OpenCV Color Correction Pipeline
    corrected_img, vial_crop, calib_metrics = run_full_color_calibration(
        cv_img, ref_card_roi=parsed_ref_roi, vial_roi=parsed_vial_roi
    )
    
    # Step 2: Encode calibrated image
    _, calib_enc = cv2.imencode(".jpg", corrected_img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    calib_bytes = calib_enc.tobytes()
    calib_base64 = base64.b64encode(calib_bytes).decode("utf-8")
    
    # Encode raw image base64 for side-by-side comparison
    raw_base64 = base64.b64encode(raw_bytes).decode("utf-8")
    
    # Step 3: HSV Feature Extraction & Reagent Classification
    hsv_metrics = extract_hsv_features(vial_crop)
    classification = classify_drug_reaction(reagent_type, hsv_metrics)
    
    # Step 4: Generate Annotated HUD image
    annotated_base64 = create_annotated_preview(
        corrected_img,
        ref_card_roi=calib_metrics.get("reference_card_bbox"),
        vial_roi=calib_metrics.get("vial_roi"),
        top_match=classification.get("top_match"),
        hsv_metrics=hsv_metrics
    )
    
    # Step 5: Construct GPS and Operator payloads
    gps_data = {
        "latitude": latitude,
        "longitude": longitude,
        "altitude": altitude,
        "accuracy": accuracy,
        "location_description": location_description,
    }
    
    operator_meta = {
        "officer_badge": officer_badge,
        "agency": agency,
        "kit_batch_lot": kit_batch_lot,
        "reagent_type": reagent_type.upper(),
    }
    
    # Step 6: Generate Tamper-Evident SHA-256 Manifest
    manifest = generate_tamper_evident_record(
        raw_image_bytes=raw_bytes,
        calibrated_image_bytes=calib_bytes,
        gps_data=gps_data,
        classification_result=classification,
        operator_metadata=operator_meta
    )
    
    return sanitize_for_json({
        "status": "success",
        "manifest": manifest,
        "classification": classification,
        "hsv_metrics": hsv_metrics,
        "calibration_metrics": calib_metrics,
        "images": {
            "calibrated_base64": f"data:image/jpeg;base64,{calib_base64}",
            "raw_base64": f"data:image/jpeg;base64,{raw_base64}",
            "annotated_base64": f"data:image/jpeg;base64,{annotated_base64}",
        },
        "cryptographic_summary": {
            "record_id": manifest["record_id"],
            "chain_of_custody_hash": manifest["chain_of_custody_hash"],
            "raw_image_sha256": manifest["cryptographic_components"]["raw_image_sha256"],
            "gps_metadata_sha256": manifest["cryptographic_components"]["gps_metadata_sha256"],
            "integrity_sealed": True,
        }
    })


class VerifyRequestModel:
    pass


@app.post("/api/verify")
async def verify_evidence(
    manifest_json: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    """
    Tamper verification endpoint:
    Validates cryptographic hashes against claimed manifest.
    Detects if GPS, pixels, badge, or test results were altered.
    """
    try:
        manifest = json.loads(manifest_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid manifest JSON: {str(e)}")
        
    raw_bytes = None
    if image is not None:
        raw_bytes = await image.read()
        
    verification = verify_tamper_evident_record(manifest, raw_image_bytes=raw_bytes)
    return sanitize_for_json(verification)


# Mount built mobile frontend
dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(dist_dir):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    import socket

    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    local_ip = get_local_ip()
    port = 8000

    print("=" * 65)
    print(" NARCO-SCAN FIELD MOBILE APPLICATION & API SERVER")
    print("=" * 65)
    print(" [✓] OpenCV Color Correction: ACTIVE")
    print(" [✓] HSV Chemical Classifier: ACTIVE")
    print(" [✓] SHA-256 Tamper-Evident Records: ACTIVE")
    print(" [✓] Mobile Web Prototype: ACTIVE")
    print("-" * 65)
    print(f" -> Local Desktop Access:  http://localhost:{port}")
    print(f" -> Mobile Phone (Wi-Fi):  http://{local_ip}:{port}")
    print("=" * 65)
    print(" Press Ctrl+C to stop the server.\n")

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
