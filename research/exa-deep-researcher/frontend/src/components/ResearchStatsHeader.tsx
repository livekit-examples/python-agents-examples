import { Trash2 } from "lucide-react";

interface ResearchStatsHeaderProps {
  totalNotes: number;
  uniqueSources: number;
  totalSources: number;
  onReset?: () => void;
  hasData?: boolean;
}

export function ResearchStatsHeader({
  totalNotes,
  uniqueSources,
  totalSources,
  onReset,
  hasData,
}: ResearchStatsHeaderProps) {
  if (totalNotes === 0 && !hasData) return null;

  return (
    <div className="sticky top-0 z-10 border-b border-separator1 bg-bg1/95 backdrop-blur-sm px-4 py-3 shrink-0">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-xs">
          {totalNotes > 0 && (
            <>
              <div className="text-fg3">
                <span className="font-semibold text-fg0">{totalNotes}</span>{" "}
                <span
                  className="cursor-help underline decoration-dotted decoration-fg4"
                  title="Research topics investigated - different aspects of the research question"
                >
                  topics
                </span>
              </div>
              <div className="text-fg3">
                <span className="font-semibold text-fg0">{uniqueSources}</span>{" "}
                <span
                  className="cursor-help underline decoration-dotted decoration-fg4"
                  title="Unique sources - different websites/articles referenced (each URL counted once)"
                >
                  sources
                </span>
              </div>
              <div className="text-fg3">
                <span className="font-semibold text-fg0">{totalSources}</span>{" "}
                <span
                  className="cursor-help underline decoration-dotted decoration-fg4"
                  title="Total citations - all references used across topics (same source may appear multiple times)"
                >
                  citations
                </span>
              </div>
            </>
          )}
        </div>
        {onReset && hasData && (
          <button
            onClick={onReset}
            className="flex items-center gap-2 px-3 py-1.5 text-xs text-fg3 hover:text-fg1 hover:bg-bg2 rounded-md transition-colors border border-separator1 hover:border-separator2"
            title="Clear all research data"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
