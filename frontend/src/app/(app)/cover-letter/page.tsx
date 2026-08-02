"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle2, Mail, TriangleAlert } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import {
  generateCoverLetter,
  reviewCoverLetter,
} from "@/lib/cover-letter-api";
import { getResumeText } from "@/lib/resume-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

export default function CoverLetterPage() {
  const [job, setJob] = useState("");
  const [letterText, setLetterText] = useState("");

  const { data: resumeText, isPending: resumePending } = useQuery({
    queryKey: ["resume-text"],
    queryFn: getResumeText,
  });

  const generateMutation = useMutation({
    mutationFn: generateCoverLetter,
    onSuccess: (data) => setLetterText(data.generated_cover_letter),
  });

  const reviewMutation = useMutation({
    mutationFn: reviewCoverLetter,
  });

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <Mail className="size-6 text-cyan-400" />
        خطاب التقديم
      </h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">إنشاء خطاب جديد</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {resumePending ? null : resumeText ? (
            <div className="flex items-center gap-2 rounded-md border border-primary/30 bg-primary/5 px-3 py-2 text-sm text-primary">
              <CheckCircle2 className="size-4 shrink-0" />
              هنستخدم سيرتك الذاتية المرفوعة تلقائيًا
            </div>
          ) : (
            <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
              <TriangleAlert className="size-4 shrink-0" />
              لسه مفيش سيرة ذاتية مرفوعة —{" "}
              <Link href="/resume" className="underline">
                ارفعها الأول
              </Link>
            </div>
          )}
          <div>
            <label className="mb-1 block text-sm text-muted-foreground">
              وصف الوظيفة
            </label>
            <Textarea
              value={job}
              onChange={(e) => setJob(e.target.value)}
              rows={5}
              placeholder="الصق وصف الوظيفة هنا..."
            />
          </div>
          <Button
            onClick={() => generateMutation.mutate({ resume: resumeText ?? "", job })}
            disabled={!resumeText || !job.trim() || generateMutation.isPending}
            className="self-start"
          >
            {generateMutation.isPending ? "جاري الإنشاء..." : "إنشاء خطاب"}
          </Button>

          {generateMutation.data && (
            <div className="mt-2 flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">نسبة التطابق:</span>
                <Badge>{generateMutation.data.score}%</Badge>
              </div>
              {generateMutation.data.matched_skills.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {generateMutation.data.matched_skills.map((skill) => (
                    <Badge key={skill} variant="secondary">
                      {skill}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {letterText && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">الخطاب الناتج</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <Textarea
              value={letterText}
              onChange={(e) => setLetterText(e.target.value)}
              rows={10}
            />
            <Button
              variant="secondary"
              onClick={() => reviewMutation.mutate(letterText)}
              disabled={reviewMutation.isPending}
              className="self-start"
            >
              {reviewMutation.isPending ? "جاري المراجعة..." : "راجع الخطاب"}
            </Button>

            {reviewMutation.data && (
              <div className="flex flex-col gap-2 rounded-md border p-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">التقييم:</span>
                  <Badge>{reviewMutation.data.score}/100</Badge>
                </div>
                {reviewMutation.data.issues.length > 0 && (
                  <div>
                    <p className="text-sm font-medium">ملاحظات:</p>
                    <ul className="list-inside list-disc text-sm text-muted-foreground">
                      {reviewMutation.data.issues.map((issue) => (
                        <li key={issue}>{issue}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {reviewMutation.data.recommendations.length > 0 && (
                  <div>
                    <p className="text-sm font-medium">توصيات:</p>
                    <ul className="list-inside list-disc text-sm text-muted-foreground">
                      {reviewMutation.data.recommendations.map((rec) => (
                        <li key={rec}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
