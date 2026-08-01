"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Bot } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { generateAIResponse } from "@/lib/ai-api";
import { getResumeText } from "@/lib/resume-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const QUICK_PROMPTS = [
  "قيّم السيرة الذاتية بتاعتي",
  "اديني نصايح لتطوير مسيرتي المهنية",
  "جهزني لأسئلة المقابلة الشخصية",
];

export default function AIAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: resumeText } = useQuery({
    queryKey: ["resume-text"],
    queryFn: getResumeText,
  });

  const mutation = useMutation({
    mutationFn: generateAIResponse,
    onSuccess: (data) => {
      setMessages((prev) => [...prev, { role: "assistant", content: data.content }]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "حصل خطأ، جرب تاني." },
      ]);
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function send(prompt: string) {
    if (!prompt.trim() || mutation.isPending) return;
    setMessages((prev) => [...prev, { role: "user", content: prompt }]);
    setInput("");
    const fullPrompt = resumeText
      ? `سيرتي الذاتية:\n\n${resumeText}\n\n---\n\n${prompt}`
      : prompt;
    mutation.mutate(fullPrompt);
  }

  return (
    <div className="flex h-full max-w-2xl flex-col gap-4">
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <Bot className="size-6 text-primary" />
        المساعد الذكي
      </h1>

      {resumeText ? (
        <Badge variant="secondary" className="w-fit text-xs">
          شايف سيرتك الذاتية المرفوعة
        </Badge>
      ) : (
        <Badge variant="outline" className="w-fit text-xs">
          لسه مرفعتليش سيرة ذاتية — ارفعها من صفحة السيرة الذاتية علشان أقدر أقيّمها
        </Badge>
      )}

      {messages.length === 0 && (
        <div className="flex flex-wrap gap-2">
          {QUICK_PROMPTS.map((prompt) => (
            <Button key={prompt} variant="outline" size="sm" onClick={() => send(prompt)}>
              {prompt}
            </Button>
          ))}
        </div>
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
          <div className="self-start rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">
            جاري الكتابة...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="flex gap-2"
      >
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send(input);
            }
          }}
          placeholder="اكتب سؤالك..."
          rows={2}
          className="flex-1"
        />
        <Button type="submit" disabled={mutation.isPending}>
          إرسال
        </Button>
      </form>
    </div>
  );
}
