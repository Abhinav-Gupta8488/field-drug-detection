"""
HSV Color Space Drug Test Reagent Classifier
Forensic colorimetric presumptive testing analysis for Marquis, Scott, Mecke,
Mandelin, Ehrlich, and Simon's field kits.
"""

import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple


# Forensic reagent profiles with expected HSV ranges (H: 0-360°, S: 0-100%, V: 0-100%)
REAGENT_PROFILES = {
    "MARQUIS": {
        "name": "Marquis Reagent",
        "description": "Formaldehyde + Conc. H2SO4; Primary screening for alkaloids and phenethylamines.",
        "reactions": [
            {
                "substance": "MDMA / Ecstasy",
                "schedule": "Schedule I",
                "danger_level": "CRITICAL",
                "color_name": "Dark Purple to Pitch Black",
                "hsv_range": {"h_min": 250, "h_max": 315, "s_min": 25, "s_max": 100, "v_min": 2, "v_max": 35},
                "target_hex": "#1b0a26",
                "reaction_speed": "Immediate (< 5s)",
                "notes": "Classic purple flash turning opaque black within seconds."
            },
            {
                "substance": "Heroin / Morphine",
                "schedule": "Schedule I / II",
                "danger_level": "CRITICAL - OPIOID",
                "color_name": "Deep Reddish-Violet / Purple",
                "hsv_range": {"h_min": 275, "h_max": 330, "s_min": 45, "s_max": 100, "v_min": 18, "v_max": 65},
                "target_hex": "#4a0e4e",
                "reaction_speed": "Rapid (< 15s)",
                "notes": "Transition from ruby red to deep purple."
            },
            {
                "substance": "Amphetamine / Methamphetamine",
                "schedule": "Schedule II",
                "danger_level": "HIGH - STIMULANT",
                "color_name": "Vivid Orange to Red-Brown",
                "hsv_range": {"h_min": 12, "h_max": 42, "s_min": 60, "s_max": 100, "v_min": 35, "v_max": 90},
                "target_hex": "#c45a0e",
                "reaction_speed": "Immediate (< 10s)",
                "notes": "Distinct fiery orange darkening into rusty red-brown."
            },
            {
                "substance": "Aspirin (Salicylate)",
                "schedule": "Over-the-Counter",
                "danger_level": "LOW",
                "color_name": "Slow Pink to Pale Red",
                "hsv_range": {"h_min": 340, "h_max": 15, "s_min": 20, "s_max": 75, "v_min": 55, "v_max": 95},
                "target_hex": "#e05c75",
                "reaction_speed": "Slow (> 60s)",
                "notes": "Common adulterant or over-the-counter pain reliever."
            },
            {
                "substance": "Negative / Sugar (Sucrose)",
                "schedule": "Non-Controlled",
                "danger_level": "NONE",
                "color_name": "Clear to Pale Straw / No Change",
                "hsv_range": {"h_min": 45, "h_max": 70, "s_min": 3, "s_max": 30, "v_min": 70, "v_max": 100},
                "target_hex": "#f5f2db",
                "reaction_speed": "None",
                "notes": "No presumptive reaction observed."
            }
        ]
    },
    "SCOTT": {
        "name": "Scott Reagent (Cobalt Thiocyanate)",
        "description": "Cobalt(II) thiocyanate reagent; Presumptive identification of Cocaine base and HCl.",
        "reactions": [
            {
                "substance": "Cocaine Hydrochloride",
                "schedule": "Schedule II",
                "danger_level": "HIGH - NARCOTIC",
                "color_name": "Brilliant Royal Blue / Turquoise Precipitate",
                "hsv_range": {"h_min": 195, "h_max": 232, "s_min": 50, "s_max": 100, "v_min": 28, "v_max": 88},
                "target_hex": "#0e5ea6",
                "reaction_speed": "Immediate (< 5s)",
                "notes": "Formation of bright blue cobalt-cocaine complex precipitate."
            },
            {
                "substance": "Crack Cocaine (Freebase)",
                "schedule": "Schedule II",
                "danger_level": "HIGH - NARCOTIC",
                "color_name": "Turquoise Blue with Acid Step",
                "hsv_range": {"h_min": 185, "h_max": 225, "s_min": 45, "s_max": 100, "v_min": 35, "v_max": 85},
                "target_hex": "#087e8b",
                "reaction_speed": "After HCl dissolution",
                "notes": "Requires second-phase hydrochloric acid drop for freebase conversion."
            },
            {
                "substance": "Negative / Cutting Agent (Inositol / Mannitol)",
                "schedule": "Non-Controlled",
                "danger_level": "NONE",
                "color_name": "Pink / Clear Reagent Solution",
                "hsv_range": {"h_min": 320, "h_max": 360, "s_min": 10, "s_max": 45, "v_min": 65, "v_max": 98},
                "target_hex": "#f2b6cb",
                "reaction_speed": "No Precipitate",
                "notes": "No blue cobalt complex formed. Solution retains original pink tint."
            }
        ]
    },
    "MECKE": {
        "name": "Mecke Reagent",
        "description": "Selenious acid in concentrated H2SO4; Opiate and alkaloid differentiation.",
        "reactions": [
            {
                "substance": "Heroin / Morphine",
                "schedule": "Schedule I / II",
                "danger_level": "CRITICAL - OPIOID",
                "color_name": "Dark Forest Green to Teal",
                "hsv_range": {"h_min": 135, "h_max": 175, "s_min": 45, "s_max": 100, "v_min": 18, "v_max": 60},
                "target_hex": "#0d522c",
                "reaction_speed": "Immediate (< 10s)",
                "notes": "Distinctive deep emerald/forest green reaction."
            },
            {
                "substance": "MDMA",
                "schedule": "Schedule I",
                "danger_level": "CRITICAL",
                "color_name": "Green flash to Dark Blue / Black",
                "hsv_range": {"h_min": 185, "h_max": 230, "s_min": 45, "s_max": 100, "v_min": 8, "v_max": 40},
                "target_hex": "#0c283b",
                "reaction_speed": "Instant (< 3s)",
                "notes": "Very rapid transition from momentary green to dark navy/black."
            },
            {
                "substance": "Negative / Neutral",
                "schedule": "Non-Controlled",
                "danger_level": "NONE",
                "color_name": "Colorless to Pale Amber",
                "hsv_range": {"h_min": 40, "h_max": 65, "s_min": 5, "s_max": 30, "v_min": 75, "v_max": 100},
                "target_hex": "#faebd7",
                "reaction_speed": "None",
                "notes": "No characteristic alkaloid reduction."
            }
        ]
    },
    "MANDELIN": {
        "name": "Mandelin Reagent",
        "description": "Ammonium vanadate in H2SO4; Dissociative and amine identification.",
        "reactions": [
            {
                "substance": "Ketamine",
                "schedule": "Schedule III",
                "danger_level": "HIGH - DISSOCIATIVE",
                "color_name": "Deep Orange to Rust Red",
                "hsv_range": {"h_min": 15, "h_max": 38, "s_min": 55, "s_max": 100, "v_min": 40, "v_max": 85},
                "target_hex": "#d35400",
                "reaction_speed": "Rapid (< 15s)",
                "notes": "Characteristic warm orange to brick red development."
            },
            {
                "substance": "Amphetamine",
                "schedule": "Schedule II",
                "danger_level": "HIGH - STIMULANT",
                "color_name": "Dark Olive Green",
                "hsv_range": {"h_min": 95, "h_max": 140, "s_min": 45, "s_max": 100, "v_min": 20, "v_max": 60},
                "target_hex": "#2e5c1e",
                "reaction_speed": "Moderate (< 30s)",
                "notes": "Olive drab green distinct from Marquis orange."
            },
            {
                "substance": "Methadone",
                "schedule": "Schedule II",
                "danger_level": "CRITICAL - OPIOID",
                "color_name": "Dark Violet-Blue",
                "hsv_range": {"h_min": 215, "h_max": 255, "s_min": 50, "s_max": 100, "v_min": 18, "v_max": 55},
                "target_hex": "#1b2859",
                "reaction_speed": "Rapid (< 15s)",
                "notes": "Deep navy to violet hue."
            }
        ]
    },
    "EHRLICH": {
        "name": "Ehrlich Reagent (p-DMAB)",
        "description": "p-Dimethylaminobenzaldehyde in ethanol + HCl; Specific to indole alkaloids (LSD, Psilocybin).",
        "reactions": [
            {
                "substance": "LSD (Lysergic acid diethylamide)",
                "schedule": "Schedule I",
                "danger_level": "HIGH - HALLUCINOGEN",
                "color_name": "Vivid Purple to Magenta",
                "hsv_range": {"h_min": 280, "h_max": 335, "s_min": 35, "s_max": 100, "v_min": 30, "v_max": 85},
                "target_hex": "#8e1b94",
                "reaction_speed": "Moderate (1-3 mins)",
                "notes": "Classic purple indole adduct formation. Crucial test: NBOMe variants will NOT turn purple."
            },
            {
                "substance": "Psilocybin / DMT",
                "schedule": "Schedule I",
                "danger_level": "HIGH - HALLUCINOGEN",
                "color_name": "Deep Violet / Pinkish Purple",
                "hsv_range": {"h_min": 290, "h_max": 345, "s_min": 40, "s_max": 100, "v_min": 25, "v_max": 80},
                "target_hex": "#7d166d",
                "reaction_speed": "Moderate (1-2 mins)",
                "notes": "Indole nucleus reaction producing characteristic chromophore."
            },
            {
                "substance": "Negative / 25I-NBOMe Alert",
                "schedule": "Harm Reduction Alert",
                "danger_level": "WARNING - DANGEROUS ADULTERANT",
                "color_name": "No Purple / Clear Yellowish",
                "hsv_range": {"h_min": 45, "h_max": 65, "s_min": 10, "s_max": 40, "v_min": 70, "v_max": 95},
                "target_hex": "#f7e8a4",
                "reaction_speed": "No Reaction",
                "notes": "Absence of purple indicates NO indole. Often sold deceptively as blotter LSD."
            }
        ]
    }
}


