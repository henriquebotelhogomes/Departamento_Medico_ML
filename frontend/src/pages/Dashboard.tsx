import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity, Gauge, Layers } from "lucide-react";
import { useTranslation } from "react-i18next";
import { fetchStats } from "@/lib/api";
import { CLASS_COLORS } from "@/lib/types";
import { useTheme } from "@/context/ThemeContext";

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Activity;
  label: string;
  value: string;
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className="rounded-lg bg-brand-50 p-3 text-brand-600 dark:bg-brand-950 dark:text-brand-400">
        <Icon className="h-6 w-6" />
      </div>
      <div>
        <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
    </div>
  );
}

export function Dashboard() {
  const { theme } = useTheme();
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({ queryKey: ["stats"], queryFn: fetchStats });
  const grid = theme === "dark" ? "#334155" : "#e2e8f0";
  const tick = theme === "dark" ? "#94a3b8" : "#64748b";
  const tooltipText = theme === "dark" ? "#e2e8f0" : "#1e293b";

  if (isLoading || !data) {
    return <p className="text-slate-400">{t("dashboard.loading")}</p>;
  }

  const topClass = [...data.by_class].sort((a, b) => b.count - a.count)[0];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("dashboard.title")}</h1>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard icon={Activity} label={t("dashboard.total_predictions")} value={String(data.total_predictions)} />
        <StatCard
          icon={Gauge}
          label={t("dashboard.avg_confidence")}
          value={`${(data.average_confidence * 100).toFixed(1)}%`}
        />
        <StatCard
          icon={Layers}
          label={t("dashboard.most_frequent")}
          value={data.total_predictions ? topClass.label : "—"}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-4 text-sm font-semibold text-slate-600 dark:text-slate-300">
            {t("dashboard.chart_by_class")}
          </h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.by_class}>
              <CartesianGrid strokeDasharray="3 3" stroke={grid} />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: tick }} stroke={grid} interval={0} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: tick }} stroke={grid} />
              <Tooltip
                contentStyle={{
                  background: theme === "dark" ? "#0f172a" : "#fff",
                  border: `1px solid ${grid}`,
                  borderRadius: 8,
                  color: tooltipText,
                }}
                labelStyle={{ color: tooltipText }}
                itemStyle={{ color: tooltipText }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {data.by_class.map((c) => (
                  <Cell key={c.class_id} fill={CLASS_COLORS[c.class_id]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="mb-4 text-sm font-semibold text-slate-600 dark:text-slate-300">
            {t("dashboard.chart_over_time")}
          </h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={data.over_time}>
              <CartesianGrid strokeDasharray="3 3" stroke={grid} />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: tick }} stroke={grid} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: tick }} stroke={grid} />
              <Tooltip
                contentStyle={{
                  background: theme === "dark" ? "#0f172a" : "#fff",
                  border: `1px solid ${grid}`,
                  borderRadius: 8,
                  color: tooltipText,
                }}
                labelStyle={{ color: tooltipText }}
                itemStyle={{ color: tooltipText }}
              />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#1f57e0"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
