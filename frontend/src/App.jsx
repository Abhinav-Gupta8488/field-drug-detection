import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ReagentSelector from './components/ReagentSelector';
import CameraViewfinder from './components/CameraViewfinder';
import ColorCorrectionPanel from './components/ColorCorrectionPanel';
import HsvClassifierPanel from './components/HsvClassifierPanel';
import TamperEvidentRecord from './components/TamperEvidentRecord';
import TamperVerifierModal from './components/TamperVerifierModal';
import ReferenceCardModal from './components/ReferenceCardModal';
import EvidenceLockerModal from './components/EvidenceLockerModal';
import { saveEvidenceRecord, getSavedEvidenceRecords } from './services/evidenceLocker';
import { ShieldCheck, Smartphone, CheckCircle2, ChevronRight, Activity, FileCheck, Layers } from 'lucide-react';

export default function App() {
  const [viewMode, setViewMode] = useState('mobile'); // 'mobile' | 'full'
  const [selectedReagent, setSelectedReagent] = useState('MARQUIS');
  const [gps, setGps] = useState({
    latitude: 37.774929,
    longitude: -122.419416,
    altitude: 16.2,
    accuracy: 3.8,
    location_description: 'Tenderloin Field Interdiction Zone, San Francisco',
  });
  const [operator, setOperator] = useState({
    officer_badge: 'SFPD-NARCO-902',
    agency: 'Narcotics Task Force',
    kit_batch_lot: 'LOT-MQ-2026-X4',
  });
  const [isAcquiringGps, setIsAcquiringGps] = useState(false);

  const [sampleCases, setSampleCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState(null);

  const [currentImageFile, setCurrentImageFile] = useState(null);
  const [currentImagePreview, setCurrentImagePreview] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  // Custom Interactive Touch ROIs [x, y, w, h] in pixels
  const [customRefRoi, setCustomRefRoi] = useState(null);
  const [customVialRoi, setCustomVialRoi] = useState(null);

  const [isVerifierOpen, setIsVerifierOpen] = useState(false);
  const [isRefCardOpen, setIsRefCardOpen] = useState(false);
  const [isLockerOpen, setIsLockerOpen] = useState(false);
  const [lockerCount, setLockerCount] = useState(0);
  const [verifierManifest, setVerifierManifest] = useState(null);

  // Refresh locker count
  const refreshLockerCount = () => {
    const list = getSavedEvidenceRecords();
    setLockerCount(list.length);
  };

  // Load sample cases and locker count on startup
  useEffect(() => {
    refreshLockerCount();
    fetch('/api/sample-cases', {
      headers: { 'Bypass-Tunnel-Reminder': 'true' },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.cases) {
          setSampleCases(data.cases);
          if (data.cases.length > 0) {
            handleSelectSampleCase(data.cases[0]);
          }
        }
      })
      .catch((err) => console.error('Failed to load sample cases', err));
  }, []);

  // GPS Acquisition
  const acquireGps = () => {
    setIsAcquiringGps(true);
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setGps({
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            altitude: pos.coords.altitude || 18.0,
            accuracy: Math.round(pos.coords.accuracy || 4.0),
            location_description: 'Acquired GNSS Real-Time Location',
          });
          setIsAcquiringGps(false);
        },
        (err) => {
          console.warn('Geolocation failed or permission denied, using simulated coordinates', err);
          setGps((prev) => ({
            ...prev,
            accuracy: 3.2,
            location_description: 'Simulated High-Precision Field GNSS Fix',
          }));
          setIsAcquiringGps(false);
        },
        { enableHighAccuracy: true, timeout: 8000 }
      );
    } else {
      setIsAcquiringGps(false);
    }
  };

  // Run full analysis on backend
  const runAnalysis = async (file, reagentToUse, gpsToUse, operatorToUse, refRoi, vialRoi) => {
    setAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('reagent_type', reagentToUse || selectedReagent);
      formData.append('latitude', (gpsToUse || gps).latitude);
      formData.append('longitude', (gpsToUse || gps).longitude);
      if ((gpsToUse || gps).altitude) {
        formData.append('altitude', (gpsToUse || gps).altitude);
      }
      formData.append('accuracy', (gpsToUse || gps).accuracy || 5.0);
      formData.append(
        'location_description',
        (gpsToUse || gps).location_description || 'Field Position'
      );
      formData.append('officer_badge', (operatorToUse || operator).officer_badge);
      formData.append('agency', (operatorToUse || operator).agency);
      formData.append('kit_batch_lot', (operatorToUse || operator).kit_batch_lot);

      const finalRefRoi = refRoi || customRefRoi;
      const finalVialRoi = vialRoi || customVialRoi;

      if (finalRefRoi) {
        formData.append('ref_card_roi', JSON.stringify(finalRefRoi));
      }
      if (finalVialRoi) {
        formData.append('vial_roi', JSON.stringify(finalVialRoi));
      }

      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Bypass-Tunnel-Reminder': 'true',
        },
        body: formData,
      });

      const responseText = await res.text();
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseErr) {
        if (responseText.includes('<!DOCTYPE') || responseText.includes('localtunnel')) {
          throw new Error(
            'Localtunnel splash page detected. Open the tunnel URL directly in your browser and click "Click to Continue", or switch to ngrok.'
          );
        }
        throw new Error(`Server returned non-JSON response (${res.status}): ${responseText.slice(0, 100)}`);
      }

      if (!res.ok) {
        throw new Error(data.detail || 'Analysis request failed');
      }

      setAnalysisResult(data);
      setVerifierManifest(data.manifest);

      // Auto-save to Offline Evidence Locker
      saveEvidenceRecord(data);
      refreshLockerCount();
    } catch (err) {
      console.error('Analysis error:', err);
      alert(`Analysis error: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  // Handle selecting one of the pre-loaded sample cases
  const handleSelectSampleCase = async (sampleCase) => {
    setSelectedCaseId(sampleCase.id);
    setSelectedReagent(sampleCase.reagent);
    setCustomRefRoi(sampleCase.ref_card_roi || null);
    setCustomVialRoi(sampleCase.vial_roi || null);

    if (sampleCase.gps) {
      setGps(sampleCase.gps);
    }

    try {
      setAnalyzing(true);
      const imgRes = await fetch(`/api/sample-image/${sampleCase.id}`, {
        headers: { 'Bypass-Tunnel-Reminder': 'true' },
      });
      const blob = await imgRes.blob();
      const file = new File([blob], sampleCase.id, { type: 'image/jpeg' });
      const previewUrl = URL.createObjectURL(blob);

      setCurrentImageFile(file);
      setCurrentImagePreview(previewUrl);

      await runAnalysis(
        file,
        sampleCase.reagent,
        sampleCase.gps,
        operator,
        sampleCase.ref_card_roi,
        sampleCase.vial_roi
      );
    } catch (err) {
      console.error('Error fetching sample image:', err);
      setAnalyzing(false);
    }
  };

  // Handle live camera capture or user file upload
  const handleImageSelected = (file, previewUrl) => {
    setSelectedCaseId(null);
    setCurrentImageFile(file);
    setCurrentImagePreview(previewUrl);
    runAnalysis(file, selectedReagent, gps, operator, customRefRoi, customVialRoi);
  };

  // Re-run analysis with newly dragged/touched ROIs
  const handleReanalyzeWithRois = () => {
    if (currentImageFile) {
      runAnalysis(currentImageFile, selectedReagent, gps, operator, customRefRoi, customVialRoi);
    }
  };

  // Load a record from the Offline Evidence Locker
  const handleLoadFromLocker = (savedItem) => {
    setAnalysisResult({
      manifest: savedItem.manifest,
      classification: savedItem.classification,
      hsv_metrics: savedItem.hsv_metrics,
      calibration_metrics: savedItem.calibration_metrics,
      images: {
        calibrated_base64: savedItem.thumbnail_base64?.startsWith('data:')
          ? savedItem.thumbnail_base64
          : `data:image/jpeg;base64,${savedItem.thumbnail_base64}`,
        raw_base64: savedItem.thumbnail_base64?.startsWith('data:')
          ? savedItem.thumbnail_base64
          : `data:image/jpeg;base64,${savedItem.thumbnail_base64}`,
        annotated_base64: savedItem.thumbnail_base64?.startsWith('data:')
          ? savedItem.thumbnail_base64
          : `data:image/jpeg;base64,${savedItem.thumbnail_base64}`,
      },
    });
    setVerifierManifest(savedItem.manifest);
    setSelectedReagent(savedItem.manifest?.evidence_data?.operator?.reagent_type || 'MARQUIS');
    if (savedItem.gps) {
      setGps(savedItem.gps);
    }
  };

  const handleOpenVerifierForManifest = (manifest) => {
    setVerifierManifest(manifest);
    setIsVerifierOpen(true);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-white">
      {/* Tactical Header */}
      <Header
        viewMode={viewMode}
        setViewMode={setViewMode}
        gpsLocked={true}
        officerBadge={operator.officer_badge}
        onOpenVerifier={() => {
          setVerifierManifest(analysisResult?.manifest);
          setIsVerifierOpen(true);
        }}
        onOpenRefCard={() => setIsRefCardOpen(true)}
        onOpenLocker={() => setIsLockerOpen(true)}
        lockerCount={lockerCount}
      />

      {/* Main Container */}
      <main className="flex-1 py-4 px-2 sm:px-6 flex justify-center">
        {/* Mobile Mockup Device Wrapper vs Fullscreen View */}
        <div
          className={`w-full transition-all duration-300 ${
            viewMode === 'mobile'
              ? 'max-w-[480px] bg-slate-900 border-4 sm:border-8 border-slate-800 rounded-[36px] sm:rounded-[44px] shadow-2xl p-2.5 sm:p-4 my-2 relative overflow-hidden'
              : 'max-w-6xl space-y-4'
          }`}
        >
          {/* Mobile Speaker / Camera Notch if in mobile mode */}
          {viewMode === 'mobile' && (
            <div className="flex justify-center mb-2">
              <div className="w-28 h-4 bg-slate-950 rounded-full flex items-center justify-center gap-2 border border-slate-800">
                <div className="w-2.5 h-2.5 rounded-full bg-slate-900 border border-slate-700" />
                <div className="w-8 h-1 bg-slate-800 rounded-full" />
              </div>
            </div>
          )}

          {/* Workflow Content Grid */}
          <div className="space-y-4">
            {/* Step 1: Reagent & Operator Setup */}
            <section>
              <div className="flex items-center gap-1.5 text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider mb-1.5 px-1">
                <span className="w-4 h-4 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 flex items-center justify-center text-[10px]">
                  1
                </span>
                <span>Select Test Kit & Field Geolocation</span>
              </div>
              <ReagentSelector
                selectedReagent={selectedReagent}
                setSelectedReagent={(reagent) => {
                  setSelectedReagent(reagent);
                  if (currentImageFile) {
                    runAnalysis(currentImageFile, reagent, gps, operator, customRefRoi, customVialRoi);
                  }
                }}
                gps={gps}
                setGps={setGps}
                operator={operator}
                setOperator={setOperator}
                isAcquiringGps={isAcquiringGps}
                acquireGps={acquireGps}
              />
            </section>

            {/* Step 2: Camera Viewfinder with Interactive Touch ROI Alignment */}
            <section>
              <div className="flex items-center gap-1.5 text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider mb-1.5 px-1">
                <span className="w-4 h-4 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 flex items-center justify-center text-[10px]">
                  2
                </span>
                <span>Capture Kit & Reference Card (Touch to Adjust Targets)</span>
              </div>
              <CameraViewfinder
                sampleCases={sampleCases}
                selectedCaseId={selectedCaseId}
                onSelectSampleCase={handleSelectSampleCase}
                onImageSelected={handleImageSelected}
                currentImagePreview={
                  analysisResult?.images?.annotated_base64 || currentImagePreview
                }
                analyzing={analyzing}
                customRefRoi={customRefRoi}
                setCustomRefRoi={setCustomRefRoi}
                customVialRoi={customVialRoi}
                setCustomVialRoi={setCustomVialRoi}
                onReanalyzeWithRois={handleReanalyzeWithRois}
              />
            </section>

            {/* Step 3: OpenCV Color Correction & Comparison */}
            {analysisResult && (
              <section>
                <div className="flex items-center gap-1.5 text-xs font-mono text-purple-400 font-bold uppercase tracking-wider mb-1.5 px-1">
                  <span className="w-4 h-4 rounded-full bg-purple-950 text-purple-400 border border-purple-800 flex items-center justify-center text-[10px]">
                    3
                  </span>
                  <span>OpenCV Reference Card Color Calibration</span>
                </div>
                <ColorCorrectionPanel
                  rawImage={analysisResult.images.raw_base64}
                  calibratedImage={analysisResult.images.calibrated_base64}
                  calibrationMetrics={analysisResult.calibration_metrics}
                />
              </section>
            )}

            {/* Step 4: HSV Chemical Classification */}
            {analysisResult && (
              <section>
                <div className="flex items-center gap-1.5 text-xs font-mono text-emerald-400 font-bold uppercase tracking-wider mb-1.5 px-1">
                  <span className="w-4 h-4 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center justify-center text-[10px]">
                    4
                  </span>
                  <span>HSV Range Colorimetric Classification</span>
                </div>
                <HsvClassifierPanel
                  classification={analysisResult.classification}
                  hsvMetrics={analysisResult.hsv_metrics}
                />
              </section>
            )}

            {/* Step 5: Tamper-Evident SHA-256 Chain of Custody */}
            {analysisResult && (
              <section>
                <div className="flex items-center gap-1.5 text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider mb-1.5 px-1">
                  <span className="w-4 h-4 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 flex items-center justify-center text-[10px]">
                    5
                  </span>
                  <span>Tamper-Evident Cryptographic Record</span>
                </div>
                <TamperEvidentRecord
                  manifest={analysisResult.manifest}
                  onLaunchTamperTest={() => {
                    setVerifierManifest(analysisResult.manifest);
                    setIsVerifierOpen(true);
                  }}
                />
              </section>
            )}
          </div>

          {/* Mobile Home Bar Indicator */}
          {viewMode === 'mobile' && (
            <div className="flex justify-center mt-4">
              <div className="w-32 h-1 bg-slate-700 rounded-full" />
            </div>
          )}
        </div>
      </main>

      {/* Modals */}
      <TamperVerifierModal
        isOpen={isVerifierOpen}
        onClose={() => setIsVerifierOpen(false)}
        initialManifest={verifierManifest || analysisResult?.manifest}
      />

      <ReferenceCardModal
        isOpen={isRefCardOpen}
        onClose={() => setIsRefCardOpen(false)}
      />

      <EvidenceLockerModal
        isOpen={isLockerOpen}
        onClose={() => {
          setIsLockerOpen(false);
          refreshLockerCount();
        }}
        onLoadRecord={handleLoadFromLocker}
        onVerifyRecord={handleOpenVerifierForManifest}
      />
    </div>
  );
}
