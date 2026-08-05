"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, ArrowUpDown, BookmarkPlus, Search, Star } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { addFavorite, listFavorites, removeFavorite, searchJobs } from "@/lib/jobs-api";
import { listProviders } from "@/lib/providers-api";
import { createSavedSearch } from "@/lib/saved-searches-api";
import { searchProvider } from "@/lib/scheduler-api";
import { PageGlow } from "@/components/page-glow";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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

const ALL_SITES_VALUE = "__all__";

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("ar-SA", { day: "numeric", month: "short", year: "numeric" });
}

function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("ar-SA", {
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
}

function SortableHeader({ field, label, activeField, activeOrder, onToggle }: SortableHeaderProps) {
  const isActive = activeField === field;
  const Icon = isActive ? (activeOrder === "asc" ? ArrowUp : ArrowDown) : ArrowUpDown;
  return (
    <TableHead>
      <button
        type="button"
        onClick={() => onToggle(field)}
        className={cn(
          "flex items-center gap-1 hover:text-foreground",
          isActive && "font-medium text-foreground",
        )}
      >
        {label}
        <Icon className={cn("size-3.5", !isActive && "text-muted-foreground/50")} />
      </button>
    </TableHead>
  );
}

export default function JobsPage() {
  return (
    <Suspense fallback={<Skeleton className="h-40 w-full" />}>
      <JobsPageContent />
    </Suspense>
  );
}

function JobsPageContent() {
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const [keyword, setKeyword] = useState(searchParams.get("keyword") ?? "");
  const [location, setLocation] = useState(searchParams.get("location") ?? "");
  const [site, setSite] = useState(ALL_SITES_VALUE);
  const [appliedFilters, setAppliedFilters] = useState({
    keyword: searchParams.get("keyword") ?? "",
    location: searchParams.get("location") ?? "",
    source: undefined as string | undefined,
  });
  // Default: newest discovered first, so anything freshly found shows up
  // at the top without the user having to do anything — clicking any
  // column header re-sorts by it, clicking the same one again flips
  // asc/desc. "source" sorts alphabetically by site name for free (the
  // backend's sort_jobs() does a plain string comparison on whatever
  // field is named).
  const [sortField, setSortField] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [siteSearchError, setSiteSearchError] = useState<string | null>(null);

  function toggleSort(field: string) {
    if (sortField === field) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  }

  const providersQuery = useQuery({
    queryKey: ["providers"],
    queryFn: listProviders,
  });
  const enabledProviders = providersQuery.data?.filter((p) => p.enabled) ?? [];

  const saveSearchMutation = useMutation({
    mutationFn: createSavedSearch,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["saved-searches"] }),
  });

  // "اختار الموقع" isn't just a filter on our own DB — choosing a specific
  // site must actually go search that site live (real navigation, not
  // our local jobs table), per explicit request. Triggering this before
  // the search-jobs query below means the freshly-inserted results are
  // already there by the time we filter by source=<site>.
  const siteSearchMutation = useMutation({
    mutationFn: ({ provider, keyword, location }: { provider: string; keyword: string; location: string }) =>
      searchProvider(provider, keyword, location || undefined),
  });

  const { data, isPending, isError } = useQuery({
    queryKey: ["search-jobs", appliedFilters, sortField, sortOrder],
    queryFn: () =>
      searchJobs({
        keyword: appliedFilters.keyword || undefined,
        location: appliedFilters.location || undefined,
        source: appliedFilters.source,
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

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setSiteSearchError(null);

    if (site !== ALL_SITES_VALUE) {
      if (!keyword.trim()) {
        setSiteSearchError("محتاج كلمة مفتاحية علشان يبحث بيها في الموقع.");
        return;
      }
      try {
        await siteSearchMutation.mutateAsync({ provider: site, keyword, location });
      } catch {
        setSiteSearchError("حصل خطأ أثناء البحث في الموقع، جرب تاني.");
        return;
      }
    }

    setAppliedFilters({
      keyword,
      location,
      source: site !== ALL_SITES_VALUE ? site : undefined,
    });
  }

  const { t } = useTranslation();

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden">
      <PageGlow />
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <Search className="size-6 text-emerald-400" />
        {t("pageTitles", "jobs")}
      </h1>

      <form onSubmit={handleSearch} className="flex flex-wrap items-center gap-2">
        <Input
          placeholder="كلمة مفتاحية (المسمى الوظيفي، الوصف...)"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="max-w-xs"
        />
        <Input
          placeholder="الموقع"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          className="max-w-xs"
        />
        <Select value={site} onValueChange={(value) => setSite(value ?? ALL_SITES_VALUE)}>
          <SelectTrigger className="w-44">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_SITES_VALUE}>كل المواقع (بحث محلي)</SelectItem>
            {enabledProviders.map((p) => (
              <SelectItem key={p.name} value={p.name} className="capitalize">
                {p.name} (بحث مباشر)
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button type="submit" disabled={siteSearchMutation.isPending}>
          {siteSearchMutation.isPending ? "جاري البحث في الموقع..." : "بحث"}
        </Button>
        {(appliedFilters.keyword || appliedFilters.location) && (
          <Button
            type="button"
            variant="outline"
            className="gap-1.5"
            disabled={saveSearchMutation.isPending}
            onClick={() =>
              saveSearchMutation.mutate({
                name: appliedFilters.keyword || appliedFilters.location,
                keyword: appliedFilters.keyword || undefined,
                location: appliedFilters.location || undefined,
              })
            }
          >
            <BookmarkPlus className="size-4" />
            {saveSearchMutation.isPending ? "جاري الحفظ..." : "احفظ البحث ده"}
          </Button>
        )}
      </form>

      {site !== ALL_SITES_VALUE && (
        <p className="text-xs text-muted-foreground">
          اختيارك موقع معيّن معناه إن دوسة &quot;بحث&quot; هتروح تدور فعلاً في
          {" "}{site} نفسه (مش بس في الوظائف المحفوظة عندنا) وتحفظ اللي تلاقيه.
        </p>
      )}
      {siteSearchError && (
        <p className="text-sm text-destructive">{siteSearchError}</p>
      )}
      {siteSearchMutation.data && (
        <p className="text-sm text-primary">
          لقينا {siteSearchMutation.data.found} وظيفة في {siteSearchMutation.data.provider}،
          {" "}أضفنا {siteSearchMutation.data.inserted} جديدة (
          {siteSearchMutation.data.duplicates} كانت موجودة قبل كده).
        </p>
      )}

      {isError && (
        <p className="text-sm text-destructive">مقدرناش نجيب الوظائف، جرب تاني.</p>
      )}

      {isPending ? (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : data && data.jobs.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead />
              <SortableHeader
                field="title"
                label="المسمى الوظيفي"
                activeField={sortField}
                activeOrder={sortOrder}
                onToggle={toggleSort}
              />
              <SortableHeader
                field="company"
                label="الشركة"
                activeField={sortField}
                activeOrder={sortOrder}
                onToggle={toggleSort}
              />
              <SortableHeader
                field="location"
                label="مكان الوظيفة"
                activeField={sortField}
                activeOrder={sortOrder}
                onToggle={toggleSort}
              />
              <SortableHeader
                field="source"
                label="المصدر"
                activeField={sortField}
                activeOrder={sortOrder}
                onToggle={toggleSort}
              />
              <SortableHeader
                field="score"
                label="التوافق"
                activeField={sortField}
                activeOrder={sortOrder}
                onToggle={toggleSort}
              />
              <SortableHeader
                field="posted_at"
                label="تاريخ نشر الوظيفة"
                activeField={sortField}
                activeOrder={sortOrder}
                onToggle={toggleSort}
              />
              <SortableHeader
                field="created_at"
                label="تاريخ الاكتشاف"
                activeField={sortField}
                activeOrder={sortOrder}
                onToggle={toggleSort}
              />
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.jobs.map((job) => (
              <TableRow key={job.id}>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="size-8"
                    disabled={toggleFavoriteMutation.isPending}
                    onClick={() => toggleFavoriteMutation.mutate(job.id)}
                    aria-label="أضف للمفضلة"
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
                <TableCell>
                  <div className="flex flex-wrap items-center gap-2">
                    <Link href={`/jobs/${job.id}`} className="font-medium underline">
                      {job.title}
                    </Link>
                    {job.no_sponsorship_signal && (
                      <Badge variant="destructive" className="text-xs">
                        بدون رعاية تأشيرة
                      </Badge>
                    )}
                    {job.post_url && (
                      <Badge variant="outline" className="text-xs text-sky-400">
                        بوست
                      </Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell>{job.company}</TableCell>
                <TableCell>{job.location ?? "—"}</TableCell>
                <TableCell>{job.source ?? "—"}</TableCell>
                <TableCell>
                  {job.score != null ? (
                    <Badge variant={job.score >= 50 ? "default" : "secondary"}>
                      {job.score}%
                    </Badge>
                  ) : (
                    "—"
                  )}
                </TableCell>
                <TableCell className="whitespace-nowrap text-sm text-muted-foreground">
                  {/* Not every provider/job exposes a real posting date
                      (e.g. jobs discovered before the LinkedIn selector
                      fix on 2026-08-04) — fall back to the discovery
                      date rather than showing a blank "—", per explicit
                      request. */}
                  {formatDate(job.posted_at ?? job.created_at)}
                </TableCell>
                <TableCell className="whitespace-nowrap text-sm text-muted-foreground">
                  {formatDateTime(job.created_at)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <p className="text-sm text-muted-foreground">
          مفيش نتايج مطابقة للبحث ده. جرب كلمة مفتاحية تانية، أو استنى دورة
          الاكتشاف التلقائي الجاية من صفحة الجدولة.
        </p>
      )}
    </div>
  );
}
