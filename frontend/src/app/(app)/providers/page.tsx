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
            {t("providers", "addNewSite")}
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("providers", "requestDialogTitle")}</DialogTitle>
            </DialogHeader>
            <div className="flex flex-col gap-3 text-sm">
              <p className="text-muted-foreground">
                {t("providers", "requestDialogBody")}
              </p>
              <Input
                placeholder={t("providers", "siteNamePlaceholder")}
                value={requestSiteName}
                onChange={(e) => setRequestSiteName(e.target.value)}
              />
              <Textarea
                placeholder={t("providers", "notesPlaceholder")}
                value={requestNote}
                onChange={(e) => setRequestNote(e.target.value)}
              />
              <Button
                disabled={!requestSiteName.trim() || requestMutation.isPending}
                onClick={() =>
                  requestMutation.mutate({
                    type: "PROVIDER_REQUEST",
                    title: `${t("providers", "requestTitlePrefix")}: ${requestSiteName.trim()}`,
                    message: requestNote.trim() || t("providers", "noAdditionalNotes"),
                    priority: "NORMAL",
                  })
                }
              >
                {requestMutation.isPending
                  ? t("providers", "savingRequest")
                  : t("providers", "saveRequest")}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {isError && (
        <p className="text-sm text-destructive">{t("providers", "loadError")}</p>
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
                      {t("providers", "realDiscovery")}
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="gap-1 text-xs">
                      <CircleDot className="size-3" />
                      {t("providers", "discoveryOnly")}
                    </Badge>
                  )}
                </div>
                <div className="flex flex-wrap gap-1 text-xs text-muted-foreground">
                  {provider.supports_login && <span>{t("providers", "supportsLogin")}</span>}
                  {provider.supports_apply && <span>{t("providers", "supportsApply")}</span>}
                  {provider.supports_resume_upload && (
                    <span>{t("providers", "supportsResumeUpload")}</span>
                  )}
                  {provider.supports_cover_letter && (
                    <span>{t("providers", "supportsCoverLetter")}</span>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
