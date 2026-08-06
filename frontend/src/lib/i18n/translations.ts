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
    settings: {
      changePassword: "تغيير الباسورد",
      currentPassword: "الباسورد الحالية",
      newPassword: "الباسورد الجديدة",
      confirmPassword: "تأكيد الباسورد الجديدة",
      changePasswordButton: "غيّر الباسورد",
      changing: "جاري التغيير...",
      passwordMinLength: "الباسورد الجديدة لازم تكون 6 حروف/أرقام على الأقل.",
      passwordMismatch: "الباسورد الجديدة والتأكيد مش متطابقين.",
      passwordChanged: "تم تغيير الباسورد بنجاح.",
      generalPreferences: "التفضيلات العامة",
      emailNotifications: "إشعارات البريد الإلكتروني",
      newJobAlerts: "تنبيهات الوظائف الجديدة",
      saving: "جاري الحفظ...",
      settingsSaved: "اتحفظت الإعدادات.",
      telegramNotifications: "إشعارات تيليجرام",
      whatsappNotifications: "إشعارات واتساب",
      emailChannelNotifications: "إشعارات الإيميل",
      telegramHint:
        "محتاج TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID متظبطين في السيرفر الأول. دوس هنا تبعت رسالة تجريبية تتأكد إنها شغالة.",
      whatsappHint:
        "محتاج WHATSAPP_API_KEY و WHATSAPP_RECIPIENT_NUMBER متظبطين في السيرفر الأول. دوس هنا تبعت رسالة تجريبية تتأكد إنها شغالة.",
      emailHint:
        "محتاج بيانات SMTP متظبطة في السيرفر الأول. دوس هنا تبعت رسالة تجريبية تتأكد إنها شغالة.",
      telegramTestMessage: "لو وصلك ده على تيليجرام، يبقى الإعداد شغال صح.",
      whatsappTestMessage: "لو وصلك ده على واتساب، يبقى الإعداد شغال صح.",
      emailTestMessage: "لو وصلك ده على الإيميل، يبقى الإعداد شغال صح.",
      testNotificationTitle: "إشعار تجريبي من SmartHunt",
      sendTestNotification: "ابعت إشعار تجريبي",
      sending: "جاري الإرسال...",
      testNotificationSentHint:
        "اتبعتت — لو القناة معطلة هتلاقيها في تبويب الإشعارات بس مش هتوصلك فعليًا لحد ما تظبط الإعدادات.",
      testNotificationError: "حصل خطأ أثناء الإرسال.",
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
    settings: {
      changePassword: "Change Password",
      currentPassword: "Current Password",
      newPassword: "New Password",
      confirmPassword: "Confirm New Password",
      changePasswordButton: "Change Password",
      changing: "Changing...",
      passwordMinLength: "New password must be at least 6 characters.",
      passwordMismatch: "New password and confirmation don't match.",
      passwordChanged: "Password changed successfully.",
      generalPreferences: "General Preferences",
      emailNotifications: "Email Notifications",
      newJobAlerts: "New Job Alerts",
      saving: "Saving...",
      settingsSaved: "Settings saved.",
      telegramNotifications: "Telegram Notifications",
      whatsappNotifications: "WhatsApp Notifications",
      emailChannelNotifications: "Email Notifications",
      telegramHint:
        "Needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID configured on the server first. Click here to send a test message and confirm it's working.",
      whatsappHint:
        "Needs WHATSAPP_API_KEY and WHATSAPP_RECIPIENT_NUMBER configured on the server first. Click here to send a test message and confirm it's working.",
      emailHint:
        "Needs SMTP details configured on the server first. Click here to send a test message and confirm it's working.",
      telegramTestMessage: "If this reaches you on Telegram, the setup is working.",
      whatsappTestMessage: "If this reaches you on WhatsApp, the setup is working.",
      emailTestMessage: "If this reaches you by email, the setup is working.",
      testNotificationTitle: "Test notification from SmartHunt",
      sendTestNotification: "Send Test Notification",
      sending: "Sending...",
      testNotificationSentHint:
        "Sent — if the channel isn't configured you'll still see it in the Notifications tab, it just won't actually reach you until it's set up.",
      testNotificationError: "An error occurred while sending.",
    },
  },
} as const;

export type TranslationKey = {
  [Section in keyof typeof translations.ar]: {
    [Key in keyof (typeof translations.ar)[Section]]: `${Section}.${Key & string}`;
  }[keyof (typeof translations.ar)[Section]];
}[keyof typeof translations.ar];
