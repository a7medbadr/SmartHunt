"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Globe, KeyRound, Settings as SettingsIcon } from "lucide-react";
import { useState } from "react";

import { getSettings, updateSettings, type UserSettings } from "@/lib/settings-api";
import { createNotification } from "@/lib/notifications-api";
import { changePassword } from "@/lib/auth-api";
import { PageGlow } from "@/components/page-glow";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { useLanguage, useTranslation } from "@/lib/i18n/language-context";
import type { Locale } from "@/lib/i18n/translations";

function LanguageCard() {
  const { locale, setLocale } = useLanguage();
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Globe className="size-4 text-sky-400" />
          {t("common", "language")}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex gap-2">
        {(["ar", "en"] as Locale[]).map((option) => (
          <Button
            key={option}
            variant={locale === option ? "default" : "outline"}
            onClick={() => setLocale(option)}
          >
            {option === "ar" ? t("common", "arabic") : t("common", "english")}
          </Button>
        ))}
      </CardContent>
    </Card>
  );
}

function ChangePasswordCard() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: changePassword,
    onSuccess: () => {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setFormError(null);
    },
  });

  function handleSubmit() {
    setFormError(null);
    mutation.reset();

    if (newPassword.length < 6) {
      setFormError("الباسورد الجديدة لازم تكون 6 حروف/أرقام على الأقل.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setFormError("الباسورد الجديدة والتأكيد مش متطابقين.");
      return;
    }

    mutation.mutate({ current_password: currentPassword, new_password: newPassword });
  }

  const serverError =
    mutation.isError &&
    (mutation.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <KeyRound className="size-4 text-amber-400" />
          تغيير الباسورد
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="current-password">الباسورد الحالية</Label>
            <Input
              id="current-password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="new-password">الباسورد الجديدة</Label>
            <Input
              id="new-password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="confirm-password">تأكيد الباسورد الجديدة</Label>
            <Input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            />
          </div>

          <Button
            type="button"
            onClick={handleSubmit}
            disabled={mutation.isPending || !currentPassword || !newPassword || !confirmPassword}
            className="self-start"
          >
            {mutation.isPending ? "جاري التغيير..." : "غيّر الباسورد"}
          </Button>

          {formError && <p className="text-sm text-destructive">{formError}</p>}
          {!formError && serverError && (
            <p className="text-sm text-destructive">{serverError}</p>
          )}
          {mutation.isSuccess && (
            <p className="text-sm text-primary">تم تغيير الباسورد بنجاح.</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

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

function NotificationTestCard({
  channel,
  title,
  hint,
  message,
}: {
  channel: "TELEGRAM" | "WHATSAPP" | "EMAIL";
  title: string;
  hint: string;
  message: string;
}) {
  const testMutation = useMutation({
    mutationFn: () =>
      createNotification({
        type: "TEST",
        title: "إشعار تجريبي من SmartHunt",
        message,
        channel,
      }),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <p className="text-sm text-muted-foreground">{hint}</p>
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
            اتبعتت — لو القناة معطلة هتلاقيها في تبويب الإشعارات بس مش هتوصلك فعليًا
            لحد ما تظبط الإعدادات.
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
  const { t } = useTranslation();
  const { data, isPending } = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  return (
    <div className="relative flex max-w-4xl flex-col gap-6 overflow-hidden">
      <PageGlow />
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <SettingsIcon className="size-6 text-slate-400" />
        {t("pageTitles", "settings")}
      </h1>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <LanguageCard />

        <ChangePasswordCard />

        {isPending || !data ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <SettingsForm initial={data} />
        )}

        <NotificationTestCard
          channel="TELEGRAM"
          title="إشعارات تيليجرام"
          hint="محتاج TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID متظبطين في السيرفر الأول. دوس هنا تبعت رسالة تجريبية تتأكد إنها شغالة."
          message="لو وصلك ده على تيليجرام، يبقى الإعداد شغال صح."
        />

        <NotificationTestCard
          channel="WHATSAPP"
          title="إشعارات واتساب"
          hint="محتاج WHATSAPP_API_KEY و WHATSAPP_RECIPIENT_NUMBER متظبطين في السيرفر الأول. دوس هنا تبعت رسالة تجريبية تتأكد إنها شغالة."
          message="لو وصلك ده على واتساب، يبقى الإعداد شغال صح."
        />

        <NotificationTestCard
          channel="EMAIL"
          title="إشعارات الإيميل"
          hint="محتاج بيانات SMTP متظبطة في السيرفر الأول. دوس هنا تبعت رسالة تجريبية تتأكد إنها شغالة."
          message="لو وصلك ده على الإيميل، يبقى الإعداد شغال صح."
        />
      </div>
    </div>
  );
}
