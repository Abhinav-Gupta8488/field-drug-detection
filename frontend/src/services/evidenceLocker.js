/**
 * Local Offline Evidence Locker Service
 * Stores tamper-evident records, SHA-256 digests, GPS, and thumbnails in browser storage.
 */

const STORAGE_KEY = 'narcoscan_evidence_vault_v1';

export function getSavedEvidenceRecords() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (e) {
    console.error('Failed to read evidence locker', e);
    return [];
  }
}

export function saveEvidenceRecord(record) {
  try {
    if (!record || !record.manifest) return false;
    const existing = getSavedEvidenceRecords();
    
    // Check if record already saved
    const recordId = record.manifest.record_id;
    const index = existing.findIndex((r) => r.manifest?.record_id === recordId);
    
    const itemToSave = {
      record_id: recordId,
      timestamp_saved: new Date().toISOString(),
      timestamp_utc: record.manifest.timestamp_utc,
      reagent_name: record.classification?.reagent_name || 'Reagent Test',
      substance: record.classification?.top_match?.substance || 'Presumptive Test',
      confidence: record.classification?.top_match?.confidence_percent || 0,
      danger_level: record.classification?.top_match?.danger_level || 'STANDARD',
      chain_of_custody_hash: record.manifest.chain_of_custody_hash,
      officer_badge: record.manifest.evidence_data?.operator?.officer_badge,
      agency: record.manifest.evidence_data?.operator?.agency,
      gps: record.manifest.evidence_data?.gps,
      hex_color: record.hsv_metrics?.representative_hex || '#000000',
      thumbnail_base64: record.images?.annotated_base64 || record.images?.calibrated_base64,
      manifest: record.manifest,
      classification: record.classification,
      hsv_metrics: record.hsv_metrics,
      calibration_metrics: record.calibration_metrics,
    };

    if (index >= 0) {
      existing[index] = itemToSave; // update
    } else {
      existing.unshift(itemToSave); // prepend newest first
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(existing));
    return true;
  } catch (e) {
    console.error('Failed to save to evidence locker', e);
    return false;
  }
}

export function deleteEvidenceRecord(recordId) {
  try {
    const existing = getSavedEvidenceRecords();
    const filtered = existing.filter((r) => r.record_id !== recordId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    return filtered;
  } catch (e) {
    console.error('Failed to delete evidence record', e);
    return [];
  }
}

export function exportEvidenceLockerJson() {
  const records = getSavedEvidenceRecords();
  const exportPayload = {
    exported_at_utc: new Date().toISOString(),
    total_records: records.length,
    device_storage_engine: 'HTML5 Offline Local Vault',
    records: records,
  };
  const jsonStr = JSON.stringify(exportPayload, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `narcoscan_offline_vault_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
