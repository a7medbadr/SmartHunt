import type { Metadata } from "next";
import { Cairo, Geist_Mono } from "next/font/google";
import "./globals.css";

import { QueryProvider } from "@/lib/query-provider";

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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ar"
      dir="rtl"
      className={`dark ${cairo.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
