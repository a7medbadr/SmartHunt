"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useTranslation } from "@/lib/i18n/language-context";

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  title?: string;
  description?: string;
  isPending?: boolean;
  confirmLabel?: string;
}

// Shared confirmation step for every destructive/delete action in the
// app — added 2026-08-07 per explicit request: nothing should delete
// immediately on click anymore, everywhere needs a "are you sure?" step
// first. Each call site owns its own open/target state (which row is
// pending deletion) and just renders one of these controlled by that
// state, matching how Dialog is already used elsewhere in this app
// (e.g. the Providers page's request dialog) rather than introducing a
// new global imperative confirm() pattern.
export function ConfirmDialog({
  open,
  onOpenChange,
  onConfirm,
  title,
  description,
  isPending,
  confirmLabel,
}: ConfirmDialogProps) {
  const { t } = useTranslation();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title ?? t("common", "confirmDeleteTitle")}</DialogTitle>
          <DialogDescription>
            {description ?? t("common", "confirmDeleteBody")}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isPending}>
            {t("common", "cancel")}
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={isPending}>
            {isPending ? t("common", "deleting") : (confirmLabel ?? t("common", "delete"))}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
