import { useTranslation } from "react-i18next";

interface Props {
  confidence: number;
}

export function ConfidenceBadge({ confidence }: Props) {
  const { t } = useTranslation();
  const pct = Math.round(confidence * 1000) / 10;
  let tone = "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300";
  if (confidence >= 0.85) {
    tone = "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300";
  } else if (confidence >= 0.6) {
    tone = "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300";
  }
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold ${tone}`}>
      {t("common.confidence", { pct })}
    </span>
  );
}
