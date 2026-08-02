"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Settings as SettingsIcon } from "lucide-react";
import { useState } from "react";

import { getSettings, updateSettings, type UserSettings } from "@/lib/settings-api";
import { createNotification } from "@/lib/notifications-api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";

function SettingsForm({ initial }: { initial: UserSettings }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<UserSettings>(initial);

  const mutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: (updated) => {
      setForm(updated);
      queryClient.setQueryData(["settings"], updated);
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">التفضيلات العامة</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <Label htmlFor="email-notif">إشعارات البريد الإلكتروني</Label>
          <Switch
            id="email-notif"
            checked={form.email_notifications}
            onCheckedChange={(v) => setForm({ ...form, email_notifications: v })}
          />
        </div>

        <div className="flex items-center justify-between">
          <Label htmlFor="job-alerts">تنبيهات الوظائف الجديدة</Label>
          <Switch
            id="job-alerts"
            checked={form.job_alerts}
            onCheckedChange={(v) => setForm({ ...form, job_alerts: v })}
          />
        </div>

        <Button
          onClick={() => mutation.mutate(form)}
          disabled={mutation.isPending}
          className="self-start"
        >
          {mutation.isPending ? "جاري الحفظ..." : "حفظ"}
        </Button>
        {mutation.isSuccess && (
          <p className="text-sm text-muted-foreground">اتحفظت الإعدادات.</p>
        )}
      </CardContent>
    </Card>
  );
}

function TelegramTestCard() {
  const testMutation = useMutation({
    mutationFn: () =>
      createNotification({
        type: "TEST",
        title: "إشعار تجريبي من SmartHunt",
        message: "لو وصلك ده على تيليجرام، يبقى الإعداد شغال صح.",
        channel: "TELEGRAM",
      }),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">إشعارات تيليجرام</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <p className="text-sm text-muted-foreground">
          محتاج TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID متظبطين في السيرفر الأول. دوس
          هنا تبعت رسالة تجريبية تتأكد إنها شغالة.
        </p>
        <Button
          variant="outline"
          onClick={() => testMutation.mutate()}
          disabled={testMutation.isPending}
          className="self-start"
        >
          {testMutation.isPending ? "جاري الإرسال..." : "ابعت إشعار تجريبي"}
        </Button>
        {testMutation.isSuccess && (
          <p className="text-sm text-muted-foreground">
            اتبعتت — لو معطلتش الـ Telegram هتلاقيها في تبويب الإشعارات بس مش هتوصلك
            على تيليجرام لحد ما تظبط الإعدادات.
          </p>
        )}
        {testMutation.isError && (
          <p className="text-sm text-destructive">حصل خطأ أثناء الإرسال.</p>
        )}
      </CardContent>
    </Card>
  );
}

export default function SettingsPage() {
  const { data, isPending } = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  return (
    <div className="flex max-w-md flex-col gap-6">
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <SettingsIcon className="size-6 text-slate-400" />
        الإعدادات
      </h1>

      {isPending || !data ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <SettingsForm initial={data} />
      )}

      <TelegramTestCard />
    </div>
  );
}
