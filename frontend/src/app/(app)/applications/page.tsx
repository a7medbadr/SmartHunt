"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  APPLICATION_STATUSES,
  type ApplicationStatus,
  createApplication,
  deleteApplication,
  listApplications,
  updateApplicationStatus,
} from "@/lib/applications-api";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

export default function ApplicationsPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("");
  const [url, setUrl] = useState("");

  const { data, isPending } = useQuery({
    queryKey: ["applications"],
    queryFn: listApplications,
  });

  const createMutation = useMutation({
    mutationFn: createApplication,
    onSuccess: () => {
      setJobTitle("");
      setCompany("");
      setUrl("");
      setDialogOpen(false);
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: ApplicationStatus }) =>
      updateApplicationStatus(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteApplication,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">التقديمات</h1>

        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger className={buttonVariants()}>تقديم جديد</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>إضافة تقديم</DialogTitle>
            </DialogHeader>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                createMutation.mutate({
                  job_title: jobTitle,
                  company,
                  url: url || undefined,
                });
              }}
              className="flex flex-col gap-3"
            >
              <Input
                placeholder="المسمى الوظيفي"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                required
              />
              <Input
                placeholder="الشركة"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                required
              />
              <Input
                placeholder="رابط الوظيفة (اختياري)"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "جاري الحفظ..." : "حفظ"}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {isPending ? (
        <Skeleton className="h-40 w-full" />
      ) : data && data.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>المسمى الوظيفي</TableHead>
              <TableHead>الشركة</TableHead>
              <TableHead>الحالة</TableHead>
              <TableHead>تاريخ التقديم</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((app) => (
              <TableRow key={app.id}>
                <TableCell className="font-medium">
                  {app.url ? (
                    <a href={app.url} target="_blank" rel="noopener noreferrer" className="underline">
                      {app.job_title}
                    </a>
                  ) : (
                    app.job_title
                  )}
                </TableCell>
                <TableCell>{app.company}</TableCell>
                <TableCell>
                  <Select
                    value={app.status}
                    onValueChange={(status) =>
                      statusMutation.mutate({ id: app.id, status: status as ApplicationStatus })
                    }
                  >
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {APPLICATION_STATUSES.map((s) => (
                        <SelectItem key={s} value={s}>
                          {s}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  {new Date(app.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteMutation.mutate(app.id)}
                  >
                    حذف
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <p className="text-sm text-muted-foreground">لسه مفيش تقديمات مسجلة.</p>
      )}
    </div>
  );
}
