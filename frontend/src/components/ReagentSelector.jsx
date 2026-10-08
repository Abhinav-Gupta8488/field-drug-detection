import React, { useState } from 'react';
import { FlaskConical, MapPin, RefreshCw, BadgeAlert, Sparkles, Navigation } from 'lucide-react';

const REAGENTS = [
  {
    id: 'MARQUIS',
    name: 'Marquis',
    subtitle: 'MDMA, Opiates, Amphetamines',
    desc: 'Formaldehyde in conc. H2SO4; General primary presumptive screen.',
    badgeColor: 'border-purple-500/50 bg-purple-950/40 text-purple-300',
    activeRing: 'ring-2 ring-purple-500 border-purple-500 bg-purple-950/70',
  },
  {
    id: 'SCOTT',
    name: 'Scott',
    subtitle: 'Cocaine HCl & Base',
    desc: 'Cobalt(II) thiocyanate; Forms bright royal blue precipitate with cocaine.',
    badgeColor: 'border-cyan-500/50 bg-cyan-950/40 text-cyan-300',
    activeRing: 'ring-2 ring-cyan-500 border-cyan-500 bg-cyan-950/70',
  },
  {
    id: 'MECKE',
    name: 'Mecke',
    subtitle: 'Heroin & Morphine',
    desc: 'Selenious acid in H2SO4; Opiate differentiation (forest green to teal).',
    badgeColor: 'border-emerald-500/50 bg-emerald-950/40 text-emerald-300',
    activeRing: 'ring-2 ring-emerald-500 border-emerald-500 bg-emerald-950/70',
  },
  {
    id: 'MANDELIN',
    name: 'Mandelin',
    subtitle: 'Ketamine & Methadone',
    desc: 'Ammonium vanadate; Distinct orange for ketamine, green for amphetamine.',
    badgeColor: 'border-amber-500/50 bg-amber-950/40 text-amber-300',
    activeRing: 'ring-2 ring-amber-500 border-amber-500 bg-amber-950/70',
  },
  {
    id: 'EHRLICH',
    name: 'Ehrlich',
    subtitle: 'LSD & Indoles',
    desc: 'p-DMAB in ethanol + HCl; Turns purple with indoles (LSD/DMT); negative for NBOMe.',
    badgeColor: 'border-pink-500/50 bg-pink-950/40 text-pink-300',
    activeRing: 'ring-2 ring-pink-500 border-pink-500 bg-pink-950/70',
  },
];

export default function ReagentSelector({
  selectedReagent,
  setSelectedReagent,
  gps,
  setGps,
  operator,
  setOperator,
  isAcquiringGps,
  acquireGps,
}) {
  const [showConfig, setShowConfig] = useState(false);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 sm:p-4 shadow-xl">
      {/* Reagent Selection Tabs */}
      <div className="flex items-center justify-between mb-2">
        <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
          <FlaskConical className="w-4 h-4 text-cyan-400" />
          Select Presumptive Reagent Kit
        </label>
        <button
          onClick={() => setShowConfig(!showConfig)}
          className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 underline"
        >
          {showConfig ? 'Hide Officer Metadata' : 'Edit Officer & Kit Info'}
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mb-3">
        {REAGENTS.map((reagent) => {
          const isSelected = selectedReagent === reagent.id;
          return (
            <button
              key={reagent.id}
              onClick={() => setSelectedReagent(reagent.id)}
              className={`p-2.5 rounded-lg border text-left transition-all relative overflow-hidden ${
                isSelected
                  ? reagent.activeRing
                  : 'border-slate-800 bg-slate-950/60 hover:bg-slate-800/60 text-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-xs text-white uppercase tracking-wide">
                  {reagent.name}
                </span>
                {isSelected && (
                  <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400" />
                )}
              </div>
              <p className="text-[10px] text-slate-400 line-clamp-1 leading-tight">
                {reagent.subtitle}
              </p>
            </button>
          );
        })}
      </div>

      {/* Expandable Officer & Kit Batch Info */}
      {showConfig && (
        <div className="bg-slate-950/80 border border-slate-800/80 rounded-lg p-2.5 mb-3 grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-0.5">OFFICER / BADGE ID</label>
            <input
              type="text"
              value={operator.officer_badge}
              onChange={(e) => setOperator({ ...operator, officer_badge: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs font-mono focus:border-cyan-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-0.5">UNIT / AGENCY</label>
            <input
              type="text"
              value={operator.agency}
              onChange={(e) => setOperator({ ...operator, agency: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs font-mono focus:border-cyan-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-0.5">KIT BATCH LOT #</label>
            <input
              type="text"
              value={operator.kit_batch_lot}
              onChange={(e) => setOperator({ ...operator, kit_batch_lot: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs font-mono focus:border-cyan-500 focus:outline-none"
            />
          </div>
        </div>
      )}

      {/* GPS Telemetry Bar */}
      <div className="bg-slate-950/90 border border-slate-800 rounded-lg px-3 py-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-cyan-950/80 text-cyan-400 border border-cyan-800/80">
            <MapPin className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase text-slate-400">GPS TELEMETRY (CANONICAL):</span>
              <span className="text-xs font-mono font-semibold text-cyan-300">
                {gps.latitude?.toFixed(6)}°, {gps.longitude?.toFixed(6)}°
              </span>
              {gps.altitude && (
                <span className="text-[10px] font-mono text-slate-400 hidden md:inline">
                  Alt: {gps.altitude.toFixed(1)}m
                </span>
              )}
            </div>
            <p className="text-[10px] text-slate-400 flex items-center gap-1.5 font-mono">
              <span>{gps.location_description || 'Active Geolocation'}</span>
              <span className="text-emerald-400">±{gps.accuracy || 3.5}m acc</span>
            </p>
          </div>
        </div>

        <button
          onClick={acquireGps}
          disabled={isAcquiringGps}
          className="self-end sm:self-center px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-cyan-300 border border-slate-700 flex items-center gap-1.5 font-mono transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3 h-3 ${isAcquiringGps ? 'animate-spin' : ''}`} />
          <span>{isAcquiringGps ? 'Locking GNSS...' : 'Refresh Fix'}</span>
        </button>
      </div>
    </div>
  );
}
