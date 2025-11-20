import { useMemo } from "react";
import type {
  ResearchStatus,
  ResearchNote,
  Report,
  Clarification,
} from "./useResearchStatus";

interface PlanStep {
  id: string;
  label: string;
  icon: string;
  status: "pending" | "active" | "completed";
  description?: string;
  timestamp?: number;
}

// Normalize topic strings for matching (trim, lowercase)
function normalizeTopic(topic: string): string {
  return topic.trim().toLowerCase();
}

export function useResearchPlan(
  currentStatus: ResearchStatus | null,
  statusHistory: ResearchStatus[],
  researchTitle: string | null,
  notes: ResearchNote[],
  report: Report | null,
  clarification: Clarification | null
): PlanStep[] {
  return useMemo(() => {
    const steps: PlanStep[] = [];

    // Determine if research has started
    const hasResearchStarted =
      !!currentStatus?.requestId || statusHistory.length > 0;

    if (!hasResearchStarted) {
      return steps; // Return empty if research hasn't started
    }

    // Filter status history to only include the active request (if report exists, use its requestId)
    const activeRequestId = report?.requestId || currentStatus?.requestId;
    const filteredStatusHistory = activeRequestId
      ? statusHistory.filter((s) => s.requestId === activeRequestId)
      : statusHistory;

    // 1. Clarification step (optional, but show if it happened)
    // Always at position 0 if present
    // Check if clarification happened in this request by looking at statusHistory
    const activeClarification =
      clarification && clarification.requestId === activeRequestId
        ? clarification
        : null;

    // Check if there was ANY clarification phase in the filtered history
    const hadClarificationPhase = filteredStatusHistory.some(
      (s) => s.phase === "clarifying"
    );

    const isClarificationActive = currentStatus?.phase === "clarifying";

    // Show clarification step if:
    // 1. Currently clarifying, OR
    // 2. Had clarification phase in history (completed), OR
    // 3. Have clarification data
    const showClarificationStep =
      isClarificationActive || hadClarificationPhase || !!activeClarification;

    if (showClarificationStep) {
      // Determine status:
      // - active: currently clarifying
      // - completed: had clarification phase and moved past it
      const isClarificationCompleted =
        (hadClarificationPhase || !!activeClarification) &&
        !isClarificationActive;

      steps.push({
        id: "clarification",
        label: "Clarification",
        icon: "clarification",
        status: isClarificationActive
          ? "active"
          : isClarificationCompleted
          ? "completed"
          : "pending",
        description: isClarificationCompleted ? "Question answered" : undefined,
        // Force order=0 (always first)
        timestamp: 0,
      });
    }

    // 2. Planning step (always visible, always at position 1 after clarification)
    // Find the FIRST briefing status (from the current research session)
    const briefingStatuses = filteredStatusHistory.filter(
      (s) => s.phase === "briefing"
    );
    const firstBriefingStatus =
      briefingStatuses.length > 0
        ? briefingStatuses[0] // Use first briefing (earliest timestamp)
        : null;

    // Planning is completed if:
    // 1. Report exists (research completed), OR
    // 2. We have topics (means we moved past planning), OR
    // 3. Current phase is beyond briefing (researching, compressing, reporting)
    const hasMovedPastPlanning =
      currentStatus &&
      (currentStatus.phase === "researching" ||
        currentStatus.phase === "compressing" ||
        currentStatus.phase === "reporting");

    const isPlanningCompleted =
      !!report || hasMovedPastPlanning || !!firstBriefingStatus;

    steps.push({
      id: "briefing",
      label: "Planning",
      icon: "planning",
      status:
        currentStatus?.phase === "briefing"
          ? "active"
          : isPlanningCompleted
          ? "completed"
          : "pending",
      description: researchTitle || firstBriefingStatus?.title || undefined,
      // Force order=1 (after clarification which is 0)
      timestamp: 1,
    });

    // 3. Collect all topics from statusHistory (when they appear)
    const allTopics = new Map<
      string,
      {
        topic: string;
        normalizedTopic: string;
        firstSeen: number;
        completedAt?: number;
      }
    >();

    // From statusHistory - when subtopic appears in stats
    filteredStatusHistory.forEach((status) => {
      if (status.phase === "researching" && status.stats?.subtopic) {
        const topic = String(status.stats.subtopic);
        const normalized = normalizeTopic(topic);
        if (!allTopics.has(normalized)) {
          allTopics.set(normalized, {
            topic,
            normalizedTopic: normalized,
            firstSeen: status.ts,
          });
        }
      }
    });

    // From notes - mark as completed (with normalized matching)
    // Only include notes from the same requestId
    const filteredNotes = activeRequestId
      ? notes.filter((n) => n.requestId === activeRequestId)
      : notes;
    filteredNotes.forEach((note) => {
      const normalizedNoteTopic = normalizeTopic(note.subtopic);
      const topicInfo = allTopics.get(normalizedNoteTopic);
      if (topicInfo) {
        topicInfo.completedAt = note.ts;
      }
    });

    // Create topic steps (sorted by firstSeen timestamp)
    // Use stable ordering: topics get order 100 + index
    const topicSteps: PlanStep[] = Array.from(allTopics.values())
      .sort((a, b) => a.firstSeen - b.firstSeen)
      .map((topicInfo, index) => {
        // Check currentStatus first, then check last status in filteredStatusHistory
        const currentTopicFromStatus =
          typeof currentStatus?.stats?.subtopic === "string"
            ? normalizeTopic(currentStatus.stats.subtopic)
            : null;

        // Also check the last status in history (in case currentStatus is slightly delayed)
        const lastResearchingStatus = filteredStatusHistory
          .filter((s) => s.phase === "researching" && s.stats?.subtopic)
          .slice(-1)[0];
        const lastTopicFromHistory = lastResearchingStatus?.stats?.subtopic
          ? normalizeTopic(String(lastResearchingStatus.stats.subtopic))
          : null;

        // Use currentStatus topic if available, otherwise use last from history
        const currentTopic = currentTopicFromStatus || lastTopicFromHistory;

        const isCompleted = !!topicInfo.completedAt;
        const isActive =
          currentTopic === topicInfo.normalizedTopic &&
          (currentStatus?.phase === "researching" ||
            lastResearchingStatus?.phase === "researching");

        return {
          id: `topic-${topicInfo.topic}`,
          label: topicInfo.topic,
          icon: "topic",
          status: (isCompleted
            ? "completed"
            : isActive
            ? "active"
            : "pending") as "pending" | "active" | "completed",
          description: isCompleted
            ? "Completed"
            : isActive
            ? "Researching..."
            : undefined,
          // Use fixed order: 100 + index to ensure topics stay between Planning and Report
          timestamp: 100 + index,
        };
      });

    // Add topic steps
    steps.push(...topicSteps);

    // 4. Final Report step (always visible, always at the end)
    // Note: Compressing/Organizing is an internal process that happens between topics,
    // not a separate step in the timeline
    const reportingStatus = filteredStatusHistory.find(
      (s) => s.phase === "reporting"
    );
    const isReportingActive = currentStatus?.phase === "reporting";
    // Report is completed only if we have the actual report data
    const isReportingCompleted = !!report;

    steps.push({
      id: "reporting",
      label: "Final Report",
      icon: "report",
      status: isReportingActive
        ? "active"
        : isReportingCompleted
        ? "completed"
        : "pending",
      description: report
        ? "Report ready"
        : reportingStatus
        ? "Writing..."
        : undefined,
      // Force order=10000 (always last)
      timestamp: 10000,
    });

    // Sort by timestamp (simple numeric sort)
    // We use fixed timestamps to ensure stable ordering:
    // - Clarification: 0
    // - Planning: 1
    // - Topics: 100 + index (order of appearance)
    // - Final Report: 10000 (always last)
    steps.sort((a, b) => {
      const aTime = a.timestamp ?? 9999;
      const bTime = b.timestamp ?? 9999;
      return aTime - bTime;
    });

    return steps;
  }, [
    currentStatus,
    statusHistory,
    researchTitle,
    notes,
    report,
    clarification,
  ]);
}
