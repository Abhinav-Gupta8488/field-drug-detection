import React, { useState } from 'react';
import { ShieldCheck, Lock, Copy, Check, Download, Printer, FileText, AlertOctagon, QrCode } from 'lucide-react';

export default function TamperEvidentRecord({
  manifest,
  onLaunchTamperTest,
}) {
  const [copiedKey, setCopiedKey] = useState(null);

  if (!manifest) return null;

  const cryptoComp = manifest.cryptographic_components || {};
  const evidenceData = manifest.evidence_data || {};
  const recordId = manifest.record_id || 'EVID-UNSEALED';
  const rootHash = manifest.chain_of_custody_hash || '';

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const downloadManifestJson = () => {
    const jsonStr = JSON.stringify(manifest, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${recordId}_tamper_evident_manifest.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const printReport = () => {
    window.print();
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 sm:p-4 shadow-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 mb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-cyan-950/80 text-cyan-400 border border-cyan-800">
            <Lock className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wide flex items-center gap-2">
              Cryptographic Tamper-Evident Chain of Custody
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                SEALED & BOUND
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              SHA-256 Merkle-composite binding raw photo, OpenCV calibrated photo, GPS, and officer ID
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={downloadManifestJson}
            className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-cyan-400" />
            <span>Export JSON</span>
          </button>
          <button
            onClick={printReport}
            className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors hidden sm:flex"
          >
            <Printer className="w-3.5 h-3.5 text-slate-300" />
            <span>Print Report</span>
          </button>
        </div>
      </div>

      {/* Primary Seal Banner */}
      <div className="bg-slate-950 border border-cyan-900/60 rounded-xl p-3 mb-3 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-cyan-950/90 border border-cyan-500/50 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-7 h-7 text-cyan-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-cyan-300">{recordId}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800">
                  ISO 17025 / RULE 901
                </span>
              </div>
              <p className="text-xs text-slate-300 font-mono mt-0.5">
                Timestamp: <span className="text-slate-400">{manifest.timestamp_utc}</span>
              </p>
              <p className="text-[10px] font-mono text-slate-400">
                Nonce: <span className="text-slate-400">{manifest.nonce}</span>
              </p>
            </div>
          </div>

          {/* Test Tamper Detection Button */}
          <button
            onClick={onLaunchTamperTest}
            className="px-3 py-2 rounded-lg text-xs font-bold font-mono bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-700 flex items-center justify-center gap-2 transition-all shadow-md self-start md:self-center"
          >
            <AlertOctagon className="w-4 h-4 text-rose-400" />
            <span>Simulate Tampering & Test Audit</span>
          </button>
        </div>

        {/* Master Root Hash */}
        <div className="mt-3 pt-2.5 border-t border-slate-800/80">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold">
              CHAIN-OF-CUSTODY MERKLE ROOT (SHA-256):
            </span>
            <button
              onClick={() => copyToClipboard(rootHash, 'root')}
              className="text-[10px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              {copiedKey === 'root' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              {copiedKey === 'root' ? 'Copied' : 'Copy Root'}
            </button>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs font-mono text-cyan-300 break-all select-all">
            {rootHash}
          </div>
        </div>
      </div>

      {/* Individual Cryptographic Hashes Grid */}
      <div className="space-y-2 mb-3">
        <div className="text-[10px] font-mono text-slate-400 uppercase font-semibold">
          Component Hashes Bound in Chain:
        </div>

        {/* 1. Raw Image SHA-256 */}
        <div className="bg-slate-950 p-2 rounded-lg border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs font-mono">
          <div className="sm:w-1/3">
            <span className="text-slate-300 font-bold text-[11px] block">Raw Captured Photo</span>
            <span className="text-[10px] text-slate-500">SHA-256 of raw sensor bytes</span>
          </div>
          <div className="sm:w-2/3 flex items-center justify-between gap-2">
            <span className="text-slate-400 truncate text-[11px] select-all">
              {cryptoComp.raw_image_sha256}
            </span>
            <button
              onClick={() => copyToClipboard(cryptoComp.raw_image_sha256, 'raw')}
              className="text-slate-500 hover:text-cyan-400 shrink-0 p-1"
              title="Copy Hash"
            >
              {copiedKey === 'raw' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            </button>
          </div>
        </div>

        {/* 2. Calibrated Image SHA-256 */}
        <div className="bg-slate-950 p-2 rounded-lg border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs font-mono">
          <div className="sm:w-1/3">
            <span className="text-slate-300 font-bold text-[11px] block">Calibrated Image (D65)</span>
            <span className="text-[10px] text-slate-500">SHA-256 of OpenCV normalized bytes</span>
          </div>
          <div className="sm:w-2/3 flex items-center justify-between gap-2">
            <span className="text-slate-400 truncate text-[11px] select-all">
              {cryptoComp.calibrated_image_sha256}
            </span>
            <button
              onClick={() => copyToClipboard(cryptoComp.calibrated_image_sha256, 'calib')}
              className="text-slate-500 hover:text-cyan-400 shrink-0 p-1"
              title="Copy Hash"
            >
              {copiedKey === 'calib' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            </button>
          </div>
        </div>

        {/* 3. GPS Metadata Canonical Hash */}
        <div className="bg-slate-950 p-2 rounded-lg border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs font-mono">
          <div className="sm:w-1/3">
            <span className="text-slate-300 font-bold text-[11px] block">GPS Geolocation Payload</span>
            <span className="text-[10px] text-slate-500">
              Lat: {evidenceData.gps?.latitude?.toFixed(4)}, Lon: {evidenceData.gps?.longitude?.toFixed(4)}
            </span>
          </div>
          <div className="sm:w-2/3 flex items-center justify-between gap-2">
            <span className="text-slate-400 truncate text-[11px] select-all">
              {cryptoComp.gps_metadata_sha256}
            </span>
            <button
              onClick={() => copyToClipboard(cryptoComp.gps_metadata_sha256, 'gps')}
              className="text-slate-500 hover:text-cyan-400 shrink-0 p-1"
              title="Copy Hash"
            >
              {copiedKey === 'gps' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            </button>
          </div>
        </div>

        {/* 4. Operator & Reagent Kit */}
        <div className="bg-slate-950 p-2 rounded-lg border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs font-mono">
          <div className="sm:w-1/3">
            <span className="text-slate-300 font-bold text-[11px] block">Operator & Kit Batch</span>
            <span className="text-[10px] text-slate-500">
              {evidenceData.operator?.officer_badge} ({evidenceData.operator?.kit_batch_lot})
            </span>
          </div>
          <div className="sm:w-2/3 flex items-center justify-between gap-2">
            <span className="text-slate-400 truncate text-[11px] select-all">
              {cryptoComp.operator_metadata_sha256}
            </span>
            <button
              onClick={() => copyToClipboard(cryptoComp.operator_metadata_sha256, 'operator')}
              className="text-slate-500 hover:text-cyan-400 shrink-0 p-1"
              title="Copy Hash"
            >
              {copiedKey === 'operator' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            </button>
          </div>
        </div>

        {/* 5. Classification Hash */}
        <div className="bg-slate-950 p-2 rounded-lg border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs font-mono">
          <div className="sm:w-1/3">
            <span className="text-slate-300 font-bold text-[11px] block">Classification Result</span>
            <span className="text-[10px] text-slate-500">
              {evidenceData.classification?.presumptive_substance} ({evidenceData.classification?.confidence_percent}%)
            </span>
          </div>
          <div className="sm:w-2/3 flex items-center justify-between gap-2">
            <span className="text-slate-400 truncate text-[11px] select-all">
              {cryptoComp.classification_sha256}
            </span>
            <button
              onClick={() => copyToClipboard(cryptoComp.classification_sha256, 'class')}
              className="text-slate-500 hover:text-cyan-400 shrink-0 p-1"
              title="Copy Hash"
            >
              {copiedKey === 'class' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
