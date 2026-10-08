import React, { useState, useEffect } from 'react';
import { Shield, Smartphone, Monitor, Satellite, BatteryCharging, Clock, FileCheck, HelpCircle, Archive, Download } from 'lucide-react';

export default function Header({ 
  viewMode, 
  setViewMode, 
  gpsLocked, 
  officerBadge, 
  onOpenVerifier, 
  onOpenRefCard,
  onOpenLocker,
  lockerCount = 0,
}) {
  const [timeStr, setTimeStr] = useState('');
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [canInstall, setCanInstall] = useState(false);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toUTCString().slice(17, 25) + ' UTC');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setCanInstall(true);
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setCanInstall(false);
    }
  };

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-30 px-3 py-2 sm:px-6">
      {/* Tactical Status Telemetry Bar */}
      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 border-b border-slate-800/60 pb-1.5 mb-2">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className={`inline-block w-2 h-2 rounded-full ${gpsLocked ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
            <Satellite className="w-3 h-3 text-cyan-400" />
            <span className="hidden sm:inline">GNSS:</span> {gpsLocked ? '3D FIX (HIGH)' : 'ACQUIRING...'}
          </span>
          <span className="hidden md:flex items-center gap-1 text-slate-400">
            <Clock className="w-3 h-3 text-slate-500" />
            {timeStr}
          </span>
          <span className="hidden sm:inline text-slate-500">|</span>
          <span className="text-slate-300 font-semibold">UNIT: {officerBadge || 'OFFICER-721'}</span>
        </div>

        <div className="flex items-center gap-3">
          {canInstall && (
            <button
              onClick={handleInstallClick}
              className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-900/80 hover:bg-cyan-800 text-cyan-300 border border-cyan-600 flex items-center gap-1 transition-colors"
            >
              <Download className="w-3 h-3" />
              <span>Install PWA</span>
            </button>
          )}
          <span className="flex items-center gap-1 text-emerald-400">
            <BatteryCharging className="w-3.5 h-3.5" />
            98%
          </span>
          <span className="text-xs font-bold px-1.5 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/80">
            SECURE SHA-256
          </span>
        </div>
      </div>

      {/* Main Header Row */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-600 to-blue-700 p-0.5 flex items-center justify-center shadow-lg shadow-cyan-900/30">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base sm:text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                NARCO-SCAN <span className="text-cyan-400 font-mono text-xs px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-800">FIELD v2.4</span>
              </h1>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Forensic Colorimetric Classifier • OpenCV Calibration • Tamper-Evident Chain of Custody
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2">
          {/* Evidence Locker Button */}
          <button
            onClick={onOpenLocker}
            className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-cyan-800/80 flex items-center gap-1.5 transition-colors relative"
            title="Open Offline Evidence Locker"
          >
            <Archive className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden md:inline">Vault</span>
            {lockerCount > 0 && (
              <span className="w-4 h-4 rounded-full bg-cyan-600 text-[9px] font-bold text-white flex items-center justify-center">
                {lockerCount}
              </span>
            )}
          </button>

          {/* Action Modals */}
          <button
            onClick={onOpenRefCard}
            className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
            title="View Standard Reference Color Card"
          >
            <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden md:inline">Ref Card</span>
          </button>

          <button
            onClick={onOpenVerifier}
            className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
            title="Verify Evidence Integrity"
          >
            <FileCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="hidden sm:inline">Audit Verifier</span>
          </button>

          {/* View Mode Toggle */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5">
            <button
              onClick={() => setViewMode('mobile')}
              className={`p-1.5 rounded text-xs flex items-center gap-1 transition-all ${
                viewMode === 'mobile'
                  ? 'bg-cyan-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Mobile Device Simulation View"
            >
              <Smartphone className="w-4 h-4" />
              <span className="text-[11px] hidden lg:inline font-medium">Handheld</span>
            </button>
            <button
              onClick={() => setViewMode('full')}
              className={`p-1.5 rounded text-xs flex items-center gap-1 transition-all ${
                viewMode === 'full'
                  ? 'bg-cyan-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Workstation Full View"
            >
              <Monitor className="w-4 h-4" />
              <span className="text-[11px] hidden lg:inline font-medium">Full View</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
