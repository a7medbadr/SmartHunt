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
  const { t } = useTranslation();
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
      setFormError(t("settings", "passwordMinLength"));
      return;
    }
    if (newPassword !== confirmPassword) {
      setFormError(t("settings", "passwordMismatch"));
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
          {t("settings", "changePassword")}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="current-password">{t("settings", "currentPassword")}</Label>
            <Input
              id="current-password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="new-password">{t("settings", "newPassword")}</Label>
            <Input
              id="new-password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="confirm-password">{t("settings", "confirmPassword")}</Label>
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
            {mutation.isPending ? t("settings", "changing") : t("settings", "changePasswordButton")}
          </Button>

          {formError && <p className="text-sm text-destructive">{formError}</p>}
          {!formError && serverError && (
            <p className="text-sm text-destructive">{serverError}</p>
          )}
          {mutation.isSuccess && (
            <p className="text-sm text-primary">{t("settings", "passwordChanged")}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function SettingsForm({ initial }: { initial: UserSettings }) {
  const { t } = useTranslation();
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
        <CardTitle className="text-base">{t("settings", "generalPreferences")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <Label htmlFor="email-notif">{t("settings", "emailNotifications")}</Label>
          <Switch
            id="email-notif"
            checked={form.email_notifications}
            onCheckedChange={(v) => setForm({ ...form, email_notifications: v })}
          />
        </div>

        <div className="flex items-center justify-between">
          <Label htmlFor="job-alerts">{t("settings", "newJobAlerts")}</Label>
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
          {mutation.isPending ? t("settings", "saving") : t("common", "save")}
        </Button>
        {mutation.isSuccess && (
          <p className="text-sm text-muted-foreground">{t("settings", "settingsSaved")}</p>
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
  const { t } = useTranslation();
  const testMutation = useMutation({
    mutationFn: () =>
      createNotification({
        type: "TEST",
        title: t("settings", "testNotificationTitle"),
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
          {testMutation.isPending
            ? t("settings", "sending")
            : t("settings", "sendTestNotification")}
        </Button>
        {testMutation.isSuccess && (
          <p className="text-sm text-muted-foreground">
            {t("settings", "testNotificationSentHint")}
          </p>
        )}
        {testMutation.isError && (
          <p className="text-sm text-destructive">{t("settings", "testNotificationError")}</p>
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
          title={t("settings", "telegramNotifications")}
          hint={t("settings", "telegramHint")}
          message={t("settings", "telegramTestMessage")}
        />

        <NotificationTestCard
          channel="WHATSAPP"
          title={t("settings", "whatsappNotifications")}
          hint={t("settings", "whatsappHint")}
          message={t("settings", "whatsappTestMessage")}
        />

        <NotificationTestCard
          channel="EMAIL"
          title={t("settings", "emailChannelNotifications")}
          hint={t("settings", "emailHint")}
          message={t("settings", "emailTestMessage")}
        />
      </div>
    </div>
  );
}
