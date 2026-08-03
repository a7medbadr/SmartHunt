import { BookmarkPlus, FileText, Heart, Mail, Send, type LucideIcon } from "lucide-react";

import type { ActivityType } from "@/lib/activity-api";

export const ACTIVITY_ICONS: Record<ActivityType, { icon: LucideIcon; color: string }> = {
  resume_uploaded: { icon: FileText, color: "text-violet-400" },
  application_created: { icon: Send, color: "text-orange-400" },
  favorite_added: { icon: Heart, color: "text-rose-400" },
  saved_search_created: { icon: BookmarkPlus, color: "text-amber-400" },
  cover_letter_generated: { icon: Mail, color: "text-cyan-400" },
};
