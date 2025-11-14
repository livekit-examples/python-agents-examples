import { useRoomContext } from "@livekit/components-react";
import { useState, useEffect, useRef } from "react";
import { RpcInvocationData } from "livekit-client";

export interface ResearchStatus {
  requestId: string;
  phase:
    | "briefing"
    | "researching"
    | "compressing"
    | "reporting"
    | "clarifying";
  title: string;
  message: string;
  progressPct?: number;
  stats: Record<string, unknown>;
  ts: number;
  clarification?: {
    question: string;
    originalQuery: string;
  };
  note?: {
    subtopic: string;
    summaryMarkdown: string;
    citations: Array<{
      id: string;
      url: string;
      title: string;
      quote: string;
    }>;
  };
  report?: {
    title: string;
    content: string;
    sizeBytes: number;
    numSources: number;
  };
}

export interface ResearchNote {
  requestId: string;
  subtopic: string;
  summaryMarkdown: string;
  citations: Array<{
    id: string;
    url: string;
    title: string;
    quote: string;
    publishedAt?: string;
  }>;
  ts: number;
}

export interface Report {
  requestId: string;
  reportTitle: string;
  reportContent: string;
  sizeBytes: number;
  numSources: number;
}

export interface Clarification {
  requestId: string;
  question: string;
  originalQuery: string;
  ts: number;
}

const STORAGE_KEY = "exa-research-state";

interface PersistedState {
  currentStatus: ResearchStatus | null;
  statusHistory: ResearchStatus[];
  notes: ResearchNote[];
  report: Report | null;
  researchTitle: string | null;
  clarification: Clarification | null;
}

function loadStateFromStorage(): PersistedState | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return null;
    return JSON.parse(stored) as PersistedState;
  } catch (error) {
    console.error("Failed to load state from localStorage:", error);
    return null;
  }
}

function saveStateToStorage(state: PersistedState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (error) {
    console.error("Failed to save state to localStorage:", error);
  }
}

function clearStateFromStorage(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error("Failed to clear state from localStorage:", error);
  }
}

export function useResearchStatus() {
  const room = useRoomContext();

  const initialState = loadStateFromStorage();

  const [currentStatus, setCurrentStatus] = useState<ResearchStatus | null>(
    initialState?.currentStatus ?? null
  );
  const [statusHistory, setStatusHistory] = useState<ResearchStatus[]>(
    initialState?.statusHistory ?? []
  );
  const [notes, setNotes] = useState<ResearchNote[]>(initialState?.notes ?? []);
  const [report, setReport] = useState<Report | null>(
    initialState?.report ?? null
  );
  const [researchTitle, setResearchTitle] = useState<string | null>(
    initialState?.researchTitle ?? null
  );
  const [clarification, setClarification] = useState<Clarification | null>(
    initialState?.clarification ?? null
  );
  const seenStatusIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    const state: PersistedState = {
      currentStatus,
      statusHistory,
      notes,
      report,
      researchTitle,
      clarification,
    };
    saveStateToStorage(state);
  }, [
    currentStatus,
    statusHistory,
    notes,
    report,
    researchTitle,
    clarification,
  ]);

  useEffect(() => {
    if (!room) return;

    const handleStatusRpc = async (
      rpcInvocation: RpcInvocationData
    ): Promise<string> => {
      try {
        const payload = JSON.parse(rpcInvocation.payload) as ResearchStatus;

        const statusId = `${payload.requestId}:${payload.phase}:${payload.title}:${payload.message}:${payload.ts}`;

        if (seenStatusIds.current.has(statusId)) {
          return JSON.stringify({ success: true, duplicate: true });
        }

        seenStatusIds.current.add(statusId);

        setCurrentStatus(payload);
        setStatusHistory((prev) => [...prev, payload].slice(-50));

        if (payload.clarification) {
          setClarification({
            requestId: payload.requestId,
            question: payload.clarification.question,
            originalQuery: payload.clarification.originalQuery,
            ts: payload.ts,
          });
        }

        if (payload.note) {
          const note = payload.note;
          setNotes((prev) => [
            ...prev,
            {
              requestId: payload.requestId,
              subtopic: note.subtopic,
              summaryMarkdown: note.summaryMarkdown,
              citations: note.citations,
              ts: payload.ts,
            },
          ]);
        }

        if (payload.report) {
          const reportData = payload.report;
          setReport({
            requestId: payload.requestId,
            reportTitle: reportData.title,
            reportContent: reportData.content,
            sizeBytes: reportData.sizeBytes,
            numSources: reportData.numSources,
          });
          setResearchTitle((prev) => prev || reportData.title);
        }

        if (payload.title && payload.title !== "Planning research") {
          setResearchTitle((prev) => {
            if (!prev || prev === "Planning research") {
              return payload.title;
            }
            return prev;
          });
        }

        return JSON.stringify({ success: true });
      } catch (error) {
        console.error("Error handling status RPC:", error);
        return JSON.stringify({ success: false, error: String(error) });
      }
    };

    const setupRpcHandlers = async () => {
      if (room.state !== "connected") {
        await new Promise<void>((resolve) => {
          const checkConnection = () => {
            if (room.state === "connected") {
              resolve();
            } else {
              setTimeout(checkConnection, 100);
            }
          };
          checkConnection();
        });
      }

      try {
        try {
          room.unregisterRpcMethod("exa.research/status");
        } catch {
          // Ignore errors
        }
        room.registerRpcMethod("exa.research/status", handleStatusRpc);
      } catch (error) {
        console.error("Error registering RPC methods:", error);
      }
    };

    setupRpcHandlers();

    const handleReportByteStream = async (reader: {
      info: { attributes?: { requestId?: string }; mimeType?: string };
      readAll: () => Promise<Uint8Array[]>;
    }) => {
      try {
        const requestId = reader.info.attributes?.requestId || "";
        const chunks = await reader.readAll();
        const blob = new Blob(chunks as BlobPart[], {
          type: reader.info.mimeType || "application/json",
        });
        const text = await blob.text();
        const reportData = JSON.parse(text) as ResearchStatus;

        if (reportData.report) {
          setReport({
            requestId: reportData.requestId || requestId,
            reportTitle: reportData.report.title,
            reportContent: reportData.report.content,
            sizeBytes: reportData.report.sizeBytes,
            numSources: reportData.report.numSources,
          });
          setResearchTitle((prev) => prev || reportData.report!.title);
          setCurrentStatus(reportData);
          setStatusHistory((prev) => [...prev, reportData].slice(-50));
        }
      } catch (error) {
        console.error("Failed to process report byte stream:", error);
      }
    };

    if (room) {
      room.registerByteStreamHandler(
        "exa_research_report",
        handleReportByteStream
      );
    }

    return () => {
      if (room) {
        try {
          room.unregisterRpcMethod("exa.research/status");
          room.unregisterByteStreamHandler("exa_research_report");
        } catch (e) {
          console.error("Error unregistering RPC/byte stream handlers:", e);
        }
      }
    };
  }, [room]);

  return {
    currentStatus,
    statusHistory,
    notes,
    report,
    researchTitle,
    clarification,
    reset: () => {
      setCurrentStatus(null);
      setStatusHistory([]);
      setNotes([]);
      setReport(null);
      setResearchTitle(null);
      setClarification(null);
      seenStatusIds.current.clear();
      clearStateFromStorage();
    },
  };
}
