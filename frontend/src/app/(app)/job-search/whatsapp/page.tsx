"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { ListChecks, MessageCircle, QrCode, Trash2, XCircle } from "lucide-react";
import { useRef, useState } from "react";

import {
  addChat,
  getWhatsAppLoginStatus,
  listChats,
  qrImageUrl,
  removeChat,
  scanChatNow,
  setChatEnabled,
  startWhatsAppLogin,
} from "@/lib/whatsapp-monitor-api";
import { listSchedulerHistory } from "@/lib/scheduler-api";
import { LastAutomatedScan } from "@/components/last-automated-scan";
import { PageGlow } from "@/components/page-glow";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslation } from "@/lib/i18n/language-context";
import { Switch } from "@/components/ui/switch";
import { EstimatedProgressBar } from "@/components/ui/estimated-progress-bar";
import { useEstimatedProgress } from "@/hooks/use-estimated-progress";
import { getApiErrorMessage } from "@/lib/api-error";

export default function JobSearchWhatsappPage() {
  const queryClient = useQueryClient();
  const { t, locale } = useTranslation();
  const dateLocale = locale === "ar" ? "ar-SA" : "en-US";

  // WhatsApp channel/group search — row-per-chat pattern, plus a
  // one-time QR-login bootstrap (WhatsApp Web has no API login, just a
  // phone-scanned QR code, unlike LinkedIn's username/password form).
  const [qrVisible, setQrVisible] = useState(false);

  const startLoginMutation = useMutation({
    mutationFn: startWhatsAppLogin,
    onSuccess: () => {
      setQrVisible(true);
      loginStatusQuery.refetch();
    },
  });

  const loginStatusQuery = useQuery({
    queryKey: ["whatsapp-login-status"],
    queryFn: getWhatsAppLoginStatus,
    // Stops polling itself once logged in — the QR/status JSX below
    // already hides based on isWhatsAppLoggedIn, so no separate "reset
    // qrVisible" effect is needed.
    refetchInterval: (query) => (qrVisible && !query.state.data?.logged_in ? 3000 : false),
  });

  const isWhatsAppLoggedIn = loginStatusQuery.data?.logged_in ?? false;

  const [newChatUrl, setNewChatUrl] = useState("");
  const [newChatLabel, setNewChatLabel] = useState("");
  const [newChatType, setNewChatType] = useState<"channel" | "group">("channel");
  const [chatScanMessage, setChatScanMessage] = useState<string | null>(null);
  const [chatScanQueue, setChatScanQueue] = useState<number[]>([]);
  const [deleteChatId, setDeleteChatId] = useState<number | null>(null);
  const chatControllerRef = useRef<AbortController | null>(null);

  const chatsQuery = useQuery({
    queryKey: ["whatsapp-chats"],
    queryFn: listChats,
  });

  const schedulerHistoryQuery = useQuery({
    queryKey: ["scheduler-history"],
    queryFn: listSchedulerHistory,
  });

  const chatScanMutation = useMutation({
    mutationFn: (id: number) => {
      const controller = new AbortController();
      chatControllerRef.current = controller;
      return scanChatNow(id, controller.signal);
    },
    onSuccess: (result) => {
      setChatScanMessage(
        t("jobSearch", "foundMessagesSaved")
          .replace("{scanned}", String(result.scanned))
          .replace("{saved}", String(result.saved)),
      );
      queryClient.invalidateQueries({ queryKey: ["whatsapp-chats"] });
      queryClient.invalidateQueries({ queryKey: ["search-jobs"] });
    },
    onError: (error) => {
      setChatScanMessage(
        axios.isCancel(error)
          ? t("jobSearch", "scanCancelled")
          : (getApiErrorMessage(error) ?? t("jobSearch", "scanError")),
      );
    },
    onSettled: () => {
      chatControllerRef.current = null;
      setChatScanQueue((queue) => {
        const [next, ...rest] = queue;
        if (next !== undefined) chatScanMutation.mutate(next);
        return rest;
      });
    },
  });

  function queueChatScan(chatId: number) {
    if (!chatScanMutation.isPending) {
      chatScanMutation.mutate(chatId);
    } else {
      setChatScanQueue((queue) => (queue.includes(chatId) ? queue : [...queue, chatId]));
    }
  }

  function scanAllChats() {
    for (const chat of chatsQuery.data ?? []) {
      queueChatScan(chat.id);
    }
  }

  function cancelChatScan() {
    chatControllerRef.current?.abort();
    setChatScanQueue([]);
  }

  // Same 200s estimate as the feed/hashtag scans on the LinkedIn tab —
  // same scroll-and-extract shape.
  const chatScanProgress = useEstimatedProgress(chatScanMutation.isPending, 200000);

  const addChatMutation = useMutation({
    mutationFn: addChat,
    onSuccess: (chat) => {
      setNewChatUrl("");
      setNewChatLabel("");
      queryClient.invalidateQueries({ queryKey: ["whatsapp-chats"] });
      queueChatScan(chat.id);
    },
  });

  const toggleChatMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) => setChatEnabled(id, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["whatsapp-chats"] }),
  });

  const removeChatMutation = useMutation({
    mutationFn: removeChat,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["whatsapp-chats"] }),
  });

  return (
    <div className="relative flex flex-col gap-6 overflow-hidden">
      <PageGlow />
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <MessageCircle className="size-6 text-teal-400" />
        {t("discoveredJobs", "tabWhatsapp")}
      </h1>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <MessageCircle className="size-4 text-green-500" />
              {t("jobSearch", "whatsappSearchTitle")}
            </CardTitle>
            {chatsQuery.data && chatsQuery.data.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5"
                onClick={scanAllChats}
                disabled={chatScanMutation.isPending || chatScanQueue.length > 0}
              >
                <ListChecks className="size-4" />
                {t("jobSearch", "scanAllChats")}
              </Button>
            )}
          </div>
          <p className="text-xs text-muted-foreground">{t("jobSearch", "whatsappSearchHint")}</p>
          <LastAutomatedScan
            history={schedulerHistoryQuery.data}
            providers={["scheduler:whatsapp-chats"]}
            isPending={schedulerHistoryQuery.isPending}
          />
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-col gap-2 rounded-md border p-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <QrCode className="size-4 text-green-500" />
              {t("jobSearch", "whatsappLoginTitle")}
            </div>
            <p className="text-xs text-muted-foreground">{t("jobSearch", "whatsappLoginHint")}</p>
            <div className="flex flex-wrap items-center gap-3">
              <Button
                variant="secondary"
                size="sm"
                className="self-start"
                disabled={startLoginMutation.isPending}
                onClick={() => startLoginMutation.mutate()}
              >
                {t("jobSearch", "whatsappLoginButton")}
              </Button>
              {isWhatsAppLoggedIn ? (
                <span className="text-sm text-primary">{t("jobSearch", "whatsappLoggedIn")}</span>
              ) : (
                loginStatusQuery.data && (
                  <span className="text-sm text-muted-foreground">
                    {t("jobSearch", "whatsappNotLoggedIn")}
                  </span>
                )
              )}
            </div>
            {qrVisible && !isWhatsAppLoggedIn && (
              <div className="flex flex-col items-start gap-2 pt-2">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={qrImageUrl()}
                  alt="WhatsApp QR code"
                  className="h-80 w-80 rounded-md border bg-white p-3"
                />
                <p className="text-xs text-muted-foreground">
                  {t("jobSearch", "whatsappLoginChecking")}
                </p>
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-2">
            <Input
              placeholder={t("jobSearch", "whatsappChatUrlPlaceholder")}
              value={newChatUrl}
              onChange={(e) => setNewChatUrl(e.target.value)}
              className="max-w-sm"
            />
            <Input
              placeholder={t("jobSearch", "whatsappLabelPlaceholder")}
              value={newChatLabel}
              onChange={(e) => setNewChatLabel(e.target.value)}
              className="max-w-xs"
            />
            <Select
              value={newChatType}
              onValueChange={(value) => setNewChatType((value as "channel" | "group") ?? "channel")}
            >
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="channel">{t("jobSearch", "whatsappChatTypeChannel")}</SelectItem>
                <SelectItem value="group">{t("jobSearch", "whatsappChatTypeGroup")}</SelectItem>
              </SelectContent>
            </Select>
            <Button
              disabled={!newChatUrl.trim() || !newChatLabel.trim() || addChatMutation.isPending}
              onClick={() =>
                addChatMutation.mutate({
                  chatUrl: newChatUrl.trim(),
                  label: newChatLabel.trim(),
                  chatType: newChatType,
                })
              }
            >
              {addChatMutation.isPending
                ? t("jobSearch", "addingAndScanning")
                : t("jobSearch", "addWhatsAppChat")}
            </Button>
          </div>

          {chatsQuery.isPending ? (
            <Skeleton className="h-20 w-full" />
          ) : chatsQuery.data && chatsQuery.data.length > 0 ? (
            <div className="flex flex-col gap-2">
              {chatsQuery.data.map((chat) => (
                <div
                  key={chat.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3"
                >
                  <div className="flex flex-col">
                    <a
                      href={chat.chat_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm underline"
                    >
                      {chat.label}
                    </a>
                    <span className="text-xs text-muted-foreground">
                      {chat.last_checked_at
                        ? t("jobSearch", "lastCheckedLabel").replace(
                            "{date}",
                            new Date(chat.last_checked_at).toLocaleString(dateLocale),
                          )
                        : t("jobSearch", "neverChecked")}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={chat.enabled}
                      onCheckedChange={(checked) =>
                        toggleChatMutation.mutate({ id: chat.id, enabled: checked })
                      }
                      disabled={toggleChatMutation.isPending}
                    />
                    <Button variant="outline" size="sm" onClick={() => queueChatScan(chat.id)}>
                      {chatScanMutation.isPending && chatScanMutation.variables === chat.id
                        ? t("jobSearch", "scanning")
                        : chatScanQueue.includes(chat.id)
                          ? t("jobSearch", "waiting")
                          : t("jobSearch", "scanNow")}
                    </Button>
                    {chatScanMutation.isPending && chatScanMutation.variables === chat.id && (
                      <>
                        <EstimatedProgressBar percent={chatScanProgress} />
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={cancelChatScan}
                          aria-label={t("jobSearch", "cancelScan")}
                        >
                          <XCircle className="size-4" />
                        </Button>
                      </>
                    )}
                    <Button variant="ghost" size="icon" onClick={() => setDeleteChatId(chat.id)}>
                      <Trash2 className="size-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t("jobSearch", "noChatsYet")}</p>
          )}
          {chatScanMessage && <p className="text-sm text-primary">{chatScanMessage}</p>}
        </CardContent>
      </Card>

      <ConfirmDialog
        open={deleteChatId !== null}
        onOpenChange={(open) => !open && setDeleteChatId(null)}
        isPending={removeChatMutation.isPending}
        onConfirm={() => {
          if (deleteChatId !== null) removeChatMutation.mutate(deleteChatId);
          setDeleteChatId(null);
        }}
      />
    </div>
  );
}
