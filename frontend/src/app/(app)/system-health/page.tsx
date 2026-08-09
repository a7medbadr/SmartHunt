"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity as ActivityIcon } from "lucide-react";

import {
  getAIHealth,
  getHealthDetails,
  getSystemVersion,
  listProviderHealth,
} from "@/lib/system-api";
import { PageGlow } from "@/components/page-glow";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslation } from "@/lib/i18n/language-context";
import { cn } from "@/lib/utils";

function StatusBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <Badge className={cn(ok ? "bg-green-600" : "bg-destructive", "text-white")}>
      {label}
    </Badge>
  );
}

export default function SystemHealthPage() {
  const { t } = useTranslation();
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
    <div className="relative flex max-w-3xl flex-col gap-6 overflow-hidden">
      <PageGlow />
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <ActivityIcon className="size-6 text-red-400" />
        {t("pageTitles", "systemHealth")}
      </h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("systemHealth", "overallStatus")}</CardTitle>
        </CardHeader>
        <CardContent>
          {detailsQuery.isPending ? (
            <Skeleton className="h-10 w-full" />
          ) : detailsQuery.data ? (
            <div className="flex flex-wrap gap-3">
              <StatusBadge
                ok={detailsQuery.data.status === "ok"}
                label={`${t("systemHealth", "overallStatusLabel")}: ${detailsQuery.data.status}`}
              />
              <StatusBadge
                ok={detailsQuery.data.database === "up"}
                label={`${t("systemHealth", "database")}: ${detailsQuery.data.database}`}
              />
              <StatusBadge
                ok={detailsQuery.data.scheduler === "up"}
                label={`${t("systemHealth", "scheduler")}: ${detailsQuery.data.scheduler}`}
              />
              <Badge variant="secondary">
                Playwright: {detailsQuery.data.playwright}
              </Badge>
            </div>
          ) : (
            <p className="text-sm text-destructive">{t("systemHealth", "connectionError")}</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("systemHealth", "systemVersion")}</CardTitle>
        </CardHeader>
        <CardContent>
          {versionQuery.isPending ? (
            <Skeleton className="h-10 w-full" />
          ) : versionQuery.data ? (
            <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
              <dt className="text-muted-foreground">{t("systemHealth", "application")}</dt>
              <dd>{versionQuery.data.application}</dd>
              <dt className="text-muted-foreground">{t("systemHealth", "version")}</dt>
              <dd>{versionQuery.data.version}</dd>
              <dt className="text-muted-foreground">{t("systemHealth", "environment")}</dt>
              <dd>{versionQuery.data.environment}</dd>
              <dt className="text-muted-foreground">Python</dt>
              <dd>{versionQuery.data.python}</dd>
            </dl>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("systemHealth", "aiProviders")}</CardTitle>
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
          <CardTitle className="text-base">{t("systemHealth", "providersStatus")}</CardTitle>
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
              {t("systemHealth", "noProviderStatus")}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
