import React from 'react';
import { X, Download, HelpCircle, Palette, CheckCircle2 } from 'lucide-react';

export default function ReferenceCardModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-xl w-full p-4 sm:p-6 shadow-2xl relative my-auto">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5 mb-3">
          <div className="p-2 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-800">
            <Palette className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white uppercase tracking-wide">
              Standardized Forensic Reference Color Card
            </h3>
            <p className="text-xs text-slate-400">
              Calibrated multi-spectral color targets for OpenCV illumination normalization
            </p>
          </div>
        </div>

        {/* Card Preview */}
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 mb-4 flex flex-col items-center">
          <img
            src="/api/reference-card-template"
            alt="Reference Card Template"
            className="w-full max-w-md rounded-lg shadow-md border border-slate-700"
          />
          <a
            href="/api/reference-card-template"
            download="forensic_reference_card_template.png"
            className="mt-3 px-3 py-1.5 rounded-lg bg-cyan-700 hover:bg-cyan-600 text-white text-xs font-medium flex items-center gap-1.5 shadow transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Printable Reference Card (PNG)</span>
          </a>
        </div>

        {/* Field Instructions */}
        <div className="space-y-2 text-xs text-slate-300 mb-4">
          <h4 className="font-bold text-white text-xs uppercase tracking-wider font-mono">
            Field Placement Instructions:
          </h4>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>
              Place the reference card flat on the same horizontal plane as the test kit reaction ampoule.
            </span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>
              Ensure identical ambient illumination hits both the reference card and the reaction liquid (avoid casting shadows with your phone or body).
            </span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>
              Align the card inside the yellow AR targeting box and the test tube in the green box.
            </span>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