def extract_hsv_features(calibrated_vial_roi: np.ndarray) -> Dict[str, Any]:
    """
    Computes robust HSV features from the calibrated vial ROI:
    - Filters out specular glare (very high value + low sat) and extreme shadow
    - Computes mean, median, and dominant cluster HSV
    - Normalizes Hue to 0-360 deg, Sat to 0-100%, Val to 0-100%
    """
    hsv_img = cv2.cvtColor(calibrated_vial_roi, cv2.COLOR_BGR2HSV)
    
    # OpenCV HSV ranges: H: 0-180, S: 0-255, V: 0-255
    h_channel = hsv_img[:, :, 0].astype(np.float32) * 2.0 # Scale to 0-360 degrees
    s_channel = (hsv_img[:, :, 1].astype(np.float32) / 255.0) * 100.0 # Scale to 0-100%
    v_channel = (hsv_img[:, :, 2].astype(np.float32) / 255.0) * 100.0 # Scale to 0-100%
    
    # Filter specular highlights and vial edge artifacts
    # Ignore pixels with V > 97% and S < 8% (direct light reflection)
    valid_mask = ~((v_channel > 97.0) & (s_channel < 8.0))
    
    # If mask is empty, use all pixels
    if np.sum(valid_mask) < 20:
        valid_mask = np.ones_like(v_channel, dtype=bool)
        
    valid_h = h_channel[valid_mask]
    valid_s = s_channel[valid_mask]
    valid_v = v_channel[valid_mask]
    
    # Circular mean for Hue (angles in degrees)
    h_rad = np.deg2rad(valid_h)
    sin_sum = np.sum(np.sin(h_rad))
    cos_sum = np.sum(np.cos(h_rad))
    mean_h_deg = (np.rad2deg(np.arctan2(sin_sum, cos_sum)) + 360.0) % 360.0
    
    mean_s = float(np.mean(valid_s))
    mean_v = float(np.mean(valid_v))
    
    med_h = float(np.median(valid_h))
    med_s = float(np.median(valid_s))
    med_v = float(np.median(valid_v))
    
    std_h = float(np.std(valid_h))
    std_s = float(np.std(valid_s))
    std_v = float(np.std(valid_v))
    
    # Extract representative BGR swatch for UI preview
    b_mean = int(np.mean(calibrated_vial_roi[:, :, 0]))
    g_mean = int(np.mean(calibrated_vial_roi[:, :, 1]))
    r_mean = int(np.mean(calibrated_vial_roi[:, :, 2]))
    
    hex_color = f"#{r_mean:02x}{g_mean:02x}{b_mean:02x}"
    
    return {
        "hue": round(mean_h_deg, 1),
        "saturation": round(mean_s, 1),
        "value": round(mean_v, 1),
        "median_hsv": [round(med_h, 1), round(med_s, 1), round(med_v, 1)],
        "std_hsv": [round(std_h, 1), round(std_s, 1), round(std_v, 1)],
        "representative_rgb": [r_mean, g_mean, b_mean],
        "representative_hex": hex_color,
        "pixel_count": int(np.sum(valid_mask)),
    }


