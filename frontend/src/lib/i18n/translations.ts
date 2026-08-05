export type Locale = "ar" | "en";

export const LOCALE_COOKIE = "smarthunt_locale";

// This dictionary covers the app's persistent "chrome" — sidebar nav
// labels, every page's header title, and the most common shared UI
// strings (loading/error/save/cancel) — the parts of the UI visible on
// every single page regardless of which feature you're using. It does
// NOT yet cover every string deep inside each page (table headers,
// individual error messages, tooltips, etc.) — that's a much larger
// follow-up effort across ~12 page files, called out explicitly rather
// than silently left half-done.
export const translations = {
  ar: {
    nav: {
      dashboard: "الرئيسية",
      jobs: "الوظائف",
      jobSearch: "البحث عن وظائف",
      applications: "التقديمات",
      resume: "السيرة الذاتية",
      aiAssistant: "المساعد الذكي",
      providers: "مواقع التوظيف",
      notifications: "الإشعارات",
      activity: "سجل النشاطات",
      docs: "الدليل",
      settings: "الإعدادات",
      systemHealth: "حالة النظام",
      logout: "تسجيل الخروج",
    },
    pageTitles: {
      dashboard: "الداشبورد",
      jobs: "الوظائف",
      jobSearch: "البحث عن وظائف",
      applications: "التقديمات",
      resume: "السيرة الذاتية",
      aiAssistant: "المساعد الذكي",
      providers: "مواقع التوظيف",
      notifications: "الإشعارات",
      activity: "سجل النشاطات",
      docs: "الدليل",
      settings: "الإعدادات",
      systemHealth: "حالة النظام",
    },
    common: {
      loading: "جاري التحميل...",
      save: "حفظ",
      cancel: "إلغاء",
      delete: "حذف",
      search: "بحث",
      error: "حصل خطأ، جرب تاني.",
      retry: "إعادة المحاولة",
      language: "اللغة",
      arabic: "العربية",
      english: "الإنجليزية",
    },
  },
  en: {
    nav: {
      dashboard: "Dashboard",
      jobs: "Jobs",
      jobSearch: "Job Search",
      applications: "Applications",
      resume: "Resume",
      aiAssistant: "AI Assistant",
      providers: "Job Sites",
      notifications: "Notifications",
      activity: "Activity Log",
      docs: "Guide",
      settings: "Settings",
      systemHealth: "System Health",
      logout: "Log Out",
    },
    pageTitles: {
      dashboard: "Dashboard",
      jobs: "Jobs",
      jobSearch: "Job Search",
      applications: "Applications",
      resume: "Resume",
      aiAssistant: "AI Assistant",
      providers: "Job Sites",
      notifications: "Notifications",
      activity: "Activity Log",
      docs: "Guide",
      settings: "Settings",
      systemHealth: "System Health",
    },
    common: {
      loading: "Loading...",
      save: "Save",
      cancel: "Cancel",
      delete: "Delete",
      search: "Search",
      error: "Something went wrong, try again.",
      retry: "Retry",
      language: "Language",
      arabic: "Arabic",
      english: "English",
    },
  },
} as const;

export type TranslationKey = {
  [Section in keyof typeof translations.ar]: {
    [Key in keyof (typeof translations.ar)[Section]]: `${Section}.${Key & string}`;
  }[keyof (typeof translations.ar)[Section]];
}[keyof typeof translations.ar];
