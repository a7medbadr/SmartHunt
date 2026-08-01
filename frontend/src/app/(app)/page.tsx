"use client";

import { useQuery } from "@tanstack/react-query";
import {
  FileText,
  Heart,
  Mail,
  Send,
  BookmarkPlus,
  Clock,
  type LucideIcon,
} from "lucide-react";

import { getDashboardStatistics } from "@/lib/dashboard-api";
import { getRecentActivities, type ActivityType } from "@/lib/activity-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const STAT_CARDS: Array<{
  key: keyof Awaited<ReturnType<typeof getDashboardStatistics>>;
  label: string;
}> = [
  { key: "jobs", label: "الوظائف المكتشفة" },
  { key: "applications", label: "التقديمات" },
  { key: "favorites", label: "المفضلة" },
  { key: "saved_searches", label: "عمليات البحث المحفوظة" },
  { key: "providers", label: "مواقع التوظيف المفعّلة" },
];

const ACTIVITY_ICONS: Record<ActivityType, LucideIcon> = {
  resume_uploaded: FileText,
  application_created: Send,
  favorite_added: Heart,
  saved_search_created: BookmarkPlus,
  cover_letter_generated: Mail,
};

function timeAgo(isoDate: string): string {
  const diffMs = Date.now() - new Date(isoDate).getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "الآن";
  if (minutes < 60) return `من ${minutes} دقيقة`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `من ${hours} ساعة`;
  const days = Math.floor(hours / 24);
  return `من ${days} يوم`;
}

export default function DashboardPage() {
  const { data, isPending, isError } = useQuery({
    queryKey: ["dashboard-statistics"],
    queryFn: getDashboardStatistics,
  });

  const { data: activities, isPending: activitiesPending } = useQuery({
    queryKey: ["recent-activity"],
    queryFn: getRecentActivities,
  });

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">الداشبورد</h1>

      {isError && (
        <p className="text-sm text-destructive">
          مقدرناش نجيب إحصائيات الداشبورد، جرب تحدّث الصفحة.
        </p>
      )}

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {STAT_CARDS.map((stat) => (
          <Card key={stat.key}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-normal text-muted-foreground">
                {stat.label}
              </CardTitle>
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
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base font-medium">
            <Clock className="size-4 text-muted-foreground" />
            آخر النشاطات
          </CardTitle>
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
                const Icon = ACTIVITY_ICONS[activity.type] ?? Clock;
                return (
                  <li
                    key={activity.id}
                    className="flex items-center gap-3 rounded-md px-2 py-2 hover:bg-muted/50"
                  >
                    <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
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