def compute_hsv_match_score(
    measured_h: float, measured_s: float, measured_v: float,
    range_def: Dict[str, float]
) -> float:
    """
    Calculates probability match score (0.0 to 1.0) against HSV target envelope.
    Accounts for Hue wrap-around (e.g. Red across 350°-15°).
    """
    h_min = range_def["h_min"]
    h_max = range_def["h_max"]
    s_min = range_def["s_min"]
    s_max = range_def["s_max"]
    v_min = range_def["v_min"]
    v_max = range_def["v_max"]
    
    # 1. Hue distance check
    if h_min <= h_max:
        h_center = (h_min + h_max) / 2.0
        h_span = (h_max - h_min) / 2.0
        # Circular distance from center
        dh = abs(measured_h - h_center)
        if dh > 180:
            dh = 360 - dh
    else:
        # Wrap-around case (e.g. h_min=340, h_max=15)
        # Total span across 0 deg
        span_total = (360 - h_min) + h_max
        h_center = (h_min + span_total / 2.0) % 360.0
        h_span = span_total / 2.0
        dh = abs(measured_h - h_center)
        if dh > 180:
            dh = 360 - dh
            
    # For very low saturation (< 15%) or very dark/bright values, Hue is less reliable
    hue_weight = 0.50
    if measured_s < 18.0 or measured_v < 12.0:
        hue_weight = 0.20 # Desaturated / near black colors
        
    # Normalized Hue score: 1.0 if inside span, decaying smoothly outside
    h_err = max(0.0, dh - h_span)
    score_h = np.exp(- (h_err ** 2) / (2.0 * (25.0 ** 2)))
    
    # 2. Saturation score
    s_center = (s_min + s_max) / 2.0
    s_span = (s_max - s_min) / 2.0
    ds = abs(measured_s - s_center)
    s_err = max(0.0, ds - s_span)
    score_s = np.exp(- (s_err ** 2) / (2.0 * (20.0 ** 2)))
    
    # 3. Value score
    v_center = (v_min + v_max) / 2.0
    v_span = (v_max - v_min) / 2.0
    dv = abs(measured_v - v_center)
    v_err = max(0.0, dv - v_span)
    score_v = np.exp(- (v_err ** 2) / (2.0 * (20.0 ** 2)))
    
    # Weighted composite score
    composite = (score_h * hue_weight) + (score_s * 0.25) + (score_v * (0.75 - hue_weight))
    return float(np.clip(composite, 0.0, 1.0))


