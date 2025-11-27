'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { RoomEvent } from 'livekit-client';
import type { RemoteTrackPublication, RpcInvocationData } from 'livekit-client';
import { useRoomContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import {
  AgentControlBar,
  type ControlBarControls,
} from '@/components/livekit/agent-control-bar/agent-control-bar';
import { useChatMessages } from '@/hooks/useChatMessages';
import { useConnectionTimeout } from '@/hooks/useConnectionTimout';
import { useDebugMode } from '@/hooks/useDebug';
import { cn } from '@/lib/utils';
import { AgentCard, type AgentMetrics, type ChatMessage } from './agent-card';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

interface SessionViewProps {
  appConfig: AppConfig;
}

interface MetricDatumPayload {
  label?: string;
  value?: number;
  latency_ms?: number;
}

interface AgentMetricsRpcPayload {
  agent_id?: string;
  participant_identity?: string;
  stt?: MetricDatumPayload;
  llm?: MetricDatumPayload;
  tts?: MetricDatumPayload;
}

interface AgentStatusRpcPayload {
  agent_id?: string;
  participant_identity?: string;
  connected?: boolean;
}

interface AgentTranscriptRpcPayload {
  agent_id?: string;
  participant_identity?: string;
  message_id?: string;
  text?: string;
  is_final?: boolean;
  speaker_id?: string;
  ts?: number;
}

const METRICS_RPC_TOPIC = 'model_battleground.agent.metrics';
const DISPATCH_RPC_TOPIC = 'model_battleground.agent.dispatch';
const STATUS_RPC_TOPIC = 'model_battleground.agent.status';
const TRANSCRIPT_RPC_TOPIC = 'model_battleground.agent.transcript';
const AGENT_ONE_ID = 'agent-1';
const AGENT_ONE_NAME = 'Agent 1';

type MetricDatum = AgentMetrics['stt'];

interface AgentCardDefinition {
  id: string;
  name: string;
  dispatchAgentName?: string;
  participantIdentities?: string[];
  initialMetrics: AgentMetrics;
  initialMessages?: ChatMessage[];
}

interface AgentChatLogEntry {
  message: ChatMessage;
  timestamp: number;
}

const AGENT_CARD_DEFINITIONS: AgentCardDefinition[] = [
  {
    id: AGENT_ONE_ID,
    name: AGENT_ONE_NAME,
    participantIdentities: ['agent', 'agent-1', 'battleground-agent'],
    initialMetrics: {
      stt: { label: 'STT (assemblyai/universal-streaming)', value: 0, latencyMs: 0 },
      llm: { label: 'LLM (gpt-4.1-mini)', value: 0, latencyMs: 0 },
      tts: { label: 'TTS (cartesia/sonic-3)', value: 0, latencyMs: 0 },
    },
  },
  {
    id: 'agent-2',
    name: 'Agent 2',
    dispatchAgentName: 'devday-battleground-agent-2',
    participantIdentities: ['devday-battleground-agent-2'],
    initialMetrics: {
      stt: { label: 'STT (TBD)', value: 22, latencyMs: 110 },
      llm: { label: 'LLM (TBD)', value: 18, latencyMs: 180 },
      tts: { label: 'TTS (TBD)', value: 19, latencyMs: 95 },
    },
    initialMessages: [],
  },
  {
    id: 'agent-3',
    name: 'Agent 3',
    dispatchAgentName: 'devday-battleground-agent-3',
    participantIdentities: ['devday-battleground-agent-3'],
    initialMetrics: {
      stt: { label: 'STT (TBD)', value: 15, latencyMs: 75 },
      llm: { label: 'LLM (TBD)', value: 21, latencyMs: 210 },
      tts: { label: 'TTS (TBD)', value: 28, latencyMs: 140 },
    },
    initialMessages: [],
  },
];

const AGENT_DEFINITION_BY_ID = AGENT_CARD_DEFINITIONS.reduce<Record<string, AgentCardDefinition>>(
  (acc, definition) => {
    acc[definition.id] = definition;
    return acc;
  },
  {}
);

const INITIAL_IDENTITY_TO_AGENT_ID = AGENT_CARD_DEFINITIONS.reduce<Record<string, string>>(
  (acc, definition) => {
    definition.participantIdentities?.forEach((identity) => {
      acc[identity] = definition.id;
    });
    return acc;
  },
  {}
);

const cloneMetrics = (metrics: AgentMetrics): AgentMetrics => ({
  stt: { ...metrics.stt },
  llm: { ...metrics.llm },
  tts: { ...metrics.tts },
});

const buildDefaultAgentMetrics = () =>
  AGENT_CARD_DEFINITIONS.reduce<Record<string, AgentMetrics>>((acc, definition) => {
    acc[definition.id] = cloneMetrics(definition.initialMetrics);
    return acc;
  }, {});

const DEFAULT_AGENT_STATUSES = AGENT_CARD_DEFINITIONS.reduce<Record<string, boolean>>(
  (acc, definition) => {
    acc[definition.name] = definition.id === AGENT_ONE_ID;
    return acc;
  },
  {}
);

const clampMetricValue = (value: unknown, fallback: number): number => {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return fallback;
  }
  return Math.max(0, Math.min(100, value));
};

