"use client";

import { useIsMutating, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Mail } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";

import { draftReply, getEmailThread, sendReply } from "@/lib/email-apply-api";
import { AI_MUTATION_KEY } from "@/lib/ai-mutation-key";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EstimatedProgressBar } from "@/components/ui/estimated-progress-bar";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useEstimatedProgress } from "@/hooks/use-estimated-progress";
import { useTranslation } from "@/lib/i18n/language-context";
import { cn } from "@/lib/utils";

export default function ApplicationThreadPage() {
  const params = useParams<{ id: string }>();
  const applicationId = params.id;
  const queryClient = useQueryClient();
  const { t, locale } = useTranslation();

  const [replyBody, setReplyBody] = useState("");

  const threadQuery = useQuery({
    queryKey: ["email-thread", applicationId],
    queryFn: () => getEmailThread(applicationId),
  });

  const aiBusyElsewhere = useIsMutating({ mutationKey: AI_MUTATION_KEY }) > 0;

  const draftReplyMutation = useMutation({
    mutationKey: AI_MUTATION_KEY,
    mutationFn: () => draftReply(applicationId),
    onSuccess: (data) => setReplyBody(data.body),
  });
  const draftReplyProgress = useEstimatedProgress(draftReplyMutation.isPending, 150000);

  const sendReplyMutation = useMutation({
    mutationFn: () => sendReply(applicationId, replyBody),
    onSuccess: () => {
      setReplyBody("");
      queryClient.invalidateQueries({ queryKey: ["email-thread", applicationId] });
    },
  });

  const hasInboundMessage = threadQuery.data?.some((m) => m.direction === "inbound");
  const dateLocale = locale === "ar" ? "ar-SA" : "en-US";

  return (
    <div className="flex max-w-2xl flex-col gap-6">
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <Mail className="size-6 text-orange-400" />
        {t("applicationDetail", "title")}
      </h1>

      {threadQuery.isPending ? (
        <Skeleton className="h-40 w-full" />
      ) : threadQuery.isError ? (
        <p className="text-sm text-destructive">{t("applicationDetail", "loadError")}</p>
      ) : threadQuery.data && threadQuery.data.length > 0 ? (
        <div className="flex flex-col gap-3">
          {threadQuery.data.map((message) => (
            <Card
              key={message.id}
              className={cn(message.direction === "outbound" && "border-primary/30")}
            >
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-sm font-normal text-muted-foreground">
                  <span>
                    {message.direction === "outbound"
                      ? t("applicationDetail", "outbound")
                      : t("applicationDetail", "inbound")}{" "}
                    —{" "}
                    {message.direction === "outbound" ? message.to_address : message.from_address}
                  </span>
                  <span>{new Date(message.created_at).toLocaleString(dateLocale)}</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                <p className="font-medium">{message.subject}</p>
                <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                  {message.body}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          {t("applicationDetail", "noThreadYet")}
        </p>
      )}

      {hasInboundMessage && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("applicationDetail", "replyToLastMessage")}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={() => draftReplyMutation.mutate()}
                disabled={draftReplyMutation.isPending || aiBusyElsewhere}
                className="self-start"
              >
                {draftReplyMutation.isPending
                  ? t("applicationDetail", "preparing")
                  : t("applicationDetail", "prepareReply")}
              </Button>
              {draftReplyMutation.isPending && (
                <EstimatedProgressBar percent={draftReplyProgress} />
              )}
            </div>

            {aiBusyElsewhere && !draftReplyMutation.isPending && (
              <p className="text-xs text-muted-foreground">
                {t("applicationDetail", "aiBusyElsewhere")}
              </p>
            )}

            {draftReplyMutation.isError && (
              <p className="text-sm text-destructive">{t("applicationDetail", "genericError")}</p>
            )}

            <Textarea
              value={replyBody}
              onChange={(e) => setReplyBody(e.target.value)}
              rows={6}
              placeholder={t("applicationDetail", "replyPlaceholder")}
            />

            <Button
              onClick={() => sendReplyMutation.mutate()}
              disabled={!replyBody.trim() || sendReplyMutation.isPending}
              className="self-start"
            >
              {sendReplyMutation.isPending
                ? t("applicationDetail", "sending")
                : t("applicationDetail", "sendReply")}
            </Button>

            {sendReplyMutation.isError && (
              <p className="text-sm text-destructive">{t("applicationDetail", "sendError")}</p>
            )}
            {sendReplyMutation.isSuccess && (
              <p className="text-sm text-primary">{t("applicationDetail", "replySent")}</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
