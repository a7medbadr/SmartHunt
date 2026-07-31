"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { searchJobs } from "@/lib/jobs-api";
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

export default function JobsPage() {
  const [keyword, setKeyword] = useState("");
  const [location, setLocation] = useState("");
  const [appliedFilters, setAppliedFilters] = useState({ keyword: "", location: "" });

  const { data, isPending, isError } = useQuery({
    queryKey: ["search-jobs", appliedFilters],
    queryFn: () =>
      searchJobs({
        keyword: appliedFilters.keyword || undefined,
        location: appliedFilters.location || undefined,
        limit: 50,
      }),
  });

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setAppliedFilters({ keyword, location });
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">الوظائف</h1>

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
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.jobs.map((job) => (
              <TableRow key={job.id}>
                <TableCell>
                  <Link href={`/jobs/${job.id}`} className="font-medium underline">
                    {job.title}
                  </Link>
                </TableCell>
                <TableCell>{job.company}</TableCell>
                <TableCell>{job.location ?? "—"}</TableCell>
                <TableCell>{job.source ?? "—"}</TableCell>
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
