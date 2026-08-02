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

import { getCurrentUser, refreshToken } from "@/lib/auth-api";
import { clearToken, getToken, setToken } from "@/lib/auth";
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
  { href: "/", label: "الرئيسية", icon: Home, color: "text-blue-400" },
  { href: "/jobs", label: "الوظائف", icon: Search, color: "text-emerald-400" },
  { href: "/favorites", label: "المفضلة", icon: Heart, color: "text-rose-400" },
  {
    href: "/saved-searches",
    label: "عمليات البحث المحفوظة",
    icon: BookmarkPlus,
    color: "text-amber-400",
  },
  { href: "/resume", label: "السيرة الذاتية", icon: FileText, color: "text-violet-400" },
  { href: "/cover-letter", label: "خطاب التقديم", icon: Mail, color: "text-cyan-400" },
  { href: "/applications", label: "التقديمات", icon: Briefcase, color: "text-orange-400" },
  { href: "/ai-assistant", label: "المساعد الذكي", icon: Bot, color: "text-fuchsia-400" },
  { href: "/scheduler", label: "الجدولة", icon: CalendarClock, color: "text-teal-400" },
  { href: "/providers", label: "مواقع التوظيف", icon: Building2, color: "text-indigo-400" },
  { href: "/notifications", label: "الإشعارات", icon: Bell, color: "text-yellow-400" },
  { href: "/settings", label: "الإعدادات", icon: Settings, color: "text-slate-400" },
  { href: "/system-health", label: "حالة النظام", icon: Activity, color: "text-red-400" },
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

  // Sliding session: keep renewing the token while the user is actually
  // active, so it never expires mid-use — but stop renewing once idle,
  // so an abandoned tab still logs out ACCESS_TOKEN_EXPIRE_MINUTES (60)
  // after the last real activity, not never. ACTIVITY_WINDOW_MS must
  // stay under the backend's token lifetime or refresh could fire on an
  // already-expired token and fail.
  useEffect(() => {
    if (!user) return;

    const REFRESH_INTERVAL_MS = 5 * 60 * 1000;
    const ACTIVITY_WINDOW_MS = 55 * 60 * 1000;
    const ACTIVITY_EVENTS = ["mousemove", "keydown", "click", "scroll", "touchstart"];

    let lastActivity = Date.now();
    const onActivity = () => {
      lastActivity = Date.now();
    };
    ACTIVITY_EVENTS.forEach((event) =>
      window.addEventListener(event, onActivity, { passive: true }),
    );

    const interval = setInterval(() => {
      if (Date.now() - lastActivity < ACTIVITY_WINDOW_MS) {
        refreshToken()
          .then((data) => setToken(data.access_token))
          .catch(() => {
            // A failed refresh just means the current token expires on
            // its own schedule — the existing 401 handling covers that.
          });
      }
    }, REFRESH_INTERVAL_MS);

    return () => {
      ACTIVITY_EVENTS.forEach((event) => window.removeEventListener(event, onActivity));
      clearInterval(interval);
    };
  }, [user]);

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
                    ? "bg-primary/10 font-medium text-foreground"
                    : "text-muted-foreground hover:bg-primary/10 hover:text-foreground",
                )}
              >
                <Icon className={cn("size-4 shrink-0", link.color)} />
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
