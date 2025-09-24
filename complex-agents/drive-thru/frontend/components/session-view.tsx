'use client';

import React, { useEffect } from 'react';
import {
  type AgentState,
  useRoomContext,
  useVoiceAssistant,
} from '@livekit/components-react';
import { toastAlert } from '@/components/alert-toast';
import { OrderStatus } from '@/components/order-status';
import { AgentControlBar } from '@/components/livekit/agent-control-bar/agent-control-bar';
import type { AppConfig } from '@/lib/types';

function isAgentAvailable(agentState: AgentState) {
  return agentState == 'listening' || agentState == 'thinking' || agentState == 'speaking';
}

interface SessionViewProps {
  appConfig: AppConfig;
  disabled: boolean;
  sessionStarted: boolean;
}

export const SessionView = ({
  appConfig,
  disabled,
  sessionStarted,
  ref,
}: React.ComponentProps<'div'> & SessionViewProps) => {
  const { state: agentState } = useVoiceAssistant();
  const room = useRoomContext();

  useEffect(() => {
    if (sessionStarted) {
      const timeout = setTimeout(() => {
        if (!isAgentAvailable(agentState)) {
          const reason =
            agentState === 'connecting'
              ? 'Agent did not join the room. '
              : 'Agent connected but did not complete initializing. ';

          toastAlert({
            title: 'Session ended',
            description: (
              <p className="w-full">
                {reason}
                <a
                  target="_blank"
                  rel="noopener noreferrer"
                  href="https://docs.livekit.io/agents/start/voice-ai/"
                  className="whitespace-nowrap underline"
                >
                  See quickstart guide
                </a>
                .
              </p>
            ),
          });
          room.disconnect();
        }
      }, 10_000);

      return () => clearTimeout(timeout);
    }
  }, [agentState, sessionStarted, room]);

  // Minimal capabilities - only microphone control
  const capabilities = {
    supportsChatInput: false,
    supportsVideoInput: false,
    supportsScreenShare: false,
  };

  // Only show microphone control
  const controls = {
    microphone: true,
    camera: false,
    screenShare: false,
    chat: false,
    leave: false,
  };

  return (
    <main ref={ref} inert={disabled}>
      {/* Order Status Display - Full Screen */}
      <OrderStatus />
      
      {/* Control Bar with only mic button - positioned far right */}
      {sessionStarted && (
        <div className="fixed bottom-4 right-4 z-50">
          <AgentControlBar
            controls={controls}
            capabilities={capabilities}
            onChatOpenChange={() => {}}
            onSendMessage={async () => {}}
          />
        </div>
      )}
    </main>
  );
};
