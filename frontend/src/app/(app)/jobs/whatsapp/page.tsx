"use client";

import { MessageCircle } from "lucide-react";

import { DiscoveredJobsTable } from "@/components/discovered-jobs-table";
import { PageGlow } from "@/components/page-glow";
import { useTranslation } from "@/lib/i18n/language-context";

export default function JobsWhatsappPage() {
  const { t } = useTranslation();

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden">
      <PageGlow />
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <MessageCircle className="size-6 text-emerald-400" />
        {t("discoveredJobs", "tabWhatsapp")}
      </h1>

      <DiscoveredJobsTable
        source="whatsapp_message"
        queryKeySuffix="whatsapp"
        emptyMessage={t("whatsappJobsPage", "noResults")}
      />
    </div>
  );
}
