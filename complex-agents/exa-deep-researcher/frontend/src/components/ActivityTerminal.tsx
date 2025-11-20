interface ActivityTerminalProps {
  statusHistory: Array<{
    phase: string;
    title: string;
    message: string;
    stats?: Record<string, unknown>;
    ts: number;
  }>;
  rollingTextIndex: number;
}

function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + "...";
}

function formatStatusMessage(
  status: ActivityTerminalProps["statusHistory"][0]
): string {
  const { phase, title, message, stats } = status;

  // Show more informative messages based on phase and stats
  // Check specific actions first, then fall back to general topic display
  if (phase === "researching") {
    // Check specific actions first (these are more informative)
    if (title.includes("Synthesizing")) {
      return `Analyzing ${
        stats?.sources_fetched || stats?.sources || ""
      } sources`;
    }
    if (title.includes("Gathering")) {
      return `Found ${stats?.results || stats?.sources || ""} sources`;
    }
    if (title.includes("Starting")) {
      const topic = stats?.subtopic || stats?.topic;
      return topic ? `Starting: ${truncate(String(topic), 35)}` : message;
    }
    // Fallback to general topic display
    if (stats?.subtopic) {
      return `Researching: ${truncate(String(stats.subtopic), 40)}`;
    }
    if (stats?.topic) {
      return `Researching: ${truncate(String(stats.topic), 40)}`;
    }
    if (message && message.length > 0) {
      return truncate(message, 50);
    }
  }

  if (phase === "compressing") {
    const notesCount = stats?.notes_count || "";
    return notesCount ? `Consolidating ${notesCount} topics` : message;
  }

  if (phase === "reporting") {
    return message || title;
  }

  if (phase === "briefing") {
    return message || title;
  }

  return message || title;
}

export function ActivityTerminal({
  statusHistory,
  rollingTextIndex,
}: ActivityTerminalProps) {
  if (statusHistory.length <= 1) return null;

  return (
    <div
      data-slot="timeline"
      className="relative bg-bg0 border border-fgAccent1/30 rounded-lg overflow-hidden shadow-lg cyber-glow"
      style={{
        boxShadow:
          "0 0 10px rgba(31, 213, 249, 0.2), inset 0 0 20px rgba(31, 213, 249, 0.05)",
      }}
    >
      <div className="absolute inset-0 cyber-scan-line pointer-events-none">
        <div className="h-px w-full bg-fgAccent1/20"></div>
      </div>

      <div className="relative bg-bgAccent1/10 border-b border-fgAccent1/30 px-3 py-2">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <div className="w-2 h-2 rounded-full bg-fgSerious1 animate-pulse"></div>
            <div
              className="w-2 h-2 rounded-full bg-fgModerate animate-pulse"
              style={{ animationDelay: "0.2s" }}
            ></div>
            <div
              className="w-2 h-2 rounded-full bg-fgSuccess animate-pulse"
              style={{ animationDelay: "0.4s" }}
            ></div>
          </div>
          <div className="flex-1 overflow-hidden min-w-0">
            <div className="flex items-center gap-1 font-mono text-[9px]">
              <span className="text-fgAccent1 shrink-0">▶</span>
              <span
                key={rollingTextIndex}
                className="text-fg2 overflow-hidden whitespace-nowrap min-w-0 transition-opacity duration-500"
              >
                {(() => {
                  const recent = statusHistory.slice(-5).reverse();
                  const active = recent[rollingTextIndex] || recent[0];
                  if (!active) return "STANDBY";
                  const message = formatStatusMessage(active);
                  return `[${active.phase.toUpperCase()}] ${message}`;
                })()}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="p-3 max-h-[300px] overflow-y-auto font-mono text-[9px] text-fg3 space-y-1">
        {statusHistory
          .slice(-10)
          .reverse()
          .map((status, idx) => {
            const message = formatStatusMessage(status);
            return (
              <div
                key={`${status.phase}-${status.ts}-${idx}`}
                className="flex items-start gap-2"
              >
                <span className="text-fgAccent1 shrink-0">
                  {new Date(status.ts * 1000).toLocaleTimeString()}
                </span>
                <span className="text-fg2 flex-1 min-w-0">
                  <span className="text-fgAccent1">
                    [{status.phase.toUpperCase()}]
                  </span>{" "}
                  {message}
                </span>
              </div>
            );
          })}
      </div>
    </div>
  );
}
