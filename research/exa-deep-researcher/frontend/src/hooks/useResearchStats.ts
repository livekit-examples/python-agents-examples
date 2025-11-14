import { useMemo } from "react";
import type { ResearchNote, Report } from "./useResearchStatus";

export interface ResearchStats {
  totalSources: number;
  totalNotes: number;
  uniqueSources: number;
}

export function useResearchStats(
  notes: ResearchNote[],
  report: Report | null
): ResearchStats {
  return useMemo(() => {
    const validCitations = notes.flatMap((note) =>
      note.citations.filter((c) => {
        const title = c.title?.toLowerCase().trim() || "";
        return title && title !== "untitled" && !title.startsWith("untitled");
      })
    );

    // If report exists, use numSources from report (actual citations in final report)
    // Otherwise, count all citations from notes
    return {
      totalSources: report?.numSources ?? validCitations.length,
      totalNotes: notes.length,
      uniqueSources: new Set(validCitations.map((c) => c.url)).size,
    };
  }, [notes, report]);
}

