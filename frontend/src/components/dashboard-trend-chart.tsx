"use client";

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { LucideIcon } from "lucide-react";

import type { DashboardTimeseriesPoint } from "@/lib/dashboard-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslation } from "@/lib/i18n/language-context";
import { cn } from "@/lib/utils";

interface DashboardTrendChartProps {
  title: string;
  icon: LucideIcon;
  iconColorClass: string;
  // A CSS color string — this project's Tailwind v4 build exposes every
  // palette shade as a real `--color-*` custom property on :root, so
  // passing e.g. "var(--color-emerald-400)" keeps the bar fill in exact
  // sync with the Tailwind class used for this same metric's icon
  // elsewhere (nav, stat cards) without duplicating a hex value here.
  color: string;
  points: DashboardTimeseriesPoint[];
  metricKey: keyof Omit<DashboardTimeseriesPoint, "date">;
  isPending: boolean;
}

export function DashboardTrendChart({
  title,
  icon: Icon,
  iconColorClass,
  color,
  points,
  metricKey,
  isPending,
}: DashboardTrendChartProps) {
  const { t, locale } = useTranslation();
  const dateLocale = locale === "ar" ? "ar-SA" : "en-US";

  const chartData = useMemo(
    () =>
      points.map((point) => ({
        value: point[metricKey],
        label: new Date(point.date).toLocaleDateString(dateLocale, {
          day: "numeric",
          month: "short",
        }),
      })),
    [points, metricKey, dateLocale],
  );

  const total = useMemo(() => chartData.reduce((sum, p) => sum + p.value, 0), [chartData]);
  const today = chartData[chartData.length - 1]?.value ?? 0;
  const yesterday = chartData[chartData.length - 2]?.value ?? 0;
  const delta = today - yesterday;
  const hasData = total > 0;

  return (
    <Card className="h-full">
      <CardHeader className="flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-normal text-muted-foreground">
          <Icon className={cn("size-4", iconColorClass)} />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {isPending ? (
          <Skeleton className="h-40 w-full" />
        ) : (
          <>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-semibold">{total}</span>
              <span className="text-xs text-muted-foreground">
                {t("dashboard", "trendTotalInRange")}
              </span>
            </div>
            <p
              className={cn(
                "text-xs",
                delta > 0
                  ? "text-emerald-400"
                  : delta < 0
                    ? "text-rose-400"
                    : "text-muted-foreground",
              )}
            >
              {delta > 0
                ? t("dashboard", "trendDeltaUp").replace("{delta}", String(delta))
                : delta < 0
                  ? t("dashboard", "trendDeltaDown").replace("{delta}", String(Math.abs(delta)))
                  : t("dashboard", "trendDeltaFlat")}
            </p>

            {hasData ? (
              <div className="h-40 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                    <CartesianGrid
                      vertical={false}
                      stroke="var(--border)"
                      strokeDasharray="0"
                    />
                    <XAxis
                      dataKey="label"
                      tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
                      axisLine={{ stroke: "var(--border)" }}
                      tickLine={false}
                      interval="preserveStartEnd"
                      minTickGap={20}
                    />
                    <YAxis
                      allowDecimals={false}
                      tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
                      axisLine={false}
                      tickLine={false}
                      width={28}
                    />
                    <Tooltip
                      cursor={{ fill: "var(--muted)", opacity: 0.4 }}
                      content={({ active, payload }) => {
                        if (!active || !payload?.length) return null;
                        const point = payload[0].payload as { label: string; value: number };
                        return (
                          <div className="rounded-md border bg-popover px-3 py-2 text-xs shadow-md">
                            <p className="text-muted-foreground">{point.label}</p>
                            <p className="font-semibold text-popover-foreground">
                              {point.value}{" "}
                              <span className="font-normal text-muted-foreground">
                                {t("dashboard", "trendTooltipValue")}
                              </span>
                            </p>
                          </div>
                        );
                      }}
                    />
                    <Bar dataKey="value" fill={color} radius={[4, 4, 0, 0]} maxBarSize={24} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="flex h-40 items-center justify-center text-xs text-muted-foreground">
                {t("dashboard", "trendNoData")}
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
