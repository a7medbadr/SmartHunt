"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { Search, XCircle } from "lucide-react";
import { useRef, useState } from "react";

import { listSchedulerHistory, searchProvider } from "@/lib/scheduler-api";
import { listProviders } from "@/lib/providers-api";
import { LastAutomatedScan } from "@/components/last-automated-scan";
import { PageGlow } from "@/components/page-glow";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTranslation } from "@/lib/i18n/language-context";
import { EstimatedProgressBar } from "@/components/ui/estimated-progress-bar";
import { useEstimatedProgress } from "@/hooks/use-estimated-progress";
import { getApiErrorMessage } from "@/lib/api-error";

// Every scheduler_history provider label backing the automated ("مواقع")
// job-sites discovery jobs — the 5 topic jobs (discover_linux etc, see
// scheduler/jobs.py's `f"scheduler:{topic}"` labels), their once-daily
// combined morning sweep, and Tanqeeb's own dedicated daily sweep.
// Mirrored here (not shared with the backend) the same way provider
// names are already duplicated across this codebase's frontend API layer.
const SITE_DISCOVERY_PROVIDERS = [
  "scheduler:linux",
  "scheduler:openshift",
  "scheduler:vmware",
  "scheduler:storage",
  "scheduler:devops",
  "scheduler:daily-morning-linux",
  "scheduler:daily-morning-openshift",
  "scheduler:daily-morning-vmware",
  "scheduler:daily-morning-storage",
  "scheduler:daily-morning-devops",
  "scheduler:tanqeeb-daily",
];

export default function JobSearchSitesPage() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  const [siteKeyword, setSiteKeyword] = useState("");
  const [siteName, setSiteName] = useState("");
  const [siteSearchError, setSiteSearchError] = useState<string | null>(null);
  const siteSearchControllerRef = useRef<AbortController | null>(null);

  const providersQuery = useQuery({
    queryKey: ["providers"],
    queryFn: listProviders,
  });
  const enabledProviders = providersQuery.data?.filter((p) => p.enabled) ?? [];

  const schedulerHistoryQuery = useQuery({
    queryKey: ["scheduler-history"],
    queryFn: listSchedulerHistory,
  });

  const siteSearchMutation = useMutation({
    mutationFn: () => {
      const controller = new AbortController();
      siteSearchControllerRef.current = controller;
      return searchProvider(siteName, siteKeyword, undefined, controller.signal);
    },
    onSettled: () => {
      siteSearchControllerRef.current = null;
    },
  });
  // 70s: real two-pass LinkedIn search (list page + each job's own detail
  // page) costs ~4.3s/job at this endpoint's limit=15, per CLAUDE.md notes.
  const siteSearchProgress = useEstimatedProgress(siteSearchMutation.isPending, 70000);

  function handleSiteSearch() {
    setSiteSearchError(null);
    if (!siteKeyword.trim() || !siteName) {
      setSiteSearchError(t("jobSearch", "keywordAndSiteRequired"));
      return;
    }
    siteSearchMutation.mutate(undefined, {
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ["search-jobs"] }),
    });
  }

  function cancelSiteSearch() {
    siteSearchControllerRef.current?.abort();
  }

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden">
      <PageGlow />
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <Search className="size-6 text-teal-400" />
        {t("discoveredJobs", "tabJobSites")}
      </h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("jobSearch", "searchJobSitesTitle")}</CardTitle>
          <p className="text-xs text-muted-foreground">{t("jobSearch", "searchJobSitesHint")}</p>
          <LastAutomatedScan
            history={schedulerHistoryQuery.data}
            providers={SITE_DISCOVERY_PROVIDERS}
            isPending={schedulerHistoryQuery.isPending}
          />
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex flex-wrap gap-2">
            <Input
              placeholder={t("jobSearch", "keywordPlaceholder")}
              value={siteKeyword}
              onChange={(e) => setSiteKeyword(e.target.value)}
              className="max-w-xs"
            />
            <Select value={siteName} onValueChange={(value) => setSiteName(value ?? "")}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder={t("jobSearch", "selectSitePlaceholder")} />
              </SelectTrigger>
              <SelectContent>
                {enabledProviders.map((p) => (
                  <SelectItem key={p.name} value={p.name} className="capitalize">
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button onClick={handleSiteSearch} disabled={siteSearchMutation.isPending}>
              {siteSearchMutation.isPending
                ? t("jobSearch", "searching")
                : t("jobSearch", "searchButton")}
            </Button>
            {siteSearchMutation.isPending && (
              <>
                <EstimatedProgressBar percent={siteSearchProgress} />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={cancelSiteSearch}
                  aria-label={t("jobSearch", "cancelScan")}
                >
                  <XCircle className="size-4" />
                </Button>
              </>
            )}
          </div>

          {siteSearchError && <p className="text-sm text-destructive">{siteSearchError}</p>}
          {siteSearchMutation.isError && !siteSearchError && (
            <p className="text-sm text-destructive">
              {axios.isCancel(siteSearchMutation.error)
                ? t("jobSearch", "scanCancelled")
                : (getApiErrorMessage(siteSearchMutation.error) ??
                  t("jobSearch", "genericSearchError"))}
            </p>
          )}
          {siteSearchMutation.data && (
            <p className="text-sm text-primary">
              {t("jobSearch", "foundJobsMessage")
                .replace("{found}", String(siteSearchMutation.data.found))
                .replace("{provider}", siteSearchMutation.data.provider)
                .replace("{inserted}", String(siteSearchMutation.data.inserted))
                .replace("{duplicates}", String(siteSearchMutation.data.duplicates))}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
