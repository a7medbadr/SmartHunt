"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell } from "lucide-react";

import {
  deleteNotification,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/notifications-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export default function NotificationsPage() {
  const queryClient = useQueryClient();

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
    <div className="flex max-w-2xl flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <Bell className="size-6 text-yellow-400" />
          الإشعارات
        </h1>
        {unreadCount > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => markAllMutation.mutate()}
            disabled={markAllMutation.isPending}
          >
            تعليم الكل كمقروء
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
                      جديد
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
                    قراءة
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => deleteMutation.mutate(notification.id)}
                >
                  حذف
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">مفيش إشعارات لسه.</p>
      )}
    </div>
  );
}
