"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Bell,
  BookmarkPlus,
  Bot,
  Briefcase,
  Building2,
  CalendarClock,
  FileText,
  Heart,
  Home,
  LogOut,
  Mail,
  Search,
  Settings,
  Activity,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { getCurrentUser } from "@/lib/auth-api";
import { clearToken, getToken } from "@/lib/auth";
import { getUnreadCount } from "@/lib/notifications-api";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "/", label: "الرئيسية", icon: Home },
  { href: "/jobs", label: "الوظائف", icon: Search },
  { href: "/favorites", label: "المفضلة", icon: Heart },
  { href: "/saved-searches", label: "عمليات البحث المحفوظة", icon: BookmarkPlus },
  { href: "/resume", label: "السيرة الذاتية", icon: FileText },
  { href: "/cover-letter", label: "خطاب التقديم", icon: Mail },
  { href: "/applications", label: "التقديمات", icon: Briefcase },
  { href: "/ai-assistant", label: "المساعد الذكي", icon: Bot },
  { href: "/scheduler", label: "الجدولة", icon: CalendarClock },
  { href: "/providers", label: "مواقع التوظيف", icon: Building2 },
  { href: "/notifications", label: "الإشعارات", icon: Bell },
  { href: "/settings", label: "الإعدادات", icon: Settings },
  { href: "/system-health", label: "حالة النظام", icon: Activity },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
    }
  }, [router]);

  const {
    data: user,
    isPending,
    isError,
  } = useQuery({
    queryKey: ["me"],
    queryFn: getCurrentUser,
    enabled: !!getToken(),
    retry: false,
  });

  useEffect(() => {
    if (isError) {
      clearToken();
      router.replace("/login");
    }
  }, [isError, router]);

  const { data: unreadCount } = useQuery({
    queryKey: ["unread-count"],
    queryFn: getUnreadCount,
    enabled: !!user,
    refetchInterval: 30000,
  });

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  if (isPending || !user) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground">جاري التحميل...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-full flex-1">
      <aside className="flex w-64 shrink-0 flex-col border-l bg-card/40">
        <div className="flex items-center gap-2 px-5 py-4">
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary">
            <Search className="size-4 text-primary-foreground" />
          </div>
          <span className="text-lg font-bold">SmartHunt</span>
        </div>

        <nav className="flex flex-1 flex-col gap-1 px-3">
          {NAV_LINKS.map((link) => {
            const Icon = link.icon;
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                  active
                    ? "bg-primary/10 font-medium text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground",
                )}
              >
                <Icon className="size-4 shrink-0" />
                <span className="flex-1">{link.label}</span>
                {link.href === "/notifications" && !!unreadCount && (
                  <Badge className="h-5 min-w-5 justify-center px-1">
                    {unreadCount}
                  </Badge>
                )}
              </Link>
            );
          })}
        </nav>

        <div className="border-t p-3">
          <DropdownMenu>
            <DropdownMenuTrigger className="flex w-full items-center gap-2 rounded-lg p-2 outline-none hover:bg-accent">
              <Avatar className="size-8">
                <AvatarFallback>
                  {user.username.slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="flex-1 truncate text-start text-sm font-medium">
                {user.username}
              </span>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="size-4" />
                تسجيل الخروج
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>

      <main className="flex flex-1 flex-col overflow-y-auto p-6">{children}</main>
    </div>
  );
}
