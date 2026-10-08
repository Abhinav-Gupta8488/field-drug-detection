# NARCO-SCAN FIELD: Mobile Drug Testing Prototype

A forensic-grade mobile application prototype for presumptive field drug testing.

The application captures a photograph of a chemical reagent test kit alongside a standardized reference color card, applies **OpenCV color correction** to eliminate environmental ambient lighting artifacts (e.g., tungsten warm shifts, overcast blue shifts), classifies reaction chromophores using **HSV color space envelopes**, and generates a **tamper-evident SHA-256 cryptographic chain-of-custody manifest** bound to GPS coordinates, device telemetry, and officer metadata.

---

## Key Features

1. **Mobile-First Tactical Interface**:
   - Ruggedized mobile handheld simulation frame + responsive tablet/workstation view.
   - Built-in camera viewfinder (`getUserMedia`) with live video stream, photo capture, and file upload.
   - Augmented Reality (AR) HUD alignment overlays for the reaction ampoule and reference color card.
   - Real-time GNSS / GPS acquisition with accuracy radius and altitude tracking.

2. **OpenCV Color Correction & Illumination Normalization**:
   - Standardized 8-Patch Reference Color Card (White 95%, 18% Neutral Gray, Black 5%, Red, Green, Blue, Yellow, Cyan).
   - 3x3 Least-Squares polynomial calibration matrix mapping measured swatches to canonical sRGB D65 targets.
   - Von Kries diagonal white patch Retinex adaptation with per-channel gain metrics ($k_R, k_G, k_B$).
   - Interactive Before/After split comparison slider in the UI.

3. **Forensic Reagent HSV Colorimetric Classification**:
   - Reagents supported:
     - **Marquis Reagent**: MDMA (Dark Purple to Black), Heroin/Morphine (Red-Violet), Methamphetamine (Vivid Orange to Red-Brown), Aspirin (Pink/Red), Sugar (No Reaction).
     - **Scott Reagent (Cobalt Thiocyanate)**: Cocaine HCl & Freebase (Royal Turquoise Blue precipitate).
     - **Mecke Reagent**: Heroin/Morphine (Forest Green to Teal), MDMA (Blue/Black).
     - **Mandelin Reagent**: Ketamine (Deep Orange/Rust Red), Amphetamine (Olive Green).
     - **Ehrlich Reagent (p-DMAB)**: LSD & Indoles (Vivid Purple to Magenta). Negative alert for dangerous 25I-NBOMe adulterants.
   - 360° Chromatic Hue circle indicator, Saturation %, Value / Brightness %, and representative Hex color chip.
   - Ranked match candidates with confidence scoring percentage and SWGDRUG Category C advisory notices.

4. **SHA-256 Cryptographic Tamper-Evident Chain of Custody**:
   - `raw_image_sha256`: SHA-256 hash of raw captured camera pixels.
   - `calibrated_image_sha256`: SHA-256 hash of OpenCV normalized image.
   - `gps_metadata_sha256`: Deterministic canonical SHA-256 hash of sorted GPS payload.
   - `operator_metadata_sha256`: Hash of officer badge ID, agency, and kit lot number.
   - `classification_sha256`: Hash of substance classification and confidence.
   - `chain_of_custody_hash`: Master Merkle composite root binding all components with a cryptographic nonce.
   - Interactive **Tamper Verification Lab**: lets users simulate coordinate altering or image editing to observe instant cryptographic breach detection!

---

## Quick Start & Running the Application

### 1. Unified Single-Command Launch

Simply run the startup script using Python:

```bash
.\venv\Scripts\python start_app.py
```
*(Or double-click `start.bat` on Windows)*

This launches the combined application on **port 8000**:
- **Desktop Browser:** [http://localhost:8000](http://localhost:8000)
- **Mobile Device on Wi-Fi:** `http://<your-ip>:8000` (e.g. `http://192.168.1.100:8000`)

---

## Project Structure

```
drugdetection/
├── backend/
│   ├── color_correction.py      # OpenCV reference card detection & color constancy
│   ├── reagent_classifier.py    # HSV feature extraction & chemical library
│   ├── tamper_evidence.py       # SHA-256 hashing, canonical JSON & audit verification
│   ├── generate_samples.py      # Realistic synthetic test cases generator
│   ├── sample_data/             # Pre-generated realistic test scenes & printable card
│   ├── main.py                  # FastAPI REST endpoints & static frontend mount
│   └── test_pipeline.py         # Pipeline validation test
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx                 # Tactical status bar & view toggles
│   │   │   ├── ReagentSelector.jsx        # Test kit & GPS telemetry selector
│   │   │   ├── CameraViewfinder.jsx       # Camera stream, AR overlay & presets
│   │   │   ├── ColorCorrectionPanel.jsx   # Before/after split slider & optical gains
│   │   │   ├── HsvClassifierPanel.jsx     # Chromatic hue circle & drug matches
│   │   │   ├── TamperEvidentRecord.jsx    # SHA-256 certificate & export tools
│   │   │   ├── TamperVerifierModal.jsx    # Live tamper testing & audit lab
│   │   │   └── ReferenceCardModal.jsx     # Printable reference card template
│   │   ├── App.jsx
│   │   └── index.css
│   └── package.json
├── start_app.py                 # Unified launcher for port 8000
├── start.bat                    # Windows 1-click launcher
├── test_e2e.py                  # Automated test suite (5/5 tests passing)
└── README.md
```

---

## Verifying the Test Suite

Run the end-to-end automated test suite:

```bash
.\venv\Scripts\python test_e2e.py
```

All 5 tests verify:
1. Backend health & OpenCV 5.0.0 integration
2. Sample test cases loading
3. Static frontend delivery
4. Color calibration and HSV classification accuracy
5. Cryptographic tamper detection on authentic and modified manifests
