"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookmarkPlus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import {
  createSavedSearch,
  deleteSavedSearch,
  listSavedSearches,
} from "@/lib/saved-searches-api";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function SavedSearchesPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [name, setName] = useState("");
  const [keyword, setKeyword] = useState("");
  const [location, setLocation] = useState("");

  const { data, isPending } = useQuery({
    queryKey: ["saved-searches"],
    queryFn: listSavedSearches,
  });

  const createMutation = useMutation({
    mutationFn: createSavedSearch,
    onSuccess: () => {
      setName("");
      setKeyword("");
      setLocation("");
      setDialogOpen(false);
      queryClient.invalidateQueries({ queryKey: ["saved-searches"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSavedSearch,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["saved-searches"] }),
  });

  function jobsHref(search: { keyword: string | null; location: string | null }) {
    const params = new URLSearchParams();
    if (search.keyword) params.set("keyword", search.keyword);
    if (search.location) params.set("location", search.location);
    const qs = params.toString();
    return qs ? `/jobs?${qs}` : "/jobs";
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <BookmarkPlus className="size-6 text-amber-400" />
          عمليات البحث المحفوظة
        </h1>

        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger className={buttonVariants()}>حفظ بحث جديد</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>حفظ بحث جديد</DialogTitle>
            </DialogHeader>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                createMutation.mutate({
                  name,
                  keyword: keyword || undefined,
                  location: location || undefined,
                });
              }}
              className="flex flex-col gap-3"
            >
              <Input
                placeholder="اسم البحث"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              <Input
                placeholder="كلمة مفتاحية (اختياري)"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
              />
              <Input
                placeholder="الموقع (اختياري)"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "جاري الحفظ..." : "حفظ"}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {isPending ? (
        <Skeleton className="h-40 w-full" />
      ) : data && data.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>الاسم</TableHead>
              <TableHead>كلمة مفتاحية</TableHead>
              <TableHead>الموقع</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((search) => (
              <TableRow key={search.id}>
                <TableCell className="font-medium">
                  <Link href={jobsHref(search)} className="underline">
                    {search.name}
                  </Link>
                </TableCell>
                <TableCell>{search.keyword ?? "—"}</TableCell>
                <TableCell>{search.location ?? "—"}</TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteMutation.mutate(search.id)}
                  >
                    حذف
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <p className="text-sm text-muted-foreground">لسه مفيش عمليات بحث محفوظة.</p>
      )}
    </div>
  );
}
