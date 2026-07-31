"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getAIHealth,
  getHealthDetails,
  getSystemVersion,
  listProviderHealth,
} from "@/lib/system-api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

function StatusBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <Badge className={cn(ok ? "bg-green-600" : "bg-destructive", "text-white")}>
      {label}
    </Badge>
  );
}

export default function SystemHealthPage() {
  const detailsQuery = useQuery({
    queryKey: ["health-details"],
    queryFn: getHealthDetails,
    refetchInterval: 15000,
  });
  const versionQuery = useQuery({
    queryKey: ["system-version"],
    queryFn: getSystemVersion,
  });
  const aiHealthQuery = useQuery({
    queryKey: ["ai-health"],
    queryFn: getAIHealth,
  });
  const providersQuery = useQuery({
    queryKey: ["providers-health"],
    queryFn: listProviderHealth,
  });

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <h1 className="text-2xl font-semibold">حالة النظام</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">الحالة العامة</CardTitle>
        </CardHeader>
        <CardContent>
          {detailsQuery.isPending ? (
            <Skeleton className="h-10 w-full" />
          ) : detailsQuery.data ? (
            <div className="flex flex-wrap gap-3">
              <StatusBadge
                ok={detailsQuery.data.status === "ok"}
                label={`الحالة العامة: ${detailsQuery.data.status}`}
              />
              <StatusBadge
                ok={detailsQuery.data.database === "up"}
                label={`قاعدة البيانات: ${detailsQuery.data.database}`}
              />
              <StatusBadge
                ok={detailsQuery.data.scheduler === "up"}
                label={`الجدولة: ${detailsQuery.data.scheduler}`}
              />
              <Badge variant="secondary">
                Playwright: {detailsQuery.data.playwright}
              </Badge>
            </div>
          ) : (
            <p className="text-sm text-destructive">مقدرناش نتصل بالسيرفر.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">إصدار النظام</CardTitle>
        </CardHeader>
        <CardContent>
          {versionQuery.isPending ? (
            <Skeleton className="h-10 w-full" />
          ) : versionQuery.data ? (
            <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
              <dt className="text-muted-foreground">التطبيق</dt>
              <dd>{versionQuery.data.application}</dd>
              <dt className="text-muted-foreground">الإصدار</dt>
              <dd>{versionQuery.data.version}</dd>
              <dt className="text-muted-foreground">البيئة</dt>
              <dd>{versionQuery.data.environment}</dd>
              <dt className="text-muted-foreground">Python</dt>
              <dd>{versionQuery.data.python}</dd>
            </dl>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">مزودات الذكاء الاصطناعي</CardTitle>
        </CardHeader>
        <CardContent>
          {aiHealthQuery.isPending ? (
            <Skeleton className="h-10 w-full" />
          ) : (
            <div className="flex flex-wrap gap-2">
              {aiHealthQuery.data?.providers.map((p) => (
                <StatusBadge key={p.provider} ok={p.available} label={p.provider} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">حالة مواقع التوظيف</CardTitle>
        </CardHeader>
        <CardContent>
          {providersQuery.isPending ? (
            <Skeleton className="h-10 w-full" />
          ) : providersQuery.data && providersQuery.data.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {providersQuery.data.map((p) => (
                <StatusBadge
                  key={p.id}
                  ok={p.status === "up" || p.status === "healthy"}
                  label={`${p.provider}: ${p.status}`}
                />
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              لسه مفيش بيانات حالة مسجلة لمواقع التوظيف.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
