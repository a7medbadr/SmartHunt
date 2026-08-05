"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Bell,
  BookOpen,
  Bot,
  Briefcase,
  Building2,
  FileText,
  History,
  Home,
  LogOut,
  Search,
  SearchCheck,
  Settings,
  Activity,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { getCurrentUser, refreshToken } from "@/lib/auth-api";
import { clearToken, getToken, setToken } from "@/lib/auth";
import { getUnreadCount } from "@/lib/notifications-api";
import { useTranslation } from "@/lib/i18n/language-context";
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
  { href: "/", key: "dashboard" as const, icon: Home, color: "text-blue-400" },
  { href: "/jobs", key: "jobs" as const, icon: Search, color: "text-emerald-400" },
  {
    href: "/job-search",
    key: "jobSearch" as const,
    icon: SearchCheck,
    color: "text-teal-400",
  },
  { href: "/applications", key: "applications" as const, icon: Briefcase, color: "text-orange-400" },
  { href: "/resume", key: "resume" as const, icon: FileText, color: "text-violet-400" },
  { href: "/ai-assistant", key: "aiAssistant" as const, icon: Bot, color: "text-fuchsia-400" },
  { href: "/providers", key: "providers" as const, icon: Building2, color: "text-indigo-400" },
  { href: "/notifications", key: "notifications" as const, icon: Bell, color: "text-yellow-400" },
  { href: "/activity", key: "activity" as const, icon: History, color: "text-teal-400" },
  { href: "/docs", key: "docs" as const, icon: BookOpen, color: "text-amber-400" },
  { href: "/settings", key: "settings" as const, icon: Settings, color: "text-slate-400" },
  { href: "/system-health", key: "systemHealth" as const, icon: Activity, color: "text-red-400" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { t, locale } = useTranslation();
  const isRtl = locale === "ar";

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
        <p className="text-muted-foreground">{t("common", "loading")}</p>
      </div>
    );
  }

  return (
    // `position: fixed` on <aside>, not a flexbox height-containment
    // trick — found 2026-08-04 that an h-screen/overflow-hidden flex
    // wrapper (the previous approach) still let the sidebar scroll away
    // on a long page for at least one real browser/session, despite
    // being correct on paper. `fixed` is anchored to the viewport by
    // definition, completely independent of any ancestor's height/
    // overflow/flex setup, so there's no chain of "does every ancestor
    // actually constrain height correctly" left to get wrong. <main>
    // just gets a matching margin so its content doesn't render under
    // the fixed sidebar, and the whole page scrolls normally.
    <div className="flex flex-1">
      <aside
        className={cn(
          "fixed inset-y-0 z-10 flex w-64 flex-col overflow-y-auto bg-card/40",
          isRtl ? "right-0 border-l" : "left-0 border-r",
        )}
      >
        <div className="px-5 py-4">
          <div className="flex w-fit items-center gap-2 rounded-lg bg-primary px-3 py-1.5">
            <Search className="size-4 text-primary-foreground" />
            <span className="text-lg font-bold text-primary-foreground">SmartHunt</span>
          </div>
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
                <span className="flex-1">{t("nav", link.key)}</span>
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
                {t("nav", "logout")}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>

      {/* mr- (physical), not me- (logical): the app is dir="rtl", where
          margin-inline-end resolves to margin-LEFT — the opposite side
          from the <aside>'s physical right-0, so the previous me-64 gave
          the content zero clearance on the side the sidebar actually
          occupies and let every page render underneath it. Found
          2026-08-04 from a live screenshot showing the dashboard fully
          overlapping the nav. */}
      <main className={cn("flex flex-1 flex-col p-6", isRtl ? "mr-64" : "ml-64")}>
        {children}
      </main>
    </div>
  );
}
