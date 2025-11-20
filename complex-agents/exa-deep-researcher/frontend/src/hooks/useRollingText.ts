import { useState, useEffect } from "react";
import type { ResearchStatus } from "./useResearchStatus";

export function useRollingText(statusHistory: ResearchStatus[]): number {
  const [rollingTextIndex, setRollingTextIndex] = useState(0);

  useEffect(() => {
    if (statusHistory.length === 0) return;
    const interval = setInterval(() => {
      setRollingTextIndex((prev) => {
        const recent = statusHistory.slice(-5).reverse();
        return (prev + 1) % recent.length;
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [statusHistory]);

  return rollingTextIndex;
}

