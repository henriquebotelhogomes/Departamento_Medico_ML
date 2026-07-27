import { useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Trash2, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { deletePrediction, fetchHistory } from "@/lib/api";
import { CLASS_LABELS, type PredictionOut } from "@/lib/types";
import { ProbabilityBar } from "@/components/ProbabilityBar";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";

const PAGE_SIZE = 10;

export function History() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const [classFilter, setClassFilter] = useState<number | "">("");
  const [selected, setSelected] = useState<PredictionOut | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState<number | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["history", page, classFilter],
    queryFn: () =>
      fetchHistory({
        page,
        page_size: PAGE_SIZE,
        predicted_class: classFilter === "" ? undefined : classFilter,
      }),
    placeholderData: keepPreviousData,
  });

  const del = useMutation({
    mutationFn: deletePrediction,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["history"] });
      void queryClient.invalidateQueries({ queryKey: ["stats"] });
      setSelected(null);
      setConfirmingDelete(null);
    },
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">{t("history.title")}</h1>
        <select
          className="input max-w-xs"
          value={classFilter}
          onChange={(e) => {
            setClassFilter(e.target.value === "" ? "" : Number(e.target.value));
            setPage(1);
          }}
        >
          <option value="">{t("history.all_classes")}</option>
          {Object.entries(CLASS_LABELS).map(([id, label]) => (
            <option key={id} value={id}>
              {label}
            </option>
          ))}
        </select>
      </div>

      <div className="card overflow-x-auto p-0">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 text-xs uppercase text-slate-500 dark:border-slate-800 dark:text-slate-400">
            <tr>
              <th className="px-4 py-3">{t("history.col_file")}</th>
              <th className="px-4 py-3">{t("history.col_class")}</th>
              <th className="px-4 py-3">{t("history.col_confidence")}</th>
              <th className="px-4 py-3">{t("history.col_date")}</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  {t("history.loading")}
                </td>
              </tr>
            )}
            {!isLoading && data?.items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  {t("history.empty")}
                </td>
              </tr>
            )}
            {data?.items.map((item) => (
              <tr
                key={item.id}
                className="cursor-pointer border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                onClick={() => setSelected(item)}
              >
                <td className="max-w-[180px] truncate px-4 py-3">{item.original_filename}</td>
                <td className="px-4 py-3">{item.label}</td>
                <td className="px-4 py-3 tabular-nums">{(item.confidence * 100).toFixed(1)}%</td>
                <td className="px-4 py-3 text-slate-500 dark:text-slate-400">
                  {new Date(item.created_at).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right">
                  {confirmingDelete === item.id ? (
                    <div className="flex items-center justify-end gap-1">
                      <button
                        className="rounded bg-red-600 px-2 py-1 text-xs font-medium text-white hover:bg-red-700"
                        onClick={(e) => {
                          e.stopPropagation();
                          del.mutate(item.id);
                        }}
                      >
                        {t("history.confirm")}
                      </button>
                      <button
                        className="rounded bg-slate-200 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
                        onClick={(e) => {
                          e.stopPropagation();
                          setConfirmingDelete(null);
                        }}
                      >
                        {t("history.cancel")}
                      </button>
                    </div>
                  ) : (
                  <button
                    className="rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950"
                    onClick={(e) => {
                      e.stopPropagation();
                      setConfirmingDelete(item.id);
                    }}
                    aria-label={t("history.delete_aria")}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
        <span>{t("history.total", { count: data?.total ?? 0 })}</span>
        <div className="flex items-center gap-2">
          <button
            className="btn-secondary px-2 py-1"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span>
            {t("history.page_info", { page, totalPages })}
          </span>
          <button
            className="btn-secondary px-2 py-1"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {selected && (
        <div
          className="fixed inset-0 z-20 flex items-center justify-center bg-black/50 p-4"
          onClick={() => setSelected(null)}
        >
          <div
            className="card w-full max-w-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold">{selected.label}</h3>
                <p className="text-xs text-slate-400">{selected.original_filename}</p>
              </div>
              <button onClick={() => setSelected(null)} aria-label={t("history.close")}>
                <X className="h-5 w-5 text-slate-400" />
              </button>
            </div>
            {selected.image_url && (
              <img
                src={selected.image_url}
                alt={selected.label}
                className="mb-4 max-h-64 w-full rounded-lg object-contain"
              />
            )}
            <div className="mb-4">
              <ConfidenceBadge confidence={selected.confidence} />
            </div>
            <div className="space-y-3">
              {Object.entries(selected.probs)
                .map(([cid, prob]) => ({ cid: Number(cid), prob }))
                .sort((a, b) => a.cid - b.cid)
                .map(({ cid, prob }) => (
                  <ProbabilityBar
                    key={cid}
                    classId={cid}
                    label={CLASS_LABELS[cid]}
                    probability={prob}
                    highlight={cid === selected.predicted_class}
                  />
                ))}
            </div>
            {confirmingDelete === selected.id ? (
              <div className="mt-5 space-y-3">
                <p className="text-center text-sm font-medium text-red-600 dark:text-red-400">
                  {t("history.delete_question")}
                </p>
                <div className="flex gap-3">
                  <button
                    className="btn-danger flex-1"
                    onClick={() => del.mutate(selected.id)}
                    disabled={del.isPending}
                  >
                    <Trash2 className="h-4 w-4" /> {t("history.confirm_delete")}
                  </button>
                  <button
                    className="btn-secondary flex-1"
                    onClick={() => setConfirmingDelete(null)}
                  >
                    {t("history.cancel")}
                  </button>
                </div>
              </div>
            ) : (
            <button
              className="btn-danger mt-5 w-full"
              onClick={() => setConfirmingDelete(selected.id)}
              disabled={del.isPending}
            >
              <Trash2 className="h-4 w-4" /> {t("history.delete")}
            </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
