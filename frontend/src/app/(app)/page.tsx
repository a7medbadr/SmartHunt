"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Briefcase,
  Building2,
  Home,
  MessageCircle,
  Rss,
  Clock,
  Search,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";

import { getDashboardStatistics, getDashboardTimeseries } from "@/lib/dashboard-api";
import { getRecentActivities } from "@/lib/activity-api";
import { ACTIVITY_ICONS } from "@/lib/activity-icons";
import { PageGlow } from "@/components/page-glow";
import { DashboardTrendChart } from "@/components/dashboard-trend-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn, timeAgo } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n/language-context";

const TREND_RANGES = [7, 14, 30, 90] as const;
type TrendRange = (typeof TREND_RANGES)[number];

const TREND_CHARTS: Array<{
  metricKey: "job_sites" | "linkedin_posts" | "whatsapp_posts" | "applications";
  labelKey: "statJobSites" | "statLinkedinPosts" | "statWhatsappPosts" | "statApplications";
  icon: LucideIcon;
  iconColorClass: string;
  color: string;
}> = [
  {
    metricKey: "job_sites",
    labelKey: "statJobSites",
    icon: Search,
    iconColorClass: "text-emerald-400",
    color: "var(--color-emerald-400)",
  },
  {
    metricKey: "linkedin_posts",
    labelKey: "statLinkedinPosts",
    icon: Rss,
    iconColorClass: "text-sky-400",
    color: "var(--color-sky-400)",
  },
  {
    metricKey: "whatsapp_posts",
    labelKey: "statWhatsappPosts",
    icon: MessageCircle,
    iconColorClass: "text-green-500",
    color: "var(--color-green-500)",
  },
  {
    metricKey: "applications",
    labelKey: "statApplications",
    icon: Briefcase,
    iconColorClass: "text-orange-400",
    color: "var(--color-orange-400)",
  },
];

// Order matters (explicit request): the 3 discovered-jobs pages first, in
// the same order as their entries under the "Discovered Jobs" nav group
// (/jobs/sites, /jobs/linkedin, /jobs/whatsapp), then applications and
// providers. The old "favorites" card was dropped to make room for the
// WhatsApp card without the grid growing further, per explicit request —
// favorites are still one click away from any Jobs page.
const STAT_CARDS: Array<{
  key: keyof Awaited<ReturnType<typeof getDashboardStatistics>>;
  labelKey: "statJobSites" | "statLinkedinPosts" | "statWhatsappPosts" | "statApplications" | "statProviders";
  href?: string;
  icon: LucideIcon;
  color: string;
}> = [
  {
    key: "job_sites",
    labelKey: "statJobSites",
    href: "/jobs/sites",
    icon: Search,
    color: "text-emerald-400",
  },
  {
    key: "linkedin_posts",
    labelKey: "statLinkedinPosts",
    href: "/jobs/linkedin",
    icon: Rss,
    color: "text-sky-400",
  },
  {
    key: "whatsapp_posts",
    labelKey: "statWhatsappPosts",
    href: "/jobs/whatsapp",
    icon: MessageCircle,
    color: "text-green-500",
  },
  {
    key: "applications",
    labelKey: "statApplications",
    href: "/applications",
    icon: Briefcase,
    color: "text-orange-400",
  },
  {
    key: "providers",
    labelKey: "statProviders",
    href: "/providers",
    icon: Building2,
    color: "text-indigo-400",
  },
];

