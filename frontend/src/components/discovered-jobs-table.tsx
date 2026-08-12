"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, ArrowUpDown, Ban, CheckCircle2, Star, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import {
  addFavorite,
  deleteJob,
  listFavorites,
  removeFavorite,
  searchJobs,
  updateJobReviewStatus,
  type ReviewStatus,
} from "@/lib/jobs-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
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
import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n/language-context";

function formatDate(iso: string | null | undefined, locale: string): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(locale, { day: "numeric", month: "short", year: "numeric" });
}

function formatDateTime(iso: string | null | undefined, locale: string): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(locale, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

interface SortableHeaderProps {
  field: string;
  label: string;
  activeField: string;
  activeOrder: "asc" | "desc";
  onToggle: (field: string) => void;
  className?: string;
}

function SortableHeader({
  field,
  label,
  activeField,
  activeOrder,
  onToggle,
  className,
}: SortableHeaderProps) {
  const isActive = activeField === field;
  const Icon = isActive ? (activeOrder === "asc" ? ArrowUp : ArrowDown) : ArrowUpDown;
  return (
    <TableHead className={className}>
      <button
        type="button"
        onClick={() => onToggle(field)}
        className={cn(
          "flex w-full min-w-0 items-center justify-center gap-1 hover:text-foreground",
          isActive && "font-medium text-foreground",
        )}
      >
        <span className="min-w-0 truncate">{label}</span>
        <Icon className={cn("size-3.5 shrink-0", !isActive && "text-muted-foreground/50")} />
      </button>
    </TableHead>
  );
}

// The job-sites tab and the Not Suitable Jobs page both mix jobs from
// several different sources (job boards, LinkedIn posts, WhatsApp
// messages), so they're the ones that pass showSource — the single-source
// tabs (LinkedIn posts, WhatsApp) don't need it.
const SOURCE_LABELS: Record<string, string> = {
  linkedin: "LinkedIn",
  linkedin_post: "LinkedIn Post",
  whatsapp_message: "WhatsApp",
  tanqeeb: "Tanqeeb",
  workable: "Workable",
  sabbar: "Sabbar",
  baaeed: "Baaeed",
  drjobs: "DrJobs",
  indeed: "Indeed",
  bayt: "Bayt",
  gulftalent: "GulfTalent",
  wuzzuf: "Wuzzuf",
  naukrigulf: "NaukriGulf",
  monstergulf: "MonsterGulf",
  wzayef: "Wzayef",
  forasnagulf: "ForasnaGulf",
};

function sourceLabel(source: string | null | undefined): string {
  if (!source) return "—";
  return SOURCE_LABELS[source] ?? source;
}

export interface DiscoveredJobsTableProps {
  // Exact-match source filter (e.g. "linkedin_post") — omit for the job
  // sites tab, which uses excludeSource instead to show every real
  // job-site source at once.
  source?: string;
  // Comma-separated source(s) to exclude — the job sites tab excludes
  // linkedin_post and whatsapp_message, which each have their own tab.
  excludeSource?: string;
  // Shows which job board each job came from — only the job-sites tab
  // (which mixes multiple real providers) needs this; the other tabs are
  // each already a single source.
  showSource?: boolean;
  // Unique per tab, used in the react-query cache key so the 3 tabs
  // don't share/clobber each other's cached results.
  queryKeySuffix: string;
  emptyMessage: string;
  // Which review-status bucket this table shows. Fixed per page (not a
  // user-facing filter anymore) — marking a job "applied" or "not
  // suitable" now moves it out of the discovered-jobs view entirely (see
  // the mutations below), so a single table only ever needs to render
  // one bucket: "none" for the still-pending discovered-jobs pages, or a
  // specific ReviewStatus for a single-status page like Not Suitable Jobs.
  reviewStatus: "none" | ReviewStatus;
  // "review" shows the mark-applied / mark-not-suitable icons (the
  // discovered-jobs pages); "delete" shows a permanent-delete icon
  // instead (the Not Suitable Jobs page — the only place a job can be
  // removed for good, since discovered jobs should only ever be
  // triaged away via the review actions, not deleted directly).
  actions: "review" | "delete";
}

export function DiscoveredJobsTable({
  source,
  excludeSource,
  showSource = false,
  queryKeySuffix,
  emptyMessage,
  reviewStatus,
  actions,
}: DiscoveredJobsTableProps) {
  const queryClient = useQueryClient();
  const { t, locale } = useTranslation();
  const dateLocale = locale === "ar" ? "ar-SA" : "en-US";

  const [keyword, setKeyword] = useState("");
  const [location, setLocation] = useState("");
  const [appliedFilters, setAppliedFilters] = useState({ keyword: "", location: "" });
  const [sortField, setSortField] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [deleteJobId, setDeleteJobId] = useState<number | null>(null);

  function toggleSort(field: string) {
    if (sortField === field) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setAppliedFilters({ keyword, location });
  }

  const { data, isPending, isError } = useQuery({
    queryKey: ["search-jobs", queryKeySuffix, appliedFilters, sortField, sortOrder, reviewStatus],
    queryFn: () =>
      searchJobs({
        keyword: appliedFilters.keyword || undefined,
        location: appliedFilters.location || undefined,
        source,
        excludeSource,
        reviewStatus,
        sort: sortField,
        order: sortOrder,
        limit: 50,
      }),
  });

  const favoritesQuery = useQuery({
    queryKey: ["favorites"],
    queryFn: listFavorites,
  });
  const favoriteJobIds = new Set(favoritesQuery.data?.map((f) => f.job_id));

  const toggleFavoriteMutation = useMutation({
    mutationFn: async (jobId: number) => {
      if (favoriteJobIds.has(jobId)) {
        await removeFavorite(jobId);
      } else {
        await addFavorite(jobId);
      }
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["favorites"] }),
  });

  function invalidateJobLists() {
    queryClient.invalidateQueries({ queryKey: ["search-jobs"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard-statistics"] });
  }

  const reviewStatusMutation = useMutation({
    mutationFn: ({ jobId, reviewStatus }: { jobId: number; reviewStatus: ReviewStatus | null }) =>
      updateJobReviewStatus(jobId, reviewStatus),
    onSuccess: () => {
      invalidateJobLists();
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });

  function toggleReviewStatus(jobId: number, current: ReviewStatus | null | undefined, target: ReviewStatus) {
    reviewStatusMutation.mutate({ jobId, reviewStatus: current === target ? null : target });
  }

  const deleteJobMutation = useMutation({
    mutationFn: deleteJob,
    onSuccess: () => {
      invalidateJobLists();
      setDeleteJobId(null);
    },
  });

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={handleSearch} className="flex flex-wrap items-center gap-2">
        <Input
          placeholder={t("jobsPage", "keywordPlaceholder")}
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="max-w-xs"
        />
        <Input
          placeholder={t("jobsPage", "locationPlaceholder")}
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          className="max-w-xs"
        />
        <Button type="submit">{t("jobsPage", "searchButton")}</Button>
      </form>

      {isError && <p className="text-sm text-destructive">{t("jobsPage", "loadError")}</p>}

      {isPending ? (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : data && data.jobs.length > 0 ? (
        <Table className="table-fixed text-xs">
          <TableHeader>
            <TableRow>
              <TableHead className="w-9 px-1" />
              <SortableHeader
                field="title"
                label={t("jobsPage", "colJobTitle")}
                activeField={sortField}
                activeOrder={sortOrder}
                onToggle={toggleSort}
                className="w-[26%]"
              />
              <SortableHeader
                field="company"
                label={t("jobsPage", "colCompany")}
                activeField={sortField}
                activeOrder={sortOrder}
                onToggle={toggleSort}
                className={showSource ? "w-[11%]" : "w-[13%]"}
              />
              <SortableHeader
                field="location"
                label={t("jobsPage", "colLocation")}
                activeField={sortField}
                activeOrder={sortOrder}
                onToggle={toggleSort}
                className={showSource ? "w-[9%]" : "w-[11%]"}
              />
              {showSource && (
                <TableHead className="w-[8%] px-1 text-center">
                  {t("jobsPage", "colSource")}
                </TableHead>
              )}
              <SortableHeader
                field="score"
                label={t("jobsPage", "colScore")}
                activeField={sortField}
                activeOrder={sortOrder}
                onToggle={toggleSort}
                className="w-[7%] px-1"
              />
              <TableHead className={cn("px-1 text-center", showSource ? "w-[9%]" : "w-[10%]")}>
                {t("discoveredJobs", "colStatus")}
              </TableHead>
              <SortableHeader
                field="posted_at"
                label={t("jobsPage", "colPostedDate")}
                activeField={sortField}
                activeOrder={sortOrder}
                onToggle={toggleSort}
                className={cn("px-1", showSource ? "w-[8%]" : "w-[9%]")}
              />
              <SortableHeader
                field="created_at"
                label={t("jobsPage", "colDiscoveredDate")}
                activeField={sortField}
                activeOrder={sortOrder}
                onToggle={toggleSort}
                className={cn("px-1", showSource ? "w-[8%]" : "w-[9%]")}
              />
              <TableHead className={cn("px-1 text-center", showSource ? "w-[14%]" : "w-[15%]")}>
                {t("discoveredJobs", "colActions")}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.jobs.map((job) => (
              <TableRow key={job.id}>
                <TableCell className="px-1 text-center">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="size-7"
                    disabled={toggleFavoriteMutation.isPending}
                    onClick={() => toggleFavoriteMutation.mutate(job.id)}
                    aria-label={t("jobsPage", "addToFavorites")}
                  >
                    <Star
                      className={cn(
                        "size-4",
                        favoriteJobIds.has(job.id)
                          ? "fill-rose-400 text-rose-400"
                          : "text-muted-foreground",
                      )}
                    />
                  </Button>
                </TableCell>
                <TableCell className="whitespace-normal">
                  <div className="flex min-w-0 items-center justify-center gap-2">
                    <Link
                      href={`/jobs/${job.id}`}
                      title={job.title}
                      className="min-w-0 flex-1 truncate text-center font-medium underline"
                    >
                      {job.title}
                    </Link>
                    {job.no_sponsorship_signal && (
                      <Badge variant="destructive" className="shrink-0 text-xs">
                        {t("jobsPage", "noSponsorship")}
                      </Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell className="whitespace-normal text-center">
                  <span className="block truncate" title={job.company}>
                    {job.company}
                  </span>
                </TableCell>
                <TableCell className="whitespace-normal text-center">
                  <span className="block truncate" title={job.location ?? undefined}>
                    {job.location ?? "—"}
                  </span>
                </TableCell>
                {showSource && (
                  <TableCell className="px-1 text-center">
                    <Badge variant="outline" className="max-w-full truncate text-xs">
                      {sourceLabel(job.source)}
                    </Badge>
                  </TableCell>
                )}
                <TableCell className="px-1 text-center">
                  {job.score != null ? (
                    <Badge variant={job.score >= 50 ? "default" : "secondary"}>
                      {job.score}%
                    </Badge>
                  ) : (
                    "—"
                  )}
                </TableCell>
                <TableCell className="px-1 text-center">
                  {job.review_status === "applied" ? (
                    <Badge className="max-w-full truncate bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/15">
                      {t("discoveredJobs", "statusApplied")}
                    </Badge>
                  ) : job.review_status === "not_suitable" ? (
                    <Badge variant="secondary" className="max-w-full truncate text-muted-foreground">
                      {t("discoveredJobs", "statusNotSuitable")}
                    </Badge>
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </TableCell>
                <TableCell className="px-1 text-center text-muted-foreground">
                  <span className="block truncate">
                    {formatDate(job.posted_at ?? job.created_at, dateLocale)}
                  </span>
                </TableCell>
                <TableCell className="px-1 text-center text-muted-foreground">
                  <span className="block truncate">
                    {formatDateTime(job.created_at, dateLocale)}
                  </span>
                </TableCell>
                <TableCell className="px-1">
                  <div className="flex items-center justify-center gap-0.5">
                    {actions === "review" ? (
                      <>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-7"
                          disabled={reviewStatusMutation.isPending}
                          onClick={() => toggleReviewStatus(job.id, job.review_status, "applied")}
                          aria-label={t("discoveredJobs", "markApplied")}
                          title={t("discoveredJobs", "markApplied")}
                        >
                          <CheckCircle2 className="size-4 text-emerald-400" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-7"
                          disabled={reviewStatusMutation.isPending}
                          onClick={() =>
                            toggleReviewStatus(job.id, job.review_status, "not_suitable")
                          }
                          aria-label={t("discoveredJobs", "markNotSuitable")}
                          title={t("discoveredJobs", "markNotSuitable")}
                        >
                          <Ban className="size-4 text-yellow-400" />
                        </Button>
                      </>
                    ) : (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="size-7"
                        onClick={() => setDeleteJobId(job.id)}
                        aria-label={t("discoveredJobs", "deleteJob")}
                        title={t("discoveredJobs", "deleteJob")}
                      >
                        <Trash2 className="size-4 text-destructive/70 hover:text-destructive" />
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <p className="text-sm text-muted-foreground">{emptyMessage}</p>
      )}

      <ConfirmDialog
        open={deleteJobId !== null}
        onOpenChange={(open) => !open && setDeleteJobId(null)}
        isPending={deleteJobMutation.isPending}
        onConfirm={() => {
          if (deleteJobId !== null) deleteJobMutation.mutate(deleteJobId);
        }}
      />
    </div>
  );
}
