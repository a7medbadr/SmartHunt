"use client";

import { Search } from "lucide-react";

import { DiscoveredJobsTable } from "@/components/discovered-jobs-table";
import { PageGlow } from "@/components/page-glow";
import { useTranslation } from "@/lib/i18n/language-context";

const NON_JOB_SITE_SOURCES = "linkedin_post,whatsapp_message";

export default function JobSitesPage() {
  const { t } = useTranslation();

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden">
      <PageGlow />
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <Search className="size-6 text-emerald-400" />
        {t("discoveredJobs", "tabJobSites")}
      </h1>

      <DiscoveredJobsTable
        excludeSource={NON_JOB_SITE_SOURCES}
        showSource
        queryKeySuffix="sites"
        emptyMessage={t("jobsPage", "noResults")}
        reviewStatus="none"
        actions="review"
      />
    </div>
  );
}
