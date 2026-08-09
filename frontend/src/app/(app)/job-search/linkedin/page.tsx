"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { ListChecks, Rss, Trash2, XCircle } from "lucide-react";
import { useRef, useState } from "react";

import {
  addHashtag,
  addMonitoredAccount,
  listHashtags,
  listMonitoredAccounts,
  removeHashtag,
  removeMonitoredAccount,
  scanAccountNow,
  scanHashtagNow,
  scanHomeFeedNow,
  setHashtagEnabled,
  setMonitoredAccountEnabled,
} from "@/lib/linkedin-monitor-api";
import { listSchedulerHistory } from "@/lib/scheduler-api";
import { LastAutomatedScan } from "@/components/last-automated-scan";
import { PageGlow } from "@/components/page-glow";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslation } from "@/lib/i18n/language-context";
import { Switch } from "@/components/ui/switch";
import { EstimatedProgressBar } from "@/components/ui/estimated-progress-bar";
import { useEstimatedProgress } from "@/hooks/use-estimated-progress";
import { getApiErrorMessage } from "@/lib/api-error";

export default function JobSearchLinkedinPage() {
  const queryClient = useQueryClient();
  const { t, locale } = useTranslation();
  const dateLocale = locale === "ar" ? "ar-SA" : "en-US";

  // 1) افحص الصفحة الرئيسية بتاعتي — منفصل خالص عن بلوك البحث في بوستات
  // لينكدان بتاع الحسابات، بلوك لوحده زي ما اتطلب.
  const [scanResultMessage, setScanResultMessage] = useState<string | null>(null);
  const feedControllerRef = useRef<AbortController | null>(null);

  const scanFeedMutation = useMutation({
    mutationFn: () => {
      const controller = new AbortController();
      feedControllerRef.current = controller;
      return scanHomeFeedNow(controller.signal);
    },
    onSuccess: (result) => {
      setScanResultMessage(
        t("jobSearch", "foundPostsSaved")
          .replace("{scanned}", String(result.scanned))
          .replace("{saved}", String(result.saved)),
      );
      queryClient.invalidateQueries({ queryKey: ["search-jobs"] });
    },
    onError: (error) => {
      setScanResultMessage(
        axios.isCancel(error)
          ? t("jobSearch", "scanCancelled")
          : (getApiErrorMessage(error) ?? t("jobSearch", "scanError")),
      );
    },
    onSettled: () => {
      feedControllerRef.current = null;
    },
  });
  // 200s: measured live 2026-08-06 after raising scroll_rounds to reach
  // the owner's ~50-post target — a real scan took ~3m19s to find all 50.
  const scanFeedProgress = useEstimatedProgress(scanFeedMutation.isPending, 200000);

  function cancelFeedScan() {
    feedControllerRef.current?.abort();
  }

  const schedulerHistoryQuery = useQuery({
    queryKey: ["scheduler-history"],
    queryFn: listSchedulerHistory,
  });

  // 2) البحث في بوستات لينكدان — حسابات الأشخاص/الاتش آر.
  const [newAccountUrl, setNewAccountUrl] = useState("");
  const [newAccountLabel, setNewAccountLabel] = useState("");
  const [accountScanMessage, setAccountScanMessage] = useState<string | null>(null);
  const [deleteAccountId, setDeleteAccountId] = useState<number | null>(null);

  const accountsQuery = useQuery({
    queryKey: ["linkedin-monitor-accounts"],
    queryFn: listMonitoredAccounts,
  });

  // A single shared Playwright page (browser_manager.get_page("linkedin"))
  // backs every account scan — two scans in flight at once would race on
  // the same page's navigation. queuedAccountIds serializes them: adding
  // 3 accounts back-to-back (each auto-scanning itself) or clicking
  // several rows quickly no longer fires overlapping requests, each
  // waits its turn instead.
  const [scanQueue, setScanQueue] = useState<number[]>([]);
  const accountControllerRef = useRef<AbortController | null>(null);

  const scanAccountMutation = useMutation({
    mutationFn: (id: number) => {
      const controller = new AbortController();
      accountControllerRef.current = controller;
      return scanAccountNow(id, controller.signal);
    },
    onSuccess: (result) => {
      setAccountScanMessage(
        t("jobSearch", "foundPostsSaved")
          .replace("{scanned}", String(result.scanned))
          .replace("{saved}", String(result.saved)),
      );
      queryClient.invalidateQueries({ queryKey: ["linkedin-monitor-accounts"] });
      queryClient.invalidateQueries({ queryKey: ["search-jobs"] });
    },
    onError: (error) => {
      setAccountScanMessage(
        axios.isCancel(error)
          ? t("jobSearch", "scanCancelled")
          : (getApiErrorMessage(error) ?? t("jobSearch", "scanError")),
      );
    },
    onSettled: () => {
      accountControllerRef.current = null;
      setScanQueue((queue) => {
        const [next, ...rest] = queue;
        if (next !== undefined) scanAccountMutation.mutate(next);
        return rest;
      });
    },
  });

  function queueAccountScan(accountId: number) {
    if (!scanAccountMutation.isPending) {
      scanAccountMutation.mutate(accountId);
    } else {
      setScanQueue((queue) => (queue.includes(accountId) ? queue : [...queue, accountId]));
    }
  }

  function scanAllAccounts() {
    for (const account of accountsQuery.data ?? []) {
      queueAccountScan(account.id);
    }
  }

  // Cancelling stops waiting on the current in-flight request AND clears
  // whatever's still queued behind it — otherwise onSettled would just
  // pick up the next queued account and keep going, which isn't what
  // "cancel" should mean when this was started via scanAllAccounts().
  function cancelAccountScan() {
    accountControllerRef.current?.abort();
    setScanQueue([]);
  }

  // 60s: a profile scan doesn't scroll (fixed "recent activity" page), so
  // it's much faster than the feed/hashtag scans — measured live ~25s.
  const scanAccountProgress = useEstimatedProgress(scanAccountMutation.isPending, 60000);

  const addAccountMutation = useMutation({
    mutationFn: addMonitoredAccount,
    onSuccess: (account) => {
      setNewAccountUrl("");
      setNewAccountLabel("");
      queryClient.invalidateQueries({ queryKey: ["linkedin-monitor-accounts"] });
      // "أضف حساب" مش بس بيحفظ الرابط — لازم كمان يدور على طول في بوستات
      // الحساب ده عن وظائف مرتبطة بيا، مش يسيبه لحد ما أدوس "افحص دلوقتي"
      // بنفسي بعدين.
      queueAccountScan(account.id);
    },
  });

  const toggleAccountMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      setMonitoredAccountEnabled(id, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["linkedin-monitor-accounts"] }),
  });

  const removeAccountMutation = useMutation({
    mutationFn: removeMonitoredAccount,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["linkedin-monitor-accounts"] }),
  });

  // 4) البحث بالهاشتاج — نفس فكرة بلوك حسابات لينكدان بالظبط: كل هاشتاج
  // صف لوحده، بزرار تفعيل/تعطيل وزرار "افحص دلوقتي" وزرار حذف، بدل مربع
  // نص واحد أو أزرار متفرقة. نفس فكرة الطابور بتاعة queueAccountScan فوق
  // — علشان لو ضغط على أكتر من هاشتاج ورا بعض، كل فحص يستنى دوره بدل ما
  // يتزاحموا على نفس صفحة لينكدان.
  const [newHashtagTag, setNewHashtagTag] = useState("");
  const [hashtagScanMessage, setHashtagScanMessage] = useState<string | null>(null);
  const [hashtagScanQueue, setHashtagScanQueue] = useState<number[]>([]);
  const [deleteHashtagId, setDeleteHashtagId] = useState<number | null>(null);
  const hashtagControllerRef = useRef<AbortController | null>(null);

  const hashtagsQuery = useQuery({
    queryKey: ["linkedin-hashtags"],
    queryFn: listHashtags,
  });

  const hashtagScanMutation = useMutation({
    mutationFn: (id: number) => {
      const controller = new AbortController();
      hashtagControllerRef.current = controller;
      return scanHashtagNow(id, controller.signal);
    },
    onSuccess: (result) => {
      setHashtagScanMessage(
        t("jobSearch", "foundPostsSaved")
          .replace("{scanned}", String(result.scanned))
          .replace("{saved}", String(result.saved)),
      );
      queryClient.invalidateQueries({ queryKey: ["linkedin-hashtags"] });
      queryClient.invalidateQueries({ queryKey: ["search-jobs"] });
    },
    onError: (error) => {
      setHashtagScanMessage(
        axios.isCancel(error)
          ? t("jobSearch", "scanCancelled")
          : (getApiErrorMessage(error) ?? t("jobSearch", "scanError")),
      );
    },
    onSettled: () => {
      hashtagControllerRef.current = null;
      setHashtagScanQueue((queue) => {
        const [next, ...rest] = queue;
        if (next !== undefined) hashtagScanMutation.mutate(next);
        return rest;
      });
    },
  });

  function queueHashtagScan(hashtagId: number) {
    if (!hashtagScanMutation.isPending) {
      hashtagScanMutation.mutate(hashtagId);
    } else {
      setHashtagScanQueue((queue) =>
        queue.includes(hashtagId) ? queue : [...queue, hashtagId],
      );
    }
  }

  function scanAllHashtags() {
    for (const hashtag of hashtagsQuery.data ?? []) {
      queueHashtagScan(hashtag.id);
    }
  }

  function cancelHashtagScan() {
    hashtagControllerRef.current?.abort();
    setHashtagScanQueue([]);
  }

  // 200s: hashtag pages use the same scroll-and-extract flow as the home
  // feed scan above (same expected duration).
  const hashtagScanProgress = useEstimatedProgress(hashtagScanMutation.isPending, 200000);

  const addHashtagMutation = useMutation({
    mutationFn: addHashtag,
    onSuccess: (hashtag) => {
      setNewHashtagTag("");
      queryClient.invalidateQueries({ queryKey: ["linkedin-hashtags"] });
      // زي "أضف حساب" بالظبط — أول ما يتضاف الهاشتاج، يتفحص على طول.
      queueHashtagScan(hashtag.id);
    },
  });

  const toggleHashtagMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      setHashtagEnabled(id, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["linkedin-hashtags"] }),
  });

  const removeHashtagMutation = useMutation({
    mutationFn: removeHashtag,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["linkedin-hashtags"] }),
  });

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden">
      <PageGlow />
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <Rss className="size-6 text-teal-400" />
        {t("discoveredJobs", "tabLinkedin")}
      </h1>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Rss className="size-4 text-sky-400" />
            {t("jobSearch", "scanHomeFeedTitle")}
          </CardTitle>
          <LastAutomatedScan
            history={schedulerHistoryQuery.data}
            providers={["scheduler:linkedin-feed"]}
            isPending={schedulerHistoryQuery.isPending}
          />
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">{t("jobSearch", "scanHomeFeedBody")}</p>
          <div className="flex items-center gap-3">
            <Button
              variant="secondary"
              disabled={scanFeedMutation.isPending}
              onClick={() => scanFeedMutation.mutate()}
              className="self-start"
            >
              {scanFeedMutation.isPending
                ? t("jobSearch", "scanningHomeFeed")
                : t("jobSearch", "scanHomeFeedButton")}
            </Button>
            {scanFeedMutation.isPending && (
              <>
                <EstimatedProgressBar percent={scanFeedProgress} />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={cancelFeedScan}
                  aria-label={t("jobSearch", "cancelScan")}
                >
                  <XCircle className="size-4" />
                </Button>
              </>
            )}
          </div>
          {scanResultMessage && <p className="text-sm text-primary">{scanResultMessage}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Rss className="size-4 text-sky-400" />
              {t("jobSearch", "linkedinPostSearchTitle")}
            </CardTitle>
            {accountsQuery.data && accountsQuery.data.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5"
                onClick={scanAllAccounts}
                disabled={scanAccountMutation.isPending || scanQueue.length > 0}
              >
                <ListChecks className="size-4" />
                {t("jobSearch", "scanAllAccounts")}
              </Button>
            )}
          </div>
          <LastAutomatedScan
            history={schedulerHistoryQuery.data}
            providers={["scheduler:linkedin-accounts"]}
            isPending={schedulerHistoryQuery.isPending}
          />
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            {t("jobSearch", "linkedinPostSearchBody")}
          </p>

          <div className="flex flex-wrap gap-2">
            <Input
              placeholder={t("jobSearch", "profileUrlPlaceholder")}
              value={newAccountUrl}
              onChange={(e) => setNewAccountUrl(e.target.value)}
              className="max-w-sm"
            />
            <Input
              placeholder={t("jobSearch", "labelPlaceholder")}
              value={newAccountLabel}
              onChange={(e) => setNewAccountLabel(e.target.value)}
              className="max-w-xs"
            />
            <Button
              disabled={!newAccountUrl.trim() || addAccountMutation.isPending}
              onClick={() =>
                addAccountMutation.mutate({
                  profileUrl: newAccountUrl.trim(),
                  label: newAccountLabel.trim(),
                })
              }
            >
              {addAccountMutation.isPending
                ? t("jobSearch", "addingAndScanning")
                : t("jobSearch", "addAccount")}
            </Button>
          </div>

          {accountsQuery.isPending ? (
            <Skeleton className="h-20 w-full" />
          ) : accountsQuery.data && accountsQuery.data.length > 0 ? (
            <div className="flex flex-col gap-2">
              {accountsQuery.data.map((account) => (
                <div
                  key={account.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3"
                >
                  <div className="flex flex-col">
                    <a
                      href={account.profile_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm underline"
                    >
                      {account.label || account.profile_url}
                    </a>
                    <span className="text-xs text-muted-foreground">
                      {account.last_checked_at
                        ? t("jobSearch", "lastCheckedLabel").replace(
                            "{date}",
                            new Date(account.last_checked_at).toLocaleString(dateLocale),
                          )
                        : t("jobSearch", "neverChecked")}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={account.enabled}
                      onCheckedChange={(checked) =>
                        toggleAccountMutation.mutate({ id: account.id, enabled: checked })
                      }
                      disabled={toggleAccountMutation.isPending}
                    />
                    <Button variant="outline" size="sm" onClick={() => queueAccountScan(account.id)}>
                      {scanAccountMutation.isPending &&
                      scanAccountMutation.variables === account.id
                        ? t("jobSearch", "scanning")
                        : scanQueue.includes(account.id)
                          ? t("jobSearch", "waiting")
                          : t("jobSearch", "scanNow")}
                    </Button>
                    {scanAccountMutation.isPending &&
                      scanAccountMutation.variables === account.id && (
                        <>
                          <EstimatedProgressBar percent={scanAccountProgress} />
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={cancelAccountScan}
                            aria-label={t("jobSearch", "cancelScan")}
                          >
                            <XCircle className="size-4" />
                          </Button>
                        </>
                      )}
                    <Button variant="ghost" size="icon" onClick={() => setDeleteAccountId(account.id)}>
                      <Trash2 className="size-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t("jobSearch", "noAccountsYet")}</p>
          )}

          {accountScanMessage && <p className="text-sm text-primary">{accountScanMessage}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="text-base">{t("jobSearch", "hashtagSearchTitle")}</CardTitle>
            {hashtagsQuery.data && hashtagsQuery.data.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5"
                onClick={scanAllHashtags}
                disabled={hashtagScanMutation.isPending || hashtagScanQueue.length > 0}
              >
                <ListChecks className="size-4" />
                {t("jobSearch", "scanAllHashtags")}
              </Button>
            )}
          </div>
          <p className="text-xs text-muted-foreground">{t("jobSearch", "hashtagSearchHint")}</p>
          <LastAutomatedScan
            history={schedulerHistoryQuery.data}
            providers={["scheduler:linkedin-hashtags"]}
            isPending={schedulerHistoryQuery.isPending}
          />
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-wrap gap-2">
            <Input
              placeholder={t("jobSearch", "hashtagPlaceholder")}
              value={newHashtagTag}
              onChange={(e) => setNewHashtagTag(e.target.value)}
              className="max-w-xs"
            />
            <Button
              disabled={!newHashtagTag.trim() || addHashtagMutation.isPending}
              onClick={() => addHashtagMutation.mutate(newHashtagTag.trim())}
            >
              {addHashtagMutation.isPending
                ? t("jobSearch", "addingAndScanning")
                : t("jobSearch", "addHashtag")}
            </Button>
          </div>

          {hashtagsQuery.isPending ? (
            <Skeleton className="h-20 w-full" />
          ) : hashtagsQuery.data && hashtagsQuery.data.length > 0 ? (
            <div className="flex flex-col gap-2">
              {hashtagsQuery.data.map((hashtag) => (
                <div
                  key={hashtag.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3"
                >
                  <div className="flex flex-col">
                    <span className="text-sm">#{hashtag.tag}</span>
                    <span className="text-xs text-muted-foreground">
                      {hashtag.last_checked_at
                        ? t("jobSearch", "lastCheckedLabel").replace(
                            "{date}",
                            new Date(hashtag.last_checked_at).toLocaleString(dateLocale),
                          )
                        : t("jobSearch", "neverChecked")}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={hashtag.enabled}
                      onCheckedChange={(checked) =>
                        toggleHashtagMutation.mutate({ id: hashtag.id, enabled: checked })
                      }
                      disabled={toggleHashtagMutation.isPending}
                    />
                    <Button variant="outline" size="sm" onClick={() => queueHashtagScan(hashtag.id)}>
                      {hashtagScanMutation.isPending &&
                      hashtagScanMutation.variables === hashtag.id
                        ? t("jobSearch", "scanning")
                        : hashtagScanQueue.includes(hashtag.id)
                          ? t("jobSearch", "waiting")
                          : t("jobSearch", "scanNow")}
                    </Button>
                    {hashtagScanMutation.isPending &&
                      hashtagScanMutation.variables === hashtag.id && (
                        <>
                          <EstimatedProgressBar percent={hashtagScanProgress} />
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={cancelHashtagScan}
                            aria-label={t("jobSearch", "cancelScan")}
                          >
                            <XCircle className="size-4" />
                          </Button>
                        </>
                      )}
                    <Button variant="ghost" size="icon" onClick={() => setDeleteHashtagId(hashtag.id)}>
                      <Trash2 className="size-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t("jobSearch", "noHashtagsYet")}</p>
          )}
          {hashtagScanMessage && <p className="text-sm text-primary">{hashtagScanMessage}</p>}
        </CardContent>
      </Card>

      <ConfirmDialog
        open={deleteAccountId !== null}
        onOpenChange={(open) => !open && setDeleteAccountId(null)}
        isPending={removeAccountMutation.isPending}
        onConfirm={() => {
          if (deleteAccountId !== null) removeAccountMutation.mutate(deleteAccountId);
          setDeleteAccountId(null);
        }}
      />
      <ConfirmDialog
        open={deleteHashtagId !== null}
        onOpenChange={(open) => !open && setDeleteHashtagId(null)}
        isPending={removeHashtagMutation.isPending}
        onConfirm={() => {
          if (deleteHashtagId !== null) removeHashtagMutation.mutate(deleteHashtagId);
          setDeleteHashtagId(null);
        }}
      />
    </div>
  );
}
