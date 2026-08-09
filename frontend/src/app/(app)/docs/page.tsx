"use client";

import {
  BookOpen,
  CalendarClock,
  CircleHelp,
  Search,
  SearchCheck,
} from "lucide-react";
import { PageGlow } from "@/components/page-glow";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTranslation } from "@/lib/i18n/language-context";

export default function DocsPage() {
  const { t } = useTranslation();

  const SECTIONS = [
    { id: "overview", label: t("docs", "overviewTitle") },
    { id: "discovery", label: t("docs", "discoveryTitle") },
    { id: "scoring", label: t("docs", "scoringTitle") },
    { id: "resume", label: t("docs", "resumeTitle") },
    { id: "apply", label: t("docs", "applyTitle") },
    { id: "notifications", label: t("docs", "notificationsTitle") },
    { id: "faq", label: t("docs", "faqTitle") },
  ];

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden lg:flex-row lg:items-start">
      <PageGlow />
      <h1 className="sr-only">{t("pageTitles", "docs")}</h1>

      <nav className="top-6 flex shrink-0 flex-col gap-1 lg:sticky lg:w-48">
        <p className="mb-1 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
          <BookOpen className="size-4" />
          {t("pageTitles", "docs")}
        </p>
        {SECTIONS.map((s) => (
          <a
            key={s.id}
            href={`#${s.id}`}
            className="rounded-md px-2 py-1.5 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            {s.label}
          </a>
        ))}
      </nav>

      <div className="flex max-w-3xl flex-1 flex-col gap-8">
        <section id="overview" className="flex flex-col gap-3 scroll-mt-6">
          <h2 className="text-xl font-semibold">{t("docs", "overviewTitle")}</h2>
          <p className="text-sm leading-7 text-muted-foreground">
            {t("docs", "overviewBody")}
          </p>
        </section>

        <section id="discovery" className="flex flex-col gap-4 scroll-mt-6">
          <h2 className="text-xl font-semibold">{t("docs", "discoveryTitle")}</h2>
          <p className="text-sm leading-7 text-muted-foreground">
            {t("docs", "discoveryIntro")}
          </p>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <CalendarClock className="size-4 text-teal-400" />
                {t("docs", "discoveryScheduledTitle")}
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm leading-7 text-muted-foreground">
              {t("docs", "discoveryScheduledBody")}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Search className="size-4 text-emerald-400" />
                {t("docs", "discoveryDirectTitle")}
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm leading-7 text-muted-foreground">
              {t("docs", "discoveryDirectBody")}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <SearchCheck className="size-4 text-sky-400" />
                {t("docs", "discoveryLinkedinTitle")}
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm leading-7 text-muted-foreground">
              {t("docs", "discoveryLinkedinBody")}
            </CardContent>
          </Card>

          <p className="text-sm leading-7 text-muted-foreground">
            {t("docs", "discoverySavedSearchBody")}
          </p>
        </section>

        <section id="scoring" className="flex flex-col gap-3 scroll-mt-6">
          <h2 className="text-xl font-semibold">{t("docs", "scoringTitle")}</h2>
          <p className="text-sm leading-7 text-muted-foreground">
            {t("docs", "scoringBody")}
          </p>
        </section>

        <section id="resume" className="flex flex-col gap-3 scroll-mt-6">
          <h2 className="text-xl font-semibold">{t("docs", "resumeTitle")}</h2>
          <p className="text-sm leading-7 text-muted-foreground">
            {t("docs", "resumeBody")}
          </p>
        </section>

        <section id="apply" className="flex flex-col gap-3 scroll-mt-6">
          <h2 className="text-xl font-semibold">{t("docs", "applyTitle")}</h2>
          <p className="text-sm leading-7 text-muted-foreground">
            {t("docs", "applyBody")}
          </p>
        </section>

        <section id="notifications" className="flex flex-col gap-3 scroll-mt-6">
          <h2 className="text-xl font-semibold">{t("docs", "notificationsTitle")}</h2>
          <p className="text-sm leading-7 text-muted-foreground">
            {t("docs", "notificationsBody")}
          </p>
        </section>

        <section id="faq" className="flex flex-col gap-3 pb-8 scroll-mt-6">
          <h2 className="flex items-center gap-2 text-xl font-semibold">
            <CircleHelp className="size-5 text-slate-400" />
            {t("docs", "faqTitle")}
          </h2>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">{t("docs", "faq1Q")}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              {t("docs", "faq1A")}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">{t("docs", "faq2Q")}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              {t("docs", "faq2A")}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">{t("docs", "faq3Q")}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              {t("docs", "faq3A")}
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
