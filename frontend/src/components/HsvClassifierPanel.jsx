import React from 'react';
import { Target, AlertTriangle, ShieldCheck, Zap, Info, ChevronRight, Activity } from 'lucide-react';

export default function HsvClassifierPanel({
  classification,
  hsvMetrics,
}) {
  if (!classification) return null;

  const topMatch = classification.top_match;
  const hsv = hsvMetrics || classification.hsv_metrics || {};
  const candidates = classification.all_candidates || [];

  // Hue angle on 360-degree color circle
  const hue = hsv.hue || 0;
  const sat = hsv.saturation || 0;
  const val = hsv.value || 0;
  const hex = hsv.representative_hex || '#000000';

  const getDangerBadge = (level) => {
    if (!level) return null;
    if (level.includes('CRITICAL')) {
      return 'bg-rose-950/90 text-rose-300 border-rose-700 animate-pulse';
    }
    if (level.includes('HIGH')) {
      return 'bg-amber-950/90 text-amber-300 border-amber-700';
    }
    if (level.includes('LOW') || level.includes('NONE')) {
      return 'bg-emerald-950/90 text-emerald-300 border-emerald-700';
    }
    return 'bg-slate-800 text-slate-300 border-slate-700';
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 sm:p-4 shadow-xl">
      {/* Title */}
      <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-emerald-950/80 text-emerald-400 border border-emerald-800">
            <Target className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wide">
              HSV Colorimetric Chemical Classification
            </h3>
            <p className="text-[11px] text-slate-400">
              Evaluated against forensic colorimetric library for {classification.reagent_name}
            </p>
          </div>
        </div>

        <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
          MATCH: {topMatch?.confidence_percent || 0}%
        </span>
      </div>

      {/* Top Presumptive Match Banner */}
      {topMatch ? (
        <div className="bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border border-slate-700 rounded-xl p-3.5 mb-3 shadow-lg relative overflow-hidden">
          {/* Subtle background glow from sample color */}
          <div
            className="absolute -right-10 -bottom-10 w-36 h-36 rounded-full blur-2xl opacity-20 pointer-events-none"
            style={{ backgroundColor: hex }}
          />

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-start gap-3">
              {/* Measured Color Chip with Hex */}
              <div className="flex flex-col items-center">
                <div
                  className="w-14 h-14 rounded-lg border-2 border-white/80 shadow-md flex items-center justify-center relative"
                  style={{ backgroundColor: hex }}
                >
                  <div className="absolute inset-0 bg-black/10 rounded-lg pointer-events-none" />
                </div>
                <span className="text-[10px] font-mono text-slate-300 mt-1 font-semibold">{hex}</span>
              </div>

              <div>
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${getDangerBadge(topMatch.danger_level)}`}>
                    {topMatch.danger_level}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    {topMatch.schedule}
                  </span>
                </div>

                <h4 className="text-base sm:text-lg font-bold text-white tracking-tight">
                  {topMatch.substance}
                </h4>

                <p className="text-xs text-slate-300 flex items-center gap-1.5 mt-0.5">
                  <span className="text-slate-400">Observed:</span>
                  <span className="font-semibold text-emerald-300">{topMatch.color_name}</span>
                </p>
                <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                  {topMatch.notes}
                </p>
              </div>
            </div>

            {/* Confidence Gauge */}
            <div className="sm:self-center flex sm:flex-col items-center sm:items-end justify-between border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-800">
              <div className="text-right">
                <span className="text-[10px] font-mono text-slate-400 block uppercase">Confidence Index</span>
                <span className="text-xl sm:text-2xl font-mono font-black text-emerald-400">
                  {topMatch.confidence_percent}%
                </span>
              </div>
              <div className="w-24 bg-slate-800 h-2 rounded-full overflow-hidden mt-1">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 rounded-full"
                  style={{ width: `${topMatch.confidence_percent}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-slate-950 p-4 rounded-xl text-center text-slate-400 text-xs">
          No conclusive chemical match found in range.
        </div>
      )}

      {/* HSV Coordinates Breakdown */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 mb-3">
        {/* Hue breakdown */}
        <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="font-mono text-slate-400 text-[10px]">HUE ANGLE (0-360°)</span>
            <span className="font-mono font-bold text-cyan-300">{hue}°</span>
          </div>
          {/* Hue Spectrum Bar */}
          <div
            className="w-full h-3 rounded relative overflow-hidden shadow-inner"
            style={{
              background:
                'linear-gradient(to right, #ff0000 0%, #ffff00 17%, #00ff00 33%, #00ffff 50%, #0000ff 67%, #ff00ff 83%, #ff0000 100%)',
            }}
          >
            {/* Indicator pin */}
            <div
              className="absolute top-0 bottom-0 w-1 bg-white border border-black shadow"
              style={{ left: `${(hue / 360) * 100}%` }}
            />
          </div>
          <span className="text-[9px] text-slate-500 mt-1 block">
            Circular distance mapped against reagent envelope
          </span>
        </div>

        {/* Saturation */}
        <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="font-mono text-slate-400 text-[10px]">SATURATION (0-100%)</span>
            <span className="font-mono font-bold text-purple-300">{sat}%</span>
          </div>
          <div className="w-full bg-slate-800 h-3 rounded overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-slate-600 to-purple-500"
              style={{ width: `${sat}%` }}
            />
          </div>
          <span className="text-[9px] text-slate-500 mt-1 block">
            Chroma intensity: {sat > 50 ? 'Vivid chromophore' : 'Desaturated / pale'}
          </span>
        </div>

        {/* Value */}
        <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="font-mono text-slate-400 text-[10px]">VALUE / BRIGHTNESS (0-100%)</span>
            <span className="font-mono font-bold text-amber-300">{val}%</span>
          </div>
          <div className="w-full bg-slate-800 h-3 rounded overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-black via-slate-600 to-amber-200"
              style={{ width: `${val}%` }}
            />
          </div>
          <span className="text-[9px] text-slate-500 mt-1 block">
            Optical density: {val < 25 ? 'Dense / Opaque' : 'Translucent liquid'}
          </span>
        </div>
      </div>

      {/* Differential Diagnosis Candidates */}
      {candidates.length > 1 && (
        <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-2.5 mb-3">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wide block mb-1.5">
            Ranked Reagent Candidates & Differential Analysis:
          </span>
          <div className="space-y-1.5">
            {candidates.slice(0, 4).map((cand, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between text-xs px-2 py-1 rounded bg-slate-900/60 border border-slate-800/80"
              >
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full border border-white/50"
                    style={{ backgroundColor: cand.target_hex }}
                  />
                  <span className="font-medium text-slate-200">{cand.substance}</span>
                  <span className="text-[10px] text-slate-400 hidden sm:inline">({cand.color_name})</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-slate-300 text-[11px]">
                    {cand.confidence_percent}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Forensic Legal Advisory Notice */}
      <div className="bg-amber-950/40 border border-amber-800/60 rounded-lg p-2.5 flex items-start gap-2 text-amber-300/90 text-xs">
        <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
        <p className="text-[11px] leading-relaxed">
          <span className="font-bold text-amber-300">SWGDRUG Category C Notice:</span> Colorimetric field reagent tests are presumptive screening aids only. Under federal and state forensic standards, positive results are preliminary and non-specific. Confirmation by GC-MS or LC-MS is legally required prior to prosecutorial filing.
        </p>
      </div>
    </div>
  );
}
