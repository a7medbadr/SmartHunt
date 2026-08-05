"use client";

import { useEffect, useRef, useState } from "react";

/**
 * There's no real step-wise progress signal from these AI calls (a
 * single black-box HTTP request) — this estimates progress against a
 * calibrated expected duration so a long wait (up to a few minutes on
 * the local CPU-bound model) shows visible movement instead of a
 * frozen-looking button. Eases toward 95% and never claims 100% until
 * the caller confirms the request actually finished. Returns 0 whenever
 * isActive is false, without needing to reset state inside the effect.
 */
export function useEstimatedProgress(isActive: boolean, expectedMs: number): number {
  const [activePercent, setActivePercent] = useState(1);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isActive) {
      startRef.current = null;
      return;
    }

    startRef.current = Date.now();

    const interval = setInterval(() => {
      const start = startRef.current;
      if (start === null) return;
      const elapsed = Date.now() - start;
      const eased = 95 * (1 - Math.exp(-elapsed / expectedMs));
      setActivePercent(Math.min(95, Math.max(1, Math.round(eased))));
    }, 400);

    return () => clearInterval(interval);
  }, [isActive, expectedMs]);

  return isActive ? activePercent : 0;
}
