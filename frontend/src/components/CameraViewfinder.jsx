import React, { useState, useRef, useEffect } from 'react';
import { Camera, Upload, Flashlight, RefreshCw, Layers, CheckCircle2, AlertCircle, Crosshair, Move, Sliders, RotateCcw } from 'lucide-react';

export default function CameraViewfinder({
  sampleCases,
  selectedCaseId,
  onSelectSampleCase,
  onImageSelected,
  currentImagePreview,
  analyzing,
  customRefRoi,
  setCustomRefRoi,
  customVialRoi,
  setCustomVialRoi,
  onReanalyzeWithRois,
}) {
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const [torchOn, setTorchOn] = useState(false);
  const [facingMode, setFacingMode] = useState('environment');
  const [roiEditMode, setRoiEditMode] = useState(false);
  const [activeTarget, setActiveTarget] = useState('vial'); // 'vial' | 'card'

  const videoRef = useRef(null);
  const fileInputRef = useRef(null);
  const streamRef = useRef(null);
  const containerRef = useRef(null);

  // Default ROI boxes in percentage coordinates (0-100)
  // Ref Card default: left: 8%, top: 28%, width: 36%, height: 38%
  // Vial default: left: 58%, top: 22%, width: 30%, height: 52%
  const [refBox, setRefBox] = useState({ x: 8, y: 28, w: 36, h: 38 });
  const [vialBox, setVialBox] = useState({ x: 58, y: 22, w: 30, h: 52 });

  const startCamera = async () => {
    setCameraError(null);
    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }

      const constraints = {
        video: {
          facingMode: { ideal: facingMode },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setCameraActive(true);
    } catch (err) {
      console.warn('Camera access error:', err);
      setCameraError(
        'Unable to access physical camera. Use file upload or test presets below.'
      );
      setCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  const toggleTorch = async () => {
    if (!streamRef.current) return;
    const track = streamRef.current.getVideoTracks()[0];
    if (track) {
      const capabilities = track.getCapabilities?.() || {};
      if (capabilities.torch) {
        try {
          await track.applyConstraints({
            advanced: [{ torch: !torchOn }],
          });
          setTorchOn(!torchOn);
        } catch (e) {
          console.error(e);
        }
      } else {
        setTorchOn(!torchOn);
      }
    }
  };

  const switchCameraFacing = () => {
    const nextMode = facingMode === 'environment' ? 'user' : 'environment';
    setFacingMode(nextMode);
    if (cameraActive) {
      setTimeout(() => startCamera(), 100);
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (blob) {
          const file = new File([blob], `field_capture_${Date.now()}.jpg`, {
            type: 'image/jpeg',
          });
          stopCamera();
          onImageSelected(file, URL.createObjectURL(blob));
        }
      },
      'image/jpeg',
      0.95
    );
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      stopCamera();
      onImageSelected(file, URL.createObjectURL(file));
    }
  };

  // Tap-to-reposition ROI center
  const handleContainerClick = (e) => {
    if (!roiEditMode || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const clickX = ((e.clientX - rect.left) / rect.width) * 100;
    const clickY = ((e.clientY - rect.top) / rect.height) * 100;

    if (activeTarget === 'vial') {
      const newX = Math.max(0, Math.min(100 - vialBox.w, clickX - vialBox.w / 2));
      const newY = Math.max(0, Math.min(100 - vialBox.h, clickY - vialBox.h / 2));
      const updated = { ...vialBox, x: Math.round(newX), y: Math.round(newY) };
      setVialBox(updated);
      updatePixelRois(refBox, updated);
    } else {
      const newX = Math.max(0, Math.min(100 - refBox.w, clickX - refBox.w / 2));
      const newY = Math.max(0, Math.min(100 - refBox.h, clickY - refBox.h / 2));
      const updated = { ...refBox, x: Math.round(newX), y: Math.round(newY) };
      setRefBox(updated);
      updatePixelRois(updated, vialBox);
    }
  };

  // Convert percentages into standard 640x480 pixel coordinates for backend OpenCV
  const updatePixelRois = (cardPct, vialPct) => {
    const imgW = 640;
    const imgH = 480;

    const rRoi = [
      Math.round((cardPct.x / 100) * imgW),
      Math.round((cardPct.y / 100) * imgH),
      Math.round((cardPct.w / 100) * imgW),
      Math.round((cardPct.h / 100) * imgH),
    ];

    const vRoi = [
      Math.round((vialPct.x / 100) * imgW),
      Math.round((vialPct.y / 100) * imgH),
      Math.round((vialPct.w / 100) * imgW),
      Math.round((vialPct.h / 100) * imgH),
    ];

    if (setCustomRefRoi) setCustomRefRoi(rRoi);
    if (setCustomVialRoi) setCustomVialRoi(vRoi);
  };

  const resetRois = () => {
    const defaultRef = { x: 8, y: 28, w: 36, h: 38 };
    const defaultVial = { x: 58, y: 22, w: 30, h: 52 };
    setRefBox(defaultRef);
    setVialBox(defaultVial);
    updatePixelRois(defaultRef, defaultVial);
  };

  useEffect(() => {
    return () => stopCamera();
  }, []);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-2xl flex flex-col">
      {/* Viewfinder Header Controls */}
      <div className="bg-slate-950 px-3 py-2 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-mono font-semibold tracking-wider text-slate-300 uppercase">
            {cameraActive ? 'OPTICAL SENSOR ACTIVE' : 'FIELD CAPTURE & VIEWFINDER'}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Interactive ROI Toggle Button */}
          {currentImagePreview && !cameraActive && (
            <button
              onClick={() => setRoiEditMode(!roiEditMode)}
              className={`px-2 py-1 rounded-md text-xs font-mono border flex items-center gap-1 transition-colors ${
                roiEditMode
                  ? 'bg-amber-950 text-amber-300 border-amber-600'
                  : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
              }`}
              title="Toggle Interactive Touch ROI Adjustment"
            >
              <Move className="w-3 h-3 text-amber-400" />
              <span>{roiEditMode ? 'Editing Target ROI' : 'Adjust Targets'}</span>
            </button>
          )}

          {cameraActive ? (
            <>
              <button
                onClick={toggleTorch}
                className={`p-1.5 rounded-md text-xs border transition-colors ${
                  torchOn
                    ? 'bg-amber-500/20 text-amber-400 border-amber-500'
                    : 'bg-slate-800 text-slate-300 border-slate-700'
                }`}
                title="Illumination Torch"
              >
                <Flashlight className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={switchCameraFacing}
                className="p-1.5 rounded-md text-xs bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700"
                title="Switch Camera"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={stopCamera}
                className="px-2 py-1 rounded-md text-[11px] font-mono bg-rose-950 text-rose-300 border border-rose-800 hover:bg-rose-900"
              >
                Close Cam
              </button>
            </>
          ) : (
            <button
              onClick={startCamera}
              className="px-2.5 py-1 rounded-md text-xs font-medium bg-cyan-700 hover:bg-cyan-600 text-white flex items-center gap-1.5 shadow-sm transition-colors"
            >
              <Camera className="w-3.5 h-3.5" />
              <span>Open Camera</span>
            </button>
          )}

          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <Upload className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">Upload</span>
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept="image/*"
            className="hidden"
          />
        </div>
      </div>

      {/* Main Viewfinder Canvas / Video Area */}
      <div
        ref={containerRef}
        onClick={handleContainerClick}
        className={`relative aspect-[4/3] sm:aspect-[16/10] bg-black flex items-center justify-center overflow-hidden select-none ${
          roiEditMode ? 'cursor-crosshair' : ''
        }`}
      >
        {cameraActive ? (
          <video
            ref={videoRef}
            playsInline
            autoPlay
            muted
            className="w-full h-full object-cover"
          />
        ) : currentImagePreview ? (
          <img
            src={currentImagePreview}
            alt="Field Capture"
            className="w-full h-full object-contain bg-slate-950 pointer-events-none"
          />
        ) : (
          <div className="text-center p-6 text-slate-500 flex flex-col items-center">
            <Camera className="w-12 h-12 text-slate-700 mb-2 stroke-[1.5]" />
            <p className="text-sm text-slate-400 font-medium">No Image Loaded</p>
            <p className="text-xs text-slate-600 max-w-xs mt-1">
              Select a pre-loaded field case below or snap/upload a photo of your test kit with reference card.
            </p>
          </div>
        )}

        {/* Augmented Reality Alignment HUD Overlay */}
        {(cameraActive || currentImagePreview) && (
          <div className="absolute inset-0 pointer-events-none p-2 sm:p-4 flex flex-col justify-between">
            <div className="relative w-full h-full pointer-events-auto">
              {/* Reference Card Target Box (Yellow) */}
              <div
                onClick={(e) => {
                  e.stopPropagation();
                  setActiveTarget('card');
                }}
                className={`absolute border-2 border-dashed rounded-md backdrop-blur-[1px] transition-all flex flex-col justify-between p-1.5 shadow-lg ${
                  activeTarget === 'card' && roiEditMode
                    ? 'border-amber-300 ring-2 ring-amber-400 bg-amber-500/20'
                    : 'border-amber-400/90 bg-amber-500/10'
                }`}
                style={{
                  left: `${refBox.x}%`,
                  top: `${refBox.y}%`,
                  width: `${refBox.w}%`,
                  height: `${refBox.h}%`,
                  cursor: roiEditMode ? 'pointer' : 'default',
                }}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[9px] sm:text-[10px] font-mono font-bold text-amber-300 bg-black/75 px-1 py-0.5 rounded border border-amber-500/50">
                    REF COLOR CARD
                  </span>
                  <div className="w-2 h-2 rounded-full bg-amber-400" />
                </div>
                {roiEditMode && activeTarget === 'card' && (
                  <div className="text-center text-[9px] font-mono text-amber-200 bg-black/80 py-0.5 rounded animate-pulse">
                    TOUCH TO MOVE CARD
                  </div>
                )}
              </div>

              {/* Reaction Vial Target Box (Emerald Green) */}
              <div
                onClick={(e) => {
                  e.stopPropagation();
                  setActiveTarget('vial');
                }}
                className={`absolute border-2 border-dashed rounded-md backdrop-blur-[1px] transition-all flex flex-col justify-between p-1.5 shadow-lg ${
                  activeTarget === 'vial' && roiEditMode
                    ? 'border-emerald-300 ring-2 ring-emerald-400 bg-emerald-500/20'
                    : 'border-emerald-400/90 bg-emerald-500/10'
                }`}
                style={{
                  left: `${vialBox.x}%`,
                  top: `${vialBox.y}%`,
                  width: `${vialBox.w}%`,
                  height: `${vialBox.h}%`,
                  cursor: roiEditMode ? 'pointer' : 'default',
                }}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[9px] sm:text-[10px] font-mono font-bold text-emerald-300 bg-black/75 px-1 py-0.5 rounded border border-emerald-500/50">
                    TEST VIAL / WELL
                  </span>
                  <div className="w-2 h-2 rounded-full bg-emerald-400" />
                </div>
                {roiEditMode && activeTarget === 'vial' && (
                  <div className="text-center text-[9px] font-mono text-emerald-200 bg-black/80 py-0.5 rounded animate-pulse">
                    TOUCH TO MOVE VIAL
                  </div>
                )}
              </div>

              {/* Center Crosshair Indicator */}
              <div className="absolute inset-0 flex items-center justify-center opacity-30 pointer-events-none">
                <Crosshair className="w-10 h-10 text-cyan-400 stroke-[1]" />
              </div>
            </div>

            {/* Viewfinder Bottom Status Line */}
            <div className="flex items-center justify-between text-[10px] font-mono text-white/90 bg-slate-950/70 backdrop-blur-md px-2.5 py-1 rounded border border-white/10 pointer-events-none">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                OPENCV CALIBRATION READY
              </span>
              <span>SHA-256 INTEGRITY ACTIVE</span>
            </div>
          </div>
        )}

        {/* Shutter Button when live camera is running */}
        {cameraActive && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20">
            <button
              onClick={capturePhoto}
              className="w-16 h-16 rounded-full border-4 border-white bg-red-600 hover:bg-red-500 active:scale-95 flex items-center justify-center shadow-2xl transition-all"
              title="Capture Image"
            >
              <div className="w-6 h-6 rounded-full bg-white" />
            </button>
          </div>
        )}

        {/* Processing Indicator Overlay */}
        {analyzing && (
          <div className="absolute inset-0 bg-slate-950/85 backdrop-blur-sm flex flex-col items-center justify-center z-30">
            <div className="relative w-16 h-16 mb-4">
              <div className="absolute inset-0 border-4 border-cyan-500/30 rounded-full" />
              <div className="absolute inset-0 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin" />
              <Crosshair className="w-6 h-6 text-cyan-400 absolute inset-0 m-auto" />
            </div>
            <p className="text-base font-bold text-white tracking-wide">
              RUNNING OPENCV CALIBRATION & CLASSIFICATION
            </p>
            <p className="text-xs font-mono text-cyan-400 mt-1">
              Extracting Reference Swatches • HSV Distance • SHA-256 Hashing...
            </p>
          </div>
        )}
      </div>

      {/* Interactive Touch ROI Control Bar (Visible when in Edit Mode) */}
      {roiEditMode && currentImagePreview && (
        <div className="bg-slate-950 p-2.5 border-t border-amber-900/60 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Target to Position:</span>
            <button
              onClick={() => setActiveTarget('vial')}
              className={`px-2 py-1 rounded text-xs font-bold border transition-colors ${
                activeTarget === 'vial'
                  ? 'bg-emerald-950 text-emerald-300 border-emerald-500'
                  : 'bg-slate-900 text-slate-400 border-slate-800'
              }`}
            >
              Reaction Vial (Green)
            </button>
            <button
              onClick={() => setActiveTarget('card')}
              className={`px-2 py-1 rounded text-xs font-bold border transition-colors ${
                activeTarget === 'card'
                  ? 'bg-amber-950 text-amber-300 border-amber-500'
                  : 'bg-slate-900 text-slate-400 border-slate-800'
              }`}
            >
              Ref Card (Yellow)
            </button>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-auto">
            <button
              onClick={resetRois}
              className="px-2 py-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-400 border border-slate-800 flex items-center gap-1"
              title="Reset to Default Coordinates"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
            <button
              onClick={onReanalyzeWithRois}
              className="px-3 py-1 rounded font-bold bg-amber-600 hover:bg-amber-500 text-white flex items-center gap-1.5 shadow"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Apply & Re-calibrate</span>
            </button>
          </div>
        </div>
      )}

      {cameraError && (
        <div className="px-3 py-2 bg-amber-950/60 border-t border-amber-800 text-amber-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-amber-400" />
          <span>{cameraError}</span>
        </div>
      )}

      {/* Pre-loaded Field Presets / Sample Cases Selector */}
      <div className="bg-slate-950 p-2.5 sm:p-3 border-t border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-mono text-slate-400 font-semibold uppercase flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            Pre-loaded Field Test Samples (Realistic Lighting & Kits)
          </span>
          <span className="text-[10px] text-cyan-400 font-mono">Click to Instant Test</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
          {sampleCases?.map((c) => {
            const isSelected = selectedCaseId === c.id;
            return (
              <button
                key={c.id}
                onClick={() => onSelectSampleCase(c)}
                className={`p-2 rounded-lg border text-left transition-all ${
                  isSelected
                    ? 'border-cyan-400 bg-cyan-950/60 ring-1 ring-cyan-400'
                    : 'border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 text-slate-300'
                }`}
              >
                <div className="flex items-center justify-between mb-0.5">
                  <span className="text-[11px] font-bold text-white uppercase truncate">
                    {c.reagent}
                  </span>
                  {isSelected && <CheckCircle2 className="w-3 h-3 text-cyan-400 shrink-0" />}
                </div>
                <p className="text-[10px] font-medium text-cyan-300 truncate">
                  {c.expected_substance}
                </p>
                <p className="text-[9px] text-slate-400 truncate mt-0.5">
                  {c.lighting?.split('(')[0]}
                </p>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
