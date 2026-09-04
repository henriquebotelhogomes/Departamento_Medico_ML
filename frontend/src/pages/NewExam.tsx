import React, { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  UploadCloud,
  FileCode,
  Sparkles,
  AlertTriangle,
  Loader2,
  Activity,
  FileCheck2,
  X,
  Search,
  ArrowLeft,
  AlertOctagon,
} from "lucide-react";
import { predictImage } from "@/lib/api";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { ProbabilityBar } from "@/components/ProbabilityBar";
import { PacsViewer } from "@/components/PacsViewer";
import { MedicalReportCard } from "@/components/MedicalReportCard";
import { ClinicalInterventionPanel } from "@/components/ClinicalInterventionPanel";
import type { PredictionResult } from "@/lib/types";

const MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024; // 15MB
const ACCEPTED_EXTENSIONS = [".dcm", ".jpg", ".jpeg", ".png", ".webp", ".bmp"];

export function NewExam() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [overrideLabel, setOverrideLabel] = useState<string | null>(null);
  const [overrideNotes, setOverrideNotes] = useState<string>("");

  const inputRef = useRef<HTMLInputElement>(null);

  const mutation = useMutation({
    mutationFn: async (uploadedFile: File) => {
      setError(null);
      return predictImage(uploadedFile);
    },
    onError: (err: Error) => {
      setError(err.message || "Falha na análise da imagem.");
    },
  });

  const selectFile = (f: File | null) => {
    if (!f) return;
    setError(null);

    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      setError(`Formato não suportado (${ext}). Utilize DICOM (.dcm), JPEG, PNG ou WEBP.`);
      return;
    }

    if (f.size > MAX_FILE_SIZE_BYTES) {
      setError("Arquivo excede o limite máximo permitido de 15 MB.");
      return;
    }

    setFile(f);

    if (f.name.toLowerCase().endsWith(".dcm")) {
      setPreview(null);
    } else {
      const url = URL.createObjectURL(f);
      setPreview(url);
    }
  };

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files?.[0]) {
      selectFile(e.dataTransfer.files[0]);
    }
  };

  const handleStartAnalysis = () => {
    if (!file) return;
    mutation.mutate(file);
  };

  const resetAll = () => {
    setFile(null);
    setPreview(null);
    setError(null);
    setOverrideLabel(null);
    setOverrideNotes("");
    mutation.reset();
  };

  const result: PredictionResult | undefined = mutation.data;
  const displayImage = result?.raw_image_data || preview || result?.image_url || "";
  const isDicomFile = file?.name.toLowerCase().endsWith(".dcm");

  return (
    <div className="space-y-6">
      {/* Page Title & Navigation Header */}
      <div className="no-print flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4 gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="flex h-2.5 w-2.5 rounded-full bg-sky-500 dark:bg-sky-400" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Novo Exame Radiológico
            </h1>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Faça o upload de uma radiografia do paciente para triagem diagnóstica e laudo médico
          </p>
        </div>

        {result && (
          <button
            onClick={resetAll}
            className="flex items-center space-x-1.5 rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 px-3.5 py-1.5 text-xs font-semibold shadow-sm transition-colors self-start sm:self-auto"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Analisar Outro Exame</span>
          </button>
        )}
      </div>

      {/* ERROR BANNER */}
      {error && (
        <div className="flex items-center space-x-2 rounded-lg bg-rose-500/10 border border-rose-500/20 px-4 py-3 text-xs text-rose-600 dark:text-rose-300">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* VIEW STATE 1: UPLOAD & CONFIRMATION (Before analysis is completed) */}
      {!result ? (
        <div className="max-w-3xl mx-auto space-y-6 py-4">
          {/* Main Upload Dropzone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => !file && inputRef.current?.click()}
            className={`relative flex min-h-[320px] flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition-all ${
              dragging
                ? "border-sky-500 bg-sky-50 dark:bg-sky-950/20"
                : file
                ? "border-sky-500/60 bg-sky-50/50 dark:bg-[#0B0F17]"
                : "border-slate-300 bg-white hover:border-slate-400 hover:bg-slate-50/50 dark:border-slate-800 dark:bg-[#070B12] dark:hover:border-slate-700 dark:hover:bg-slate-900/30 cursor-pointer shadow-sm dark:shadow-none"
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".dcm,image/jpeg,image/png,image/webp,image/bmp"
              className="hidden"
              onChange={(e) => selectFile(e.target.files?.[0] ?? null)}
            />

            {!file ? (
              /* Empty Dropzone State */
              <div className="flex flex-col items-center">
                <div className="rounded-2xl bg-sky-500/10 p-5 text-sky-600 dark:text-sky-400 border border-sky-500/20 mb-4 shadow-inner">
                  <UploadCloud className="h-12 w-12" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">
                  Arraste e solte o exame aqui
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 max-w-md mb-5 leading-relaxed">
                  Suporta arquivos hospitalares <strong>DICOM (.dcm)</strong> ou imagens médicas convencionais (JPEG, PNG, WEBP).
                </p>

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    inputRef.current?.click();
                  }}
                  className="rounded-xl bg-sky-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-sky-600/20 hover:bg-sky-500 transition-all flex items-center gap-2"
                >
                  <Search className="h-4 w-4" />
                  <span>Selecionar Arquivo do Computador</span>
                </button>

                <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-900/90 px-3.5 py-1.5 rounded-full border border-slate-200 dark:border-slate-800 mt-6">
                  <FileCode className="h-3.5 w-3.5 text-sky-500 dark:text-sky-400" />
                  <span>DICOM (.dcm), JPEG, PNG, WEBP · máx. 15 MB</span>
                </div>
              </div>
            ) : (
              /* File Selected State (Ready to Run) */
              <div className="w-full max-w-lg space-y-4">
                <div className="flex items-center justify-between bg-white dark:bg-slate-900/90 p-4 rounded-xl border border-slate-200 dark:border-slate-800 text-left shadow-sm">
                  <div className="flex items-center space-x-3">
                    {preview ? (
                      <img
                        src={preview}
                        alt="Preview do Exame"
                        className="h-16 w-16 rounded-lg object-cover border border-slate-200 dark:border-slate-700 bg-black shrink-0"
                      />
                    ) : (
                      <div className="flex h-16 w-16 items-center justify-center rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-600 dark:text-sky-400 shrink-0">
                        <FileCode className="h-8 w-8" />
                      </div>
                    )}
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center space-x-1.5">
                        <FileCheck2 className="h-4 w-4 text-emerald-500 dark:text-emerald-400 shrink-0" />
                        <p className="font-semibold text-sm text-slate-900 dark:text-white truncate">{file.name}</p>
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        {(file.size / (1024 * 1024)).toFixed(2)} MB ·{" "}
                        {isDicomFile ? "Arquivo Hospitalar DICOM" : "Imagem Radiológica"}
                      </p>
                      <span className="inline-block mt-1 rounded bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                        Pronto para Análise
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      resetAll();
                    }}
                    className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                    title="Remover e escolher outro arquivo"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                {/* Prominent Action Button */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleStartAnalysis();
                  }}
                  disabled={mutation.isPending}
                  className="w-full rounded-xl bg-gradient-to-r from-sky-600 to-blue-600 py-3.5 px-6 text-sm font-bold text-white shadow-xl shadow-sky-600/25 hover:from-sky-500 hover:to-blue-500 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                >
                  {mutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Processando Redes Neurais & OOD Check…</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4" />
                      <span>Analisar Exame & Gerar Laudo</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* VIEW STATE 2: PACS WORKSTATION & MULTI-LLM REPORT (After analysis) */
        <div className="grid gap-6 lg:grid-cols-12 print:block">
          {/* Left Column: Interactive PACS Viewer */}
          <div className="no-print lg:col-span-7 xl:col-span-8 space-y-4">
            <PacsViewer
              originalImage={displayImage}
              gradcamImage={result.gradcam_image}
              pureHeatmap={result.pure_heatmap}
              dicomMetadata={result.dicom_metadata}
              inferenceMs={result.inference_ms}
              label={result.label}
            />

            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 font-mono">
              <span>EXAME: {file?.name ?? "Exame do Paciente"}</span>
              <span>INFERÊNCIA: {result.inference_ms} ms</span>
            </div>
          </div>

          {/* Right Column: Clinical Triage & Multi-LLM Report */}
          <div className="lg:col-span-5 xl:col-span-4 space-y-4 print:w-full print:block">
            {/* Triage Decision Card */}
            <div className="no-print rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-[#0B0F17] p-5 shadow-sm dark:shadow-xl space-y-4">
              {result.is_ood ? (
                <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-amber-800 dark:text-amber-300 space-y-2">
                  <div className="flex items-center space-x-2">
                    <AlertOctagon className="h-5 w-5 text-amber-500 dark:text-amber-400" />
                    <h3 className="font-bold text-sm">Imagem Fora da Distribuição (OOD)</h3>
                  </div>
                  <p className="text-xs leading-relaxed text-amber-900/90 dark:text-amber-200/90">
                    O filtro de anomalias rejeitou a imagem pois seus embeddings neurais não correspondem ao espaço de radiografias de tórax.
                  </p>
                  <p className="text-[11px] font-mono text-amber-700 dark:text-amber-400">
                    Similaridade Cosseno: {(result.ood_similarity ? result.ood_similarity * 100 : 0).toFixed(1)}% (Limiar: 45.0%)
                  </p>
                </div>
              ) : (
                <div>
                  <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3 mb-3">
                    <div className="flex items-center space-x-2">
                      <Activity className="h-4 w-4 text-sky-500 dark:text-sky-400" />
                      <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        Triagem Diagnóstica
                      </span>
                    </div>
                    <ConfidenceBadge confidence={result.confidence} />
                  </div>

                  <div className="mb-4">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono uppercase text-slate-500 tracking-wider">
                        Diagnóstico Principal:
                      </span>
                      {overrideLabel && (
                        <span className="inline-flex items-center rounded-full bg-purple-500/10 px-2 py-0.5 text-[10px] font-bold text-purple-700 dark:text-purple-300 border border-purple-500/20">
                          👨‍⚕️ Parecer Médico
                        </span>
                      )}
                    </div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-0.5">
                      {overrideLabel || result.label}
                    </h2>
                    {overrideLabel ? (
                      <p className="text-xs text-purple-700 dark:text-purple-300 mt-0.5 font-medium">
                        Sobrescrito pelo médico assistente (IA original: {result.label})
                      </p>
                    ) : (
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        Confiança calibrada: {(result.confidence * 100).toFixed(1)}% · Inferência em {result.inference_ms} ms
                      </p>
                    )}
                  </div>

                  {/* Probability distribution across classes */}
                  <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800/80">
                    <span className="text-[10px] font-mono uppercase text-slate-500 tracking-wider">
                      Distribuição de Probabilidade por Classe:
                    </span>
                    {result.probs.map((p) => (
                      <ProbabilityBar
                        key={p.class_id}
                        classId={p.class_id}
                        label={p.label}
                        probability={p.probability}
                        highlight={
                          overrideLabel
                            ? p.label.toLowerCase() === overrideLabel.toLowerCase()
                            : p.class_id === result.predicted_class
                        }
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* DICOM Metadata Summary Tag */}
              {result.dicom_metadata?.is_dicom && (
                <div className="rounded-lg bg-slate-50 border border-slate-200 dark:bg-slate-900/80 dark:border-slate-800 p-2.5 text-[11px] font-mono text-slate-600 dark:text-slate-400 space-y-1">
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold">✓ Metadados DICOM Extraídos:</span>
                  <p>
                    Modalidade: {result.dicom_metadata.modality} · Incidência: {result.dicom_metadata.patient_position} · {result.dicom_metadata.kvp} kVp
                  </p>
                </div>
              )}
            </div>

            {/* Clinical Ambiguity Alert & Human-in-the-Loop Override Panel */}
            {!result.is_ood && (
              <ClinicalInterventionPanel
                probs={result.probs}
                originalLabel={result.label}
                overrideLabel={overrideLabel}
                overrideNotes={overrideNotes}
                onOverrideChange={(label, notes) => {
                  setOverrideLabel(label);
                  setOverrideNotes(notes);
                }}
              />
            )}

            {/* Multi-LLM Radiology Report Card */}
            {!result.is_ood && (
              <MedicalReportCard
                prediction={result}
                overrideLabel={overrideLabel}
                overrideNotes={overrideNotes}
                isAmbiguous={
                  (() => {
                    const sorted = [...result.probs].sort((a, b) => b.probability - a.probability);
                    const top1 = sorted[0];
                    const top2 = sorted[1];
                    const delta = top1 && top2 ? (top1.probability - top2.probability) * 100 : 100;
                    return delta < 15.0 || (top1 && top1.probability < 0.65);
                  })()
                }
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
