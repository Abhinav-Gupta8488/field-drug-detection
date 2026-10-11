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
from tamper_evidence import generate_tamper_evident_record, verify_tamper_evident_record
import generate_samples


# ==============================================================================
# Tactical Augmented Reality HUD Drawing Utilities
# Draws high-visibility Yellow Reference Card and Green Reaction Vial Dashed Boxes
# ==============================================================================

def draw_dashed_line(img, pt1, pt2, color, thickness=2, dash_len=12, gap_len=8):
    dist = float(np.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1]))
    if dist < 1:
        return
    dx = (pt2[0] - pt1[0]) / dist
    dy = (pt2[1] - pt1[1]) / dist
    curr = 0.0
    while curr < dist:
        end = min(curr + dash_len, dist)
        p1 = (int(round(pt1[0] + dx * curr)), int(round(pt1[1] + dy * curr)))
        p2 = (int(round(pt1[0] + dx * end)), int(round(pt1[1] + dy * end)))
        cv2.line(img, p1, p2, color, thickness, cv2.LINE_AA)
        curr += dash_len + gap_len

def draw_corner_brackets(img, x, y, w, h, color, bracket_len=16, thickness=3):
    bl = min(bracket_len, max(6, w // 4), max(6, h // 4))
    # Top-Left
    cv2.line(img, (x, y), (x + bl, y), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x, y), (x, y + bl), color, thickness, cv2.LINE_AA)
    # Top-Right
    cv2.line(img, (x + w, y), (x + w - bl, y), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x + w, y), (x + w, y + bl), color, thickness, cv2.LINE_AA)
    # Bottom-Left
    cv2.line(img, (x, y + h), (x + bl, y + h), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x, y + h), (x, y + h - bl), color, thickness, cv2.LINE_AA)
    # Bottom-Right
    cv2.line(img, (x + w, y + h), (x + w - bl, y + h), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x + w, y + h), (x + w, y + h - bl), color, thickness, cv2.LINE_AA)

