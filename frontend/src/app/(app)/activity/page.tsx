"use client";

import { useQuery } from "@tanstack/react-query";
import { History } from "lucide-react";

import { getRecentActivities } from "@/lib/activity-api";
import { ACTIVITY_ICONS } from "@/lib/activity-icons";
import { listFailedSchedulerJobs, listSchedulerHistory } from "@/lib/scheduler-api";
import { PageGlow } from "@/components/page-glow";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslation } from "@/lib/i18n/language-context";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn, timeAgo } from "@/lib/utils";

export default function ActivityPage() {
  const { t, locale } = useTranslation();
  const { data: activities, isPending, isError } = useQuery({
    queryKey: ["activity-log"],
    queryFn: () => getRecentActivities(200),
  });

  const historyQuery = useQuery({
    queryKey: ["scheduler-history"],
    queryFn: listSchedulerHistory,
  });
  const failedJobsQuery = useQuery({
    queryKey: ["scheduler-failed-jobs"],
    queryFn: listFailedSchedulerJobs,
  });

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden">
      <PageGlow />
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <History className="size-6 text-teal-400" />
        {t("pageTitles", "activity")}
      </h1>

      {isError && (
        <p className="text-sm text-destructive">{t("activity", "loadError")}</p>
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
                      {timeAgo(activity.created_at, locale)}
                    </span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">{t("activity", "noActivityYet")}</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("activity", "runHistory")}</CardTitle>
          <p className="text-xs text-muted-foreground">
            {t("activity", "runHistoryHint")}
          </p>
        </CardHeader>
        <CardContent>
          {historyQuery.isPending ? (
            <Skeleton className="h-24 w-full" />
          ) : historyQuery.data && historyQuery.data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("activity", "source")}</TableHead>
                  <TableHead>{t("activity", "status")}</TableHead>
                  <TableHead>{t("activity", "jobsFound")}</TableHead>
                  <TableHead>{t("activity", "startedAt")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {historyQuery.data.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell>{entry.provider}</TableCell>
                    <TableCell>{entry.status}</TableCell>
                    <TableCell>{entry.jobs_found}</TableCell>
                    <TableCell>{new Date(entry.started_at).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-muted-foreground">{t("activity", "noRunHistoryYet")}</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("activity", "failedJobs")}</CardTitle>
          <p className="text-xs text-muted-foreground">
            {t("activity", "failedJobsHint")}
          </p>
        </CardHeader>
        <CardContent>
          {failedJobsQuery.isPending ? (
            <Skeleton className="h-8 w-full" />
          ) : failedJobsQuery.data && failedJobsQuery.data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("activity", "source")}</TableHead>
                  <TableHead>{t("activity", "status")}</TableHead>
                  <TableHead>{t("activity", "retryCount")}</TableHead>
                  <TableHead>{t("activity", "lastError")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {failedJobsQuery.data.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell>{job.provider}</TableCell>
                    <TableCell>{job.status}</TableCell>
                    <TableCell>{job.retry_count}</TableCell>
                    <TableCell className="max-w-xs truncate">{job.last_error}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-muted-foreground">{t("activity", "noFailedJobs")}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
