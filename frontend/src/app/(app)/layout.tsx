"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Ban,
  Bell,
  BookOpen,
  Bot,
  Briefcase,
  Building2,
  ChevronDown,
  FileText,
  History,
  Home,
  LogOut,
  MessageCircle,
  Rss,
  Search,
  SearchCheck,
  Settings,
  Activity,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getCurrentUser, refreshToken } from "@/lib/auth-api";
import { clearToken, getToken, setToken } from "@/lib/auth";
import { getUnreadCount } from "@/lib/notifications-api";
import { useTranslation } from "@/lib/i18n/language-context";
import type { translations } from "@/lib/i18n/translations";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

// Discovered Jobs and Job Search each used to hold their 3 sub-views
// (job sites / LinkedIn posts / WhatsApp messages) as in-page Tabs. Moved
// to real nested nav entries (own routes, own back button, deep-linkable)
// per explicit request 2026-08-09 — a "group" entry has no href of its
// own and just expands/collapses its children in place, matching "دوس
// عليها تفتح تحتها 3 تابات، ودوس على واحدة فيهم تفتح الصفحة بتاعتها".
interface NavChild {
  href: string;
  icon: LucideIcon;
  section: "discoveredJobs";
  labelKey: keyof typeof translations.ar.discoveredJobs;
}

interface NavLeaf {
  kind: "link";
  href: string;
  key: keyof typeof translations.ar.nav;
  icon: LucideIcon;
  color: string;
}

interface NavGroup {
  kind: "group";
  key: keyof typeof translations.ar.nav;
  icon: LucideIcon;
  color: string;
  children: NavChild[];
}

const DISCOVERED_JOBS_CHILDREN = (basePath: string): NavChild[] => [
  { href: `${basePath}/sites`, icon: Search, section: "discoveredJobs", labelKey: "tabJobSites" },
  { href: `${basePath}/linkedin`, icon: Rss, section: "discoveredJobs", labelKey: "tabLinkedin" },
  {
    href: `${basePath}/whatsapp`,
    icon: MessageCircle,
    section: "discoveredJobs",
    labelKey: "tabWhatsapp",
  },
];

const NAV_LINKS: Array<NavLeaf | NavGroup> = [
  { kind: "link", href: "/", key: "dashboard", icon: Home, color: "text-blue-400" },
  {
    kind: "group",
    key: "jobs",
    icon: Search,
    color: "text-emerald-400",
    children: DISCOVERED_JOBS_CHILDREN("/jobs"),
  },
  {
    kind: "group",
    key: "jobSearch",
    icon: SearchCheck,
    color: "text-teal-400",
    children: DISCOVERED_JOBS_CHILDREN("/job-search"),
  },
  { kind: "link", href: "/applications", key: "applications", icon: Briefcase, color: "text-orange-400" },
  {
    kind: "link",
    href: "/not-suitable-jobs",
    key: "notSuitableJobs",
    icon: Ban,
    color: "text-rose-400",
  },
  { kind: "link", href: "/resume", key: "resume", icon: FileText, color: "text-violet-400" },
  { kind: "link", href: "/ai-assistant", key: "aiAssistant", icon: Bot, color: "text-fuchsia-400" },
  { kind: "link", href: "/providers", key: "providers", icon: Building2, color: "text-indigo-400" },
  { kind: "link", href: "/notifications", key: "notifications", icon: Bell, color: "text-yellow-400" },
  { kind: "link", href: "/activity", key: "activity", icon: History, color: "text-teal-400" },
  { kind: "link", href: "/docs", key: "docs", icon: BookOpen, color: "text-amber-400" },
  { kind: "link", href: "/settings", key: "settings", icon: Settings, color: "text-slate-400" },
  { kind: "link", href: "/system-health", key: "systemHealth", icon: Activity, color: "text-red-400" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { t, locale } = useTranslation();
  const isRtl = locale === "ar";

  // Undefined (not yet manually toggled) falls back to "expanded because
  // the current page lives inside this group" — so landing on /jobs/linkedin
  // directly (a deep link, a refresh) shows that group already open instead
  // of requiring an extra click to reveal the page you're already on.
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({});

  function isGroupExpanded(group: NavGroup) {
    const activeByPath = group.children.some((child) => pathname === child.href);
    return openGroups[group.key] ?? activeByPath;
  }

  function toggleGroup(group: NavGroup) {
    setOpenGroups((prev) => ({ ...prev, [group.key]: !isGroupExpanded(group) }));
  }

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

            if (link.kind === "group") {
              const expanded = isGroupExpanded(link);
              const groupActive = link.children.some((child) => pathname === child.href);
              return (
                <div key={link.key} className="flex flex-col gap-1">
                  <button
                    type="button"
                    onClick={() => toggleGroup(link)}
                    aria-expanded={expanded}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-start text-sm transition-colors",
                      groupActive
                        ? "bg-primary/10 font-medium text-foreground"
                        : "text-muted-foreground hover:bg-primary/10 hover:text-foreground",
                    )}
                  >
                    <Icon className={cn("size-4 shrink-0", link.color)} />
                    <span className="flex-1">{t("nav", link.key)}</span>
                    <ChevronDown
                      className={cn(
                        "size-4 shrink-0 transition-transform",
                        expanded ? "" : "-rotate-90",
                      )}
                    />
                  </button>
                  {expanded && (
                    <div className="flex flex-col gap-1 ps-6">
                      {link.children.map((child) => {
                        const ChildIcon = child.icon;
                        const active = pathname === child.href;
                        return (
                          <Link
                            key={child.href}
                            href={child.href}
                            className={cn(
                              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                              active
                                ? "bg-primary/10 font-medium text-foreground"
                                : "text-muted-foreground hover:bg-primary/10 hover:text-foreground",
                            )}
                          >
                            <ChildIcon className={cn("size-4 shrink-0", link.color)} />
                            <span className="flex-1">{t(child.section, child.labelKey)}</span>
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            }

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