const clampLatencyMs = (value: unknown, fallback: number): number => {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return fallback;
  }
  return Math.max(0, value);
};

const coerceMetricDatum = (
  datum: MetricDatumPayload | undefined,
  fallback: MetricDatum
): MetricDatum => {
  const label =
    typeof datum?.label === 'string' && datum.label.trim().length > 0
      ? datum.label
      : fallback.label;
  const value = clampMetricValue(datum?.value, fallback.value);
  const latencyMs = clampLatencyMs(datum?.latency_ms, fallback.latencyMs);
  return { label, value, latencyMs };
};

const INITIAL_MESSAGE_TIMESTAMP = 0;
const TIMESTAMP_INCREMENT = 1;

const coerceTimestamp = (value: unknown, fallback: number): number => {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return fallback;
  }
  return value;
};

export const SessionView = ({
  appConfig,
  ...props
}: React.ComponentProps<'section'> & SessionViewProps) => {
  useConnectionTimeout(200_000);
  useDebugMode({ enabled: IN_DEVELOPMENT });

  const controlBarRef = useRef<HTMLElement | null>(null);
  const [controlBarHeight, setControlBarHeight] = useState(0);
  const room = useRoomContext();
  const livekitMessages = useChatMessages();
  const [agentMetrics, setAgentMetrics] = useState<Record<string, AgentMetrics>>(() =>
    buildDefaultAgentMetrics()
  );
  const [agentStatuses, setAgentStatuses] =
    useState<Record<string, boolean>>(DEFAULT_AGENT_STATUSES);
  const [dispatchingAgents, setDispatchingAgents] = useState<Record<string, boolean>>({});
  const [identityToAgentId, setIdentityToAgentId] = useState<Record<string, string>>(
    INITIAL_IDENTITY_TO_AGENT_ID
  );
  const [activeAgentId, setActiveAgentId] = useState<string>(AGENT_ONE_ID);
  const [userTranscriptMessages, setUserTranscriptMessages] = useState<
    Record<string, AgentChatLogEntry[]>
  >({});
  const [highlightedAgentId, setHighlightedAgentId] = useState<string>(AGENT_ONE_ID);

  useEffect(() => {
    setUserTranscriptMessages({});
    setHighlightedAgentId(AGENT_ONE_ID);
  }, [room?.name]);

  useEffect(() => {
    const recalcHeight = () => {
      setControlBarHeight(controlBarRef.current?.offsetHeight ?? 0);
    };

    recalcHeight();
    window.addEventListener('resize', recalcHeight);
    return () => {
      window.removeEventListener('resize', recalcHeight);
    };
  }, []);

  const { messagesByAgent, pendingIdentityAssignments } = useMemo(() => {
    const base = AGENT_CARD_DEFINITIONS.reduce<Record<string, AgentChatLogEntry[]>>(
      (acc, definition) => {
        const initialMessages = definition.initialMessages
          ? definition.initialMessages.map((message, index) => ({
              message: { ...message },
              timestamp: INITIAL_MESSAGE_TIMESTAMP + index * TIMESTAMP_INCREMENT,
            }))
          : [];
        acc[definition.id] = initialMessages;
        return acc;
      },
      {}
    );
    const pending: Record<string, string> = {};

    const appendMessage = (agentId: string, entry: AgentChatLogEntry) => {
      if (!base[agentId]) {
        base[agentId] = [];
      }
      base[agentId] = [...base[agentId], entry];
    };

    Object.entries(userTranscriptMessages).forEach(([agentId, transcripts]) => {
      if (!transcripts || transcripts.length === 0) {
        return;
      }
      transcripts.forEach((entry) => {
        appendMessage(agentId, entry);
      });
    });

    let currentAgentId = activeAgentId || AGENT_ONE_ID;

    livekitMessages.forEach((message) => {
      const identity = message.from?.identity;
      const isUser = message.from?.isLocal ?? false;
      const messageTimestamp = coerceTimestamp(message.timestamp, Date.now());
      if (isUser && message.source === 'transcription') {
        return;
      }
      let agentId = identity ? identityToAgentId[identity] : undefined;

      if (!agentId) {
        agentId = currentAgentId;
        if (!isUser && identity) {
          pending[identity] = agentId;
        }
      }

      if (!agentId) {
        return;
      }

      currentAgentId = agentId;

      const payload: ChatMessage = {
        id: message.id ?? `${message.timestamp}-${agentId}`,
        text: message.message,
        isUser,
      };
      appendMessage(agentId, { message: payload, timestamp: messageTimestamp });
    });

    const sortedMessages = Object.entries(base).reduce<Record<string, ChatMessage[]>>(
      (acc, [agentId, entries]) => {
        const sorted = entries.length
          ? [...entries].sort((a, b) => a.timestamp - b.timestamp).map((entry) => entry.message)
          : [];
        acc[agentId] = sorted;
        return acc;
      },
      {}
    );

    return { messagesByAgent: sortedMessages, pendingIdentityAssignments: pending };
  }, [activeAgentId, identityToAgentId, livekitMessages, userTranscriptMessages]);

  useEffect(() => {
    const identities = Object.keys(pendingIdentityAssignments);
    if (identities.length === 0) {
      return;
    }
    setIdentityToAgentId((prev) => {
      let changed = false;
      const next = { ...prev };
      identities.forEach((identity) => {
        const agentId = pendingIdentityAssignments[identity];
        if (!agentId) {
          return;
        }
        if (next[identity] !== agentId) {
          next[identity] = agentId;
          changed = true;
        }
      });
      return changed ? next : prev;
    });
  }, [pendingIdentityAssignments]);

  const dispatchAgent = useCallback(
    async (displayName: string, agentName: string) => {
      const currentRoom = room;
      if (!currentRoom || !currentRoom.localParticipant) {
        throw new Error('Room is not ready for dispatch');
      }

      const remoteParticipants = Array.from(currentRoom.remoteParticipants.values());
      if (remoteParticipants.length === 0) {
        throw new Error('No remote agent participants available for dispatch RPC');
      }

      let lastError: unknown = null;
      for (const participant of remoteParticipants) {
        try {
          const response = await currentRoom.localParticipant.performRpc({
            destinationIdentity: participant.identity,
            method: DISPATCH_RPC_TOPIC,
            payload: JSON.stringify({
              agent_name: agentName,
              metadata: { display_name: displayName },
            }),
          });
          const parsed = response ? JSON.parse(response) : null;
          if (parsed?.success) {
            return parsed;
          }
          lastError = parsed?.error ?? 'dispatch rejected';
        } catch (error) {
          lastError = error;
        }
      }

      if (lastError instanceof Error) {
        throw lastError;
      }
      throw new Error(String(lastError ?? 'dispatch failed'));
    },
    [room]
  );

  const handleDispatch = useCallback(
    async (agentId: string, displayName: string, agentName: string) => {
      setDispatchingAgents((prev) => ({ ...prev, [agentId]: true }));
      try {
        await dispatchAgent(displayName, agentName);
        setActiveAgentId(agentId);
      } catch (error) {
        console.error('Failed to dispatch agent:', error);
        setDispatchingAgents((prev) => {
          if (!prev[agentId]) {
            return prev;
          }
          const next = { ...prev };
          delete next[agentId];
          return next;
        });
      }
    },
    [dispatchAgent]
  );

  const lastAgentStatusesRef = useRef(agentStatuses);

  useEffect(() => {
    const previousStatuses = lastAgentStatusesRef.current;
    const newlyConnectedAgents = AGENT_CARD_DEFINITIONS.filter(({ name }) => {
      return !previousStatuses[name] && agentStatuses[name];
    });
    if (newlyConnectedAgents.length === 0) {
      lastAgentStatusesRef.current = agentStatuses;
      return;
    }

    setDispatchingAgents((prev) => {
      let nextState: Record<string, boolean> | null = null;
      newlyConnectedAgents.forEach(({ id }) => {
        if (prev[id]) {
          if (!nextState) {
            nextState = { ...prev };
          }
          delete nextState[id];
        }
      });
      return nextState ?? prev;
    });

    lastAgentStatusesRef.current = agentStatuses;
  }, [agentStatuses]);

  useEffect(() => {
    if (!room) {
      return;
    }

    const updateSubscriptions = () => {
      const targetAgentId = highlightedAgentId || activeAgentId || AGENT_ONE_ID;
      const allowedIdentities = new Set(
        Object.entries(identityToAgentId)
          .filter(([, agentId]) => agentId === targetAgentId)
          .map(([identity]) => identity)
      );

      room.remoteParticipants.forEach((participant) => {
        const shouldSubscribe = allowedIdentities.has(participant.identity);
        participant.getTrackPublications().forEach((publication) => {
          const remotePublication = publication as RemoteTrackPublication;
          if (remotePublication.isSubscribed !== shouldSubscribe) {
            remotePublication.setSubscribed(shouldSubscribe);
          }
        });
      });
    };

    updateSubscriptions();

    const subscriptionEvents = [
      RoomEvent.ParticipantConnected,
      RoomEvent.ParticipantDisconnected,
      RoomEvent.TrackPublished,
      RoomEvent.TrackUnpublished,
    ] as const;

    subscriptionEvents.forEach((event) => {
      room.on(event, updateSubscriptions);
    });

    return () => {
      subscriptionEvents.forEach((event) => {
        room.off(event, updateSubscriptions);
      });
    };
  }, [room, highlightedAgentId, identityToAgentId, activeAgentId]);

  useEffect(() => {
    if (!room) return;

    let isMounted = true;

    const waitForConnection = async () => {
      if (room.state === 'connected') {
        return;
      }
      await new Promise<void>((resolve) => {
        const checkConnection = () => {
          if (room.state === 'connected') {
            resolve();
          } else {
            setTimeout(checkConnection, 100);
          }
        };
        checkConnection();
      });
    };

    const handleMetricsRpc = async (rpcInvocation: RpcInvocationData): Promise<string> => {
      try {
        if (!rpcInvocation.payload) {
          return JSON.stringify({ success: false, error: 'empty payload' });
        }
        const payload = JSON.parse(rpcInvocation.payload) as AgentMetricsRpcPayload;
        const agentId = payload.agent_id;
        if (!isMounted || !agentId) {
          return JSON.stringify({ success: true });
        }

        setAgentMetrics((prev) => {
          const existing = prev[agentId];
          const fallbackDefinition =
            AGENT_DEFINITION_BY_ID[agentId] ?? AGENT_DEFINITION_BY_ID[AGENT_ONE_ID];
          const fallback = existing ?? cloneMetrics(fallbackDefinition.initialMetrics);

          return {
            ...prev,
            [agentId]: {
              stt: coerceMetricDatum(payload.stt, fallback.stt),
              llm: coerceMetricDatum(payload.llm, fallback.llm),
              tts: coerceMetricDatum(payload.tts, fallback.tts),
            },
          };
        });

        const agentDefinition = AGENT_DEFINITION_BY_ID[agentId];
        if (agentDefinition) {
          setAgentStatuses((prev) => {
            if (prev[agentDefinition.name]) {
              return prev;
            }
            return { ...prev, [agentDefinition.name]: true };
          });
          setActiveAgentId(agentDefinition.id);
        }
        const participantIdentity = payload.participant_identity;
        if (participantIdentity) {
          setIdentityToAgentId((prev) => {
            if (prev[participantIdentity] === agentId) {
              return prev;
            }
            return {
              ...prev,
              [participantIdentity]: agentId,
            };
          });
        }

        return JSON.stringify({ success: true });
      } catch (error) {
        console.error('Failed to handle agent metrics RPC:', error);
        return JSON.stringify({ success: false, error: String(error) });
      }
    };

    const handleStatusRpc = async (rpcInvocation: RpcInvocationData): Promise<string> => {
      try {
        if (!rpcInvocation.payload) {
          return JSON.stringify({ success: false, error: 'empty payload' });
        }
        const payload = JSON.parse(rpcInvocation.payload) as AgentStatusRpcPayload;
        const agentId = payload.agent_id;
        if (!isMounted || !agentId) {
          return JSON.stringify({ success: true });
        }

        const agentDefinition = AGENT_DEFINITION_BY_ID[agentId];
        if (!agentDefinition) {
          return JSON.stringify({ success: true });
        }

        const connected = payload.connected === undefined ? true : Boolean(payload.connected);
        setAgentStatuses((prev) => {
          if (prev[agentDefinition.name] === connected) {
            return prev;
          }
          return { ...prev, [agentDefinition.name]: connected };
        });

        if (connected) {
          setActiveAgentId(agentDefinition.id);
        }

        if (payload.participant_identity) {
          setIdentityToAgentId((prev) => {
            if (prev[payload.participant_identity!] === agentId) {
              return prev;
            }
            return {
              ...prev,
              [payload.participant_identity!]: agentId,
            };
          });
        }

        return JSON.stringify({ success: true });
      } catch (error) {
        console.error('Failed to handle agent status RPC:', error);
        return JSON.stringify({ success: false, error: String(error) });
      }
    };

    const handleTranscriptRpc = async (rpcInvocation: RpcInvocationData): Promise<string> => {
      try {
        if (!rpcInvocation.payload) {
          return JSON.stringify({ success: false, error: 'empty payload' });
        }
        const payload = JSON.parse(rpcInvocation.payload) as AgentTranscriptRpcPayload;
        const agentId = payload.agent_id;
        if (!isMounted || !agentId || typeof payload.text !== 'string') {
          return JSON.stringify({ success: true });
        }

        const agentDefinition = AGENT_DEFINITION_BY_ID[agentId];
        if (!agentDefinition) {
          return JSON.stringify({ success: true });
        }

        const messageId = payload.message_id || `${payload.ts ?? Date.now()}-${agentId}`;
        const timestampMs =
          typeof payload.ts === 'number' && Number.isFinite(payload.ts)
            ? payload.ts * 1000
            : Date.now();
        const nextMessage: ChatMessage = {
          id: messageId,
          text: payload.text,
          isUser: true,
        };

        setUserTranscriptMessages((prev) => {
          const existing = prev[agentId] ?? [];
          const index = existing.findIndex((entry) => entry.message.id === messageId);
          let updated: AgentChatLogEntry[];
          if (index === -1) {
            updated = [...existing, { message: nextMessage, timestamp: timestampMs }];
          } else {
            updated = [...existing];
            updated[index] = { message: nextMessage, timestamp: timestampMs };
          }
          return {
            ...prev,
            [agentId]: updated,
          };
        });

        setAgentStatuses((prev) => {
          if (prev[agentDefinition.name]) {
            return prev;
          }
          return { ...prev, [agentDefinition.name]: true };
        });
        setActiveAgentId(agentDefinition.id);

        if (payload.participant_identity) {
          setIdentityToAgentId((prev) => {
            if (prev[payload.participant_identity!] === agentId) {
              return prev;
            }
            return {
              ...prev,
              [payload.participant_identity!]: agentId,
            };
          });
        }

        return JSON.stringify({ success: true });
      } catch (error) {
        console.error('Failed to handle agent transcript RPC:', error);
        return JSON.stringify({ success: false, error: String(error) });
      }
    };

    const registerRpcHandlers = async () => {
      await waitForConnection();
      try {
        try {
          room.unregisterRpcMethod(METRICS_RPC_TOPIC);
        } catch {
          // ignore cleanup errors
        }
        try {
          room.unregisterRpcMethod(STATUS_RPC_TOPIC);
        } catch {
          // ignore cleanup errors
        }
        try {
          room.unregisterRpcMethod(TRANSCRIPT_RPC_TOPIC);
        } catch {
          // ignore cleanup errors
        }
        room.registerRpcMethod(METRICS_RPC_TOPIC, handleMetricsRpc);
        room.registerRpcMethod(STATUS_RPC_TOPIC, handleStatusRpc);
        room.registerRpcMethod(TRANSCRIPT_RPC_TOPIC, handleTranscriptRpc);
      } catch (error) {
        console.error('Error registering agent RPC handlers:', error);
      }
    };

    registerRpcHandlers();

    return () => {
      isMounted = false;
      try {
        room.unregisterRpcMethod(METRICS_RPC_TOPIC);
      } catch (error) {
        console.error('Error unregistering agent metrics RPC handler:', error);
      }
      try {
        room.unregisterRpcMethod(STATUS_RPC_TOPIC);
      } catch (error) {
        console.error('Error unregistering agent status RPC handler:', error);
      }
      try {
        room.unregisterRpcMethod(TRANSCRIPT_RPC_TOPIC);
      } catch (error) {
        console.error('Error unregistering agent transcript RPC handler:', error);
      }
    };
  }, [room]);

  const controls: ControlBarControls = {
    leave: true,
    microphone: true,
    chat: appConfig.supportsChatInput,
  };

  const contentPaddingBottom = controlBarHeight > 0 ? controlBarHeight + 16 : 0;
  const agentCards = AGENT_CARD_DEFINITIONS.map((definition) => {
    const metrics = agentMetrics[definition.id] ?? definition.initialMetrics;
    const messages = messagesByAgent[definition.id] ?? definition.initialMessages ?? [];

    return {
      name: definition.name,
      metrics,
      messages,
      isDispatched: agentStatuses[definition.name] ?? false,
      isDispatching: Boolean(dispatchingAgents[definition.id]),
      isHighlighted: highlightedAgentId === definition.id,
      onDispatch: definition.dispatchAgentName
        ? () => handleDispatch(definition.id, definition.name, definition.dispatchAgentName!)
        : undefined,
      onHover: () => setHighlightedAgentId(definition.id),
    };
  });

  return (
    <section
      className={cn(
        'bg-bg0 relative z-10 flex h-full w-full flex-col overflow-hidden pt-6 md:pt-28',
        props.className
      )}
    >
      {/* Main Content */}
      <main
        className="flex-1 overflow-hidden px-4 py-8 md:px-10"
        style={{ paddingBottom: `${contentPaddingBottom}px` }}
      >
        <div className="mx-auto grid h-full max-w-7xl grid-cols-1 gap-6 md:gap-8 lg:grid-cols-3">
          {agentCards.map((agent) => (
            <AgentCard
              key={agent.name}
              agentName={agent.name}
              metrics={agent.metrics}
              messages={agent.messages}
              isDispatched={agent.isDispatched}
              isDispatching={agent.isDispatching}
              isHighlighted={agent.isHighlighted}
              onDispatch={agent.onDispatch}
              onHover={agent.onHover}
            />
          ))}
        </div>
      </main>

      {/* Bottom Control Bar - matching drive-thru style */}
      <section
        ref={controlBarRef}
        className="border-separator1 bg-bg1 fixed inset-x-0 bottom-0 z-50 border-t px-4 py-6 shadow-[0_-12px_20px_-18px_rgba(0,0,0,0.35)]"
      >
        <AgentControlBar
          controls={controls}
          onChatOpenChange={() => {}}
          className="mx-auto w-full max-w-xl"
        />
      </section>
    </section>
  );
};
