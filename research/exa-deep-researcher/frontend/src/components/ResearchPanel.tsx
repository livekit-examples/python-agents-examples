import { ResearchPlanSteps } from "./ResearchPlanSteps";
import { ResearchStatsHeader } from "./ResearchStatsHeader";
import { ClarificationCard } from "./ClarificationCard";
import { ReportCard } from "./ReportCard";
import { StatusCard } from "./StatusCard";
import { ActivityTerminal } from "./ActivityTerminal";
import { ResearchNotesList } from "./ResearchNotesList";
import { EmptyState } from "./EmptyState";
import { useResearchStatus } from "../hooks/useResearchStatus";
import { useResearchPlan } from "../hooks/useResearchPlan";
import { useResearchStats } from "../hooks/useResearchStats";
import { useRollingText } from "../hooks/useRollingText";

const PHASE_CONFIG = {
  briefing: {
    label: "Briefing",
    icon: "file-text",
    bg: "bg-bgAccent1/30",
    border: "border-separatorAccent",
    text: "text-fgAccent1",
    progressBg: "bg-fgAccent1",
    dot: "bg-fgAccent1",
  },
  researching: {
    label: "Researching",
    icon: "search",
    bg: "bg-bgAccent1/30",
    border: "border-separatorAccent",
    text: "text-fgAccent1",
    progressBg: "bg-fgAccent1",
    dot: "bg-fgAccent1",
  },
  compressing: {
    label: "Compressing",
    icon: "package",
    bg: "bg-bgModerate1/30",
    border: "border-separatorModerate",
    text: "text-fgModerate",
    progressBg: "bg-fgModerate",
    dot: "bg-fgModerate",
  },
  reporting: {
    label: "Reporting",
    icon: "file-text",
    bg: "bg-bgSuccess1/30",
    border: "border-separatorSuccess",
    text: "text-fgSuccess",
    progressBg: "bg-fgSuccess",
    dot: "bg-fgSuccess",
  },
  clarifying: {
    label: "Clarifying",
    icon: "help-circle",
    bg: "bg-bgAccent1/30",
    border: "border-separatorAccent",
    text: "text-fgAccent1",
    progressBg: "bg-fgAccent1",
    dot: "bg-fgAccent1",
  },
};

export function ResearchPanel() {
  const {
    currentStatus,
    statusHistory,
    notes,
    report,
    researchTitle,
    clarification,
    reset,
  } = useResearchStatus();

  const planSteps = useResearchPlan(
    currentStatus,
    statusHistory,
    researchTitle,
    notes,
    report,
    clarification
  );

  const stats = useResearchStats(notes, report);
  const rollingTextIndex = useRollingText(statusHistory);

  const phaseConfig = currentStatus ? PHASE_CONFIG[currentStatus.phase] : null;

  return (
    <div className="flex-1 flex flex-col bg-bg0 h-full min-h-0">
      <ResearchStatsHeader
        totalNotes={stats.totalNotes}
        uniqueSources={stats.uniqueSources}
        totalSources={stats.totalSources}
        onReset={reset}
        hasData={notes.length > 0 || !!report || statusHistory.length > 0}
      />

      <div className="flex-1 overflow-y-auto min-h-0" data-scroll-container>
        {clarification && currentStatus?.phase === "clarifying" && (
          <ClarificationCard
            clarification={{
              question: clarification.question,
              originalQuery: clarification.originalQuery,
            }}
          />
        )}

        {statusHistory.length > 0 && planSteps.length > 0 && (
          <ResearchPlanSteps steps={planSteps} title={researchTitle} />
        )}

        {report && (
          <div className="p-6">
            <ReportCard
              report={{
                reportTitle: report.reportTitle,
                reportContent: report.reportContent,
              }}
            />
          </div>
        )}

        <div className="flex flex-col gap-4 p-6">
          {currentStatus && phaseConfig && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <StatusCard
                phase={currentStatus.phase}
                title={currentStatus.title}
                message={currentStatus.message}
                progressPct={currentStatus.progressPct}
                stats={currentStatus.stats}
                phaseConfig={phaseConfig}
              />
              <ActivityTerminal
                statusHistory={statusHistory}
                rollingTextIndex={rollingTextIndex}
              />
            </div>
          )}

          {notes.length > 0 && <ResearchNotesList notes={notes} />}

          {!currentStatus && notes.length === 0 && !report && <EmptyState />}
        </div>
      </div>
    </div>
  );
}
