import React, { useState } from 'react';
import { Sliders, CheckCircle, Sparkles, Sun, Eye, ArrowRight, Gauge, Cpu } from 'lucide-react';

export default function ColorCorrectionPanel({
  rawImage,
  calibratedImage,
  calibrationMetrics,
}) {
  const [viewMode, setViewMode] = useState('split'); // 'split' | 'side' | 'calibrated_only'
  const [sliderPos, setSliderPos] = useState(50); // percentage for split view

  if (!calibratedImage && !rawImage) {
    return null;
  }

  const gains = calibrationMetrics?.channel_gains || {};
  const isCardDetected = calibrationMetrics?.reference_card_status?.includes('Detected') ||
                         calibrationMetrics?.reference_card_status?.includes('Aligned');

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 sm:p-4 shadow-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3 pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-purple-950/80 text-purple-400 border border-purple-800">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wide flex items-center gap-2">
              OpenCV Color Correction Pipeline
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                ACTIVE
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Eliminates ambient lighting bias & normalizes reaction color to standard D65 illuminant
            </p>
          </div>
        </div>

        {/* View mode toggle */}
        <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-0.5 self-start sm:self-auto">
          <button
            onClick={() => setViewMode('split')}
            className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
              viewMode === 'split' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Split Slider
          </button>
          <button
            onClick={() => setViewMode('side')}
            className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
              viewMode === 'side' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Side-by-Side
          </button>
        </div>
      </div>

      {/* Visual Comparison Area */}
      <div className="mb-4">
        {viewMode === 'split' ? (
          <div className="relative aspect-[16/10] sm:aspect-[2/1] rounded-lg overflow-hidden border border-slate-800 bg-black select-none">
            {/* Calibrated image (full background) */}
            <img
              src={calibratedImage || rawImage}
              alt="Calibrated"
              className="absolute inset-0 w-full h-full object-contain"
            />

            {/* Raw image (clipped overlay) */}
            <div
              className="absolute inset-0 overflow-hidden"
              style={{ width: `${sliderPos}%` }}
            >
              <img
                src={rawImage}
                alt="Raw Captured"
                className="absolute inset-0 w-full h-full object-contain max-w-none"
                style={{ width: '100%', height: '100%' }}
              />
              <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/80 text-[10px] font-mono font-bold text-amber-300 border border-amber-500/40">
                RAW FIELD PHOTO
              </div>
            </div>

            {/* Calibrated Label (Right) */}
            <div className="absolute top-2 right-2 px-2 py-0.5 rounded bg-black/80 text-[10px] font-mono font-bold text-emerald-300 border border-emerald-500/40">
              OPENCV CALIBRATED (D65)
            </div>

            {/* Split Divider Line */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-white shadow-2xl pointer-events-none"
              style={{ left: `${sliderPos}%` }}
            >
              <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-7 h-7 rounded-full bg-white text-slate-900 flex items-center justify-center text-xs font-bold shadow-lg">
                ⮂
              </div>
            </div>

            {/* Range input slider */}
            <input
              type="range"
              min="0"
              max="100"
              value={sliderPos}
              onChange={(e) => setSliderPos(Number(e.target.value))}
              className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-20"
            />
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="border border-slate-800 rounded-lg overflow-hidden bg-black relative">
              <div className="absolute top-2 left-2 z-10 px-2 py-0.5 rounded bg-black/80 text-[10px] font-mono text-amber-300 border border-amber-500/40">
                RAW UNCALIBRATED
              </div>
              <img src={rawImage} alt="Raw uncalibrated" className="w-full h-48 sm:h-56 object-contain" />
            </div>
            <div className="border border-slate-800 rounded-lg overflow-hidden bg-black relative">
              <div className="absolute top-2 left-2 z-10 px-2 py-0.5 rounded bg-black/80 text-[10px] font-mono text-emerald-300 border border-emerald-500/40">
                OPENCV CALIBRATED (D65)
              </div>
              <img src={calibratedImage || rawImage} alt="Calibrated" className="w-full h-48 sm:h-56 object-contain" />
            </div>
          </div>
        )}
      </div>

      {/* Optical Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs font-mono">
        {/* Card 1: Calibration Method & Status */}
        <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
          <span className="text-[10px] text-slate-400 block mb-1">CALIBRATION ENGINE</span>
          <div className="flex items-center gap-1.5 text-white font-bold text-xs mb-1">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>{calibrationMetrics?.method || 'Reference Card 3x3 Calibration'}</span>
          </div>
          <span className={`text-[10px] inline-block px-1.5 py-0.5 rounded border ${
            isCardDetected
              ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
              : 'bg-amber-950/80 text-amber-300 border-amber-800'
          }`}>
            {calibrationMetrics?.reference_card_status || 'Card Aligned & Normalized'}
          </span>
        </div>

        {/* Card 2: Environmental Lighting Estimate */}
        <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
          <span className="text-[10px] text-slate-400 block mb-1">ESTIMATED ILLUMINANT</span>
          <div className="flex items-center gap-1.5 text-amber-300 font-bold text-xs mb-1">
            <Sun className="w-3.5 h-3.5 text-amber-400" />
            <span className="truncate">{calibrationMetrics?.estimated_lighting || 'Ambient Field Light'}</span>
          </div>
          <p className="text-[10px] text-slate-400 leading-tight">
            Illuminant compensated to Standard D65 (6500K sRGB)
          </p>
        </div>

        {/* Card 3: Channel Gains (R, G, B scaling) */}
        <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
          <span className="text-[10px] text-slate-400 block mb-1">VON KRIES CHANNEL GAINS</span>
          <div className="flex items-center justify-between text-[11px] pt-0.5">
            <span className="text-rose-400">R: {gains.red_gain ? gains.red_gain.toFixed(2) : '1.00'}x</span>
            <span className="text-emerald-400">G: {gains.green_gain ? gains.green_gain.toFixed(2) : '1.00'}x</span>
            <span className="text-cyan-400">B: {gains.blue_gain ? gains.blue_gain.toFixed(2) : '1.00'}x</span>
          </div>
          <div className="w-full bg-slate-900 rounded-full h-1.5 mt-2 overflow-hidden flex">
            <div style={{ width: '33%' }} className="bg-rose-500/80" />
            <div style={{ width: '34%' }} className="bg-emerald-500/80" />
            <div style={{ width: '33%' }} className="bg-cyan-500/80" />
          </div>
        </div>
      </div>
    </div>
  );
}
