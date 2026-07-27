import { useCallback, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { UploadCloud, Loader2, ImageIcon, Brain, AlertTriangle } from "lucide-react";
import { useTranslation } from "react-i18next";
import { apiError, predict } from "@/lib/api";
import type { PredictionResult } from "@/lib/types";
import { ProbabilityBar } from "@/components/ProbabilityBar";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";

const ACCEPTED = ["image/jpeg", "image/png", "image/webp", "image/bmp"];

export function Predict() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResult | null>(null);

  const mutation = useMutation({
    mutationFn: predict,
    onSuccess: (data) => {
      setResult(data);
      void queryClient.invalidateQueries({ queryKey: ["history"] });
      void queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
    onError: (err) => setError(apiError(err, t("predict.prediction_failed"))),
  });

  const selectFile = useCallback((f: File | null) => {
    setError(null);
    setResult(null);
    if (!f) return;
    if (!ACCEPTED.includes(f.type)) {
      setError(t("predict.unsupported_type"));
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }, []);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    selectFile(e.dataTransfer.files?.[0] ?? null);
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <section>
        <h1 className="mb-1 text-2xl font-bold">{t("predict.title")}</h1>
        <p className="mb-4 text-sm text-slate-500 dark:text-slate-400">
          {t("predict.description")}
        </p>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
            dragging
              ? "border-brand-500 bg-brand-50 dark:bg-brand-950/40"
              : "border-slate-300 hover:border-brand-400 dark:border-slate-700"
          }`}
        >
          {preview ? (
            <img src={preview} alt="preview" className="max-h-64 rounded-lg object-contain" />
          ) : (
            <>
              <UploadCloud className="mb-2 h-10 w-10 text-slate-400" />
              <p className="text-sm font-medium">{t("predict.drop_zone")}</p>
              <p className="text-xs text-slate-400">{t("predict.formats")}</p>
            </>
          )}
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED.join(",")}
            className="hidden"
            onChange={(e) => selectFile(e.target.files?.[0] ?? null)}
          />
        </div>

        {error && (
          <div className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </div>
        )}

        <button
          className="btn-primary mt-4 w-full"
          disabled={!file || mutation.isPending}
          onClick={() => file && mutation.mutate(file)}
        >
          {mutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" /> {t("predict.analyzing")}
            </>
          ) : (
            t("predict.run_prediction")
          )}
        </button>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold">{t("predict.result")}</h2>
        {result ? (
          result.is_ood ? (
            <div className="card space-y-4 border-2 border-amber-400 dark:border-amber-500">
              <div className="flex items-center gap-3">
                <div className="rounded-full bg-amber-100 p-3 dark:bg-amber-900/40">
                  <AlertTriangle className="h-7 w-7 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <p className="text-lg font-bold text-amber-700 dark:text-amber-300">
                    {t("predict.ood_title")}
                  </p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {t("predict.ood_subtitle")}
                  </p>
                </div>
              </div>
              <div className="rounded-lg bg-amber-50 px-4 py-3 dark:bg-amber-950/30">
                <p className="text-sm text-amber-800 dark:text-amber-200">
                  {t("predict.ood_explanation")}
                </p>
              </div>
              {result.ood_similarity !== null && (
                <p className="text-xs text-slate-400">
                  {t("predict.ood_similarity", { value: (result.ood_similarity * 100).toFixed(1) })}
                </p>
              )}
              <p className="text-xs text-slate-400">
                {t("predict.inference_time", { ms: result.inference_ms.toFixed(0) })}
              </p>
            </div>
          ) : (
          <div className="card space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">{t("predict.predicted_class")}</p>
                <p className="text-2xl font-bold">{result.label}</p>
              </div>
              <ConfidenceBadge confidence={result.confidence} />
            </div>

            {result.gradcam_image && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
                  <Brain className="h-4 w-4" />
                  <span>{t("predict.gradcam_title")}</span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {preview && (
                    <div>
                      <p className="mb-1 text-xs text-slate-400">{t("predict.gradcam_original")}</p>
                      <img
                        src={preview}
                        alt="Original X-ray"
                        className="w-full rounded-lg border border-slate-200 dark:border-slate-700"
                      />
                    </div>
                  )}
                  <div>
                    <p className="mb-1 text-xs text-slate-400">{t("predict.gradcam_heatmap")}</p>
                    <img
                      src={result.gradcam_image}
                      alt="Grad-CAM heatmap showing model attention"
                      className="w-full rounded-lg border border-slate-200 dark:border-slate-700"
                    />
                  </div>
                </div>
                <p className="text-xs text-slate-400">
                  {t("predict.gradcam_explanation")}
                </p>
              </div>
            )}

            <div className="space-y-3">
              {result.probs.map((p) => (
                <ProbabilityBar
                  key={p.class_id}
                  classId={p.class_id}
                  label={p.label}
                  probability={p.probability}
                  highlight={p.class_id === result.predicted_class}
                />
              ))}
            </div>
            <p className="text-xs text-slate-400">
              {t("predict.inference_time", { ms: result.inference_ms.toFixed(0) })}
            </p>
          </div>
          )
        ) : (
          <div className="card flex flex-col items-center justify-center py-16 text-slate-400">
            <ImageIcon className="mb-2 h-10 w-10" />
            <p className="text-sm">{t("predict.placeholder")}</p>
          </div>
        )}
      </section>
    </div>
  );
}
