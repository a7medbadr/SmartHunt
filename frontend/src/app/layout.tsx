import type { Metadata } from "next";
import { cookies } from "next/headers";
import { Cairo, Geist_Mono } from "next/font/google";
import "./globals.css";

import { QueryProvider } from "@/lib/query-provider";
import { LanguageProvider } from "@/lib/i18n/language-context";
import { LOCALE_COOKIE, type Locale } from "@/lib/i18n/translations";

const cairo = Cairo({
  variable: "--font-sans",
  subsets: ["arabic", "latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SmartHunt",
  description: "منصة البحث الذكي عن الوظائف والتقديم التلقائي بالذكاء الاصطناعي",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const cookieStore = await cookies();
  const locale: Locale = cookieStore.get(LOCALE_COOKIE)?.value === "en" ? "en" : "ar";
  const dir = locale === "ar" ? "rtl" : "ltr";

  return (
    <html
      lang={locale}
      dir={dir}
      className={`dark ${cairo.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <QueryProvider>
          <LanguageProvider initialLocale={locale}>{children}</LanguageProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
