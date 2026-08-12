"use client";

import { Rss } from "lucide-react";

import { DiscoveredJobsTable } from "@/components/discovered-jobs-table";
import { PageGlow } from "@/components/page-glow";
import { useTranslation } from "@/lib/i18n/language-context";

export default function JobsLinkedinPage() {
  const { t } = useTranslation();

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden">
      <PageGlow />
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <Rss className="size-6 text-emerald-400" />
        {t("discoveredJobs", "tabLinkedin")}
      </h1>

      <DiscoveredJobsTable
        source="linkedin_post"
        queryKeySuffix="linkedin"
        emptyMessage={t("linkedinPostsPage", "noResults")}
        reviewStatus="none"
        actions="review"
      />
    </div>
  );
}
