import React, { useState } from "react";
import {
  FileText,
  Sparkles,
  Copy,
  Check,
  Printer,
  ShieldCheck,
  AlertCircle,
  Loader2,
  Cpu,
  Bot,
  Columns,
  Layers,
  Clock,
  BarChart2,
  DollarSign,
  AlertTriangle,
} from "lucide-react";
import { generateReport } from "@/lib/api";
import type { PredictionResult, ReportResponse } from "@/lib/types";

interface MedicalReportCardProps {
  prediction: PredictionResult;
  overrideLabel?: string | null;
  overrideNotes?: string;
  isAmbiguous?: boolean;
}

interface LlmOption {
  id: string;
  name: string;
  provider: string;
  badge: string;
  color: string;
}

const LLM_OPTIONS: LlmOption[] = [
  {
    id: "gemini-3.8-flash",
    name: "Gemini 3.8 Flash",
    provider: "Google AI Studio",
    badge: "Google AI Studio · Cota API",
    color: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
  },
  {
    id: "gpt-5.6-luna",
    name: "GPT 5.6 Luna",
    provider: "OpenCode Go (2.050 reqs)",
    badge: "Diagnóstico Avançado",
    color: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30",
  },
  {
    id: "deepseek-v4-flash",
    name: "DeepSeek V4 Flash",
    provider: "OpenCode Go (7.600 reqs)",
    badge: "Raciocínio & CID-10",
    color: "bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/30",
  },
  {
    id: "qwen3.7-plus",
    name: "Qwen 3.7 Plus",
    provider: "OpenCode Go (5.400 reqs)",
    badge: "Precisão Anatômica",
    color: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30",
  },
  {
    id: "deterministic-local",
    name: "Motor Clínico Determinístico",
    provider: "Local Offline Rules",
    badge: "Offline · Sem Consumo de API",
    color: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30",
  },
];

