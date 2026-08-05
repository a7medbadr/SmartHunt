"use client";

import { createContext, useCallback, useContext, useMemo } from "react";

import { LOCALE_COOKIE, translations, type Locale } from "./translations";

interface LanguageContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({
  initialLocale,
  children,
}: {
  initialLocale: Locale;
  children: React.ReactNode;
}) {
  // Switching language needs the very first server-rendered HTML (lang/dir
  // attributes, every translated string) to already be correct on the
  // NEXT load — a client-only state flip would show the old language for
  // a flash, or need every Server Component to somehow know about client
  // state. Writing the choice to a cookie (readable by the root layout's
  // Server Component via cookies()) and then reloading is what makes
  // "pick a language and the whole site switches" actually work end to
  // end, per the explicit request that this happen automatically.
  const setLocale = useCallback((next: Locale) => {
    document.cookie = `${LOCALE_COOKIE}=${next}; path=/; max-age=31536000; SameSite=Lax`;
    window.location.reload();
  }, []);

  const value = useMemo(() => ({ locale: initialLocale, setLocale }), [initialLocale, setLocale]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useLanguage must be used inside a LanguageProvider");
  }
  return ctx;
}

type Section = keyof typeof translations.ar;

export function useTranslation() {
  const { locale } = useLanguage();

  const t = useCallback(
    <S extends Section>(section: S, key: keyof (typeof translations.ar)[S]): string => {
      const dict = translations[locale][section] as Record<string, string>;
      return dict[key as string];
    },
    [locale],
  );

  return { t, locale };
}