def classify_drug_reaction(reagent_type: str, hsv_features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates measured HSV against candidate substance reaction profiles for the chosen reagent.
    Returns ranked matches, top presumptive result, confidence score, and forensic notices.
    """
    key = reagent_type.upper().strip()
    if key not in REAGENT_PROFILES:
        key = "MARQUIS" # fallback
        
    profile = REAGENT_PROFILES[key]
    measured_h = hsv_features["hue"]
    measured_s = hsv_features["saturation"]
    measured_v = hsv_features["value"]
    
    matches = []
    
    for reaction in profile["reactions"]:
        score = compute_hsv_match_score(measured_h, measured_s, measured_v, reaction["hsv_range"])
        confidence_pct = round(score * 100.0, 1)
        
        matches.append({
            "substance": reaction["substance"],
            "schedule": reaction["schedule"],
            "danger_level": reaction["danger_level"],
            "color_name": reaction["color_name"],
            "target_hex": reaction["target_hex"],
            "confidence_percent": confidence_pct,
            "reaction_speed": reaction["reaction_speed"],
            "notes": reaction["notes"],
            "hsv_range": reaction["hsv_range"],
        })
        
    # Sort matches by highest confidence
    matches.sort(key=lambda x: x["confidence_percent"], reverse=True)
    top_match = matches[0] if matches else None
    
    # Determine test confidence threshold
    is_positive = False
    if top_match and top_match["confidence_percent"] >= 65.0:
        is_positive = True
    elif top_match and top_match["confidence_percent"] >= 45.0:
        is_positive = True # moderate confidence
        
    return {
        "reagent_name": profile["name"],
        "reagent_description": profile["description"],
        "top_match": top_match,
        "all_candidates": matches,
        "is_presumptive_positive": is_positive,
        "forensic_notice": (
            "NOTICE: Colorimetric test kits are presumptive screening tools only. "
            "Pursuant to forensic standards (SWGDRUG Category C), results cannot confirm molecular structure. "
            "Confirmatory testing via Gas Chromatography-Mass Spectrometry (GC-MS) or LC-MS is legally required."
        ),
        "hsv_metrics": hsv_features,
    }
