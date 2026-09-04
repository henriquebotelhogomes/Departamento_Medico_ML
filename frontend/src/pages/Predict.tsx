import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  Loader2,
  Sparkles,
  CheckCircle2,
  ArrowRight,
  ScanLine,
  AlertOctagon,
} from "lucide-react";
import { predictImage } from "@/lib/api";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { ProbabilityBar } from "@/components/ProbabilityBar";
import { PacsViewer } from "@/components/PacsViewer";
import { MedicalReportCard } from "@/components/MedicalReportCard";
import { ClinicalInterventionPanel } from "@/components/ClinicalInterventionPanel";
import type { PredictionResult } from "@/lib/types";

interface DemoSample {
  label: string;
  filename: string;
  icon: string;
  desc: string;
  isDicom?: boolean;
}

const DEMO_SAMPLES: DemoSample[] = [
  {
    label: "Normal",
    filename: "sample_normal.jpeg",
    icon: "🫁",
    desc: "Transparência pulmonar preservada",
  },
  {
    label: "Covid-19",
    filename: "sample_covid.jpg",
    icon: "🦠",
    desc: "Opacidades em vidro fosco bilateral",
  },
  {
    label: "Pneumonia Bacteriana",
    filename: "sample_pneumonia_bacteriana.jpeg",
    icon: "🧫",
    desc: "Consolidação lobar com broncograma",
  },
  {
    label: "Pneumonia Viral",
    filename: "sample_pneumonia_viral.jpeg",
    icon: "🧬",
    desc: "Infiltrado intersticial difuso",
  },
  {
    label: "Anomalia (OOD)",
    filename: "sample_ood.png",
    icon: "⚠️",
    desc: "Fora da distribuição torácica",
  },
  {
    label: "Exame DICOM (.dcm)",
    filename: "sample_dicom.dcm",
    icon: "🏥",
    desc: "Padrão hospitalar PS 3.15",
    isDicom: true,
  },
];

