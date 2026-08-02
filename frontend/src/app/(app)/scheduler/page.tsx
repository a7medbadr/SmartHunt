"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarClock } from "lucide-react";
import { useState } from "react";

import {
  listFailedSchedulerJobs,
  listSchedulerHistory,
  listSchedulerLocks,
  runDiscovery,
} from "@/lib/scheduler-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

export default function SchedulerPage() {
  const queryClient = useQueryClient();
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");

  const historyQuery = useQuery({
    queryKey: ["scheduler-history"],
    queryFn: listSchedulerHistory,
  });
  const locksQuery = useQuery({
    queryKey: ["scheduler-locks"],
    queryFn: listSchedulerLocks,
  });
  const failedJobsQuery = useQuery({
    queryKey: ["scheduler-failed-jobs"],
    queryFn: listFailedSchedulerJobs,
  });

  const runMutation = useMutation({
    mutationFn: () => runDiscovery(query, location || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduler-history"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-statistics"] });
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <CalendarClock className="size-6 text-teal-400" />
        الجدولة والبحث
      </h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">تشغيل بحث الآن</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex flex-wrap gap-2">
            <Input
              placeholder="كلمة مفتاحية (مطلوبة)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="max-w-xs"
            />
            <Input
              placeholder="الموقع (افتراضيًا: السعودية)"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="max-w-xs"
            />
            <Button
              onClick={() => runMutation.mutate()}
              disabled={!query.trim() || runMutation.isPending}
            >
              {runMutation.isPending ? "جاري البحث..." : "تشغيل الآن"}
            </Button>
          </div>

          {runMutation.data && (
            <p className="text-sm text-muted-foreground">
              {runMutation.data.providers} مصدر · اكتُشف {runMutation.data.discovered} ·
              أُضيف {runMutation.data.inserted} · مكرر {runMutation.data.duplicates}
            </p>
          )}
          {runMutation.isError && (
            <p className="text-sm text-destructive">حصل خطأ أثناء التشغيل.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">أقفال نشطة</CardTitle>
        </CardHeader>
        <CardContent>
          {locksQuery.isPending ? (
            <Skeleton className="h-8 w-full" />
          ) : locksQuery.data && locksQuery.data.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {locksQuery.data.map((lock) => (
                <Badge key={lock.id} variant="secondary">
                  {lock.job_id}
                </Badge>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">مفيش أقفال نشطة دلوقتي.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">سجل التشغيل</CardTitle>
        </CardHeader>
        <CardContent>
          {historyQuery.isPending ? (
            <Skeleton className="h-24 w-full" />
          ) : historyQuery.data && historyQuery.data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>المصدر</TableHead>
                  <TableHead>الحالة</TableHead>
                  <TableHead>الوظائف الموجودة</TableHead>
                  <TableHead>البداية</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {historyQuery.data.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell>{entry.provider}</TableCell>
                    <TableCell>{entry.status}</TableCell>
                    <TableCell>{entry.jobs_found}</TableCell>
                    <TableCell>
                      {new Date(entry.started_at).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-muted-foreground">مفيش سجل تشغيل لسه.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">مهام فاشلة</CardTitle>
        </CardHeader>
        <CardContent>
          {failedJobsQuery.isPending ? (
            <Skeleton className="h-8 w-full" />
          ) : failedJobsQuery.data && failedJobsQuery.data.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>المصدر</TableHead>
                  <TableHead>الحالة</TableHead>
                  <TableHead>عدد المحاولات</TableHead>
                  <TableHead>آخر خطأ</TableHead>
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
            <p className="text-sm text-muted-foreground">مفيش مهام فاشلة.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
