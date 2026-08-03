"use client";

import { useQuery } from "@tanstack/react-query";
import { History } from "lucide-react";

import { getRecentActivities } from "@/lib/activity-api";
import { ACTIVITY_ICONS } from "@/lib/activity-icons";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn, timeAgo } from "@/lib/utils";

export default function ActivityPage() {
  const { data: activities, isPending, isError } = useQuery({
    queryKey: ["activity-log"],
    queryFn: () => getRecentActivities(200),
  });

  return (
    <div className="flex flex-col gap-6">
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <History className="size-6 text-teal-400" />
        سجل النشاطات
      </h1>

      {isError && (
        <p className="text-sm text-destructive">مقدرناش نجيب سجل النشاطات، جرب تحدّث الصفحة.</p>
      )}

      <Card>
        <CardContent className="pt-6">
          {isPending ? (
            <div className="flex flex-col gap-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : activities && activities.length > 0 ? (
            <ul className="flex flex-col gap-1">
              {activities.map((activity) => {
                const entry = ACTIVITY_ICONS[activity.type];
                const Icon = entry?.icon ?? History;
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
