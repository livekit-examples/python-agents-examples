'use client';

import React, { useEffect } from 'react';
import { motion } from 'motion/react';
import { type AgentState, useRoomContext, useVoiceAssistant } from '@livekit/components-react';
import { toastAlert } from '@/components/alert-toast';
import { MedicalNotes } from '@/components/medical-notes';
import { SimpleControlBar } from '@/components/simple-control-bar';
import { useDebugMode } from '@/hooks/useDebug';
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

  useDebugMode({
    enabled: process.env.NODE_END !== 'production',
  });

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

  return (
    <main ref={ref} inert={disabled} className="flex h-screen flex-col overflow-hidden bg-gray-50">
      {/* Main content area - full width medical notes */}
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="h-full max-h-[calc(100vh-200px)] w-full">
          <MedicalNotes className="h-full" />
        </div>
      </div>

      {/* Simple control bar at bottom */}
      <div className="fixed right-0 bottom-0 left-0 z-50 border-t border-gray-200 bg-white/80 px-3 pt-2 pb-6 backdrop-blur-sm md:px-12 md:pb-8">
        <motion.div
          key="control-bar"
          initial={{ opacity: 0, translateY: '100%' }}
          animate={{
            opacity: sessionStarted ? 1 : 0,
            translateY: sessionStarted ? '0%' : '100%',
          }}
          transition={{ duration: 0.3, delay: sessionStarted ? 0.5 : 0, ease: 'easeOut' }}
        >
          <SimpleControlBar />
        </motion.div>
      </div>
    </main>
  );
};
