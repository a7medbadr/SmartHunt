"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Heart } from "lucide-react";
import Link from "next/link";

import { listFavorites, removeFavorite } from "@/lib/jobs-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function FavoritesPage() {
  const queryClient = useQueryClient();

  const { data, isPending, isError } = useQuery({
    queryKey: ["favorites"],
    queryFn: listFavorites,
  });

  const removeMutation = useMutation({
    mutationFn: removeFavorite,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["favorites"] }),
  });

  return (
    <div className="flex flex-col gap-6">
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <Heart className="size-6 text-primary" />
        المفضلة
      </h1>

      {isError && (
        <p className="text-sm text-destructive">مقدرناش نجيب المفضلة، جرب تاني.</p>
      )}

      {isPending ? (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : data && data.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>المسمى الوظيفي</TableHead>
              <TableHead>الشركة</TableHead>
              <TableHead>الموقع</TableHead>
              <TableHead>المصدر</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((favorite) => (
              <TableRow key={favorite.id}>
                <TableCell>
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      href={`/jobs/${favorite.job_id}`}
                      className="font-medium underline"
                    >
                      {favorite.job?.title ?? `وظيفة #${favorite.job_id}`}
                    </Link>
                    {favorite.job?.no_sponsorship_signal && (
                      <Badge variant="destructive" className="text-xs">
                        بدون رعاية تأشيرة
                      </Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell>{favorite.job?.company ?? "—"}</TableCell>
                <TableCell>{favorite.job?.location ?? "—"}</TableCell>
                <TableCell>{favorite.job?.source ?? "—"}</TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeMutation.mutate(favorite.job_id)}
                    disabled={removeMutation.isPending}
                  >
                    حذف
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <p className="text-sm text-muted-foreground">لسه مفيش وظائف في المفضلة.</p>
      )}
    </div>
  );
}
