import React, { useState, useEffect } from 'react';
import { X, Archive, Download, Trash2, Eye, ShieldCheck, MapPin, Search, Calendar, FileText, CheckCircle2 } from 'lucide-react';
import { getSavedEvidenceRecords, deleteEvidenceRecord, exportEvidenceLockerJson } from '../services/evidenceLocker';

export default function EvidenceLockerModal({
  isOpen,
  onClose,
  onLoadRecord,
  onVerifyRecord,
}) {
  if (!isOpen) return null;

  const [records, setRecords] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [copiedId, setCopiedId] = useState(null);

  useEffect(() => {
    setRecords(getSavedEvidenceRecords());
  }, [isOpen]);

  const handleDelete = (recordId) => {
    if (confirm(`Delete record ${recordId} from device locker?`)) {
      const updated = deleteEvidenceRecord(recordId);
      setRecords(updated);
    }
  };

  const copyHash = (hash, id) => {
    navigator.clipboard.writeText(hash);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredRecords = records.filter((r) => {
    const q = searchTerm.toLowerCase();
    return (
      r.record_id?.toLowerCase().includes(q) ||
      r.substance?.toLowerCase().includes(q) ||
      r.reagent_name?.toLowerCase().includes(q) ||
      r.officer_badge?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-3xl w-full p-4 sm:p-6 shadow-2xl relative my-auto flex flex-col max-h-[90vh]">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-800">
              <Archive className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white uppercase tracking-wide flex items-center gap-2">
                Offline Evidence Locker
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                  {records.length} {records.length === 1 ? 'RECORD' : 'RECORDS'}
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Encrypted local device vault with canonical SHA-256 chain of custody
              </p>
            </div>
          </div>

          {records.length > 0 && (
            <button
              onClick={exportEvidenceLockerJson}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 flex items-center gap-1.5 self-start sm:self-auto transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              <span>Export All Vault (JSON)</span>
            </button>
          )}
        </div>

        {/* Search Bar */}
        {records.length > 0 && (
          <div className="relative mb-3">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by substance, reagent, officer badge, or record ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs font-mono text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
        )}

        {/* Records List */}
        <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
          {records.length === 0 ? (
            <div className="text-center py-12 text-slate-500 flex flex-col items-center">
              <Archive className="w-12 h-12 text-slate-700 mb-2 stroke-[1.5]" />
              <p className="text-sm text-slate-400 font-medium">No Evidence Records in Local Vault</p>
              <p className="text-xs text-slate-600 max-w-sm mt-1">
                Any field test you capture or analyze is automatically stored here with its full cryptographic chain of custody.
              </p>
            </div>
          ) : filteredRecords.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-xs">
              No records matching "{searchTerm}".
            </div>
          ) : (
            filteredRecords.map((rec) => (
              <div
                key={rec.record_id}
                className="bg-slate-950 border border-slate-800/80 hover:border-slate-700 rounded-xl p-3 transition-all"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-start gap-3">
                    {/* Thumbnail */}
                    {rec.thumbnail_base64 ? (
                      <img
                        src={
                          rec.thumbnail_base64.startsWith('data:')
                            ? rec.thumbnail_base64
                            : `data:image/jpeg;base64,${rec.thumbnail_base64}`
                        }
                        alt="Thumbnail"
                        className="w-16 h-16 rounded-lg object-cover border border-slate-700 bg-black shrink-0"
                      />
                    ) : (
                      <div
                        className="w-16 h-16 rounded-lg border border-slate-700 flex items-center justify-center shrink-0"
                        style={{ backgroundColor: rec.hex_color }}
                      >
                        <span className="text-[9px] font-mono font-bold text-white bg-black/60 px-1 py-0.5 rounded">
                          {rec.hex_color}
                        </span>
                      </div>
                    )}

                    <div>
                      <div className="flex flex-wrap items-center gap-1.5 mb-1">
                        <span className="font-mono font-bold text-xs text-cyan-300">
                          {rec.record_id}
                        </span>
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                          {rec.reagent_name}
                        </span>
                        <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                          {rec.confidence}%
                        </span>
                      </div>

                      <h4 className="text-sm font-bold text-white">
                        {rec.substance}
                      </h4>

                      <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[10px] font-mono text-slate-400 mt-1">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3 text-slate-500" />
                          {rec.timestamp_utc?.slice(0, 19).replace('T', ' ')} UTC
                        </span>
                        {rec.gps && (
                          <span className="flex items-center gap-1 text-cyan-400">
                            <MapPin className="w-3 h-3" />
                            {rec.gps.latitude?.toFixed(4)}°, {rec.gps.longitude?.toFixed(4)}°
                          </span>
                        )}
                        <span className="text-slate-500">
                          UNIT: {rec.officer_badge || 'OFFICER'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-1.5 border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-800 shrink-0">
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => {
                          onLoadRecord(rec);
                          onClose();
                        }}
                        className="px-2.5 py-1 rounded-md text-xs font-medium bg-cyan-700 hover:bg-cyan-600 text-white flex items-center gap-1 transition-colors"
                        title="Load into Main Viewfinder"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Load</span>
                      </button>

                      <button
                        onClick={() => {
                          onVerifyRecord(rec.manifest);
                          onClose();
                        }}
                        className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-slate-700 flex items-center gap-1 transition-colors"
                        title="Verify SHA-256 Hashes"
                      >
                        <ShieldCheck className="w-3 h-3 text-emerald-400" />
                        <span>Verify</span>
                      </button>

                      <button
                        onClick={() => handleDelete(rec.record_id)}
                        className="p-1 rounded-md text-slate-500 hover:text-rose-400 hover:bg-rose-950/40 transition-colors"
                        title="Delete Record"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {/* Truncated Root Hash */}
                    <button
                      onClick={() => copyHash(rec.chain_of_custody_hash, rec.record_id)}
                      className="text-[9px] font-mono text-slate-500 hover:text-cyan-400 truncate max-w-[150px]"
                      title="Click to copy full Merkle root"
                    >
                      {copiedId === rec.record_id ? '✓ Copied' : `Root: ${rec.chain_of_custody_hash?.slice(0, 12)}...`}
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-800">
          <span className="text-[11px] font-mono text-slate-500">
            Offline Storage: HTML5 Vault (Local Device)
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
