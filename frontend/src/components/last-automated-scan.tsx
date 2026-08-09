"use client";

import type { SchedulerHistoryEntry } from "@/lib/scheduler-api";
import { useTranslation } from "@/lib/i18n/language-context";

export interface LastAutomatedScanProps {
  history: SchedulerHistoryEntry[] | undefined;
  providers: string[];
  isPending?: boolean;
  className?: string;
}

// Small "when did the scheduled job for this block last actually run"
// line — added 2026-08-09 per explicit request to make every job-search
// scan block show this the same way the LinkedIn accounts/hashtags rows
// already show their own per-item last_checked_at. Takes the most recent
// scheduler_history row across `providers` (a block can be backed by more
// than one scheduled job, e.g. hourly + daily variants of the same scan)
// rather than a single provider string.
export function LastAutomatedScan({
  history,
  providers,
  isPending = false,
  className,
}: LastAutomatedScanProps) {
  const { t, locale } = useTranslation();
  const dateLocale = locale === "ar" ? "ar-SA" : "en-US";

  if (isPending) return null;

  const latest = (history ?? [])
    .filter((entry) => providers.includes(entry.provider))
    .reduce<SchedulerHistoryEntry | null>((acc, entry) => {
      if (!acc || new Date(entry.started_at) > new Date(acc.started_at)) return entry;
      return acc;
    }, null);

  return (
    <p className={className ?? "text-xs text-muted-foreground"}>
      {latest
        ? t("jobSearch", "lastAutomatedScanLabel").replace(
            "{date}",
            new Date(latest.started_at).toLocaleString(dateLocale),
          )
        : t("jobSearch", "noAutomatedScanYet")}
    </p>
  );
}
