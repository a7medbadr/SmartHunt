"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookmarkPlus, Search, Sparkles } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { searchJobs } from "@/lib/jobs-api";
import { createSavedSearch } from "@/lib/saved-searches-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  const [appliedFilters, setAppliedFilters] = useState({
    keyword: searchParams.get("keyword") ?? "",
    location: searchParams.get("location") ?? "",
  });
  const [sortByMatch, setSortByMatch] = useState(false);

  const saveSearchMutation = useMutation({
    mutationFn: createSavedSearch,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["saved-searches"] }),
  });

  const { data, isPending, isError } = useQuery({
    queryKey: ["search-jobs", appliedFilters, sortByMatch],
    queryFn: () =>
      searchJobs({
        keyword: appliedFilters.keyword || undefined,
        location: appliedFilters.location || undefined,
        sort: sortByMatch ? "score" : undefined,
        order: sortByMatch ? "desc" : undefined,
        limit: 50,
      }),
  });

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setAppliedFilters({ keyword, location });
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <Search className="size-6 text-primary" />
        الوظائف
      </h1>

      <form onSubmit={handleSearch} className="flex flex-wrap gap-2">
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
        <Button type="submit">بحث</Button>
        <Button
          type="button"
          variant={sortByMatch ? "default" : "outline"}
          className={cn("gap-1.5")}
          onClick={() => setSortByMatch((v) => !v)}
        >
          <Sparkles className="size-4" />
          الأكثر توافقًا مع سيرتي الذاتية
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
              <TableHead>المسمى الوظيفي</TableHead>
              <TableHead>الشركة</TableHead>
              <TableHead>الموقع</TableHead>
              <TableHead>المصدر</TableHead>
              {sortByMatch && <TableHead>التوافق</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.jobs.map((job) => (
              <TableRow key={job.id}>
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
                  </div>
                </TableCell>
                <TableCell>{job.company}</TableCell>
                <TableCell>{job.location ?? "—"}</TableCell>
                <TableCell>{job.source ?? "—"}</TableCell>
                {sortByMatch && (
                  <TableCell>
                    {job.score != null ? (
                      <Badge variant={job.score >= 50 ? "default" : "secondary"}>
                        {job.score}%
                      </Badge>
                    ) : (
                      "—"
                    )}
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <p className="text-sm text-muted-foreground">
          مفيش وظائف لسه — لما نربط الـ Discovery الحقيقي هيبدأ يظهرلك نتايج هنا.
        </p>
      )}
    </div>
  );
}
