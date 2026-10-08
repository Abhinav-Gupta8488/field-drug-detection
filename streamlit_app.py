"""
NARCO-SCAN FIELD: Streamlit Cloud Native Edition
Field Narcotics Colorimetric Classifier with OpenCV Color Correction & SHA-256 Tamper Evident Records.
"""

import sys
import os
import json
import base64
import cv2
import numpy as np
import streamlit as st

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from color_correction import run_full_color_calibration
from reagent_classifier import extract_hsv_features, classify_drug_reaction, REAGENT_PROFILES
from tamper_evidence import generate_tamper_evident_record, verify_tamper_evident_record, sanitize_for_json
import generate_samples


# Page Configuration
st.set_page_config(
    page_title="NARCO-SCAN FIELD | Presumptive Drug Testing",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Tactical Forensic CSS
st.markdown("""
<style>
    .main {
        background-color: #020617;
        color: #f8fafc;
    }
    .stMetric {
        background-color: #0f172a;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #1e293b;
    }
    .forensic-badge {
        padding: 4px 8px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "backend", "sample_data")
if not os.path.exists(os.path.join(SAMPLE_DIR, "case_01_marquis_mdma.jpg")):
    generate_samples.generate_all_sample_cases()


# Sidebar: Telemetry & Kit Configuration
st.sidebar.title("🛡️ NARCO-SCAN FIELD")
st.sidebar.caption("Forensic Mobile Presumptive Testing Engine")

reagent_options = list(REAGENT_PROFILES.keys())
selected_reagent = st.sidebar.selectbox(
    "🧪 Select Reagent Kit",
    reagent_options,
    format_func=lambda r: f"{REAGENT_PROFILES[r]['name']}"
)
st.sidebar.info(REAGENT_PROFILES[selected_reagent]["description"])

with st.sidebar.expander("📍 Officer & GPS Telemetry", expanded=True):
    officer_badge = st.text_input("Officer Badge #", value="SFPD-NARCO-902")
    agency = st.text_input("Agency / Unit", value="Narcotics Task Force")
    kit_lot = st.text_input("Kit Batch Lot", value="LOT-MQ-2026-X4")
    
    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat = st.number_input("Latitude", value=37.774929, format="%.6f")
    with col_lon:
        lon = st.number_input("Longitude", value=-122.419416, format="%.6f")
    alt = st.number_input("Altitude (m)", value=16.2, format="%.1f")
    acc = st.number_input("Accuracy (m)", value=3.8, format="%.1f")


# Main Dashboard Header
st.title("🔬 Field Narcotics Colorimetric Analyzer")
st.markdown("""
Captures test kit photo with **standardized reference color card**, applies **OpenCV color constancy calibration**, 
classifies reaction chromophore in **HSV color space**, and seals **SHA-256 tamper-evident chain of custody**.
""")

# Input Source Selector
input_source = st.radio(
    "Select Image Input Mode:",
    ["📷 Phone Camera Input", "📂 Upload Image File", "🧪 Load Realistic Field Preset"],
    horizontal=True
)

raw_image_bytes = None
ref_roi_override = None
vial_roi_override = None

if input_source == "📷 Phone Camera Input":
    cam_file = st.camera_input("Take a photo of the test kit with reference card:")
    if cam_file:
        raw_image_bytes = cam_file.getvalue()

elif input_source == "📂 Upload Image File":
    uploaded_file = st.file_uploader("Upload kit photo from gallery (JPEG/PNG):", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        raw_image_bytes = uploaded_file.getvalue()

else:
    preset_choice = st.selectbox(
        "Select Verified Field Case:",
        [
            "Case 1: Marquis with MDMA (Warm Tungsten ~3000K Lighting)",
            "Case 2: Scott with Cocaine HCl (Outdoor Overcast / Cool Shade)",
            "Case 3: Ehrlich with LSD Blotter (Commercial Fluorescent)",
            "Case 4: Marquis with Methamphetamine (Night Sodium Lamp)",
            "Case 5: Mecke with Heroin (Standard Daylight D65)",
            "Case 6: Negative Control / Sugar (Ambient Office Light)",
        ]
    )
    
    preset_files = {
        "Case 1": ("case_01_marquis_mdma.jpg", "MARQUIS", [60, 150, 220, 140], [400, 185, 120, 135]),
        "Case 2": ("case_02_scott_cocaine.jpg", "SCOTT", [60, 150, 220, 140], [400, 185, 120, 135]),
        "Case 3": ("case_03_ehrlich_lsd.jpg", "EHRLICH", [60, 150, 220, 140], [400, 185, 120, 135]),
        "Case 4": ("case_04_marquis_meth.jpg", "MARQUIS", [60, 150, 220, 140], [400, 185, 120, 135]),
        "Case 5": ("case_05_mecke_heroin.jpg", "MECKE", [60, 150, 220, 140], [400, 185, 120, 135]),
        "Case 6": ("case_06_marquis_sugar.jpg", "MARQUIS", [60, 150, 220, 140], [400, 185, 120, 135]),
    }
    
    key = preset_choice.split(":")[0]
    filename, preset_reagent, ref_roi_override, vial_roi_override = preset_files[key]
    
    preset_path = os.path.join(SAMPLE_DIR, filename)
    if os.path.exists(preset_path):
        with open(preset_path, "rb") as f:
            raw_image_bytes = f.read()
        selected_reagent = preset_reagent


# Process Pipeline if image loaded
if raw_image_bytes:
    nparr = np.frombuffer(raw_image_bytes, np.uint8)
    cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if cv_img is None:
        st.error("Error decoding image. Please try a different photo.")
    else:
        st.divider()

        # Target ROI Controls
        with st.expander("🎯 Target Alignment Bounding Boxes (Optional Adjustment)", expanded=False):
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.caption("Reference Color Card [X, Y, Width, Height]")
                rx = st.slider("Card X", 0, cv_img.shape[1], ref_roi_override[0] if ref_roi_override else 60)
                ry = st.slider("Card Y", 0, cv_img.shape[0], ref_roi_override[1] if ref_roi_override else 150)
                rw = st.slider("Card Width", 20, 350, ref_roi_override[2] if ref_roi_override else 220)
                rh = st.slider("Card Height", 20, 250, ref_roi_override[3] if ref_roi_override else 140)
                ref_roi_override = [rx, ry, rw, rh]
                
            with col_r2:
                st.caption("Reaction Vial / Well [X, Y, Width, Height]")
                vx = st.slider("Vial X", 0, cv_img.shape[1], vial_roi_override[0] if vial_roi_override else 400)
                vy = st.slider("Vial Y", 0, cv_img.shape[0], vial_roi_override[1] if vial_roi_override else 185)
                vw = st.slider("Vial Width", 20, 250, vial_roi_override[2] if vial_roi_override else 120)
                vh = st.slider("Vial Height", 20, 250, vial_roi_override[3] if vial_roi_override else 135)
                vial_roi_override = [vx, vy, vw, vh]

        # Step 1: Run OpenCV Color Correction Pipeline
        corrected_img, vial_crop, calib_metrics = run_full_color_calibration(
            cv_img, ref_card_roi=ref_roi_override, vial_roi=vial_roi_override
        )
        
        _, calib_enc = cv2.imencode(".jpg", corrected_img, [cv2.IMWRITE_JPEG_QUALITY, 92])
        calib_bytes = calib_enc.tobytes()

        # Step 2: HSV Extraction & Reagent Classification
        hsv_metrics = extract_hsv_features(vial_crop)
        classification = classify_drug_reaction(selected_reagent, hsv_metrics)
        top_match = classification["top_match"]

        # Step 3: SHA-256 Tamper-Evident Record Generation
        gps_data = {
            "latitude": lat,
            "longitude": lon,
            "altitude": alt,
            "accuracy": acc,
            "location_description": "Field Coordinate Position",
        }
        operator_meta = {
            "officer_badge": officer_badge,
            "agency": agency,
            "kit_batch_lot": kit_lot,
            "reagent_type": selected_reagent,
        }
        manifest = generate_tamper_evident_record(
            raw_image_bytes=raw_image_bytes,
            calibrated_image_bytes=calib_bytes,
            gps_data=gps_data,
            classification_result=classification,
            operator_metadata=operator_meta
        )

        # Tabs layout for Results
        tab_analysis, tab_optical, tab_evidence, tab_tamper, tab_refcard = st.tabs([
            "🧪 Chemical Classification",
            "🎨 OpenCV Color Calibration",
            "🔒 SHA-256 Tamper Record",
            "🛡️ Tamper Verification Lab",
            "📋 Reference Card Template"
        ])

        with tab_analysis:
            st.subheader(f"Presumptive Result: {top_match['substance'] if top_match else 'Inconclusive'}")
            
            # Summary Metrics Banner
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Confidence Score", f"{top_match['confidence_percent']}%")
            with col_m2:
                st.metric("Controlled Schedule", top_match['schedule'])
            with col_m3:
                st.metric("Hazard Rating", top_match['danger_level'])
            with col_m4:
                st.metric("Observed Color", top_match['color_name'])

            # Substance Details Card
            rep_hex = hsv_metrics.get("representative_hex", "#000000")
            st.markdown(f"""
            <div style="background-color: #0f172a; padding: 15px; border-radius: 10px; border-left: 6px solid {rep_hex}; margin-bottom: 15px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 48px; height: 48px; border-radius: 8px; background-color: {rep_hex}; border: 2px solid #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.3);"></div>
                    <div>
                        <h4 style="margin: 0; color: #ffffff;">{top_match['substance']}</h4>
                        <p style="margin: 2px 0 0 0; color: #94a3b8; font-size: 13px;">Representative Color Swatch: <code>{rep_hex}</code> | Speed: {top_match['reaction_speed']}</p>
                    </div>
                </div>
                <p style="margin: 8px 0 0 0; color: #cbd5e1; font-size: 13px;"><b>Reaction Notes:</b> {top_match['notes']}</p>
            </div>
            """, unsafe_allow_html=True)

            # HSV Coordinate Breakdown
            st.markdown("##### 🌈 HSV Color Space Metrics")
            col_h, col_s, col_v = st.columns(3)
            with col_h:
                st.metric("Hue Angle", f"{hsv_metrics['hue']}°", help="0-360 degrees on chromatic wheel")
                st.progress(float(hsv_metrics['hue']) / 360.0)
            with col_s:
                st.metric("Saturation", f"{hsv_metrics['saturation']}%", help="Chroma purity")
                st.progress(float(hsv_metrics['saturation']) / 100.0)
            with col_v:
                st.metric("Value (Brightness)", f"{hsv_metrics['value']}%", help="Light intensity")
                st.progress(float(hsv_metrics['value']) / 100.0)

            # Candidate Table
            st.markdown("##### 📊 Differential Reaction Candidates")
            cands = []
            for c in classification["all_candidates"]:
                cands.append({
                    "Substance": c["substance"],
                    "Confidence": f"{c['confidence_percent']}%",
                    "Expected Color": c["color_name"],
                    "Schedule": c["schedule"]
                })
            st.dataframe(cands, use_container_width=True)

            # SWGDRUG Notice
            st.warning(f"⚠️ **Forensic Notice:** {classification['forensic_notice']}")

        with tab_optical:
            st.subheader("OpenCV Illumination Compensation & Reference Card Normalization")
            col_img1, col_img2 = st.columns(2)
            with col_img1:
                st.markdown("**1. Raw Captured Field Photo**")
                st.image(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB), use_container_width=True)
            with col_img2:
                st.markdown("**2. OpenCV Calibrated Image (Normalized D65)**")
                st.image(cv2.cvtColor(corrected_img, cv2.COLOR_BGR2RGB), use_container_width=True)

            st.markdown("##### 📐 Optical Telemetry")
            col_opt1, col_opt2, col_opt3 = st.columns(3)
            with col_opt1:
                st.info(f"**Method:** {calib_metrics.get('method')}")
            with col_opt2:
                st.info(f"**Card Status:** {calib_metrics.get('reference_card_status')}")
            with col_opt3:
                st.info(f"**Estimated Light:** {calib_metrics.get('estimated_lighting')}")

            gains = calib_metrics.get("channel_gains", {})
            if gains:
                st.markdown(f"**Channel Scaling Gains:** `Red: {gains.get('red_gain', 1.0)}x` | `Green: {gains.get('green_gain', 1.0)}x` | `Blue: {gains.get('blue_gain', 1.0)}x`")

        with tab_evidence:
            st.subheader(f"🔒 Tamper-Evident Certificate: {manifest['record_id']}")
            st.success("✅ INTEGRITY SEALED: Bound to GPS, raw pixels, officer ID, and timestamp via SHA-256 Merkle root.")

            st.code(f"MASTER MERKLE ROOT HASH:\n{manifest['chain_of_custody_hash']}", language="text")

            col_h1, col_h2 = st.columns(2)
            with col_h1:
                st.markdown("**Raw Image SHA-256:**")
                st.code(manifest["cryptographic_components"]["raw_image_sha256"], language="text")
                st.markdown("**GPS Metadata Canonical Hash:**")
                st.code(manifest["cryptographic_components"]["gps_metadata_sha256"], language="text")
            with col_h2:
                st.markdown("**Calibrated Image SHA-256:**")
                st.code(manifest["cryptographic_components"]["calibrated_image_sha256"], language="text")
                st.markdown("**Classification SHA-256:**")
                st.code(manifest["cryptographic_components"]["classification_sha256"], language="text")

            # Download JSON Manifest Button
            json_manifest_str = json.dumps(manifest, indent=2)
            st.download_button(
                label="📥 Download Evidence Manifest (JSON)",
                data=json_manifest_str,
                file_name=f"{manifest['record_id']}_manifest.json",
                mime="application/json"
            )

        with tab_tamper:
            st.subheader("🛡️ Cryptographic Tamper Simulation & Verification Lab")
            st.markdown("Test how the SHA-256 chain of custody detects even a single bit of tampering:")

            tamper_action = st.radio(
                "Select Tampering Simulation:",
                [
                    "None (Authentic Record)",
                    "Alter GPS Latitude (+0.001° spoofing)",
                    "Alter Substance Result (Falsifying outcome)",
                    "Alter Officer Badge ID"
                ]
            )

            test_manifest = json.loads(json.dumps(manifest))
            if tamper_action == "Alter GPS Latitude (+0.001° spoofing)":
                test_manifest["evidence_data"]["gps"]["latitude"] += 0.001
            elif tamper_action == "Alter Substance Result (Falsifying outcome)":
                test_manifest["evidence_data"]["classification"]["presumptive_substance"] = "Negative / Sugar (Tampered)"
            elif tamper_action == "Alter Officer Badge ID":
                test_manifest["evidence_data"]["operator"]["officer_badge"] = "UNAUTHORIZED-BADGE-00"

            verif = verify_tamper_evident_record(test_manifest, raw_image_bytes=raw_image_bytes)

            if verif["is_authentic"]:
                st.success("✅ VERIFICATION SUCCESS: All cryptographic hashes bitwise match! No tampering detected.")
                for chk in verif["checks_passed"]:
                    st.write(f"✓ {chk}")
            else:
                st.error("🚨 TAMPER DETECTED: Cryptographic hash discrepancy identified!")
                for disc in verif["discrepancies"]:
                    st.markdown(f"**Target:** `{disc['target']}` — {disc['error']}")
                    if "expected_hash" in disc:
                        st.code(f"Expected:   {disc['expected_hash']}\nCalculated: {disc['calculated_hash']}")

        with tab_refcard:
            st.subheader("Standardized 8-Patch Forensic Reference Color Card")
            st.markdown("Place this reference card adjacent to the reaction liquid in the field:")
            ref_path = os.path.join(SAMPLE_DIR, "forensic_reference_card_template.png")
            if os.path.exists(ref_path):
                st.image(ref_path, use_container_width=True)
                with open(ref_path, "rb") as rf:
                    st.download_button("📥 Download Printable Card (PNG)", rf.read(), file_name="forensic_reference_card.png", mime="image/png")
