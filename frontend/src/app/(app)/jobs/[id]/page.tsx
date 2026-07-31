"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Star } from "lucide-react";
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
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";

export default function JobDetailsPage() {
  const params = useParams<{ id: string }>();
  const jobId = Number(params.id);
  const queryClient = useQueryClient();

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
    return <p className="text-sm text-destructive">الوظيفة دي مش موجودة.</p>;
  }

  const job = jobQuery.data;

  return (
    <div className="flex max-w-2xl flex-col gap-6">
      <Card>
        <CardHeader className="flex flex-row items-start justify-between">
          <div>
            <CardTitle className="text-xl">{job.title}</CardTitle>
            <p className="text-muted-foreground">
              {job.company} · {job.location ?? "—"} · {job.source ?? "—"}
            </p>
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={() => toggleFavorite.mutate()}
            disabled={toggleFavorite.isPending}
            aria-label="مفضلة"
          >
            <Star className={isFavorite ? "fill-current" : ""} />
          </Button>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {job.description && <p className="whitespace-pre-wrap">{job.description}</p>}
          {job.requirements && (
            <div>
              <h3 className="mb-1 font-medium">المتطلبات</h3>
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
              رابط الوظيفة الأصلي
            </a>
          )}

          <div className="flex flex-wrap gap-2 pt-2">
            {tagsQuery.data?.map((tag) => (
              <Badge
                key={tag.id}
                variant="secondary"
                className="cursor-pointer"
                onClick={() => removeTag.mutate(tag.id)}
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
              placeholder="ضيف Tag (مثلاً: Remote)"
              value={tagText}
              onChange={(e) => setTagText(e.target.value)}
              className="max-w-xs"
            />
            <Button type="submit" variant="secondary" disabled={addTag.isPending}>
              إضافة
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">الملاحظات</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {notesQuery.data?.map((note) => (
            <div key={note.id} className="flex items-start justify-between gap-2 rounded-md border p-2">
              <p className="text-sm">{note.note}</p>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeNote.mutate(note.id)}
              >
                حذف
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
              placeholder="اكتب ملاحظة..."
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
            />
            <Button type="submit" disabled={addNote.isPending} className="self-start">
              حفظ الملاحظة
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
