"use client";

import { useIsMutating, useMutation, useQuery } from "@tanstack/react-query";
import { Bot } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { generateAIResponse, truncateResumeForAI } from "@/lib/ai-api";
import { AI_MUTATION_KEY } from "@/lib/ai-mutation-key";
import { getResumeText } from "@/lib/resume-api";
import { PageGlow } from "@/components/page-glow";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EstimatedProgressBar } from "@/components/ui/estimated-progress-bar";
import { Textarea } from "@/components/ui/textarea";
import { useEstimatedProgress } from "@/hooks/use-estimated-progress";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n/language-context";

interface Message {
  role: "user" | "assistant";
  content: string;
}

// A bare "evaluate my resume" + raw resume text gave the small local
// model too little structure — it would go off-topic instead of
// evaluating. Mirrors the structured-template approach that already
// works for deep job analysis (matching/services/deep_analysis.py).
function buildResumeEvaluationPrompt(template: string, resumeText: string): string {
  return `${template}${resumeText}`;
}

export default function AIAssistantPage() {
  const { t, locale } = useTranslation();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: resumeText } = useQuery({
    queryKey: ["resume-text"],
    queryFn: getResumeText,
  });

  const evaluateResumePrompt = t("aiAssistant", "quickPromptEvaluate");
  const quickPrompts = [
    evaluateResumePrompt,
    t("aiAssistant", "quickPromptCareerAdvice"),
    t("aiAssistant", "quickPromptInterviewPrep"),
  ];

  // The backend can only run one AI generation at a time — see
  // ai-mutation-key.ts.
  const aiBusyElsewhere = useIsMutating({ mutationKey: AI_MUTATION_KEY }) > 0;

  const mutation = useMutation({
    mutationKey: AI_MUTATION_KEY,
    mutationFn: ({ prompt, maxTokens }: { prompt: string; maxTokens?: number }) =>
      generateAIResponse(prompt, maxTokens),
    onSuccess: (data) => {
      // The real AI provider can fail/time out and silently fall back
      // to a "local" stub that just echoes the prompt back — a 200
      // response, but not a real answer. Treat that the same as an
      // error instead of showing the raw echoed prompt as if it were
      // a reply.
      const content =
        data.provider === "local"
          ? t("aiAssistant", "providerLocalFallback")
          : data.content;
      setMessages((prev) => [...prev, { role: "assistant", content }]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: t("aiAssistant", "genericError") },
      ]);
    },
  });
  const chatProgress = useEstimatedProgress(mutation.isPending, 200000);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function send(prompt: string) {
    if (!prompt.trim() || mutation.isPending || aiBusyElsewhere) return;
    setMessages((prev) => [...prev, { role: "user", content: prompt }]);
    setInput("");

    let fullPrompt: string;
    let maxTokens: number | undefined;
    if (prompt === evaluateResumePrompt && resumeText) {
      fullPrompt = buildResumeEvaluationPrompt(
        t("aiAssistant", "resumeEvaluationTemplate"),
        truncateResumeForAI(resumeText, locale),
      );
      maxTokens = 400;
    } else if (resumeText) {
      fullPrompt = `${t("aiAssistant", "resumePrefixLabel")}:\n\n${truncateResumeForAI(resumeText, locale)}\n\n---\n\n${prompt}`;
    } else {
      fullPrompt = prompt;
    }

    mutation.mutate({ prompt: fullPrompt, maxTokens });
  }

  return (
    <div className="relative flex h-full max-w-2xl flex-col gap-4 overflow-hidden">
      <PageGlow />
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <Bot className="size-6 text-fuchsia-400" />
        {t("pageTitles", "aiAssistant")}
      </h1>

      {resumeText ? (
        <Badge variant="secondary" className="w-fit text-xs">
          {t("aiAssistant", "resumeAttached")}
        </Badge>
      ) : (
        <Badge variant="outline" className="w-fit text-xs">
          {t("aiAssistant", "noResumeUploaded")}
        </Badge>
      )}

      {messages.length === 0 && (
        <div className="flex flex-wrap gap-2">
          {quickPrompts.map((prompt) => (
            <Button
              key={prompt}
              variant="outline"
              size="sm"
              disabled={aiBusyElsewhere}
              onClick={() => send(prompt)}
            >
              {prompt}
            </Button>
          ))}
        </div>
      )}

      {aiBusyElsewhere && !mutation.isPending && (
        <p className="text-xs text-muted-foreground">
          {t("aiAssistant", "aiBusyElsewhere")}
        </p>
      )}

      <div className="flex flex-1 flex-col gap-3 overflow-y-auto rounded-md border p-4">
        {messages.map((message, i) => (
          <div
            key={i}
            className={cn(
              "max-w-[80%] rounded-lg px-3 py-2 text-sm",
              message.role === "user"
                ? "self-end bg-primary text-primary-foreground"
                : "self-start bg-muted",
            )}
          >
            {message.content}
          </div>
        ))}
        {mutation.isPending && (
          <div className="flex flex-col gap-2 self-start rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">
            {t("aiAssistant", "typing")}
            <EstimatedProgressBar percent={chatProgress} />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send(input);
            }
          }}
          placeholder={t("aiAssistant", "inputPlaceholder")}
          rows={2}
          className="flex-1"
        />
        <Button
          type="button"
          onClick={() => send(input)}
          disabled={mutation.isPending || aiBusyElsewhere}
        >
          {t("aiAssistant", "send")}
        </Button>
      </div>
    </div>
  );
}
