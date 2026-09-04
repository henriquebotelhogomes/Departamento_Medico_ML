import React, { useState, useRef, useEffect } from "react";
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Sliders,
  Eye,
  Activity,
  Layers,
  Maximize2,
  Minimize2,
  Sun,
  Contrast,
} from "lucide-react";
import type { DicomMetadata } from "@/lib/types";

interface PacsViewerProps {
  originalImage: string;
  gradcamImage?: string | null;
  pureHeatmap?: string | null;
  dicomMetadata?: DicomMetadata | null;
  inferenceMs?: number;
  label: string;
}

type WindowPreset = "default" | "lung" | "bone" | "mediastinum" | "custom";

export const PacsViewer: React.FC<PacsViewerProps> = ({
  originalImage,
  gradcamImage,
  pureHeatmap,
  dicomMetadata,
  inferenceMs,
  label,
}) => {
  // Image transformation and filter states
  const [zoom, setZoom] = useState<number>(100); // 50% to 300%
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [brightness, setBrightness] = useState<number>(100); // 50% to 200%
  const [contrast, setContrast] = useState<number>(100); // 50% to 250%
  const [inverted, setInverted] = useState<boolean>(false);
  const [heatmapOpacity, setHeatmapOpacity] = useState<number>(gradcamImage ? 60 : 0);
  const [windowPreset, setWindowPreset] = useState<WindowPreset>("default");

  // Dragging and fullscreen states
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleFsChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", handleFsChange);
    return () => document.removeEventListener("fullscreenchange", handleFsChange);
  }, []);

  // Quick preset changer
  const applyPreset = (preset: WindowPreset) => {
    setWindowPreset(preset);
    switch (preset) {
      case "lung":
        setContrast(160);
        setBrightness(115);
        break;
      case "bone":
        setContrast(220);
        setBrightness(85);
        break;
      case "mediastinum":
        setContrast(135);
        setBrightness(95);
        break;
      case "default":
      default:
        setContrast(100);
        setBrightness(100);
        break;
    }
  };

  const getFilterStyle = (): string => {
    const b = brightness / 100;
    const c = contrast / 100;
    const inv = inverted ? "invert(1)" : "invert(0)";
    return `contrast(${c}) brightness(${b}) ${inv}`;
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  const toggleFullScreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      void containerRef.current.requestFullscreen();
    } else {
      void document.exitFullscreen();
    }
  };

  const resetAll = () => {
    setZoom(100);
    setPan({ x: 0, y: 0 });
    setBrightness(100);
    setContrast(100);
    setInverted(false);
    setWindowPreset("default");
    setHeatmapOpacity(gradcamImage ? 60 : 0);
  };

  return (
    <div className="flex flex-col rounded-2xl border border-slate-800 bg-[#070B12] text-slate-200 shadow-2xl overflow-hidden w-full">
      {/* 1. Barra Superior Principal: Presets Rápidos e Modos */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-800/80 bg-slate-900/95 px-4 py-2.5 text-xs backdrop-blur gap-2">
        {/* Presets Rápidos */}
        <div className="flex items-center space-x-1.5">
          <span className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase mr-1 flex items-center">
            <Sliders className="h-3.5 w-3.5 mr-1 text-sky-400" /> Presets:
          </span>
          {(["default", "lung", "bone", "mediastinum"] as WindowPreset[]).map((preset) => (
            <button
              key={preset}
              onClick={() => applyPreset(preset)}
              className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                windowPreset === preset
                  ? "bg-sky-500 text-white shadow-sm font-semibold"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              {preset === "default"
                ? "Padrão"
                : preset === "lung"
                ? "Pulmão"
                : preset === "bone"
                ? "Osso"
                : "Mediastino"}
            </button>
          ))}
        </div>

        {/* Ferramentas Rápidas (Invert, Tela Cheia, Reset Geral) */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setInverted(!inverted)}
            title="Inverter escala de cinza (Visão em Negativo)"
            className={`flex items-center space-x-1.5 rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
              inverted
                ? "bg-amber-500 text-slate-950 font-bold"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            <Eye className="h-3.5 w-3.5" />
            <span>Negativo</span>
          </button>

          <button
            onClick={resetAll}
            title="Resetar todos os ajustes (Zoom, Pan, Brilho, Contraste)"
            className="flex items-center space-x-1 rounded-lg bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-300 hover:bg-slate-700 transition-colors"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Resetar</span>
          </button>

          <button
            onClick={toggleFullScreen}
            title={isFullscreen ? "Sair da tela cheia" : "Modo Tela Cheia"}
            className="rounded-lg bg-slate-800 p-1.5 text-slate-300 hover:bg-slate-700 transition-colors"
          >
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* 2. Painel de Controles Manuais (Sliders dedicados de Zoom, Brilho, Contraste e Heatmap) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 border-b border-slate-800/80 bg-slate-950/90 px-4 py-2 text-xs">
        {/* Controle de Zoom */}
        <div className="flex items-center space-x-2 bg-slate-900/60 px-2.5 py-1.5 rounded-lg border border-slate-800/70">
          <span className="text-[11px] font-semibold text-sky-400 shrink-0">Zoom:</span>
          <button
            onClick={() => setZoom((z) => Math.max(z - 15, 50))}
            className="rounded bg-slate-800 p-1 text-slate-300 hover:bg-slate-700 shrink-0"
            title="Diminuir Zoom"
          >
            <ZoomOut className="h-3 w-3" />
          </button>
          <input
            type="range"
            min="50"
            max="300"
            step="5"
            value={zoom}
            onChange={(e) => setZoom(Number(e.target.value))}
            className="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-slate-800 accent-sky-500"
          />
          <button
            onClick={() => setZoom((z) => Math.min(z + 15, 300))}
            className="rounded bg-slate-800 p-1 text-slate-300 hover:bg-slate-700 shrink-0"
            title="Aumentar Zoom"
          >
            <ZoomIn className="h-3 w-3" />
          </button>
          <span className="font-mono text-[10px] text-slate-300 w-8 text-right shrink-0">{zoom}%</span>
        </div>

        {/* Controle de Brilho */}
        <div className="flex items-center space-x-2 bg-slate-900/60 px-2.5 py-1.5 rounded-lg border border-slate-800/70">
          <Sun className="h-3.5 w-3.5 text-amber-400 shrink-0" />
          <span className="text-[11px] font-semibold text-slate-300 shrink-0">Brilho:</span>
          <input
            type="range"
            min="50"
            max="200"
            step="5"
            value={brightness}
            onChange={(e) => {
              setBrightness(Number(e.target.value));
              setWindowPreset("custom");
            }}
            className="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-slate-800 accent-amber-500"
          />
          <span className="font-mono text-[10px] text-slate-300 w-8 text-right shrink-0">{brightness}%</span>
        </div>

        {/* Controle de Contraste */}
        <div className="flex items-center space-x-2 bg-slate-900/60 px-2.5 py-1.5 rounded-lg border border-slate-800/70">
          <Contrast className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
          <span className="text-[11px] font-semibold text-slate-300 shrink-0">Contraste:</span>
          <input
            type="range"
            min="50"
            max="250"
            step="5"
            value={contrast}
            onChange={(e) => {
              setContrast(Number(e.target.value));
              setWindowPreset("custom");
            }}
            className="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-slate-800 accent-indigo-500"
          />
          <span className="font-mono text-[10px] text-slate-300 w-8 text-right shrink-0">{contrast}%</span>
        </div>

        {/* Grad-CAM Heatmap Blend */}
        <div className="flex items-center space-x-2 bg-slate-900/60 px-2.5 py-1.5 rounded-lg border border-slate-800/70">
          <Layers className="h-3.5 w-3.5 text-rose-400 shrink-0" />
          <span className="text-[11px] font-semibold text-rose-300 shrink-0">Grad-CAM:</span>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={heatmapOpacity}
            onChange={(e) => setHeatmapOpacity(Number(e.target.value))}
            className="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-slate-800 accent-rose-500"
          />
          <span className="font-mono text-[10px] text-slate-300 w-8 text-right shrink-0">{heatmapOpacity}%</span>
        </div>
      </div>

      {/* 3. Main PACS Canvas Viewport */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className="relative flex h-[580px] lg:h-[640px] w-full items-center justify-center overflow-hidden bg-black select-none cursor-grab active:cursor-grabbing"
      >
        {/* HUD: Top-Left (Patient & Acquisition Metadata) */}
        <div className="absolute top-4 left-4 z-20 pointer-events-none font-mono text-xs leading-relaxed text-emerald-400 drop-shadow-[0_2px_4px_rgba(0,0,0,0.95)]">
          <p className="font-bold tracking-wider text-[13px]">
            PATIENT: {dicomMetadata?.is_dicom ? "DICOM_DEIDENTIFIED" : "ANON_CHEST_01"}
          </p>
          <p className="text-slate-300 text-xs">
            MODALITY: {dicomMetadata?.modality ?? "CR/DX"} · VIEW: {dicomMetadata?.patient_position ?? "PA"}
          </p>
          <p className="text-slate-400 text-[11px]">
            {dicomMetadata?.study_description ?? "Chest Radiography High-Res"}
          </p>
        </div>

        {/* HUD: Top-Right (Technique & Tube Exposure) */}
        <div className="absolute top-4 right-4 z-20 pointer-events-none font-mono text-xs text-right leading-relaxed text-sky-400 drop-shadow-[0_2px_4px_rgba(0,0,0,0.95)]">
          <p className="font-bold text-[13px]">KVP: {dicomMetadata?.kvp ?? "120 kVp"}</p>
          <p className="text-slate-300 text-xs">MATRIX: 256x256 · BITS: 8</p>
          <p className="text-slate-400 text-[11px]">PRESET: {windowPreset.toUpperCase()}</p>
        </div>

        {/* HUD: Bottom-Left (Diagnostic Class & Latency) */}
        <div className="absolute bottom-4 left-4 z-20 pointer-events-none font-mono text-xs text-slate-200 drop-shadow-[0_2px_4px_rgba(0,0,0,0.95)]">
          <p className="flex items-center text-amber-300 font-bold text-[13px]">
            <Activity className="h-4 w-4 mr-1.5" /> DIAGNOSIS: {label}
          </p>
          {inferenceMs !== undefined && (
            <p className="text-slate-400 text-[11px]">INFERENCE LATENCY: {inferenceMs} ms</p>
          )}
        </div>

        {/* HUD: Lateral Anatomical Markers */}
        <div className="absolute right-6 top-1/2 -translate-y-1/2 z-20 pointer-events-none font-bold text-3xl font-mono text-white/50 border-2 border-white/20 px-3 py-1.5 rounded-lg bg-black/40 backdrop-blur-sm">
          L
        </div>
        <div className="absolute left-6 top-1/2 -translate-y-1/2 z-20 pointer-events-none font-bold text-3xl font-mono text-white/30 border-2 border-white/15 px-3 py-1.5 rounded-lg bg-black/30 backdrop-blur-sm">
          R
        </div>

        {/* Render Layers (Base X-ray + Heatmap Blend) */}
        <div
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom / 100})`,
            transformOrigin: "center center",
            transition: isDragging ? "none" : "transform 0.08s ease-out",
          }}
          className="relative flex items-center justify-center h-[520px] w-[520px] max-h-full max-w-full"
        >
          {/* Base X-ray Image with CSS filters */}
          <img
            src={originalImage}
            alt="Raio-X Torácico"
            style={{ filter: getFilterStyle() }}
            className="h-full w-full object-contain rounded-lg shadow-2xl pointer-events-none"
          />

          {/* Grad-CAM Heatmap Layer (Overlay) */}
          {(pureHeatmap || gradcamImage) && heatmapOpacity > 0 && (
            <img
              src={pureHeatmap || gradcamImage || ""}
              alt="Grad-CAM Layer"
              style={{
                opacity: heatmapOpacity / 100,
                mixBlendMode: pureHeatmap ? "screen" : "normal",
              }}
              className="absolute inset-0 h-full w-full object-contain rounded-lg pointer-events-none transition-opacity duration-150"
            />
          )}
        </div>
      </div>

      {/* 4. PACS Footer Status Bar */}
      <div className="flex items-center justify-between border-t border-slate-800/80 bg-slate-900/80 px-4 py-2 text-xs text-slate-400 font-mono">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          CLINICAL PACS ACTIVE · Clique e arraste para mover a imagem
        </span>
        <div className="flex items-center space-x-3 text-slate-300">
          <span>ZOOM: {zoom}%</span>
          <span>•</span>
          <span>BRILHO: {brightness}%</span>
          <span>•</span>
          <span>CONTRASTE: {contrast}%</span>
        </div>
      </div>
    </div>
  );
};