export default function DashboardPage() {
  const { t, locale } = useTranslation();
  const { data, isPending, isError } = useQuery({
    queryKey: ["dashboard-statistics"],
    queryFn: getDashboardStatistics,
  });

  const { data: activities, isPending: activitiesPending } = useQuery({
    queryKey: ["recent-activity"],
    queryFn: () => getRecentActivities(5),
  });

  const [trendRange, setTrendRange] = useState<TrendRange>(14);
  const { data: timeseries, isPending: timeseriesPending } = useQuery({
    queryKey: ["dashboard-timeseries", trendRange],
    queryFn: () => getDashboardTimeseries(trendRange),
    // Keeps the previous range's charts on screen (instead of a flash to
    // skeletons) while a new range loads — "refetch keeps the frame".
    placeholderData: (previousData) => previousData,
  });
  const trendPoints = timeseries?.points ?? [];

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden">
      <PageGlow />

      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <Home className="size-6 text-blue-400" />
        {t("pageTitles", "dashboard")}
      </h1>

      {isError && (
        <p className="text-sm text-destructive">{t("dashboard", "statsError")}</p>
      )}

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {STAT_CARDS.map((stat) => {
          const Icon = stat.icon;
          const card = (
            <Card
              className={
                stat.href
                  ? "h-full transition-colors hover:border-primary hover:bg-muted/50"
                  : "h-full"
              }
            >
              <CardHeader className="flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-normal text-muted-foreground">
                  {t("dashboard", stat.labelKey)}
                </CardTitle>
                <Icon className={cn("size-4", stat.color)} />
              </CardHeader>
              <CardContent>
                {isPending ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <span className="text-3xl font-semibold">
                    {data?.[stat.key] ?? 0}
                  </span>
                )}
              </CardContent>
            </Card>
          );

          return stat.href ? (
            <Link key={stat.key} href={stat.href}>
              {card}
            </Link>
          ) : (
            <div key={stat.key}>{card}</div>
          );
        })}
      </div>

      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="flex items-center gap-2 text-base font-medium">
            <TrendingUp className="size-4 text-teal-400" />
            {t("dashboard", "dailyTrendsTitle")}
            <span className="text-xs font-normal text-muted-foreground">
              — {t("dashboard", "dailyTrendsSubtitle")}
            </span>
          </h2>
          <div className="flex items-center gap-1 rounded-lg border p-1">
            {TREND_RANGES.map((range) => (
              <button
                key={range}
                type="button"
                onClick={() => setTrendRange(range)}
                className={cn(
                  "rounded-md px-2.5 py-1 text-xs transition-colors",
                  trendRange === range
                    ? "bg-primary/10 font-medium text-foreground"
                    : "text-muted-foreground hover:bg-primary/10 hover:text-foreground",
                )}
              >
                {t("dashboard", `range${range}` as "range7" | "range14" | "range30" | "range90")}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {TREND_CHARTS.map((chart) => (
            <DashboardTrendChart
              key={chart.metricKey}
              title={t("dashboard", chart.labelKey)}
              icon={chart.icon}
              iconColorClass={chart.iconColorClass}
              color={chart.color}
              metricKey={chart.metricKey}
              points={trendPoints}
              isPending={timeseriesPending}
            />
          ))}
        </div>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base font-medium">
            <Clock className="size-4 text-muted-foreground" />
            {t("dashboard", "recentActivity")}
          </CardTitle>
          <Link href="/activity" className="text-xs text-primary hover:underline">
            {t("dashboard", "viewAllActivity")}
          </Link>
        </CardHeader>
        <CardContent>
          {activitiesPending ? (
            <div className="flex flex-col gap-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : activities && activities.length > 0 ? (
            <ul className="flex flex-col gap-1">
              {activities.map((activity) => {
                const entry = ACTIVITY_ICONS[activity.type];
                const Icon = entry?.icon ?? Clock;
                const color = entry?.color ?? "text-muted-foreground";
                return (
                  <li
                    key={activity.id}
                    className="flex items-center gap-3 rounded-md px-2 py-2 hover:bg-muted/50"
                  >
                    <span
                      className={cn(
                        "flex size-8 shrink-0 items-center justify-center rounded-full bg-current/10",
                        color,
                      )}
                    >
                      <Icon className="size-4" />
                    </span>
                    <div className="flex min-w-0 flex-1 flex-col">
                      <p className="truncate text-sm">{activity.title}</p>
                      {activity.details && (
                        <p className="truncate text-xs text-muted-foreground">
                          {activity.details}
                        </p>
                      )}
                    </div>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {timeAgo(activity.created_at, locale)}
                    </span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">{t("dashboard", "noActivityYet")}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
