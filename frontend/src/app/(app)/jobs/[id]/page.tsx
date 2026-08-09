"use client";

import { useIsMutating, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Mail, MessageCircleQuestion, Sparkles, Star } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import {
  addFavorite,
  addJobTag,
  createJobNote,
  deleteJobNote,
  deleteJobTag,
  getJob,
  listFavorites,
  listJobNotes,
  listJobTags,
  removeFavorite,
} from "@/lib/jobs-api";
import { deepAnalyzeJob } from "@/lib/matching-api";
import { generateInterviewPrep } from "@/lib/ai-api";
import { AI_MUTATION_KEY } from "@/lib/ai-mutation-key";
import { draftApplicationEmail, sendApplicationEmail } from "@/lib/email-apply-api";
import {
  generateTailoredResumeForJob,
  getResumeText,
  getTailoredResumeForJob,
} from "@/lib/resume-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { EstimatedProgressBar } from "@/components/ui/estimated-progress-bar";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useEstimatedProgress } from "@/hooks/use-estimated-progress";
import { useTranslation } from "@/lib/i18n/language-context";

const EMAIL_PATTERN = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;

function AnalysisMarkdown({ text }: { text: string }) {
  const lines = text.split("\n").filter((l) => l.trim().length > 0);
  return (
    <div className="flex flex-col gap-1.5 text-sm">
      {lines.map((line, i) => {
        const trimmed = line.trim();
        if (trimmed.startsWith("## ")) {
          return (
            <h4 key={i} className="mt-2 font-semibold first:mt-0">
              {trimmed.slice(3)}
            </h4>
          );
        }
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          return (
            <p key={i} className="text-muted-foreground">
              • {trimmed.slice(2)}
            </p>
          );
        }
        return (
          <p key={i} className="text-muted-foreground">
            {trimmed}
          </p>
        );
      })}
    </div>
  );
}