export function Predict() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [activeSample, setActiveSample] = useState<DemoSample | null>(null);
  const [displayImage, setDisplayImage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [overrideLabel, setOverrideLabel] = useState<string | null>(null);
  const [overrideNotes, setOverrideNotes] = useState<string>("");

  const mutation = useMutation({
    mutationFn: async (file: File) => {
      setError(null);
      return predictImage(file);
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const loadSample = async (sample: DemoSample) => {
    setActiveSample(sample);
    setError(null);
    setOverrideLabel(null);
    setOverrideNotes("");

    try {
      const sampleUrl = `/samples/${sample.filename}`;
      const response = await fetch(sampleUrl);
      if (!response.ok) {
        throw new Error(`Amostra não encontrada: ${sample.filename}`);
      }

      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("text/html")) {
        throw new Error(`Arquivo não encontrado no servidor: ${sample.filename}`);
      }

      const blob = await response.blob();
      const mime = sample.isDicom
        ? "application/dicom"
        : sample.filename.endsWith(".png")
        ? "image/png"
        : "image/jpeg";
      const file = new File([blob], sample.filename, { type: mime });

      if (!sample.isDicom) {
        const objectUrl = URL.createObjectURL(blob);
        setDisplayImage(objectUrl);
      }

      mutation.mutate(file, {
        onSuccess: (data) => {
          if (sample.isDicom && data.raw_image_data) {
            setDisplayImage(data.raw_image_data);
          }
        },
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao carregar amostra clínica");
    }
  };

  const result: PredictionResult | undefined = mutation.data;

  return (
    <div className="space-y-6">
      {/* Workstation Header */}
      <div className="no-print flex flex-col md:flex-row md:items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4 gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              Estação PACS & Galeria Clínica (Demonstração)
            </h1>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Ambiente interativo de teste rápido: explore radiografias com IA ResNet50, Grad-CAM e Laudos Multi-LLM
          </p>
        </div>

        {/* Status Badge */}
        <div className="flex items-center space-x-2">
          {mutation.isPending ? (
            <span className="inline-flex items-center rounded-full bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-600 dark:text-amber-400 border border-amber-500/20">
              <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
              Processando Inferência Neural…
            </span>
          ) : result ? (
            <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" />
              Caso Clínico em Exibição
            </span>
          ) : (
            <span className="inline-flex items-center rounded-full bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 px-3 py-1 text-xs font-medium">
              Selecione uma Amostra Abaixo
            </span>
          )}
        </div>
      </div>

      {/* 1-Click Demo Gallery Bar */}
      <div className="no-print rounded-xl border border-slate-200 bg-white dark:border-slate-800/80 dark:bg-slate-900/60 p-4 backdrop-blur shadow-sm dark:shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-sky-600 dark:text-sky-400 tracking-wider uppercase flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5" /> Casos Clínicos Disponíveis (Clique para Testar):
          </span>
          <span className="text-[11px] text-slate-500 dark:text-slate-400 hidden sm:inline">
            Clique em qualquer botão para carregar instantaneamente na estação
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
          {DEMO_SAMPLES.map((s) => {
            const isSelected = activeSample?.filename === s.filename;
            return (
              <button
                key={s.label}
                onClick={() => loadSample(s)}
                disabled={mutation.isPending}
                className={`flex flex-col items-center justify-center p-3 rounded-xl border transition-all text-center group disabled:opacity-50 ${
                  isSelected
                    ? "border-sky-500 bg-sky-50 dark:bg-sky-950/40 shadow-md shadow-sky-500/10 scale-[1.02]"
                    : "border-slate-200 bg-slate-50/80 hover:bg-slate-100 hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950/80 dark:hover:bg-slate-800/80 dark:hover:border-slate-700"
                }`}
              >
                <span className="text-2xl mb-1.5 group-hover:scale-110 transition-transform">{s.icon}</span>
                <span
                  className={`text-xs font-semibold ${
                    isSelected
                      ? "text-sky-700 dark:text-sky-300"
                      : "text-slate-800 group-hover:text-sky-600 dark:text-slate-200 dark:group-hover:text-sky-300"
                  }`}
                >
                  {s.label}
                </span>
                <span className="text-[9px] text-slate-500 line-clamp-1 mt-1">{s.desc}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="flex items-center space-x-2 rounded-lg bg-rose-500/10 border border-rose-500/20 px-3 py-2 text-xs text-rose-600 dark:text-rose-300">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Showcase Layout */}
      {result && displayImage ? (
        /* Render Loaded PACS Workstation */
        <div className="grid gap-6 lg:grid-cols-12 print:block">
          {/* Left: PACS Viewer */}
          <div className="no-print lg:col-span-7 xl:col-span-8 space-y-3">
            <PacsViewer
              originalImage={displayImage}
              gradcamImage={result.gradcam_image}
              pureHeatmap={result.pure_heatmap}
              dicomMetadata={result.dicom_metadata}
              inferenceMs={result.inference_ms}
              label={result.label}
            />

            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 font-mono">
              <span>CASO DEMO: {activeSample?.label} ({activeSample?.filename})</span>
              <span>INFERÊNCIA: {result.inference_ms} ms</span>
            </div>
          </div>

          {/* Right: Diagnosis & Multi-LLM Report */}
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
                        Diagnóstico Previsto:
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

                  {/* Probability distribution */}
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

              {/* DICOM Metadata Summary */}
              {result.dicom_metadata?.is_dicom && (
                <div className="rounded-lg bg-slate-50 border-slate-200 dark:bg-slate-900/80 dark:border-slate-800 p-2.5 text-[11px] font-mono text-slate-600 dark:text-slate-400 space-y-1">
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
      ) : (
        /* Empty / Welcome State (Encouraging to pick a sample or go to New Exam) */
        <div className="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-[#070B12] p-10 text-center space-y-5 shadow-sm dark:shadow-2xl">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-sky-500/10 border border-sky-500/20 text-sky-500 dark:text-sky-400">
            <ScanLine className="h-8 w-8" />
          </div>

          <div className="max-w-md mx-auto space-y-2">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              Estação de Demonstração PACS
            </h2>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              {t("predict.placeholder")} Clique em qualquer um dos <strong>6 botões acima</strong> para carregar o exame correspondente com explicabilidade Grad-CAM e laudo inteligente.
            </p>
          </div>

          {/* Direct CTA Banner to New Exam */}
          <div className="pt-4 border-t border-slate-100 dark:border-slate-800/80 max-w-lg mx-auto flex flex-col sm:flex-row items-center justify-between bg-slate-50 dark:bg-slate-900/80 p-4 rounded-xl border border-slate-200 dark:border-slate-800 gap-3">
            <div className="text-left">
              <p className="text-xs font-semibold text-slate-900 dark:text-white">Deseja analisar um exame próprio?</p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Envie suas radiografias ou arquivos DICOM (.dcm)</p>
            </div>
            <button
              onClick={() => navigate("/new-exam")}
              className="flex items-center space-x-1.5 rounded-lg bg-sky-600 px-3.5 py-2 text-xs font-bold text-white shadow hover:bg-sky-500 transition-colors shrink-0"
            >
              <span>Ir para Novo Exame</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
