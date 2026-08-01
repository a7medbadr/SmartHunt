"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Settings as SettingsIcon } from "lucide-react";
import { useState } from "react";

import { getSettings, updateSettings, type UserSettings } from "@/lib/settings-api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
        <div className="flex flex-col gap-2">
          <Label>المظهر</Label>
          <Select
            value={form.theme}
            onValueChange={(theme) => theme && setForm({ ...form, theme })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="dark">داكن</SelectItem>
              <SelectItem value="light">فاتح</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-2">
          <Label>اللغة</Label>
          <Select
            value={form.language}
            onValueChange={(language) => language && setForm({ ...form, language })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ar">العربية</SelectItem>
              <SelectItem value="en">English</SelectItem>
            </SelectContent>
          </Select>
        </div>

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

export default function SettingsPage() {
  const { data, isPending } = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  return (
    <div className="flex max-w-md flex-col gap-6">
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <SettingsIcon className="size-6 text-primary" />
        الإعدادات
      </h1>

      {isPending || !data ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <SettingsForm initial={data} />
      )}
    </div>
  );
}
