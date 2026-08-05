"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Briefcase,
  Building2,
  Heart,
  Home,
  Rss,
  Clock,
  Search,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";

import { getDashboardStatistics } from "@/lib/dashboard-api";
import { getRecentActivities } from "@/lib/activity-api";
import { ACTIVITY_ICONS } from "@/lib/activity-icons";
import { PageGlow } from "@/components/page-glow";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn, timeAgo } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n/language-context";

const STAT_CARDS: Array<{
  key: keyof Awaited<ReturnType<typeof getDashboardStatistics>>;
  label: string;
  href?: string;
  icon: LucideIcon;
  color: string;
}> = [
  { key: "jobs", label: "الوظائف المكتشفة", href: "/jobs", icon: Search, color: "text-emerald-400" },
  {
    key: "linkedin_posts",
    label: "وظائف من بوستات لينكدان",
    href: "/job-search",
    icon: Rss,
    color: "text-sky-400",
  },
  {
    key: "applications",
    label: "التقديمات",
    href: "/applications",
    icon: Briefcase,
    color: "text-orange-400",
  },
  { key: "favorites", label: "المفضلة", href: "/jobs", icon: Heart, color: "text-rose-400" },
  {
    key: "providers",
    label: "مواقع التوظيف المفعّلة",
    href: "/providers",
    icon: Building2,
    color: "text-indigo-400",
  },
];

export default function DashboardPage() {
  const { t } = useTranslation();
  const { data, isPending, isError } = useQuery({
    queryKey: ["dashboard-statistics"],
    queryFn: getDashboardStatistics,
  });

  const { data: activities, isPending: activitiesPending } = useQuery({
    queryKey: ["recent-activity"],
    queryFn: () => getRecentActivities(5),
  });

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden">
      <PageGlow />

      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <Home className="size-6 text-blue-400" />
        {t("pageTitles", "dashboard")}
      </h1>

      {isError && (
        <p className="text-sm text-destructive">
          مقدرناش نجيب إحصائيات الداشبورد، جرب تحدّث الصفحة.
        </p>
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
                  {stat.label}
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

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base font-medium">
            <Clock className="size-4 text-muted-foreground" />
            آخر النشاطات
          </CardTitle>
          <Link href="/activity" className="text-xs text-primary hover:underline">
            شوف كل النشاطات
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
                      {timeAgo(activity.created_at)}
                    </span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">مفيش نشاط لسه.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
