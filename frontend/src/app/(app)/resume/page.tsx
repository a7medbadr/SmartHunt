"use client";

import { useIsMutating, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, FileText, Mail, TriangleAlert } from "lucide-react";
import { useRef, useState } from "react";

import {
  analyzeResume,
  deleteResume,
  getResume,
  getResumeText,
  uploadResume,
} from "@/lib/resume-api";
import { generateCoverLetter, reviewCoverLetter } from "@/lib/cover-letter-api";
import { AI_MUTATION_KEY } from "@/lib/ai-mutation-key";
import { PageGlow } from "@/components/page-glow";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { EstimatedProgressBar } from "@/components/ui/estimated-progress-bar";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslation } from "@/lib/i18n/language-context";
import { Textarea } from "@/components/ui/textarea";
import { useEstimatedProgress } from "@/hooks/use-estimated-progress";

function formatSize(bytes?: number) {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} bytes`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export default function ResumePage() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [skills, setSkills] = useState<string[] | null>(null);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);

  const resumeQuery = useQuery({
    queryKey: ["resume"],
    queryFn: getResume,
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      await uploadResume(file);
      if (file.name.toLowerCase().endsWith(".pdf")) {
        const analysis = await analyzeResume(file);
        setSkills(analysis.skills);
      } else {
        setSkills(null);
      }
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["resume"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteResume,
    onSuccess: () => {
      setSkills(null);
      queryClient.invalidateQueries({ queryKey: ["resume"] });
    },
  });

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
  }

  // Cover letter — merged into this page since both work off the same
  // uploaded resume and were previously split across two mostly-empty tabs.
  const [job, setJob] = useState("");
  const [letterText, setLetterText] = useState("");

  const { data: resumeText, isPending: resumeTextPending } = useQuery({
    queryKey: ["resume-text"],
    queryFn: getResumeText,
  });

  // The backend can only run one AI generation at a time — see
  // ai-mutation-key.ts.
  const aiBusyElsewhere = useIsMutating({ mutationKey: AI_MUTATION_KEY }) > 0;

  const generateMutation = useMutation({
    mutationKey: AI_MUTATION_KEY,
    mutationFn: generateCoverLetter,
    onSuccess: (data) => setLetterText(data.generated_cover_letter),
  });
  const generateProgress = useEstimatedProgress(generateMutation.isPending, 200000);

  const reviewMutation = useMutation({
    mutationKey: AI_MUTATION_KEY,
    mutationFn: reviewCoverLetter,
  });

  return (
    <div className="relative flex max-w-3xl flex-col gap-6 overflow-hidden">
      <PageGlow />
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <FileText className="size-6 text-violet-400" />
        {t("pageTitles", "resume")}
      </h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("resume", "currentFile")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {resumeQuery.isPending ? (
            <Skeleton className="h-10 w-full" />
          ) : resumeQuery.data?.uploaded ? (
            <div className="flex items-center justify-between rounded-md border p-3">
              <div>
                <p className="font-medium">{resumeQuery.data.filename}</p>
                <p className="text-sm text-muted-foreground">
                  {formatSize(resumeQuery.data.size)}
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setConfirmDeleteOpen(true)}
                disabled={deleteMutation.isPending}
              >
                {t("common", "delete")}
              </Button>
              <ConfirmDialog
                open={confirmDeleteOpen}
                onOpenChange={setConfirmDeleteOpen}
                isPending={deleteMutation.isPending}
                onConfirm={() => {
                  deleteMutation.mutate();
                  setConfirmDeleteOpen(false);
                }}
              />
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              {t("resume", "noResumeUploaded")}
            </p>
          )}

          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx"
              className="hidden"
              onChange={handleFileChange}
            />
            <Button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadMutation.isPending}
            >
              {uploadMutation.isPending
                ? t("resume", "uploading")
                : resumeQuery.data?.uploaded
                  ? t("resume", "replaceFile")
                  : t("resume", "uploadResume")}
            </Button>
          </div>

          {uploadMutation.isError && (
            <p className="text-sm text-destructive">
              {t("resume", "uploadError")}
            </p>
          )}
        </CardContent>
      </Card>

      {skills && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("resume", "extractedSkills")}</CardTitle>
          </CardHeader>
          <CardContent>
            {skills.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {skills.map((skill) => (
                  <Badge key={skill} variant="secondary">
                    {skill}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                {t("resume", "noSkillsExtracted")}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      <h2 className="flex items-center gap-2 text-xl font-semibold">
        <Mail className="size-5 text-cyan-400" />
        {t("resume", "coverLetter")}
      </h2>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("resume", "createNewLetter")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {resumeTextPending ? null : resumeText ? (
            <div className="flex items-center gap-2 rounded-md border border-primary/30 bg-primary/5 px-3 py-2 text-sm text-primary">
              <CheckCircle2 className="size-4 shrink-0" />
              {t("resume", "willUseResume")}
            </div>
          ) : (
            <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
              <TriangleAlert className="size-4 shrink-0" />
              {t("resume", "uploadResumeFirst")}
            </div>
          )}
          <div>
            <label className="mb-1 block text-sm text-muted-foreground">
              {t("resume", "jobDescription")}
            </label>
            <Textarea
              value={job}
              onChange={(e) => setJob(e.target.value)}
              rows={5}
              placeholder={t("resume", "jobDescriptionPlaceholder")}
            />
          </div>
          <div className="flex items-center gap-3">
            <Button
              onClick={() => generateMutation.mutate({ resume: resumeText ?? "", job })}
              disabled={
                !resumeText || !job.trim() || generateMutation.isPending || aiBusyElsewhere
              }
              className="self-start"
            >
              {generateMutation.isPending ? t("resume", "generating") : t("resume", "generateLetter")}
            </Button>
            {generateMutation.isPending && (
              <EstimatedProgressBar percent={generateProgress} />
            )}
          </div>

          {aiBusyElsewhere && !generateMutation.isPending && (
            <p className="text-xs text-muted-foreground">
              {t("resume", "aiBusyElsewhere")}
            </p>
          )}

          {generateMutation.isError && (
            <p className="text-sm text-destructive">
              {t("resume", "generateError")}
            </p>
          )}

          {generateMutation.data && (
            <div className="mt-2 flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">{t("resume", "matchScore")}</span>
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
            <CardTitle className="text-base">{t("resume", "resultingLetter")}</CardTitle>
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
              disabled={reviewMutation.isPending || aiBusyElsewhere}
              className="self-start"
            >
              {reviewMutation.isPending ? t("resume", "reviewing") : t("resume", "reviewLetter")}
            </Button>

            {reviewMutation.isError && (
              <p className="text-sm text-destructive">{t("resume", "genericError")}</p>
            )}

            {reviewMutation.data && (
              <div className="flex flex-col gap-2 rounded-md border p-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">{t("resume", "evaluation")}</span>
                  <Badge>{reviewMutation.data.score}/100</Badge>
                </div>
                {reviewMutation.data.issues.length > 0 && (
                  <div>
                    <p className="text-sm font-medium">{t("resume", "notes")}</p>
                    <ul className="list-inside list-disc text-sm text-muted-foreground">
                      {reviewMutation.data.issues.map((issue) => (
                        <li key={issue}>{issue}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {reviewMutation.data.recommendations.length > 0 && (
                  <div>
                    <p className="text-sm font-medium">{t("resume", "recommendations")}</p>
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
