"use client";

import { Ban } from "lucide-react";

import { DiscoveredJobsTable } from "@/components/discovered-jobs-table";
import { PageGlow } from "@/components/page-glow";
import { useTranslation } from "@/lib/i18n/language-context";

export default function NotSuitableJobsPage() {
  const { t } = useTranslation();

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden">
      <PageGlow />
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <Ban className="size-6 text-rose-400" />
        {t("pageTitles", "notSuitableJobs")}
      </h1>

      <DiscoveredJobsTable
        showSource
        queryKeySuffix="not-suitable"
        emptyMessage={t("discoveredJobs", "notSuitableEmpty")}
        reviewStatus="not_suitable"
        actions="delete"
      />
    </div>
  );
}
