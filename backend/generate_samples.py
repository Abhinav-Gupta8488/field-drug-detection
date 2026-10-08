"""
Generate Realistic Field Sample Images & Printable Reference Cards
Creates authentic synthetic field photos of drug test kits with reference color cards
under varied real-world lighting conditions (tungsten, daylight, fluorescent, shade).
"""

import os
import cv2
import numpy as np


SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_data")
os.makedirs(SAMPLE_DIR, exist_ok=True)


def draw_reference_card(
    canvas: np.ndarray,
    top_left: tuple,
    card_size: tuple = (180, 120),
    illuminant_tint: tuple = (1.0, 1.0, 1.0)
) -> dict:
    """
    Renders an 8-patch standardized forensic reference card onto the canvas
    and applies an illuminant tint representing environmental ambient lighting.
    Returns the bounding box [x, y, w, h] of the reference card.
    """
    x, y = top_left
    w, h = card_size
    
    # Card background (matte white plastic border)
    cv2.rectangle(canvas, (x, y), (x + w, y + h), (240, 240, 240), -1)
    cv2.rectangle(canvas, (x, y), (x + w, y + h), (90, 90, 90), 2)
    
    # Forensic Card Header text
    cv2.putText(canvas, "REF COLOR CARD V2", (x + 8, y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (40, 40, 40), 1)
    
    # 2 rows x 4 columns of standard swatches
    # Row 1: White, 18% Gray, Black, Red
    # Row 2: Green, Blue, Yellow, Cyan
    swatches_bgr = [
        # (B, G, R)
        [(245, 245, 245), (118, 118, 118), (30, 30, 30), (35, 35, 215)],
        [(60, 180, 40), (210, 60, 30), (30, 215, 240), (200, 180, 0)],
    ]
    
    margin_x = 10
    margin_top = 22
    patch_w = (w - (2 * margin_x) - (3 * 6)) // 4
    patch_h = (h - margin_top - 12 - 6) // 2
    
    for row_idx, row in enumerate(swatches_bgr):
        for col_idx, bgr in enumerate(row):
            px = x + margin_x + col_idx * (patch_w + 6)
            py = y + margin_top + row_idx * (patch_h + 6)
            
            # Apply illuminant tint to swatch
            tinted_b = int(np.clip(bgr[0] * illuminant_tint[0], 0, 255))
            tinted_g = int(np.clip(bgr[1] * illuminant_tint[1], 0, 255))
            tinted_r = int(np.clip(bgr[2] * illuminant_tint[2], 0, 255))
            
            cv2.rectangle(canvas, (px, py), (px + patch_w, py + patch_h), (tinted_b, tinted_g, tinted_r), -1)
            cv2.rectangle(canvas, (px, py), (px + patch_w, py + patch_h), (50, 50, 50), 1)
            
    return {"bbox": [x, y, w, h]}


def draw_test_vial(
    canvas: np.ndarray,
    center: tuple,
    vial_size: tuple = (120, 220),
    liquid_bgr: tuple = (10, 10, 10),
    illuminant_tint: tuple = (1.0, 1.0, 1.0),
    label: str = "TEST VIAL"
) -> dict:
    """
    Renders a realistic field test tube / ampoule with reaction liquid.
    Returns the bounding box [x, y, w, h] of the reaction liquid zone.
    """
    cx, cy = center
    vw, vh = vial_size
    vx = cx - vw // 2
    vy = cy - vh // 2
    
    # Glass ampoule outer casing
    cv2.rectangle(canvas, (vx, vy), (vx + vw, vy + vh), (215, 220, 225), 2)
    # Glass reflections / highlight lines
    cv2.line(canvas, (vx + 8, vy + 10), (vx + 8, vy + vh - 20), (255, 255, 255), 2)
    
    # Cap / stopper
    cv2.rectangle(canvas, (vx + 5, vy), (vx + vw - 5, vy + 25), (40, 45, 50), -1)
    
    # Liquid chamber (bottom 60% of vial)
    liq_x = vx + 10
    liq_y = vy + 65
    liq_w = vw - 20
    liq_h = vh - 85
    
    # Tint the reaction liquid according to environmental lighting
    tinted_b = int(np.clip(liquid_bgr[0] * illuminant_tint[0], 0, 255))
    tinted_g = int(np.clip(liquid_bgr[1] * illuminant_tint[1], 0, 255))
    tinted_r = int(np.clip(liquid_bgr[2] * illuminant_tint[2], 0, 255))
    
    # Liquid body with slight meniscus and depth gradient
    for i in range(liq_h):
        grad_factor = 0.85 + 0.25 * (i / float(liq_h))
        cur_b = int(np.clip(tinted_b * grad_factor, 0, 255))
        cur_g = int(np.clip(tinted_g * grad_factor, 0, 255))
        cur_r = int(np.clip(tinted_r * grad_factor, 0, 255))
        cv2.line(canvas, (liq_x, liq_y + i), (liq_x + liq_w, liq_y + i), (cur_b, cur_g, cur_r), 1)
        
    # Specular curved highlight on glass
    cv2.line(canvas, (liq_x + 6, liq_y + 10), (liq_x + 6, liq_y + liq_h - 15), (250, 250, 250), 1)
    
    # Label
    cv2.putText(canvas, label, (vx + 10, vy + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (20, 20, 20), 1)
    
    return {"bbox": [liq_x, liq_y, liq_w, liq_h]}


def create_sample_scene(
    bg_color_base: tuple,
    illuminant_tint: tuple, # (B_factor, G_factor, R_factor) e.g. (0.75, 0.95, 1.25) for warm tungsten
    reagent_name: str,
    reaction_liquid_bgr: tuple,
    filename: str,
    meta_info: dict
) -> str:
    """Creates a full 640x480 realistic field photo."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Synthetic worktable background (tactical mat / field bench texture)
    base_b = int(bg_color_base[0] * illuminant_tint[0])
    base_g = int(bg_color_base[1] * illuminant_tint[1])
    base_r = int(bg_color_base[2] * illuminant_tint[2])
    img[:, :] = (base_b, base_g, base_r)
    
    # Subtle field mat grid texture
    for gx in range(0, 640, 40):
        cv2.line(img, (gx, 0), (gx, 480), (base_b - 8, base_g - 8, base_r - 8), 1)
    for gy in range(0, 480, 40):
        cv2.line(img, (0, gy), (640, gy), (base_b - 8, base_g - 8, base_r - 8), 1)
        
    # Draw reference card on the left side
    card_info = draw_reference_card(img, top_left=(60, 150), card_size=(220, 140), illuminant_tint=illuminant_tint)
    
    # Draw reaction test vial on the right side
    vial_info = draw_test_vial(
        img,
        center=(460, 240),
        vial_size=(140, 260),
        liquid_bgr=reaction_liquid_bgr,
        illuminant_tint=illuminant_tint,
        label=reagent_name
    )
    
    # Add subtle Gaussian camera noise and field vignette
    noise = np.random.normal(0, 2.5, img.shape).astype(np.float32)
    img_noisy = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    
    out_path = os.path.join(SAMPLE_DIR, filename)
    cv2.imwrite(out_path, img_noisy, [cv2.IMWRITE_JPEG_QUALITY, 94])
    
    meta_info["ref_card_roi"] = card_info["bbox"]
    meta_info["vial_roi"] = vial_info["bbox"]
    meta_info["image_path"] = out_path
    
    return out_path


def generate_all_sample_cases():
    """Generates 6 distinct forensic cases with verified reagents and known ground truths."""
    cases = []
    
    # Case 1: Marquis Reagent on MDMA under Warm Tungsten Ambient Lighting
    c1_meta = {
        "id": "case-01-marquis-mdma",
        "title": "MDMA (Ecstasy) Presumptive Reaction",
        "reagent": "MARQUIS",
        "expected_substance": "MDMA / Ecstasy",
        "expected_schedule": "Schedule I",
        "lighting_condition": "Indoor Tungsten (Warm ~3000K, Heavy Yellow/Red shift)",
        "ground_truth_color": "Dark Purple / Black",
        "gps": {"latitude": 37.774929, "longitude": -122.419416, "altitude": 16.2, "accuracy": 3.8, "location_description": "Tenderloin Field Checkpoint, SF"}
    }
    # Marquis on MDMA creates dark purple-black: BGR ~(30, 10, 25)
    create_sample_scene(
        bg_color_base=(120, 130, 135),
        illuminant_tint=(0.75, 0.95, 1.30), # Heavy tungsten warm cast
        reagent_name="MARQUIS VIAL",
        reaction_liquid_bgr=(35, 12, 28),
        filename="case_01_marquis_mdma.jpg",
        meta_info=c1_meta
    )
    cases.append(c1_meta)
    
    # Case 2: Scott Reagent on Cocaine HCl under Outdoor Cool Shade
    c2_meta = {
        "id": "case-02-scott-cocaine",
        "title": "Cocaine HCl Cobalt Complex",
        "reagent": "SCOTT",
        "expected_substance": "Cocaine Hydrochloride",
        "expected_schedule": "Schedule II",
        "lighting_condition": "Outdoor Overcast / Cool Shade (~7000K, Blue shift)",
        "ground_truth_color": "Royal Turquoise Blue Precipitate",
        "gps": {"latitude": 34.052234, "longitude": -118.243685, "altitude": 85.0, "accuracy": 4.1, "location_description": "Port of Los Angeles Inspection Zone"}
    }
    # Scott on Cocaine creates brilliant royal blue: BGR ~(170, 95, 15)
    create_sample_scene(
        bg_color_base=(135, 130, 125),
        illuminant_tint=(1.25, 1.05, 0.85), # Blue/cool shift
        reagent_name="SCOTT REAGENT",
        reaction_liquid_bgr=(165, 90, 14),
        filename="case_02_scott_cocaine.jpg",
        meta_info=c2_meta
    )
    cases.append(c2_meta)
    
    # Case 3: Ehrlich Reagent on LSD Blotter under Office Fluorescent Light
    c3_meta = {
        "id": "case-03-ehrlich-lsd",
        "title": "LSD Indole Alkaloid Confirmation",
        "reagent": "EHRLICH",
        "expected_substance": "LSD (Lysergic acid diethylamide)",
        "expected_schedule": "Schedule I",
        "lighting_condition": "Commercial Fluorescent (~4000K, Slight Green Cast)",
        "ground_truth_color": "Vivid Purple to Magenta",
        "gps": {"latitude": 40.712776, "longitude": -74.005974, "altitude": 10.5, "accuracy": 2.9, "location_description": "Midtown Manhattan Interdiction Center"}
    }
    # Ehrlich on LSD creates vibrant purple: BGR ~(150, 25, 140)
    create_sample_scene(
        bg_color_base=(130, 135, 130),
        illuminant_tint=(0.95, 1.15, 0.90), # Slight green fluorescent tint
        reagent_name="EHRLICH AMPOULE",
        reaction_liquid_bgr=(145, 28, 142),
        filename="case_03_ehrlich_lsd.jpg",
        meta_info=c3_meta
    )
    cases.append(c3_meta)
    
    # Case 4: Marquis Reagent on Methamphetamine under Warm Indoor Lamp
    c4_meta = {
        "id": "case-04-marquis-meth",
        "title": "Methamphetamine Presumptive Orange-Brown",
        "reagent": "MARQUIS",
        "expected_substance": "Amphetamine / Methamphetamine",
        "expected_schedule": "Schedule II",
        "lighting_condition": "Low-light Sodium/Tungsten Streetlamp (~2700K)",
        "ground_truth_color": "Vivid Orange to Reddish Brown",
        "gps": {"latitude": 32.715738, "longitude": -117.161085, "altitude": 22.0, "accuracy": 5.0, "location_description": "San Diego Border Tactical Station"}
    }
    # Marquis on Meth creates orange-brown: BGR ~(15, 80, 190)
    create_sample_scene(
        bg_color_base=(120, 125, 130),
        illuminant_tint=(0.70, 0.90, 1.35),
        reagent_name="MARQUIS VIAL",
        reaction_liquid_bgr=(18, 85, 195),
        filename="case_04_marquis_meth.jpg",
        meta_info=c4_meta
    )
    cases.append(c4_meta)
    
    # Case 5: Mecke Reagent on Heroin
    c5_meta = {
        "id": "case-05-mecke-heroin",
        "title": "Heroin Mecke Dark Forest Green",
        "reagent": "MECKE",
        "expected_substance": "Heroin / Morphine",
        "expected_schedule": "Schedule I / II",
        "lighting_condition": "Neutral Daylight D65 (~5500K)",
        "ground_truth_color": "Dark Forest Green to Teal",
        "gps": {"latitude": 47.606209, "longitude": -122.332071, "altitude": 45.0, "accuracy": 3.4, "location_description": "Seattle Taskforce Field Laboratory"}
    }
    # Mecke on Heroin creates deep green: BGR ~(45, 85, 12)
    create_sample_scene(
        bg_color_base=(140, 140, 140),
        illuminant_tint=(1.0, 1.0, 1.0),
        reagent_name="MECKE VIAL",
        reaction_liquid_bgr=(45, 85, 14),
        filename="case_05_mecke_heroin.jpg",
        meta_info=c5_meta
    )
    cases.append(c5_meta)
    
    # Case 6: Marquis Reagent Negative / Sugar (Sucrose Control)
    c6_meta = {
        "id": "case-06-marquis-sugar",
        "title": "Negative Control (Sugar / No Reaction)",
        "reagent": "MARQUIS",
        "expected_substance": "Negative / Sugar (Sucrose)",
        "expected_schedule": "Non-Controlled",
        "lighting_condition": "Office Ambient Lighting",
        "ground_truth_color": "Clear Straw Yellow / No Color Change",
        "gps": {"latitude": 39.739236, "longitude": -104.990251, "altitude": 1600.0, "accuracy": 3.0, "location_description": "Denver Forensic Field Unit"}
    }
    # Clear pale straw: BGR ~(215, 238, 245)
    create_sample_scene(
        bg_color_base=(135, 135, 135),
        illuminant_tint=(0.95, 1.0, 1.05),
        reagent_name="MARQUIS VIAL",
        reaction_liquid_bgr=(215, 238, 245),
        filename="case_06_marquis_sugar.jpg",
        meta_info=c6_meta
    )
    cases.append(c6_meta)
    
    # Also generate a high-res printable standalone Reference Color Card
    ref_card_img = np.ones((400, 600, 3), dtype=np.uint8) * 250
    draw_reference_card(ref_card_img, top_left=(50, 40), card_size=(500, 320), illuminant_tint=(1.0, 1.0, 1.0))
    cv2.putText(ref_card_img, "FORENSIC DRUG TESTING - STANDARDIZED COLOR CALIBRATION CARD", (50, 385), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (20, 20, 20), 1)
    ref_template_path = os.path.join(SAMPLE_DIR, "forensic_reference_card_template.png")
    cv2.imwrite(ref_template_path, ref_card_img)
    
    print(f"Successfully generated {len(cases)} field sample cases and reference template at {SAMPLE_DIR}")
    return cases


if __name__ == "__main__":
    generate_all_sample_cases()
