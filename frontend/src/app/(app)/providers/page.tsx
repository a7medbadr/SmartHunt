"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, CheckCircle2, CircleDot, Plus } from "lucide-react";
import { useState } from "react";

import { createNotification } from "@/lib/notifications-api";
import { listProviders, setProviderEnabled } from "@/lib/providers-api";
import { PageGlow } from "@/components/page-glow";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslation } from "@/lib/i18n/language-context";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";

export default function ProvidersPage() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();
  const [requestDialogOpen, setRequestDialogOpen] = useState(false);
  const [requestSiteName, setRequestSiteName] = useState("");
  const [requestNote, setRequestNote] = useState("");

  const { data, isPending, isError } = useQuery({
    queryKey: ["providers"],
    queryFn: listProviders,
  });

  const toggleMutation = useMutation({
    mutationFn: ({ name, enabled }: { name: string; enabled: boolean }) =>
      setProviderEnabled(name, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["providers"] }),
  });

  const requestMutation = useMutation({
    mutationFn: createNotification,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      setRequestDialogOpen(false);
      setRequestSiteName("");
      setRequestNote("");
    },
  });

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden">
      <PageGlow />
      <div className="flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <Building2 className="size-6 text-indigo-400" />
          {t("pageTitles", "providers")}
        </h1>

        <Dialog open={requestDialogOpen} onOpenChange={setRequestDialogOpen}>
          <DialogTrigger className="inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm hover:bg-muted">
            <Plus className="size-4" />
            إضافة موقع جديد
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>طلب إضافة موقع توظيف جديد</DialogTitle>
            </DialogHeader>
            <div className="flex flex-col gap-3 text-sm">
              <p className="text-muted-foreground">
                إضافة موقع جديد محتاجة كود اكتشاف حقيقي مكتوب خصيصًا له (كل
                موقع بنية صفحاته مختلفة) — مش زرار سحري بيشتغل مع أي رابط.
                اكتب اسم الموقع ورابطه هنا وهبني هعمله بنفس الطريقة اللي
                عملت بيها LinkedIn.
              </p>
              <Input
                placeholder="اسم الموقع (مثلاً: Bayt)"
                value={requestSiteName}
                onChange={(e) => setRequestSiteName(e.target.value)}
              />
              <Textarea
                placeholder="أي تفاصيل إضافية (رابط البحث، هل محتاج تسجيل دخول...)"
                value={requestNote}
                onChange={(e) => setRequestNote(e.target.value)}
              />
              <Button
                disabled={!requestSiteName.trim() || requestMutation.isPending}
                onClick={() =>
                  requestMutation.mutate({
                    type: "PROVIDER_REQUEST",
                    title: `طلب إضافة موقع: ${requestSiteName.trim()}`,
                    message: requestNote.trim() || "بدون تفاصيل إضافية",
                    priority: "NORMAL",
                  })
                }
              >
                {requestMutation.isPending ? "جاري الحفظ..." : "حفظ الطلب"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {isError && (
        <p className="text-sm text-destructive">مقدرناش نجيب مواقع التوظيف، جرب تاني.</p>
      )}

      {isPending ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data?.map((provider) => (
            <Card key={provider.name}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-base capitalize">{provider.name}</CardTitle>
                <Switch
                  checked={provider.enabled}
                  onCheckedChange={(checked) =>
                    toggleMutation.mutate({ name: provider.name, enabled: checked })
                  }
                  disabled={toggleMutation.isPending}
                />
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                <div>
                  {provider.real_discovery ? (
                    <Badge variant="default" className="gap-1 text-xs">
                      <CheckCircle2 className="size-3" />
                      اكتشاف حقيقي
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="gap-1 text-xs">
                      <CircleDot className="size-3" />
                      اكتشاف فقط (لسه مش حقيقي)
                    </Badge>
                  )}
                </div>
                <div className="flex flex-wrap gap-1 text-xs text-muted-foreground">
                  {provider.supports_login && <span>تسجيل دخول</span>}
                  {provider.supports_apply && <span>· تقديم تلقائي</span>}
                  {provider.supports_resume_upload && <span>· رفع سيرة ذاتية</span>}
                  {provider.supports_cover_letter && <span>· خطاب تقديم</span>}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
