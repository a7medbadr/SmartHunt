"use client";

import { useQuery } from "@tanstack/react-query";

import { getDashboardStatistics } from "@/lib/dashboard-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const STAT_CARDS: Array<{
  key: keyof Awaited<ReturnType<typeof getDashboardStatistics>>;
  label: string;
}> = [
  { key: "jobs", label: "الوظائف المكتشفة" },
  { key: "applications", label: "التقديمات" },
  { key: "favorites", label: "المفضلة" },
  { key: "saved_searches", label: "عمليات البحث المحفوظة" },
  { key: "providers", label: "مواقع التوظيف المفعّلة" },
];

export default function DashboardPage() {
  const { data, isPending, isError } = useQuery({
    queryKey: ["dashboard-statistics"],
    queryFn: getDashboardStatistics,
  });

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">الداشبورد</h1>

      {isError && (
        <p className="text-sm text-destructive">
          مقدرناش نجيب إحصائيات الداشبورد، جرب تحدّث الصفحة.
        </p>
      )}

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {STAT_CARDS.map((stat) => (
          <Card key={stat.key}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-normal text-muted-foreground">
                {stat.label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isPending ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <span className="text-3xl font-semibold">
                  {data?.[stat.key] ?? 0}
                </span>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
