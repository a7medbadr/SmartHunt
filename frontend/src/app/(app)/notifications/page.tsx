"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell } from "lucide-react";
import { useState } from "react";

import {
  deleteNotification,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/notifications-api";
import { PageGlow } from "@/components/page-glow";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslation } from "@/lib/i18n/language-context";
import { cn } from "@/lib/utils";

export default function NotificationsPage() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null);

  const { data, isPending } = useQuery({
    queryKey: ["notifications"],
    queryFn: listNotifications,
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
  }

  const markReadMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: invalidate,
  });
  const markAllMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: invalidate,
  });
  const deleteMutation = useMutation({
    mutationFn: deleteNotification,
    onSuccess: invalidate,
  });

  const unreadCount = data?.filter((n) => !n.read_at).length ?? 0;

  return (
    <div className="relative flex max-w-2xl flex-col gap-4 overflow-hidden">
      <PageGlow />
      <div className="flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <Bell className="size-6 text-yellow-400" />
          {t("pageTitles", "notifications")}
        </h1>
        {unreadCount > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => markAllMutation.mutate()}
            disabled={markAllMutation.isPending}
          >
            {t("notifications", "markAllRead")}
          </Button>
        )}
      </div>

      {isPending ? (
        <Skeleton className="h-40 w-full" />
      ) : data && data.length > 0 ? (
        <div className="flex flex-col gap-2">
          {data.map((notification) => (
            <div
              key={notification.id}
              className={cn(
                "flex items-start justify-between gap-3 rounded-md border p-3",
                !notification.read_at && "border-primary/50 bg-primary/5",
              )}
            >
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <p className="font-medium">{notification.title}</p>
                  {!notification.read_at && (
                    <Badge variant="secondary" className="text-xs">
                      {t("notifications", "new")}
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">{notification.message}</p>
                <p className="text-xs text-muted-foreground">
                  {new Date(notification.created_at).toLocaleString()}
                </p>
              </div>
              <div className="flex shrink-0 gap-2">
                {!notification.read_at && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => markReadMutation.mutate(notification.id)}
                  >
                    {t("notifications", "markAsRead")}
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setDeleteTargetId(notification.id)}
                >
                  {t("common", "delete")}
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">{t("notifications", "noNotificationsYet")}</p>
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