def draw_tactical_alignment_hud(base_img, ref_roi, vial_roi):
    annotated = base_img.copy()
    h_img, w_img = annotated.shape[:2]
    # High-visibility Tactical Amber / Yellow for Reference Card (BGR: (0, 215, 255))
    yellow_bgr = (0, 215, 255)
    # High-visibility Emerald Green for Reaction Vial (BGR: (70, 230, 70))
    green_bgr = (70, 230, 70)
    
    # 1. Overlay Reference Card Box (Yellow Dashed)
    if ref_roi and len(ref_roi) == 4:
        rx, ry, rw, rh = ref_roi
        rx = max(0, min(rx, w_img - 10))
        ry = max(0, min(ry, h_img - 10))
        rw = max(10, min(rw, w_img - rx))
        rh = max(10, min(rh, h_img - ry))
        
        # Subtle tint overlay (12% amber)
        overlay = annotated.copy()
        cv2.rectangle(overlay, (rx, ry), (rx + rw, ry + rh), yellow_bgr, -1)
        cv2.addWeighted(overlay, 0.12, annotated, 0.88, 0, annotated)
        
        # Dashed perimeter
        draw_dashed_line(annotated, (rx, ry), (rx + rw, ry), yellow_bgr, 2)
        draw_dashed_line(annotated, (rx + rw, ry), (rx + rw, ry + rh), yellow_bgr, 2)
        draw_dashed_line(annotated, (rx + rw, ry + rh), (rx, ry + rh), yellow_bgr, 2)
        draw_dashed_line(annotated, (rx, ry + rh), (rx, ry), yellow_bgr, 2)
        
        # Reinforced solid corners
        draw_corner_brackets(annotated, rx, ry, rw, rh, yellow_bgr, bracket_len=18, thickness=3)
        
        # Labeled Tactical Badge
        label = "REF COLOR CARD"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
        badge_y = max(ry - 8, th + 8)
        cv2.rectangle(annotated, (rx, badge_y - th - 6), (rx + tw + 14, badge_y + 4), (15, 23, 42), -1)
        cv2.rectangle(annotated, (rx, badge_y - th - 6), (rx + tw + 14, badge_y + 4), yellow_bgr, 1)
        cv2.putText(annotated, label, (rx + 7, badge_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.42, yellow_bgr, 1, cv2.LINE_AA)
        
    # 2. Overlay Reaction Vial Box (Green Dashed)
    if vial_roi and len(vial_roi) == 4:
        vx, vy, vw, vh = vial_roi
        vx = max(0, min(vx, w_img - 10))
        vy = max(0, min(vy, h_img - 10))
        vw = max(10, min(vw, w_img - vx))
        vh = max(10, min(vh, h_img - vy))
        
        # Subtle tint overlay (12% emerald)
        overlay = annotated.copy()
        cv2.rectangle(overlay, (vx, vy), (vx + vw, vy + vh), green_bgr, -1)
        cv2.addWeighted(overlay, 0.12, annotated, 0.88, 0, annotated)
        
        # Dashed perimeter
        draw_dashed_line(annotated, (vx, vy), (vx + vw, vy), green_bgr, 2)
        draw_dashed_line(annotated, (vx + vw, vy), (vx + vw, vy + vh), green_bgr, 2)
        draw_dashed_line(annotated, (vx + vw, vy + vh), (vx, vy + vh), green_bgr, 2)
        draw_dashed_line(annotated, (vx, vy + vh), (vx, vy), green_bgr, 2)
        
        # Reinforced solid corners
        draw_corner_brackets(annotated, vx, vy, vw, vh, green_bgr, bracket_len=18, thickness=3)
        
        # Labeled Tactical Badge
        label = "TEST VIAL / WELL"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
        badge_y = max(vy - 8, th + 8)
        cv2.rectangle(annotated, (vx, badge_y - th - 6), (vx + tw + 14, badge_y + 4), (15, 23, 42), -1)
        cv2.rectangle(annotated, (vx, badge_y - th - 6), (vx + tw + 14, badge_y + 4), green_bgr, 1)
        cv2.putText(annotated, label, (vx + 7, badge_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.42, green_bgr, 1, cv2.LINE_AA)
        
    # Center crosshair reticle
    cx, cy = w_img // 2, h_img // 2
    cv2.line(annotated, (cx - 15, cy), (cx + 15, cy), (148, 163, 184), 1, cv2.LINE_AA)
    cv2.line(annotated, (cx, cy - 15), (cx, cy + 15), (148, 163, 184), 1, cv2.LINE_AA)
    cv2.circle(annotated, (cx, cy), 8, (148, 163, 184), 1, cv2.LINE_AA)
    
    return annotated


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
    .stApp {
        background-color: #020617;
        color: #f8fafc;
    }
    .stMetric {
        background-color: #0f172a;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #1e293b;
    }
</style>
""", unsafe_allow_html=True)


SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "backend", "sample_data")

@st.cache_data(show_spinner=False)
def ensure_samples_exist():
    if not os.path.exists(os.path.join(SAMPLE_DIR, "case_01_marquis_mdma.jpg")):
        generate_samples.generate_all_sample_cases()
    return True

ensure_samples_exist()


# Sidebar: Telemetry & Kit Configuration
st.sidebar.title("🛡️ NARCO-SCAN FIELD")
st.sidebar.caption("Forensic Mobile Presumptive Testing Engine")

reagent_options = list(REAGENT_PROFILES.keys())
selected_reagent = st.sidebar.selectbox(
    "🧪 Select Reagent Kit",
    reagent_options,
    index=0,
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

# Input Source Selector (Defaulting to Verified Preset so app loads instantly in 0.1s)
input_source = st.radio(
    "Select Image Input Mode:",
    ["🧪 Load Verified Field Preset (Instant Demo)", "📷 Mobile Camera Capture", "📂 Upload Photo File"],
    index=0,
    horizontal=True
)

raw_image_bytes = None
ref_roi_override = None
vial_roi_override = None

preset_files = {
    "Case 1: Marquis with MDMA (Warm Tungsten ~3000K Lighting)": ("case_01_marquis_mdma.jpg", "MARQUIS", [60, 150, 220, 140], [400, 185, 120, 135]),
    "Case 2: Scott with Cocaine HCl (Outdoor Cool Shade)": ("case_02_scott_cocaine.jpg", "SCOTT", [60, 150, 220, 140], [400, 185, 120, 135]),
    "Case 3: Ehrlich with LSD Blotter (Commercial Fluorescent)": ("case_03_ehrlich_lsd.jpg", "EHRLICH", [60, 150, 220, 140], [400, 185, 120, 135]),
    "Case 4: Marquis with Methamphetamine (Night Sodium Lamp)": ("case_04_marquis_meth.jpg", "MARQUIS", [60, 150, 220, 140], [400, 185, 120, 135]),
    "Case 5: Mecke with Heroin (Standard Daylight D65)": ("case_05_mecke_heroin.jpg", "MECKE", [60, 150, 220, 140], [400, 185, 120, 135]),
    "Case 6: Negative Control / Sugar (Ambient Office Light)": ("case_06_marquis_sugar.jpg", "MARQUIS", [60, 150, 220, 140], [400, 185, 120, 135]),
}

if input_source == "🧪 Load Verified Field Preset (Instant Demo)":
    preset_choice = st.selectbox(
        "Choose Field Sample Scenario:",
        list(preset_files.keys()),
        index=0
    )
    filename, preset_reagent, ref_roi_override, vial_roi_override = preset_files[preset_choice]
    preset_path = os.path.join(SAMPLE_DIR, filename)
    if os.path.exists(preset_path):
        with open(preset_path, "rb") as f:
            raw_image_bytes = f.read()
        selected_reagent = preset_reagent

elif input_source == "📷 Mobile Camera Capture":
    st.info("Tap below to activate device camera and snap a photo of the kit:")
    cam_file = st.camera_input("Field Kit Viewfinder:")
    if cam_file:
        raw_image_bytes = cam_file.getvalue()
    else:
        st.warning("Awaiting camera snapshot. Snap a photo above to run analysis.")

elif input_source == "📂 Upload Photo File":
    uploaded_file = st.file_uploader("Upload kit photo from device (JPEG/PNG):", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        raw_image_bytes = uploaded_file.getvalue()
    else:
        st.warning("Upload an image above to analyze.")


# Process Pipeline if image loaded
if raw_image_bytes:
    nparr = np.frombuffer(raw_image_bytes, np.uint8)
    cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if cv_img is None:
        st.error("Error decoding image. Please try a different photo.")
    else:
        st.divider()

        # Target ROI Controls
        with st.expander("🎯 Target Alignment Bounding Boxes (Fine-Tune Coordinates)", expanded=False):
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.caption("🟨 Reference Color Card [X, Y, Width, Height]")
                rx = st.slider("Card X", 0, cv_img.shape[1], ref_roi_override[0] if ref_roi_override else 60)
                ry = st.slider("Card Y", 0, cv_img.shape[0], ref_roi_override[1] if ref_roi_override else 150)
                rw = st.slider("Card Width", 20, 350, ref_roi_override[2] if ref_roi_override else 220)
                rh = st.slider("Card Height", 20, 250, ref_roi_override[3] if ref_roi_override else 140)
                ref_roi_override = [rx, ry, rw, rh]
                
            with col_r2:
                st.caption("🟩 Reaction Vial / Well [X, Y, Width, Height]")
                vx = st.slider("Vial X", 0, cv_img.shape[1], vial_roi_override[0] if vial_roi_override else 400)
                vy = st.slider("Vial Y", 0, cv_img.shape[0], vial_roi_override[1] if vial_roi_override else 185)
                vw = st.slider("Vial Width", 20, 250, vial_roi_override[2] if vial_roi_override else 120)
                vh = st.slider("Vial Height", 20, 250, vial_roi_override[3] if vial_roi_override else 135)
                vial_roi_override = [vx, vy, vw, vh]

        # Draw Augmented Reality HUD with Yellow Card & Green Vial Dashed Boxes
        hud_img = draw_tactical_alignment_hud(cv_img, ref_roi_override, vial_roi_override)

        # Field Optical Viewfinder Section
        st.markdown("### 📷 Field Optical Capture & AR Alignment Viewfinder")
        show_ar = st.toggle(
            "🎯 Display Yellow & Green AR Alignment Guides",
            value=True,
            help="Toggles the yellow dashed reference card box and green dashed reaction vial box overlay"
        )
        
        col_vf1, col_vf2 = st.columns([3, 2])
        with col_vf1:
            preview_canvas = hud_img if show_ar else cv_img
            st.image(
                cv2.cvtColor(preview_canvas, cv2.COLOR_BGR2RGB),
                caption="Field Optical Viewfinder — 🟨 Yellow Box: Reference Card | 🟩 Green Box: Test Vial",
                use_container_width=True
            )
        with col_vf2:
            st.markdown("##### 🔬 Sensor Target Isolations")
            rx, ry, rw, rh = ref_roi_override
            vx, vy, vw, vh = vial_roi_override
            crop_card = cv_img[max(0, ry):min(cv_img.shape[0], ry+rh), max(0, rx):min(cv_img.shape[1], rx+rw)]
            crop_vial_raw = cv_img[max(0, vy):min(cv_img.shape[0], vy+vh), max(0, vx):min(cv_img.shape[1], vx+vw)]
            
            c_c1, c_c2 = st.columns(2)
            with c_c1:
                st.caption("🟨 Ref Card Target")
                if crop_card.size > 0:
                    st.image(cv2.cvtColor(crop_card, cv2.COLOR_BGR2RGB), use_container_width=True)
            with c_c2:
                st.caption("🟩 Reaction Vial Target")
                if crop_vial_raw.size > 0:
                    st.image(cv2.cvtColor(crop_vial_raw, cv2.COLOR_BGR2RGB), use_container_width=True)
                    
            st.markdown("""
            <div style="background-color: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #1e293b; font-size: 13px; line-height: 1.5;">
                <div style="color: #fbbf24; font-weight: bold; margin-bottom: 4px;">🟨 Yellow Dashed Box:</div>
                <div style="color: #94a3b8; margin-bottom: 8px;">Target for 8-patch forensic reference card standard. Calibrates lighting & shadows.</div>
                <div style="color: #34d399; font-weight: bold; margin-bottom: 4px;">🟩 Green Dashed Box:</div>
                <div style="color: #94a3b8;">Target for test reaction vial / spot plate well. Isolates liquid chromophore.</div>
            </div>
            """, unsafe_allow_html=True)

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
                st.markdown("**1. Raw Field Capture with AR Alignment Reticles**")
                st.image(
                    cv2.cvtColor(hud_img, cv2.COLOR_BGR2RGB),
                    caption="🟨 Yellow Box: Reference Card Standard | 🟩 Green Box: Test Reaction Vial",
                    use_container_width=True
                )
            with col_img2:
                st.markdown("**2. OpenCV Calibrated Image (Normalized D65 Retinex)**")
                st.image(
                    cv2.cvtColor(corrected_img, cv2.COLOR_BGR2RGB),
                    caption="Ambient illumination compensated via 3x3 polynomial color constancy",
                    use_container_width=True
                )

            st.markdown("##### 🔬 Reaction Vial Chromophore: Raw vs. Normalized")
            col_v_raw, col_v_cal = st.columns(2)
            with col_v_raw:
                st.caption("Raw Captured Reaction Vial (Uncalibrated)")
                if crop_vial_raw.size > 0:
                    st.image(cv2.cvtColor(crop_vial_raw, cv2.COLOR_BGR2RGB), use_container_width=True)
            with col_v_cal:
                st.caption("OpenCV Calibrated Reaction Vial (Standard D65)")
                if vial_crop.size > 0:
                    st.image(cv2.cvtColor(vial_crop, cv2.COLOR_BGR2RGB), use_container_width=True)

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
