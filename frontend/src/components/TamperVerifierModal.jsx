import React, { useState } from 'react';
import { X, ShieldAlert, ShieldCheck, CheckCircle2, AlertTriangle, RefreshCw, Terminal, Sliders } from 'lucide-react';

export default function TamperVerifierModal({
  isOpen,
  onClose,
  initialManifest,
}) {
  if (!isOpen) return null;

  const [manifestText, setManifestText] = useState(
    initialManifest ? JSON.stringify(initialManifest, null, 2) : ''
  );
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [activeTamperMode, setActiveTamperMode] = useState('none');

  const runVerification = async (currentJsonText) => {
    setVerifying(true);
    setVerificationResult(null);
    try {
      const formData = new FormData();
      formData.append('manifest_json', currentJsonText || manifestText);

      const res = await fetch('/api/verify', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Verification request failed');
      }

      const data = await res.json();
      setVerificationResult(data);
    } catch (e) {
      setVerificationResult({
        is_authentic: false,
        verdict: 'VERIFICATION_ERROR',
        discrepancies: [{ target: 'Format', error: e.message }],
        checks_passed: [],
      });
    } finally {
      setVerifying(false);
    }
  };

  const applyTamperSimulation = (type) => {
    if (!initialManifest) return;
    const cloned = JSON.parse(JSON.stringify(initialManifest));

    if (type === 'gps') {
      cloned.evidence_data.gps.latitude += 0.00125;
      setActiveTamperMode('gps');
    } else if (type === 'substance') {
      cloned.evidence_data.classification.presumptive_substance = 'Negative / Sugar (Altered)';
      setActiveTamperMode('substance');
    } else if (type === 'badge') {
      cloned.evidence_data.operator.officer_badge = 'UNAUTHORIZED-AGENT-99';
      setActiveTamperMode('badge');
    } else {
      setActiveTamperMode('none');
    }

    const newJson = JSON.stringify(cloned, null, 2);
    setManifestText(newJson);
    runVerification(newJson);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-4 sm:p-6 shadow-2xl relative my-auto">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-2.5 mb-3">
          <div className="p-2 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-800">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white uppercase tracking-wide">
              Forensic Tamper Verification & Audit Lab
            </h3>
            <p className="text-xs text-slate-400">
              Validates cryptographic bit-level integrity against SHA-256 Merkle root
            </p>
          </div>
        </div>

        {/* Tamper Simulation Quick Action Buttons */}
        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-slate-300 font-bold uppercase flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-cyan-400" />
              Simulate Field Tampering Scenarios:
            </span>
            <span className="text-[10px] text-slate-400 font-mono">
              Mode: <span className="text-cyan-300 uppercase">{activeTamperMode}</span>
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            <button
              onClick={() => applyTamperSimulation('none')}
              className={`p-2 rounded-lg border font-mono transition-all text-left ${
                activeTamperMode === 'none'
                  ? 'border-emerald-500 bg-emerald-950/80 text-emerald-300'
                  : 'border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800'
              }`}
            >
              <div className="font-bold text-[11px]">Original Sealed</div>
              <div className="text-[9px] text-slate-400">Authentic Manifest</div>
            </button>

            <button
              onClick={() => applyTamperSimulation('gps')}
              className={`p-2 rounded-lg border font-mono transition-all text-left ${
                activeTamperMode === 'gps'
                  ? 'border-rose-500 bg-rose-950/80 text-rose-300'
                  : 'border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800'
              }`}
            >
              <div className="font-bold text-[11px] text-rose-300">Alter GPS (+0.001°)</div>
              <div className="text-[9px] text-slate-400">Spoof Coordinates</div>
            </button>

            <button
              onClick={() => applyTamperSimulation('substance')}
              className={`p-2 rounded-lg border font-mono transition-all text-left ${
                activeTamperMode === 'substance'
                  ? 'border-rose-500 bg-rose-950/80 text-rose-300'
                  : 'border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800'
              }`}
            >
              <div className="font-bold text-[11px] text-rose-300">Alter Drug Result</div>
              <div className="text-[9px] text-slate-400">Modify Classification</div>
            </button>

            <button
              onClick={() => applyTamperSimulation('badge')}
              className={`p-2 rounded-lg border font-mono transition-all text-left ${
                activeTamperMode === 'badge'
                  ? 'border-rose-500 bg-rose-950/80 text-rose-300'
                  : 'border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800'
              }`}
            >
              <div className="font-bold text-[11px] text-rose-300">Alter Officer ID</div>
              <div className="text-[9px] text-slate-400">Switch Operator Badge</div>
            </button>
          </div>
        </div>

        {/* Verification Result Banner */}
        {verificationResult && (
          <div
            className={`p-3.5 rounded-xl border mb-4 ${
              verificationResult.is_authentic
                ? 'bg-emerald-950/80 border-emerald-600/80 text-emerald-200'
                : 'bg-rose-950/80 border-rose-600/80 text-rose-200'
            }`}
          >
            <div className="flex items-center gap-2 mb-1.5">
              {verificationResult.is_authentic ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              ) : (
                <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0" />
              )}
              <span className="font-mono font-bold text-sm">
                {verificationResult.verdict}
              </span>
            </div>

            {verificationResult.is_authentic ? (
              <div className="text-xs space-y-1 mt-2 text-emerald-300/90 font-mono">
                {verificationResult.checks_passed?.map((chk, i) => (
                  <div key={i} className="flex items-center gap-1.5">
                    <span className="text-emerald-400">✓</span> {chk}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs space-y-1.5 mt-2 font-mono">
                <span className="font-bold text-rose-300 block">Cryptographic Discrepancies:</span>
                {verificationResult.discrepancies?.map((disc, i) => (
                  <div key={i} className="bg-black/40 p-2 rounded border border-rose-800/80">
                    <span className="text-rose-400 font-bold block">[{disc.target}] {disc.error}</span>
                    {disc.expected_hash && (
                      <div className="text-[10px] text-slate-400 mt-1 truncate">
                        Expected: {disc.expected_hash}
                      </div>
                    )}
                    {disc.calculated_hash && (
                      <div className="text-[10px] text-rose-300 truncate">
                        Calculated: {disc.calculated_hash}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Manifest Editor / Raw JSON */}
        <div className="mb-4">
          <label className="text-[11px] font-mono text-slate-400 block mb-1">
            CANONICAL MANIFEST PAYLOAD (JSON):
          </label>
          <textarea
            value={manifestText}
            onChange={(e) => setManifestText(e.target.value)}
            rows={7}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs font-mono text-slate-300 focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300"
          >
            Close
          </button>
          <button
            onClick={() => runVerification(manifestText)}
            disabled={verifying}
            className="px-4 py-2 rounded-lg text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white flex items-center gap-1.5 shadow-lg shadow-cyan-900/30 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
            <span>{verifying ? 'Verifying Hashes...' : 'Re-verify Hashes'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
