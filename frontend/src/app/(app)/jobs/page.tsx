"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function JobsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/jobs/sites");
  }, [router]);

  return null;
}
