"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Briefcase, Zap } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import {
  APPLICATION_STATUSES,
  type ApplicationStatus,
  createApplication,
  deleteApplication,
  listApplications,
  updateApplicationStatus,
} from "@/lib/applications-api";
import { quickApply } from "@/lib/apply-queue-api";
import { PageGlow } from "@/components/page-glow";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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

const STATUS_STYLES: Record<string, string> = {
  Applied: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  Interviewing: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  "Technical Interview": "bg-amber-500/15 text-amber-400 border-amber-500/30",
  Offered: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  Rejected: "bg-red-500/15 text-red-400 border-red-500/30",
  Pending: "bg-slate-500/15 text-slate-400 border-slate-500/30",
};

export default function ApplicationsPage() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("");
  const [url, setUrl] = useState("");
  const [quickApplyResult, setQuickApplyResult] = useState<string | null>(null);

  const { data, isPending } = useQuery({
    queryKey: ["applications"],
    queryFn: listApplications,
  });

  const createMutation = useMutation({
    mutationFn: createApplication,
    onSuccess: () => {
      setJobTitle("");
      setCompany("");
      setUrl("");
      setDialogOpen(false);
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: ApplicationStatus }) =>
      updateApplicationStatus(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteApplication,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
  });

  const quickApplyMutation = useMutation({
    mutationFn: quickApply,
    onSuccess: (item) => {
      setQuickApplyResult(
        item.status === "SUCCESS"
          ? t("applications", "quickApplySuccess")
          : t("applications", "quickApplyFailed").replace("{status}", item.status),
      );
    },
    onError: () => setQuickApplyResult(t("applications", "quickApplyError")),
  });

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden">
      <PageGlow />
      <div className="flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <Briefcase className="size-6 text-orange-400" />
          {t("pageTitles", "applications")}
        </h1>

        <Dialog
          open={dialogOpen}
          onOpenChange={(open) => {
            setDialogOpen(open);
            if (!open) setQuickApplyResult(null);
          }}
        >
          <DialogTrigger className={buttonVariants()}>
            {t("applications", "newApplication")}
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("applications", "addApplicationTitle")}</DialogTitle>
            </DialogHeader>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                createMutation.mutate({
                  job_title: jobTitle,
                  company,
                  url: url || undefined,
                });
              }}
              className="flex flex-col gap-3"
            >
              <Input
                placeholder={t("applications", "jobTitlePlaceholder")}
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                required
              />
              <Input
                placeholder={t("applications", "companyPlaceholder")}
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                required
              />
              <Input
                placeholder={t("applications", "urlPlaceholder")}
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
              <div className="flex gap-2">
                <Button type="submit" disabled={createMutation.isPending} className="flex-1">
                  {createMutation.isPending
                    ? t("applications", "saving")
                    : t("applications", "saveOnly")}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  className="flex-1 gap-1.5"
                  disabled={!url || !jobTitle || !company || quickApplyMutation.isPending}
                  onClick={() =>
                    quickApplyMutation.mutate({ url, title: jobTitle, company })
                  }
                >
                  <Zap className="size-4" />
                  {quickApplyMutation.isPending
                    ? t("applications", "quickApplying")
                    : t("applications", "quickApplyNow")}
                </Button>
              </div>
              {quickApplyResult && (
                <p className="text-sm text-muted-foreground">{quickApplyResult}</p>
              )}
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {!isPending && data && data.length > 0 && (
        <div className="flex flex-wrap gap-3">
          {APPLICATION_STATUSES.map((status) => {
            const count = data.filter((a) => a.status === status).length;
            if (count === 0) return null;
            return (
              <Card key={status} className="min-w-28">
                <CardContent className="flex flex-col gap-1 p-3">
                  <span className="text-xs text-muted-foreground">{status}</span>
                  <span className="text-xl font-semibold">{count}</span>
                </CardContent>
              </Card>
            );
          })}
          <Card className="min-w-28">
            <CardContent className="flex flex-col gap-1 p-3">
              <span className="text-xs text-muted-foreground">{t("applications", "total")}</span>
              <span className="text-xl font-semibold">{data.length}</span>
            </CardContent>
          </Card>
        </div>
      )}

      {isPending ? (
        <Skeleton className="h-40 w-full" />
      ) : data && data.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("applications", "jobTitleHeader")}</TableHead>
              <TableHead>{t("applications", "companyHeader")}</TableHead>
              <TableHead>{t("applications", "statusHeader")}</TableHead>
              <TableHead>{t("applications", "appliedDateHeader")}</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((app) => (
              <TableRow key={app.id}>
                <TableCell className="font-medium">
                  <div className="flex flex-wrap items-center gap-2">
                    {app.url ? (
                      <a
                        href={app.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="underline"
                      >
                        {app.job_title}
                      </a>
                    ) : (
                      app.job_title
                    )}
                    {app.needs_follow_up && (
                      <Badge variant="secondary" className="text-xs">
                        {t("applications", "needsFollowUp").replace(
                          "{days}",
                          String(app.days_since_applied),
                        )}
                      </Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell>{app.company}</TableCell>
                <TableCell>
                  <Select
                    value={app.status}
                    onValueChange={(status) =>
                      statusMutation.mutate({ id: app.id, status: status as ApplicationStatus })
                    }
                  >
                    <SelectTrigger
                      className={cn("w-40", STATUS_STYLES[app.status])}
                    >
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {APPLICATION_STATUSES.map((s) => (
                        <SelectItem key={s} value={s}>
                          {s}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  {new Date(app.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Link
                      href={`/applications/${app.id}`}
                      className={buttonVariants({ variant: "ghost", size: "sm" })}
                    >
                      {t("applications", "conversation")}
                    </Link>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setDeleteTargetId(app.id)}
                    >
                      {t("common", "delete")}
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <p className="text-sm text-muted-foreground">{t("applications", "noApplicationsYet")}</p>
      )}
      <ConfirmDialog
        open={deleteTargetId !== null}
        onOpenChange={(open) => !open && setDeleteTargetId(null)}
        isPending={deleteMutation.isPending}
        onConfirm={() => {
          if (deleteTargetId !== null) deleteMutation.mutate(deleteTargetId);
          setDeleteTargetId(null);
        }}
      />
    </div>
  );
}
