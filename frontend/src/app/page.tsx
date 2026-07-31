"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { getToken, clearToken } from "@/lib/auth";
import { getCurrentUser } from "@/lib/auth-api";
import { Button } from "@/components/ui/button";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
    }
  }, [router]);

  const { data: user, isLoading, isError } = useQuery({
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

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  if (isLoading || !user) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground">جاري التحميل...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 p-4">
      <h1 className="text-2xl font-semibold">أهلاً، {user.username}</h1>
      <p className="text-muted-foreground">
        الداشبورد جاي في Sprint 2 — الحساب متسجل دخول فعليًا دلوقتي.
      </p>
      <Button variant="outline" onClick={handleLogout}>
        تسجيل الخروج
      </Button>
    </div>
  );
}
