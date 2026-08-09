"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function JobSearchPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/job-search/sites");
  }, [router]);

  return null;
}
