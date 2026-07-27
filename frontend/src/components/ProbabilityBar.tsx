import { useTranslation } from "react-i18next";
import { CLASS_COLORS } from "@/lib/types";

interface Props {
  label: string;
  classId: number;
  probability: number;
  highlight?: boolean;
}

export function ProbabilityBar({ label, classId, probability, highlight }: Props) {
  const { t } = useTranslation();
  const pct = Math.round(probability * 1000) / 10;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className={highlight ? "font-semibold" : "text-slate-600 dark:text-slate-300"}>
          {label}
        </span>
        <span className="tabular-nums text-slate-500 dark:text-slate-400">{pct}%</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: CLASS_COLORS[classId] ?? "#3b82f6" }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={t("common.probability_aria", { label })}
        />
      </div>
    </div>
  );
}
