"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";

import {
  analyzeResume,
  deleteResume,
  getResume,
  uploadResume,
} from "@/lib/resume-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

function formatSize(bytes?: number) {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} bytes`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export default function ResumePage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [skills, setSkills] = useState<string[] | null>(null);

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

  return (
    <div className="flex max-w-xl flex-col gap-6">
      <h1 className="text-2xl font-semibold">السيرة الذاتية</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">الملف الحالي</CardTitle>
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
                onClick={() => deleteMutation.mutate()}
                disabled={deleteMutation.isPending}
              >
                حذف
              </Button>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              لسه مفيش سيرة ذاتية مرفوعة.
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
                ? "جاري الرفع..."
                : resumeQuery.data?.uploaded
                  ? "استبدال الملف"
                  : "رفع سيرة ذاتية (PDF أو DOCX)"}
            </Button>
          </div>

          {uploadMutation.isError && (
            <p className="text-sm text-destructive">
              الرفع فشل — تأكد إن الملف PDF أو DOCX.
            </p>
          )}
        </CardContent>
      </Card>

      {skills && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">المهارات المستخرجة</CardTitle>
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
                مقدرناش نستخرج مهارات من الملف ده.
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