export default function JobDetailsPage() {
  const params = useParams<{ id: string }>();
  const jobId = Number(params.id);
  const queryClient = useQueryClient();
  const { t, locale } = useTranslation();
  const [deleteNoteId, setDeleteNoteId] = useState<number | null>(null);
  const [deleteTagId, setDeleteTagId] = useState<number | null>(null);

  const jobQuery = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJob(jobId),
  });

  const favoritesQuery = useQuery({
    queryKey: ["favorites"],
    queryFn: listFavorites,
  });

  const notesQuery = useQuery({
    queryKey: ["job-notes", jobId],
    queryFn: () => listJobNotes(jobId),
  });

  const tagsQuery = useQuery({
    queryKey: ["job-tags", jobId],
    queryFn: () => listJobTags(jobId),
  });

  const isFavorite = favoritesQuery.data?.some((f) => f.job_id === jobId) ?? false;

  const toggleFavorite = useMutation({
    mutationFn: async () => {
      if (isFavorite) {
        await removeFavorite(jobId);
      } else {
        await addFavorite(jobId);
      }
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["favorites"] }),
  });

  const resumeQuery = useQuery({
    queryKey: ["resume-text"],
    queryFn: getResumeText,
  });
  const resumeText = resumeQuery.data ?? "";

  function jobText() {
    return [jobQuery.data?.title, jobQuery.data?.description, jobQuery.data?.requirements]
      .filter(Boolean)
      .join("\n");
  }

  // The backend can only run one AI generation at a time (see
  // ai-mutation-key.ts) — every AI-triggering mutation on this page
  // shares the same mutationKey so they can't pile up behind each other.
  const aiBusyElsewhere = useIsMutating({ mutationKey: AI_MUTATION_KEY }) > 0;

  const analyzeMutation = useMutation({
    mutationKey: AI_MUTATION_KEY,
    mutationFn: () => deepAnalyzeJob(resumeText, jobText()),
  });
  const analyzeProgress = useEstimatedProgress(analyzeMutation.isPending, 150000);

  const interviewPrepMutation = useMutation({
    mutationKey: AI_MUTATION_KEY,
    mutationFn: () => generateInterviewPrep(resumeText, jobText(), locale),
  });
  const interviewPrepProgress = useEstimatedProgress(interviewPrepMutation.isPending, 150000);

  const tailoredResumeQuery = useQuery({
    queryKey: ["tailored-resume", jobId],
    queryFn: () => getTailoredResumeForJob(jobId),
  });

  const tailorResumeMutation = useMutation({
    mutationKey: AI_MUTATION_KEY,
    mutationFn: () => generateTailoredResumeForJob(jobId),
    onSuccess: (data) => {
      queryClient.setQueryData(["tailored-resume", jobId], data);
    },
  });
  const tailorResumeProgress = useEstimatedProgress(tailorResumeMutation.isPending, 150000);

  const jobHasEmail = EMAIL_PATTERN.test(
    `${jobQuery.data?.description ?? ""} ${jobQuery.data?.requirements ?? ""}`,
  );

  const [emailDraft, setEmailDraft] = useState<{
    recipientEmail: string;
    subject: string;
    body: string;
  } | null>(null);
  const [emailSentApplicationId, setEmailSentApplicationId] = useState<string | null>(null);

  const draftEmailMutation = useMutation({
    mutationKey: AI_MUTATION_KEY,
    mutationFn: () => draftApplicationEmail(jobId),
    onSuccess: (data) => {
      setEmailDraft({
        recipientEmail: data.recipient_email,
        subject: data.subject,
        body: data.body,
      });
    },
  });
  const draftEmailProgress = useEstimatedProgress(draftEmailMutation.isPending, 150000);

  const sendEmailMutation = useMutation({
    mutationFn: () =>
      sendApplicationEmail({
        jobId,
        recipientEmail: emailDraft!.recipientEmail,
        subject: emailDraft!.subject,
        body: emailDraft!.body,
      }),
    onSuccess: (data) => {
      setEmailSentApplicationId(data.application_id);
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });

  const [noteText, setNoteText] = useState("");
  const addNote = useMutation({
    mutationFn: () => createJobNote(jobId, noteText),
    onSuccess: () => {
      setNoteText("");
      queryClient.invalidateQueries({ queryKey: ["job-notes", jobId] });
    },
  });
  const removeNote = useMutation({
    mutationFn: (noteId: number) => deleteJobNote(noteId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["job-notes", jobId] }),
  });

  const [tagText, setTagText] = useState("");
  const addTag = useMutation({
    mutationFn: () => addJobTag(jobId, tagText),
    onSuccess: () => {
      setTagText("");
      queryClient.invalidateQueries({ queryKey: ["job-tags", jobId] });
    },
  });
  const removeTag = useMutation({
    mutationFn: (tagId: number) => deleteJobTag(tagId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["job-tags", jobId] }),
  });

  if (jobQuery.isPending) {
    return <Skeleton className="h-40 w-full" />;
  }

  if (jobQuery.isError || !jobQuery.data) {
    return <p className="text-sm text-destructive">{t("jobDetail", "notFound")}</p>;
  }

  const job = jobQuery.data;

  return (
    <div className="flex max-w-2xl flex-col gap-6">
      <Card>
        <CardHeader className="flex flex-row items-start justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="text-xl">{job.title}</CardTitle>
              {job.no_sponsorship_signal && (
                <Badge variant="destructive" className="text-xs">
                  {t("jobDetail", "noSponsorship")}
                </Badge>
              )}
              {job.post_url && (
                <Badge variant="outline" className="gap-1 text-xs text-sky-400">
                  {t("jobDetail", "fromLinkedinPost")}
                </Badge>
              )}
            </div>
            <p className="text-muted-foreground">
              {job.company} · {job.location ?? "—"} · {job.source ?? "—"}
            </p>
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={() => toggleFavorite.mutate()}
            disabled={toggleFavorite.isPending}
            aria-label={t("jobDetail", "addToFavorites")}
          >
            <Star className={isFavorite ? "fill-current" : ""} />
          </Button>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {job.post_url && (
            <a
              href={job.post_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-sky-400 underline"
            >
              {t("jobDetail", "originalPostLink")}
            </a>
          )}
          {job.description && <p className="whitespace-pre-wrap">{job.description}</p>}
          {job.requirements && (
            <div>
              <h3 className="mb-1 font-medium">{t("jobDetail", "requirements")}</h3>
              <p className="whitespace-pre-wrap text-muted-foreground">
                {job.requirements}
              </p>
            </div>
          )}
          {job.url && (
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm underline"
            >
              {t("jobDetail", "originalJobLink")}
            </a>
          )}

          <div className="flex flex-wrap gap-2 pt-2">
            {tagsQuery.data?.map((tag) => (
              <Badge
                key={tag.id}
                variant="secondary"
                className="cursor-pointer"
                onClick={() => setDeleteTagId(tag.id)}
              >
                {tag.tag} ×
              </Badge>
            ))}
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (tagText.trim()) addTag.mutate();
            }}
            className="flex gap-2"
          >
            <Input
              placeholder={t("jobDetail", "addTagPlaceholder")}
              value={tagText}
              onChange={(e) => setTagText(e.target.value)}
              className="max-w-xs"
            />
            <Button type="submit" variant="secondary" disabled={addTag.isPending}>
              {t("jobDetail", "addTag")}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="size-4" />
            {t("jobDetail", "deepAiAnalysis")}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {!resumeQuery.isPending && !resumeText && (
            <p className="text-sm text-destructive">
              {t("jobDetail", "noResumeUploaded")}
            </p>
          )}
          <div className="flex items-center gap-3">
            <Button
              onClick={() => analyzeMutation.mutate()}
              disabled={!resumeText.trim() || analyzeMutation.isPending || aiBusyElsewhere}
              className="self-start"
            >
              {analyzeMutation.isPending ? t("jobDetail", "analyzing") : t("jobDetail", "startAnalysis")}
            </Button>
            {analyzeMutation.isPending && <EstimatedProgressBar percent={analyzeProgress} />}
          </div>

          {aiBusyElsewhere && !analyzeMutation.isPending && (
            <p className="text-xs text-muted-foreground">
              {t("jobDetail", "aiBusyElsewhere")}
            </p>
          )}
          {analyzeMutation.isError && (
            <p className="text-sm text-destructive">
              {t("jobDetail", "analysisFailed")}
            </p>
          )}

          {analyzeMutation.data && (
            <div className="flex flex-col gap-3 rounded-md border p-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm text-muted-foreground">{t("jobDetail", "matchScore")}</span>
                <Badge>{analyzeMutation.data.score}%</Badge>
                {analyzeMutation.data.missing_skills.map((skill) => (
                  <Badge key={skill} variant="outline">
                    {t("jobDetail", "missingSkill").replace("{skill}", skill)}
                  </Badge>
                ))}
              </div>
              {analyzeMutation.data.provider === "local" ? (
                <p className="text-sm text-muted-foreground">
                  {t("jobDetail", "aiBusyDuringAnalysis")}
                </p>
              ) : (
                <AnalysisMarkdown text={analyzeMutation.data.ai_summary} />
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <MessageCircleQuestion className="size-4" />
            {t("jobDetail", "interviewPrepTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <Button
              onClick={() => interviewPrepMutation.mutate()}
              disabled={!resumeText.trim() || interviewPrepMutation.isPending || aiBusyElsewhere}
              className="self-start"
            >
              {interviewPrepMutation.isPending
                ? t("jobDetail", "preparing")
                : t("jobDetail", "prepareInterviewQuestions")}
            </Button>
            {interviewPrepMutation.isPending && (
              <EstimatedProgressBar percent={interviewPrepProgress} />
            )}
          </div>

          {aiBusyElsewhere && !interviewPrepMutation.isPending && (
            <p className="text-xs text-muted-foreground">
              {t("jobDetail", "aiBusyElsewhere")}
            </p>
          )}
          {interviewPrepMutation.isError && (
            <p className="text-sm text-destructive">
              {t("jobDetail", "genericError")}
            </p>
          )}

          {interviewPrepMutation.data && (
            <div className="rounded-md border p-3">
              <AnalysisMarkdown text={interviewPrepMutation.data.content} />
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="size-4 text-violet-400" />
            {t("jobDetail", "tailoredResumeTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p className="text-sm text-muted-foreground">
            {t("jobDetail", "tailoredResumeBody")}
          </p>

          <div className="flex items-center gap-3">
            <Button
              onClick={() => tailorResumeMutation.mutate()}
              disabled={!resumeText.trim() || tailorResumeMutation.isPending || aiBusyElsewhere}
              className="self-start"
            >
              {tailorResumeMutation.isPending
                ? t("jobDetail", "generating")
                : tailoredResumeQuery.data
                  ? t("jobDetail", "regenerate")
                  : t("jobDetail", "generateTailoredResume")}
            </Button>
            {tailorResumeMutation.isPending && (
              <EstimatedProgressBar percent={tailorResumeProgress} />
            )}
          </div>

          {aiBusyElsewhere && !tailorResumeMutation.isPending && (
            <p className="text-xs text-muted-foreground">
              {t("jobDetail", "aiBusyElsewhere")}
            </p>
          )}
          {tailorResumeMutation.isError && (
            <p className="text-sm text-destructive">{t("jobDetail", "simpleError")}</p>
          )}

          {(tailorResumeMutation.data ?? tailoredResumeQuery.data) && (
            <div className="flex flex-col gap-3 rounded-md border p-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm text-muted-foreground">{t("jobDetail", "matchScore")}</span>
                <Badge>{(tailorResumeMutation.data ?? tailoredResumeQuery.data)?.score}%</Badge>
                {(tailorResumeMutation.data ?? tailoredResumeQuery.data)?.missing_skills.map(
                  (skill) => (
                    <Badge key={skill} variant="outline">
                      {t("jobDetail", "missingSkill").replace("{skill}", skill)}
                    </Badge>
                  ),
                )}
              </div>
              <p className="text-sm font-medium">{t("jobDetail", "addedSummary")}</p>
              <p className="text-sm text-muted-foreground">
                {(tailorResumeMutation.data ?? tailoredResumeQuery.data)?.summary}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {jobHasEmail && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Mail className="size-4 text-cyan-400" />
              {t("jobDetail", "emailApplyTitle")}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <p className="text-sm text-muted-foreground">
              {t("jobDetail", "emailApplyBody")}
            </p>

            {emailSentApplicationId ? (
              <p className="text-sm text-primary">
                {t("jobDetail", "emailSentMessage")}{" "}
                <Link href="/applications" className="underline">
                  {t("jobDetail", "viewInApplications")}
                </Link>
                .
              </p>
            ) : (
              <>
                <div className="flex items-center gap-3">
                  <Button
                    onClick={() => draftEmailMutation.mutate()}
                    disabled={!resumeText.trim() || draftEmailMutation.isPending || aiBusyElsewhere}
                    className="self-start"
                  >
                    {draftEmailMutation.isPending
                      ? t("jobDetail", "preparing")
                      : t("jobDetail", "prepareEmail")}
                  </Button>
                  {draftEmailMutation.isPending && (
                    <EstimatedProgressBar percent={draftEmailProgress} />
                  )}
                </div>

          {aiBusyElsewhere && !draftEmailMutation.isPending && (
            <p className="text-xs text-muted-foreground">
              {t("jobDetail", "aiBusyElsewhere")}
            </p>
          )}
                {draftEmailMutation.isError && (
                  <p className="text-sm text-destructive">{t("jobDetail", "simpleError")}</p>
                )}

                {emailDraft && (
                  <div className="flex flex-col gap-3 rounded-md border p-3">
                    <div>
                      <label className="mb-1 block text-sm text-muted-foreground">
                        {t("jobDetail", "sendTo")}
                      </label>
                      <Input
                        value={emailDraft.recipientEmail}
                        onChange={(e) =>
                          setEmailDraft({ ...emailDraft, recipientEmail: e.target.value })
                        }
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-muted-foreground">{t("jobDetail", "subject")}</label>
                      <Input
                        value={emailDraft.subject}
                        onChange={(e) => setEmailDraft({ ...emailDraft, subject: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-muted-foreground">{t("jobDetail", "body")}</label>
                      <Textarea
                        value={emailDraft.body}
                        onChange={(e) => setEmailDraft({ ...emailDraft, body: e.target.value })}
                        rows={8}
                      />
                    </div>
                    <Button
                      onClick={() => sendEmailMutation.mutate()}
                      disabled={sendEmailMutation.isPending}
                      className="self-start"
                    >
                      {sendEmailMutation.isPending ? t("jobDetail", "sending") : t("jobDetail", "sendIt")}
                    </Button>
                    {sendEmailMutation.isError && (
                      <p className="text-sm text-destructive">
                        {t("jobDetail", "sendError")}
                      </p>
                    )}
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("jobDetail", "notes")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {notesQuery.data?.map((note) => (
            <div key={note.id} className="flex items-start justify-between gap-2 rounded-md border p-2">
              <p className="text-sm">{note.note}</p>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setDeleteNoteId(note.id)}
              >
                {t("common", "delete")}
              </Button>
            </div>
          ))}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (noteText.trim()) addNote.mutate();
            }}
            className="flex flex-col gap-2"
          >
            <Textarea
              placeholder={t("jobDetail", "notePlaceholder")}
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
            />
            <Button type="submit" disabled={addNote.isPending} className="self-start">
              {t("jobDetail", "saveNote")}
            </Button>
          </form>
        </CardContent>
      </Card>
      <ConfirmDialog
        open={deleteNoteId !== null}
        onOpenChange={(open) => !open && setDeleteNoteId(null)}
        isPending={removeNote.isPending}
        onConfirm={() => {
          if (deleteNoteId !== null) removeNote.mutate(deleteNoteId);
          setDeleteNoteId(null);
        }}
      />
      <ConfirmDialog
        open={deleteTagId !== null}
        onOpenChange={(open) => !open && setDeleteTagId(null)}
        isPending={removeTag.isPending}
        onConfirm={() => {
          if (deleteTagId !== null) removeTag.mutate(deleteTagId);
          setDeleteTagId(null);
        }}
      />
    </div>
  );
}
