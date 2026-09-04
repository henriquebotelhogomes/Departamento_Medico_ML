import React, { useState } from "react";
import { AlertTriangle, UserCheck, RotateCcw, Check, Sparkles, MessageSquare } from "lucide-react";
import type { ClassProbability } from "@/lib/types";

interface ClinicalInterventionPanelProps {
  probs: ClassProbability[];
  originalLabel: string;
  overrideLabel: string | null;
  overrideNotes: string;
  onOverrideChange: (label: string | null, notes: string) => void;
}

const AVAILABLE_DIAGNOSES = [
  { id: "Pneumonia bacteriana", label: "Pneumonia Bacteriana", icon: "🧫" },
  { id: "Pneumonia viral", label: "Pneumonia Viral", icon: "🧬" },
  { id: "Covid-19", label: "Covid-19", icon: "🦠" },
  { id: "Normal", label: "Normal (Sem Infecção)", icon: "🫁" },
];

export const ClinicalInterventionPanel: React.FC<ClinicalInterventionPanelProps> = ({
  probs,
  originalLabel,
  overrideLabel,
  overrideNotes,
  onOverrideChange,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(Boolean(overrideLabel));
  const [tempNotes, setTempNotes] = useState<string>(overrideNotes);

  // Analisa se há empate técnico / incerteza diagnóstica (margem < 15% ou top1 < 65%)
  const sorted = [...probs].sort((a, b) => b.probability - a.probability);
  const top1 = sorted[0];
  const top2 = sorted[1];
  const delta = top1 && top2 ? (top1.probability - top2.probability) * 100 : 100;
  const isAmbiguous = delta < 15.0 || (top1 && top1.probability < 0.65);

  const handleSelectDiagnosis = (chosen: string) => {
    if (chosen === originalLabel && !overrideLabel) {
      return;
    }
    if (chosen === originalLabel) {
      // Restaurando para original
      onOverrideChange(null, "");
      setTempNotes("");
      return;
    }
    onOverrideChange(chosen, tempNotes);
  };

  const handleNotesBlur = () => {
    if (overrideLabel) {
      onOverrideChange(overrideLabel, tempNotes);
    }
  };

  const handleReset = () => {
    onOverrideChange(null, "");
    setTempNotes("");
    setIsOpen(false);
  };

  return (
    <div className="no-print space-y-3">
      {/* 1. Alerta de Incerteza Clínica (Empate Técnico / Margem Estreita) */}
      {isAmbiguous && !overrideLabel && top1 && top2 && (
        <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-3.5 text-xs text-amber-900 dark:text-amber-200 space-y-2 shadow-sm animate-in fade-in duration-300">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0" />
            <h4 className="font-bold text-xs">
              Alerta de Ambiguidade Diagnóstica (Margem Estreita: {delta.toFixed(1)}%)
            </h4>
          </div>
          <p className="text-[11px] leading-relaxed text-amber-800 dark:text-amber-200/90">
            A rede neural identificou proximidade estatística entre as hipóteses principais:{" "}
            <strong>{top1.label} ({(top1.probability * 100).toFixed(1)}%)</strong> versus{" "}
            <strong>{top2.label} ({(top2.probability * 100).toFixed(1)}%)</strong>. A supervisão
            médica e a correlação com biomarcadores (ex: Procalcitonina) são mandatórias.
          </p>
          <div className="pt-1">
            <button
              onClick={() => setIsOpen(true)}
              className="inline-flex items-center space-x-1.5 rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-amber-500 transition-colors shadow-sm"
            >
              <UserCheck className="h-3.5 w-3.5" />
              <span>Intervir / Definir Conduta Médica</span>
            </button>
          </div>
        </div>
      )}

      {/* 2. Painel de Intervenção Humana (Human-in-the-Loop) */}
      <div
        className={`rounded-xl border transition-all p-4 space-y-3 ${
          overrideLabel
            ? "border-purple-500/50 bg-purple-500/5 dark:bg-purple-950/20 shadow-md shadow-purple-500/5"
            : "border-slate-200 bg-slate-50/70 dark:border-slate-800 dark:bg-slate-900/40"
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 text-xs">
              👨‍⚕️
            </span>
            <div>
              <h4 className="font-semibold text-xs text-slate-900 dark:text-white flex items-center gap-1.5">
                Supervisão Médica (Human-in-the-Loop)
                {overrideLabel && (
                  <span className="inline-flex items-center rounded-full bg-purple-500/15 px-2 py-0.2 text-[10px] font-bold text-purple-700 dark:text-purple-300 border border-purple-500/30">
                    Sobrescrita Ativa
                  </span>
                )}
              </h4>
              <p className="text-[10px] text-slate-500 dark:text-slate-400">
                O médico assistente pode sobrescrever soberanamente a IA para orientar o laudo
              </p>
            </div>
          </div>

          {overrideLabel ? (
            <button
              onClick={handleReset}
              className="flex items-center space-x-1 text-[11px] font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 transition-colors"
              title="Restaurar predição original da IA"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Restaurar IA</span>
            </button>
          ) : (
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-[11px] font-semibold text-sky-600 dark:text-sky-400 hover:underline"
            >
              {isOpen ? "Ocultar Opções" : "Alterar Diagnóstico"}
            </button>
          )}
        </div>

        {/* Opções de Seleção de Conduta */}
        {isOpen && (
          <div className="space-y-3 pt-2 border-t border-slate-200 dark:border-slate-800 animate-in fade-in duration-200">
            <div>
              <span className="text-[10px] font-mono uppercase text-slate-500 dark:text-slate-400 tracking-wider block mb-1.5">
                Selecione o Diagnóstico Soberano do Médico:
              </span>
              <div className="grid grid-cols-2 gap-2">
                {AVAILABLE_DIAGNOSES.map((diag) => {
                  const isSelected = overrideLabel
                    ? overrideLabel.toLowerCase() === diag.id.toLowerCase()
                    : originalLabel.toLowerCase() === diag.id.toLowerCase();
                  const isNeural = originalLabel.toLowerCase() === diag.id.toLowerCase();

                  return (
                    <button
                      key={diag.id}
                      onClick={() => handleSelectDiagnosis(diag.id)}
                      className={`flex items-center space-x-2 p-2.5 rounded-lg border text-left text-xs transition-all ${
                        isSelected
                          ? "border-purple-500 bg-purple-50 text-purple-950 dark:bg-purple-950/40 dark:text-purple-200 font-bold shadow-sm"
                          : "border-slate-200 bg-white hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-950/80 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
                      }`}
                    >
                      <span className="text-base">{diag.icon}</span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between">
                          <span className="truncate">{diag.label}</span>
                          {isSelected && <Check className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400 shrink-0 ml-1" />}
                        </div>
                        {isNeural && (
                          <span className="text-[9px] text-sky-600 dark:text-sky-400 font-normal block">
                            (Sugestão Neural Original)
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Justificativa Clínica / Biomarcadores */}
            {overrideLabel && (
              <div className="space-y-1.5 pt-1">
                <label className="text-[10px] font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1">
                  <MessageSquare className="h-3 w-3 text-purple-500" />
                  <span>Justificativa Médica / Biomarcadores (Opcional):</span>
                </label>
                <input
                  type="text"
                  value={tempNotes}
                  onChange={(e) => setTempNotes(e.target.value)}
                  onBlur={handleNotesBlur}
                  placeholder="Ex: Procalcitonina baixa (<0.1 ug/L), padrão intersticial difuso compatível com etiologia viral"
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 placeholder:text-slate-400 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                />
                <p className="text-[10px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
                  <Sparkles className="h-3 w-3 text-amber-500" />
                  Ao clicar em <strong>Emitir Laudo</strong>, a IA incorporará esta justificativa na redação formal.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
