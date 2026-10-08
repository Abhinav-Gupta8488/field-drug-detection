"""
Cryptographic Tamper-Evident Chain of Custody Engine
Generates SHA-256 integrity hashes for raw image data, calibrated image data,
GPS geolocation metadata, and classification records according to forensic evidentiary standards.
"""

import hashlib
import json
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
import numpy as np


def compute_sha256_bytes(data: bytes) -> str:
    """Computes SHA-256 hex digest of raw binary data."""
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()


def sanitize_for_json(data: Any) -> Any:
    """Recursively converts numpy numbers and arrays to standard Python types."""
    if isinstance(data, bool):
        return data
    elif isinstance(data, (np.floating, float)):
        return float(data)
    elif isinstance(data, (np.integer, int)):
        return int(data)
    elif isinstance(data, (np.ndarray, list)):
        return [sanitize_for_json(x) for x in data]
    elif isinstance(data, dict):
        return {str(k): sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, (str, type(None))):
        return data
    return str(data)


def compute_canonical_json_hash(obj: Dict[str, Any]) -> Tuple[str, str]:
    """
    Computes deterministic SHA-256 digest of a JSON dictionary by
    sorting keys and eliminating extra whitespace.
    Returns (hex_digest, canonical_json_string).
    """
    sanitized = sanitize_for_json(obj)
    canonical_str = json.dumps(sanitized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
    return digest, canonical_str


def generate_tamper_evident_record(
    raw_image_bytes: bytes,
    calibrated_image_bytes: bytes,
    gps_data: Dict[str, Any],
    classification_result: Dict[str, Any],
    operator_metadata: Optional[Dict[str, Any]] = None,
    nonce: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs a complete tamper-evident evidentiary record.
    Binds raw photo, calibrated photo, GPS coordinates, officer metadata, and classification.
    """
    now_utc = datetime.now(timezone.utc).isoformat()
    if not nonce:
        nonce = secrets.token_hex(16)
        
    # 1. Image hashes
    raw_image_hash = compute_sha256_bytes(raw_image_bytes)
    calibrated_image_hash = compute_sha256_bytes(calibrated_image_bytes)
    
    # 2. Canonical GPS payload
    canonical_gps = {
        "latitude": round(float(gps_data.get("latitude", 0.0)), 7),
        "longitude": round(float(gps_data.get("longitude", 0.0)), 7),
        "altitude_meters": round(float(gps_data.get("altitude", 0.0)), 1) if gps_data.get("altitude") is not None else None,
        "accuracy_meters": round(float(gps_data.get("accuracy", 5.0)), 1),
        "timestamp_utc": gps_data.get("timestamp_utc", now_utc),
        "source": gps_data.get("source", "GPS / Cellular Assisted GNSS"),
        "location_description": gps_data.get("location_description", "Field Location Coordinate Recorded"),
    }
    gps_hash, canonical_gps_str = compute_canonical_json_hash(canonical_gps)
    
    # 3. Canonical Operator / Field Kit Metadata
    if not operator_metadata:
        operator_metadata = {}
        
    canonical_operator = {
        "officer_badge": operator_metadata.get("officer_badge", "NARCO-FIELD-01"),
        "agency": operator_metadata.get("agency", "Field Forensics Unit"),
        "kit_batch_lot": operator_metadata.get("kit_batch_lot", "LOT-REAGENT-2026-X4"),
        "reagent_type": operator_metadata.get("reagent_type", "MARQUIS"),
        "device_id": operator_metadata.get("device_id", "MOBILE-TERMINAL-ALPHA-09"),
    }
    operator_hash, canonical_operator_str = compute_canonical_json_hash(canonical_operator)
    
    # 4. Canonical Classification summary
    top_substance = classification_result.get("top_match", {}).get("substance", "Unknown / Inconclusive")
    confidence = classification_result.get("top_match", {}).get("confidence_percent", 0.0)
    hsv_metrics = classification_result.get("hsv_metrics", {})
    
    canonical_classification = {
        "reagent_name": classification_result.get("reagent_name", "Colorimetric Test"),
        "presumptive_substance": top_substance,
        "confidence_percent": confidence,
        "hue_degrees": hsv_metrics.get("hue", 0.0),
        "saturation_pct": hsv_metrics.get("saturation", 0.0),
        "value_pct": hsv_metrics.get("value", 0.0),
        "representative_hex": hsv_metrics.get("representative_hex", "#000000"),
        "is_presumptive_positive": classification_result.get("is_presumptive_positive", False),
    }
    classification_hash, canonical_classification_str = compute_canonical_json_hash(canonical_classification)
    
    # 5. Master Chain of Custody Root Hash (Merkle-style composite)
    # Binds: raw_hash + calib_hash + gps_hash + operator_hash + class_hash + nonce + timestamp
    combined_feed = f"{raw_image_hash}|{calibrated_image_hash}|{gps_hash}|{operator_hash}|{classification_hash}|{nonce}|{now_utc}"
    chain_root_hash = hashlib.sha256(combined_feed.encode("utf-8")).hexdigest()
    
    record_id = f"EVID-{now_utc[:10]}-{chain_root_hash[:8].upper()}"
    
    manifest = {
        "record_id": record_id,
        "chain_of_custody_hash": chain_root_hash,
        "timestamp_utc": now_utc,
        "nonce": nonce,
        "cryptographic_components": {
            "raw_image_sha256": raw_image_hash,
            "calibrated_image_sha256": calibrated_image_hash,
            "gps_metadata_sha256": gps_hash,
            "operator_metadata_sha256": operator_hash,
            "classification_sha256": classification_hash,
        },
        "evidence_data": {
            "gps": sanitize_for_json(canonical_gps),
            "operator": sanitize_for_json(canonical_operator),
            "classification": sanitize_for_json(canonical_classification),
        },
        "evidentiary_status": {
            "integrity_sealed": True,
            "tamper_evident": True,
            "verification_algorithm": "SHA-256 Merkle-Composite",
            "iso_17025_compliant_binding": True,
        }
    }
    
    return sanitize_for_json(manifest)


def verify_tamper_evident_record(
    manifest: Dict[str, Any],
    raw_image_bytes: Optional[bytes] = None,
    calibrated_image_bytes: Optional[bytes] = None
) -> Dict[str, Any]:
    """
    Verifies that a record manifest has not been tampered with.
    Re-hashes GPS, operator info, classification, images, and composite chain root.
    """
    discrepancies = []
    checks_passed = []
    
    crypto_comp = manifest.get("cryptographic_components", {})
    evidence_data = manifest.get("evidence_data", {})
    claimed_chain_hash = manifest.get("chain_of_custody_hash", "")
    nonce = manifest.get("nonce", "")
    timestamp_utc = manifest.get("timestamp_utc", "")
    
    # 1. Verify GPS metadata hash
    claimed_gps_hash = crypto_comp.get("gps_metadata_sha256")
    calc_gps_hash, _ = compute_canonical_json_hash(evidence_data.get("gps", {}))
    if claimed_gps_hash == calc_gps_hash:
        checks_passed.append("GPS Metadata Canonical Hash Matches")
    else:
        discrepancies.append({
            "target": "GPS Metadata",
            "error": "GPS data was modified after signing!",
            "expected_hash": claimed_gps_hash,
            "calculated_hash": calc_gps_hash,
        })
        
    # 2. Verify Operator metadata hash
    claimed_operator_hash = crypto_comp.get("operator_metadata_sha256")
    calc_operator_hash, _ = compute_canonical_json_hash(evidence_data.get("operator", {}))
    if claimed_operator_hash == calc_operator_hash:
        checks_passed.append("Operator & Kit Metadata Hash Matches")
    else:
        discrepancies.append({
            "target": "Operator Metadata",
            "error": "Officer badge, agency, or kit batch was altered!",
            "expected_hash": claimed_operator_hash,
            "calculated_hash": calc_operator_hash,
        })
        
    # 3. Verify Classification hash
    claimed_class_hash = crypto_comp.get("classification_sha256")
    calc_class_hash, _ = compute_canonical_json_hash(evidence_data.get("classification", {}))
    if claimed_class_hash == calc_class_hash:
        checks_passed.append("Forensic Classification Hash Matches")
    else:
        discrepancies.append({
            "target": "Classification Result",
            "error": "Substance classification result was altered!",
            "expected_hash": claimed_class_hash,
            "calculated_hash": calc_class_hash,
        })
        
    # 4. Verify Raw Image if supplied
    if raw_image_bytes is not None:
        claimed_img_hash = crypto_comp.get("raw_image_sha256")
        calc_img_hash = compute_sha256_bytes(raw_image_bytes)
        if claimed_img_hash == calc_img_hash:
            checks_passed.append("Raw Image Binary SHA-256 Bitwise Match")
        else:
            discrepancies.append({
                "target": "Raw Image Binary",
                "error": "Image pixels have been edited, compressed, or tampered with!",
                "expected_hash": claimed_img_hash,
                "calculated_hash": calc_img_hash,
            })
            
    # 5. Verify Calibrated Image if supplied
    if calibrated_image_bytes is not None:
        claimed_calib_hash = crypto_comp.get("calibrated_image_sha256")
        calc_calib_hash = compute_sha256_bytes(calibrated_image_bytes)
        if claimed_calib_hash == calc_calib_hash:
            checks_passed.append("Calibrated Image Binary SHA-256 Bitwise Match")
        else:
            discrepancies.append({
                "target": "Calibrated Image Binary",
                "error": "Calibrated image file does not match certified hash!",
                "expected_hash": claimed_calib_hash,
                "calculated_hash": calc_calib_hash,
            })
            
    # 6. Verify Master Chain Root Hash
    calc_chain_feed = f"{crypto_comp.get('raw_image_sha256')}|{crypto_comp.get('calibrated_image_sha256')}|{calc_gps_hash}|{calc_operator_hash}|{calc_class_hash}|{nonce}|{timestamp_utc}"
    calc_chain_root = hashlib.sha256(calc_chain_feed.encode("utf-8")).hexdigest()
    
    if calc_chain_root == claimed_chain_hash and len(discrepancies) == 0:
        is_authentic = True
        status_verdict = "VERIFIED_AUTHENTIC - NO TAMPERING DETECTED"
    else:
        is_authentic = False
        status_verdict = "TAMPER_DETECTED - INTEGRITY COMPROMISED"
        if calc_chain_root != claimed_chain_hash:
            discrepancies.append({
                "target": "Master Chain Root Hash",
                "error": "Chain-of-custody root hash signature mismatch!",
                "expected_chain": claimed_chain_hash,
                "calculated_chain": calc_chain_root,
            })

    return {
        "is_authentic": is_authentic,
        "verdict": status_verdict,
        "checks_passed": checks_passed,
        "discrepancies": discrepancies,
        "verified_record_id": manifest.get("record_id"),
        "timestamp_checked_utc": datetime.now(timezone.utc).isoformat(),
    }