export const MedicalReportCard: React.FC<MedicalReportCardProps> = ({
  prediction,
  overrideLabel,
  overrideNotes,
  isAmbiguous,
}) => {
  const [selectedModel, setSelectedModel] = useState<string>("gemini-3.8-flash");
  const [loading, setLoading] = useState<boolean>(false);
  const [reportsMap, setReportsMap] = useState<Record<string, ReportResponse>>({});
  const [activeTab, setActiveTab] = useState<string>("gemini-3.8-flash");
  const [copied, setCopied] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await generateReport({
        predicted_class: prediction.predicted_class,
        label: overrideLabel || prediction.label,
        confidence: prediction.confidence,
        probs: prediction.probs,
        model: selectedModel,
        dicom_metadata: prediction.dicom_metadata,
        override_label: overrideLabel,
        override_notes: overrideNotes,
        is_ambiguous: isAmbiguous,
      });
      setReportsMap((prev) => ({ ...prev, [selectedModel]: data }));
      setActiveTab(selectedModel);
    } catch {
      setError("Falha ao contatar a LLM selecionada. Tente o Motor Local Determinístico.");
    } finally {
      setLoading(false);
    }
  };

  const activeReport = reportsMap[activeTab];
  const generatedModelKeys = Object.keys(reportsMap);
  const hasMultipleReports = generatedModelKeys.length > 1;

  const copyToClipboard = () => {
    if (!activeReport) return;
    const text = `
LAUDO RADIOLÓGICO SUGERIDO — RADIOAI PACS
=========================================
MODELO: ${activeReport.model_used} (${activeReport.provider})
EMITIDO EM: ${new Date(activeReport.generated_at).toLocaleString("pt-BR")}

1. TÉCNICA:
${activeReport.technique}

2. ACHADOS RADIOLÓGICOS:
${activeReport.findings}

3. IMPRESSÃO DIAGNÓSTICA:
${activeReport.impression}

4. CLASSIFICAÇÃO CID-10:
${activeReport.icd_10}

5. RECOMENDAÇÕES CLÍNICAS:
${activeReport.recommendations}

${activeReport.disclaimer}
    `.trim();

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const printReport = () => {
    window.print();
  };

  const activeOption = LLM_OPTIONS.find((o) => o.id === selectedModel) || LLM_OPTIONS[0];

  return (
    <>
      {/* 1. VISUALIZAÇÃO EM TELA (INTERATIVA) */}
      <div className="no-print rounded-xl border border-slate-200 bg-white text-slate-800 dark:border-slate-800 dark:bg-[#0B0F17] dark:text-slate-200 shadow-sm dark:shadow-xl p-5 space-y-4">
        {/* Header */}
        <div className="flex items-center space-x-3 border-b border-slate-200 dark:border-slate-800 pb-3.5">
          <div className="rounded-lg bg-sky-500/10 p-2 text-sky-600 dark:text-sky-400 border border-sky-500/20">
            <FileText className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5 text-sm">
              Laudo Radiológico & Comparativo Multi-IA
              <Sparkles className="h-4 w-4 text-amber-500 dark:text-amber-400" />
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Compare conclusões diagnósticas entre diferentes inteligências artificiais
            </p>
          </div>
        </div>

        {/* Banner de Intervenção Médica Ativa */}
        {overrideLabel && (
          <div className="rounded-lg bg-purple-500/10 border border-purple-500/30 p-2.5 text-xs text-purple-900 dark:text-purple-200 flex items-start space-x-2">
            <span className="text-base shrink-0">👨‍⚕️</span>
            <div>
              <span className="font-bold">Intervenção do Especialista Ativa:</span>
              <p className="text-[11px] text-purple-800 dark:text-purple-200/90 mt-0.5">
                Laudo orientado para <strong>{overrideLabel}</strong>
                {overrideNotes ? ` · Justificativa: "${overrideNotes}"` : ""}.
              </p>
            </div>
          </div>
        )}

        {/* Caixa de Seleção e Geração da LLM */}
        <div className="rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-800/90 dark:bg-slate-900/70 p-3.5 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <label htmlFor="llm-select" className="font-medium text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <Bot className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
              <span>Selecionar LLM para Emissão:</span>
            </label>
            <span className={`rounded border px-2 py-0.5 text-[10px] font-semibold ${activeOption.color}`}>
              {activeOption.badge}
            </span>
          </div>

          <div className="relative">
            <select
              id="llm-select"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full appearance-none rounded-lg border border-slate-300 bg-white py-2.5 pl-3 pr-9 text-xs font-medium text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 cursor-pointer shadow-sm"
            >
              {LLM_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.name} — {opt.provider} ({opt.badge})
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs">
              ▼
            </div>
          </div>

          <button
            onClick={handleGenerateReport}
            disabled={loading}
            className="w-full flex items-center justify-center space-x-2 rounded-lg bg-sky-600 py-2.5 px-4 text-xs font-bold text-white shadow-md hover:bg-sky-500 disabled:opacity-50 transition-all"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Processando Laudo Clínico com {activeOption.name}…</span>
              </>
            ) : (
              <>
                <Cpu className="h-4 w-4" />
                <span>
                  {reportsMap[selectedModel]
                    ? `Regerar Laudo com ${activeOption.name}`
                    : `Emitir Laudo com ${activeOption.name}`}
                </span>
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="flex items-center space-x-2 rounded-lg bg-rose-500/10 border border-rose-500/20 p-3 text-xs text-rose-600 dark:text-rose-300">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Barra de Abas dos Laudos Gerados */}
        {generatedModelKeys.length > 0 && (
          <div className="space-y-3 pt-1">
            <div className="flex flex-wrap items-center gap-1.5 border-b border-slate-200 dark:border-slate-800 pb-2">
              <span className="text-[11px] font-semibold uppercase text-slate-500 dark:text-slate-400 mr-1 flex items-center gap-1">
                <Layers className="h-3 w-3" /> Laudos:
              </span>

              {generatedModelKeys.map((modelKey) => {
                const opt = LLM_OPTIONS.find((o) => o.id === modelKey);
                const isActive = activeTab === modelKey;
                return (
                  <button
                    key={modelKey}
                    onClick={() => setActiveTab(modelKey)}
                    className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
                      isActive
                        ? "bg-sky-600 text-white font-semibold shadow-sm"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-slate-200"
                    }`}
                  >
                    {opt?.name ?? modelKey}
                  </button>
                );
              })}

              {hasMultipleReports && (
                <button
                  onClick={() => setActiveTab("comparison")}
                  className={`flex items-center space-x-1 rounded-lg px-3 py-1 text-xs font-bold transition-all ml-auto ${
                    activeTab === "comparison"
                      ? "bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20"
                      : "bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/30 hover:bg-amber-500/25"
                  }`}
                >
                  <Columns className="h-3.5 w-3.5" />
                  <span>⚖️ Comparar Lado a Lado ({generatedModelKeys.length} IAs)</span>
                </button>
              )}
            </div>

            {/* Modo Comparativo Lado a Lado */}
            {activeTab === "comparison" ? (
              <div className="space-y-4 pt-2">
                <div className="bg-amber-500/10 border border-amber-500/20 p-3 rounded-lg text-xs text-amber-800 dark:text-amber-300">
                  <span className="font-bold">Painel de Consenso Radiológico:</span> Comparação direta
                  entre as conclusões das {generatedModelKeys.length} inteligências artificiais consultadas.
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[520px] overflow-y-auto pr-1">
                  {generatedModelKeys.map((key) => {
                    const rep = reportsMap[key];
                    const opt = LLM_OPTIONS.find((o) => o.id === key);
                    return (
                      <div
                        key={key}
                        className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-3 text-xs shadow-sm dark:border-slate-800 dark:bg-slate-950/80 dark:shadow-md"
                      >
                        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800/80 pb-2">
                          <span className="font-bold text-sky-700 dark:text-sky-300">{opt?.name ?? key}</span>
                          <span className="text-[10px] text-slate-500 dark:text-slate-400">{rep.provider}</span>
                        </div>

                        <div>
                          <h5 className="font-mono text-[10px] text-amber-700 dark:text-amber-400 uppercase font-bold">
                            Impressão Diagnóstica:
                          </h5>
                          <p className="mt-0.5 text-slate-800 dark:text-slate-200 font-medium leading-relaxed">
                            {rep.impression}
                          </p>
                        </div>

                        <div>
                          <h5 className="font-mono text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold">
                            CID-10 Sugerido:
                          </h5>
                          <span className="inline-block mt-0.5 rounded bg-sky-100 text-sky-800 border-sky-300 dark:bg-sky-950 dark:text-sky-300 dark:border-sky-800/60 px-2 py-0.5 font-mono text-[11px] border font-bold">
                            {rep.icd_10}
                          </span>
                        </div>

                        <div>
                          <h5 className="font-mono text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold">
                            Achados Chave:
                          </h5>
                          <p className="mt-0.5 text-slate-600 dark:text-slate-300 text-[11px] line-clamp-4 leading-relaxed">
                            {rep.findings}
                          </p>
                        </div>

                        <div>
                          <h5 className="font-mono text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold">
                            Recomendações:
                          </h5>
                          <p className="mt-0.5 text-slate-600 dark:text-slate-400 text-[11px]">{rep.recommendations}</p>
                        </div>

                        {rep.telemetry && (
                          <div className="pt-2 border-t border-slate-200 dark:border-slate-800/60 flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3 text-sky-500" />
                              {(rep.telemetry.latency_ms / 1000).toFixed(2)}s
                            </span>
                            <span>{rep.telemetry.total_tokens} tok</span>
                            <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                              ${rep.telemetry.estimated_cost_usd.toFixed(5)}
                            </span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : activeReport ? (
              /* Modo Laudo Individual */
              <div className="space-y-4 pt-1">
                <div className="flex flex-wrap items-center justify-between text-xs border-b border-slate-200 dark:border-slate-800/80 pb-2.5 gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-slate-500 dark:text-slate-400 text-[11px]">Inteligência:</span>
                    <span className="font-semibold text-sky-600 dark:text-sky-400 font-mono text-[11px]">
                      {activeReport.model_used}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={copyToClipboard}
                      className="flex items-center space-x-1 rounded bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 px-2.5 py-1 text-[11px] font-medium transition-colors"
                      title="Copiar texto do laudo"
                    >
                      {copied ? (
                        <Check className="h-3.5 w-3.5 text-emerald-500" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                      <span>{copied ? "Copiado!" : "Copiar"}</span>
                    </button>
                    <button
                      onClick={printReport}
                      className="flex items-center space-x-1 rounded bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 px-2.5 py-1 text-[11px] font-medium transition-colors"
                      title="Imprimir laudo médico em PDF"
                    >
                      <Printer className="h-3.5 w-3.5" />
                      <span>Imprimir / PDF</span>
                    </button>
                  </div>
                </div>

                <div className="space-y-3 font-sans text-xs leading-relaxed text-slate-700 bg-slate-50 border border-slate-200 dark:text-slate-300 dark:bg-slate-950/70 dark:border-slate-800/80 p-4 rounded-xl shadow-inner">
                  <div>
                    <h4 className="font-mono text-[10px] font-bold tracking-wider text-sky-600 dark:text-sky-400 uppercase">
                      1. Técnica do Exame
                    </h4>
                    <p className="mt-0.5 text-slate-700 dark:text-slate-300">{activeReport.technique}</p>
                  </div>

                  <div>
                    <h4 className="font-mono text-[10px] font-bold tracking-wider text-sky-600 dark:text-sky-400 uppercase">
                      2. Achados Radiológicos
                    </h4>
                    <p className="mt-0.5 text-slate-700 dark:text-slate-300">{activeReport.findings}</p>
                  </div>

                  <div className="border-t border-slate-200 dark:border-slate-800/60 pt-2">
                    <h4 className="font-mono text-[10px] font-bold tracking-wider text-amber-600 dark:text-amber-400 uppercase">
                      3. Impressão Diagnóstica
                    </h4>
                    <p className="mt-0.5 font-semibold text-slate-900 dark:text-white">{activeReport.impression}</p>
                  </div>

                  <div className="flex items-center space-x-2 border-t border-slate-200 dark:border-slate-800/60 pt-2">
                    <span className="font-mono text-[10px] font-bold tracking-wider text-slate-500 dark:text-slate-400 uppercase">
                      4. Classificação CID-10:
                    </span>
                    <span className="rounded bg-sky-100 text-sky-800 border-sky-300 dark:bg-sky-950/90 dark:text-sky-300 dark:border-sky-800/50 px-2.5 py-0.5 font-mono text-[11px] font-bold border">
                      {activeReport.icd_10}
                    </span>
                  </div>

                  <div>
                    <h4 className="font-mono text-[10px] font-bold tracking-wider text-slate-500 dark:text-slate-400 uppercase">
                      5. Recomendações Clínicas
                    </h4>
                    <p className="mt-0.5 text-slate-600 dark:text-slate-400">{activeReport.recommendations}</p>
                  </div>
                </div>

                {/* AI Observability & FinOps Telemetry Card */}
                {activeReport.telemetry && (
                  <div className="no-print rounded-xl bg-slate-50 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 p-3 text-xs text-slate-600 dark:text-slate-400 space-y-2">
                    <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800/80 pb-1.5">
                      <span className="font-mono text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                        <BarChart2 className="h-3.5 w-3.5 text-sky-500" />
                        Observabilidade & FinOps de IA
                      </span>
                      {activeReport.telemetry.fallback_triggered ? (
                        <span className="inline-flex items-center space-x-1 rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-bold text-amber-700 dark:text-amber-300 border border-amber-500/30">
                          <AlertTriangle className="h-3 w-3" />
                          <span>Degradação / Fallback</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-700 dark:text-emerald-300 border border-emerald-500/20">
                          <span>✓ Conectado</span>
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-0.5 text-[11px] font-mono">
                      <div className="flex flex-col">
                        <span className="text-[9px] uppercase text-slate-400">Latência Líquida:</span>
                        <span className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1 mt-0.5">
                          <Clock className="h-3 w-3 text-sky-500" />
                          {(activeReport.telemetry.latency_ms / 1000).toFixed(2)}s
                        </span>
                      </div>

                      <div className="flex flex-col">
                        <span className="text-[9px] uppercase text-slate-400">Consumo de Tokens:</span>
                        <span className="font-semibold text-slate-800 dark:text-slate-200 mt-0.5">
                          {activeReport.telemetry.total_tokens > 0 ? (
                            <span>{activeReport.telemetry.total_tokens} <span className="text-[9px] text-slate-400 font-normal">({activeReport.telemetry.prompt_tokens} in / {activeReport.telemetry.completion_tokens} out)</span></span>
                          ) : (
                            <span className="text-slate-400 font-normal">0 (Offline)</span>
                          )}
                        </span>
                      </div>

                      <div className="flex flex-col">
                        <span className="text-[9px] uppercase text-slate-400">Custo Estimado:</span>
                        <span className="font-semibold text-emerald-700 dark:text-emerald-400 flex items-center gap-1 mt-0.5">
                          <DollarSign className="h-3 w-3 text-emerald-500" />
                          ${activeReport.telemetry.estimated_cost_usd.toFixed(5)} USD
                        </span>
                      </div>
                    </div>

                    {activeReport.telemetry.fallback_triggered && activeReport.telemetry.fallback_reason && (
                      <p className="text-[10px] text-amber-700 dark:text-amber-400 font-medium pt-1 border-t border-amber-500/20">
                        Nota de Resiliência: {activeReport.telemetry.fallback_reason}
                      </p>
                    )}
                  </div>
                )}

                <div className="flex items-start space-x-2 rounded-lg bg-amber-500/10 border border-amber-500/20 p-2.5 text-[11px] text-amber-800 dark:text-amber-300/80">
                  <ShieldCheck className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
                  <p className="leading-normal">{activeReport.disclaimer}</p>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* Estado Inicial */}
        {generatedModelKeys.length === 0 && (
          <div className="flex flex-col items-center justify-center py-5 text-center text-slate-400 dark:text-slate-500">
            <FileText className="h-9 w-9 stroke-[1.2] text-slate-400 dark:text-slate-600 mb-1.5" />
            <p className="text-xs font-medium text-slate-600 dark:text-slate-400">Nenhum laudo emitido ainda</p>
            <p className="text-[11px] text-slate-500 max-w-xs mt-0.5">
              Selecione uma IA acima e clique em <strong>Emitir Laudo</strong>. Você poderá gerar com
              múltiplas IAs e compará-las lado a lado!
            </p>
          </div>
        )}
      </div>

      {/* 2. DOCUMENTO HOSPITALAR FORMATADO PARA IMPRESSÃO A4 / PDF (PRINT ONLY) */}
      {activeReport && (
        <div className="print-only text-slate-900 bg-white p-6 space-y-6 w-full max-w-[210mm] mx-auto">
          {/* Cabeçalho Hospitalar */}
          <div className="flex items-center justify-between border-b-2 border-slate-900 pb-3">
            <div>
              <h1 className="text-lg font-bold tracking-tight uppercase text-slate-900">
                RadioAI · Centro Hospitalar & Diagnóstico por Imagem
              </h1>
              <p className="text-[10px] text-slate-600 font-medium">
                Serviço de Radiologia Torácica · Suporte à Decisão Clínica por Visão Computacional e IA
              </p>
            </div>
            <div className="text-right text-[10px] text-slate-600 font-mono">
              <p className="font-bold text-slate-900">LAUDO MÉDICO RADIOLÓGICO</p>
              <p>EMITIDO: {new Date(activeReport.generated_at).toLocaleString("pt-BR")}</p>
            </div>
          </div>

          {/* Dados do Paciente e do Exame */}
          <div className="grid grid-cols-2 gap-3 bg-slate-50 border border-slate-300 rounded-lg p-3 text-[11px]">
            <div className="space-y-1">
              <p>
                <strong>Paciente:</strong>{" "}
                {prediction.dicom_metadata?.is_dicom ? "DESIDENTIFICADO (DICOM PS 3.15)" : "ANON_CHEST_01"}
              </p>
              <p>
                <strong>Exame:</strong> Radiografia Digital de Tórax
              </p>
              <p>
                <strong>Incidência:</strong>{" "}
                {prediction.dicom_metadata?.patient_position ?? "Póstero-Anterior (PA)"}
              </p>
            </div>
            <div className="space-y-1">
              <p>
                <strong>Triagem Neural (IA):</strong> {prediction.label} ({(prediction.confidence * 100).toFixed(1)}%)
              </p>
              {overrideLabel && (
                <>
                  <p className="font-bold text-purple-900">
                    <strong>Parecer e Sobrescrita Médica:</strong> {overrideLabel}
                  </p>
                  {overrideNotes && (
                    <p className="text-[10px] text-slate-600 italic">
                      <strong>Justificativa Médica:</strong> {overrideNotes}
                    </p>
                  )}
                </>
              )}
              <p>
                <strong>Inteligência da Redação:</strong> {activeReport.model_used} ({activeReport.provider})
              </p>
              <p>
                <strong>Classificação CID-10:</strong> {activeReport.icd_10}
              </p>
            </div>
          </div>

          {/* Seções Clínicas Estruturadas do Laudo */}
          <div className="space-y-4 text-xs leading-relaxed text-slate-900">
            <div>
              <h2 className="font-bold text-xs uppercase tracking-wider text-slate-900 border-b border-slate-300 pb-1">
                1. Técnica do Exame
              </h2>
              <p className="mt-1 text-slate-800">{activeReport.technique}</p>
            </div>

            <div>
              <h2 className="font-bold text-xs uppercase tracking-wider text-slate-900 border-b border-slate-300 pb-1">
                2. Achados Radiológicos
              </h2>
              <p className="mt-1 text-slate-800">{activeReport.findings}</p>
            </div>

            <div className="bg-slate-50 p-2.5 rounded border border-slate-200">
              <h2 className="font-bold text-xs uppercase tracking-wider text-slate-900 border-b border-slate-300 pb-1">
                3. Impressão Diagnóstica Conclusiva
              </h2>
              <p className="mt-1 font-bold text-slate-950 text-sm">{activeReport.impression}</p>
            </div>

            <div>
              <h2 className="font-bold text-xs uppercase tracking-wider text-slate-900 border-b border-slate-300 pb-1">
                4. Classificação Internacional de Doenças (CID-10)
              </h2>
              <p className="mt-1 font-semibold text-slate-900 font-mono">{activeReport.icd_10}</p>
            </div>

            <div>
              <h2 className="font-bold text-xs uppercase tracking-wider text-slate-900 border-b border-slate-300 pb-1">
                5. Recomendações e Conduta Clínica
              </h2>
              <p className="mt-1 text-slate-800">{activeReport.recommendations}</p>
            </div>
          </div>

          {/* Validação e Campo de Assinatura Médica */}
          <div className="pt-8 border-t border-slate-300 grid grid-cols-2 gap-8 text-xs text-center text-slate-600 print-page-avoid">
            <div className="space-y-1">
              <div className="border-t border-slate-400 w-3/4 mx-auto pt-1">
                <p className="font-semibold text-slate-900">Médico(a) Assistente / Radiologista</p>
                <p className="text-[10px] text-slate-500">CRM / RQE</p>
              </div>
            </div>
            <div className="space-y-1">
              <div className="border-t border-slate-400 w-3/4 mx-auto pt-1">
                <p className="font-semibold text-slate-900">Data e Assinatura</p>
                <p className="text-[10px] text-slate-500">____ / ____ / ________</p>
              </div>
            </div>
          </div>

          {/* Aviso Legal Mandatório */}
          <div className="text-[8.5px] text-slate-500 border-t border-slate-200 pt-2 text-justify leading-tight">
            <p><strong>Aviso Regulatório (Suporte à Decisão Clínica):</strong> {activeReport.disclaimer}</p>
          </div>
        </div>
      )}
    </>
  );
};
