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

  const agentStateTokens: Partial<
    Record<
      AgentState,
      {
        label: string;
        badge: string;
        dot: string;
      }
    >
  > = {
    connecting: {
      label: 'Connecting',
      badge:
        'bg-amber-100 text-amber-700 ring-1 ring-white/60 dark:bg-amber-400/20 dark:text-amber-200 dark:ring-amber-200/20',
      dot: 'bg-amber-400',
    },
    listening: {
      label: 'Listening',
      badge:
        'bg-emerald-100 text-emerald-700 ring-1 ring-white/60 dark:bg-emerald-500/20 dark:text-emerald-200 dark:ring-emerald-400/20',
      dot: 'bg-emerald-400',
    },
    thinking: {
      label: 'Processing',
      badge:
        'bg-sky-100 text-sky-700 ring-1 ring-white/60 dark:bg-sky-500/20 dark:text-sky-200 dark:ring-sky-400/20',
      dot: 'bg-sky-400',
    },
    speaking: {
      label: 'Responding',
      badge:
        'bg-indigo-100 text-indigo-700 ring-1 ring-white/60 dark:bg-indigo-500/20 dark:text-indigo-200 dark:ring-indigo-400/20',
      dot: 'bg-indigo-400',
    },
    disconnected: {
      label: 'Agent offline',
      badge:
        'bg-slate-200 text-slate-600 ring-1 ring-white/60 dark:bg-slate-700/50 dark:text-slate-200 dark:ring-slate-600/30',
      dot: 'bg-slate-500',
    },
  };

  const agentStatus = agentStateTokens[agentState] || {
    label: 'Standby',
    badge:
      'bg-slate-200 text-slate-600 ring-1 ring-white/60 dark:bg-slate-700/50 dark:text-slate-200 dark:ring-slate-600/30',
    dot: 'bg-slate-500',
  };

  const sessionStatusBadge = sessionStarted
    ? 'bg-emerald-500/10 text-emerald-600 ring-1 ring-emerald-100 dark:bg-emerald-500/20 dark:text-emerald-200 dark:ring-emerald-400/20'
    : 'bg-slate-200 text-slate-600 ring-1 ring-white/60 dark:bg-slate-700/50 dark:text-slate-200 dark:ring-slate-600/30';

  return (
    <main
      ref={ref}
      inert={disabled}
      className="relative flex h-[100svh] min-h-svh flex-col overflow-hidden px-4 py-6 text-slate-900 sm:px-8 lg:px-12 dark:text-slate-100"
    >
      <div className="mx-auto flex w-full max-w-6xl flex-1 min-h-0 flex-col gap-6">
        <section className="flex flex-1 min-h-0 flex-col overflow-hidden rounded-[2.75rem] border border-white/70 bg-white/80 p-6 shadow-[0_40px_140px_-80px_rgba(15,23,42,0.65)] ring-1 ring-black/5 backdrop-blur-xl transition-all sm:p-8 lg:p-10 dark:border-slate-700/60 dark:bg-slate-900/80 dark:ring-white/10">
          <header className="flex flex-col gap-6 border-b border-slate-200/60 pb-6 lg:flex-row lg:items-center lg:justify-between dark:border-slate-700/60">
            <div className="flex flex-1 flex-col gap-4 sm:flex-row sm:items-center sm:gap-6">
              <div className="flex items-center gap-4">
                <span className="flex size-14 items-center justify-center rounded-3xl bg-gradient-to-br from-sky-100 via-white to-white text-sky-600 shadow-lg ring-1 ring-white/70 dark:from-slate-800 dark:via-slate-900 dark:to-slate-900 dark:text-sky-300 dark:ring-slate-700/60">
                  <svg viewBox="0 0 64 64" aria-hidden="true" className="size-9">
                    <path
                      d="M15 24V40C15 40.7957 14.6839 41.5587 14.1213 42.1213C13.5587 42.6839 12.7956 43 12 43C11.2044 43 10.4413 42.6839 9.87868 42.1213C9.31607 41.5587 9 40.7957 9 40V24C9 23.2044 9.31607 22.4413 9.87868 21.8787C10.4413 21.3161 11.2044 21 12 21C12.7956 21 13.5587 21.3161 14.1213 21.8787C14.6839 22.4413 15 23.2044 15 24ZM22 5C21.2044 5 20.4413 5.31607 19.8787 5.87868C19.3161 6.44129 19 7.20435 19 8V56C19 56.7957 19.3161 57.5587 19.8787 58.1213C20.4413 58.6839 21.2044 59 22 59C22.7956 59 23.5587 58.6839 24.1213 58.1213C24.6839 57.5587 25 56.7957 25 56V8C25 7.20435 24.6839 6.44129 24.1213 5.87868C23.5587 5.31607 22.7956 5 22 5ZM32 13C31.2044 13 30.4413 13.3161 29.8787 13.8787C29.3161 14.4413 29 15.2044 29 16V48C29 48.7957 29.3161 49.5587 29.8787 50.1213C30.4413 50.6839 31.2044 51 32 51C32.7956 51 33.5587 50.6839 34.1213 50.1213C34.6839 49.5587 35 48.7957 35 48V16C35 15.2044 34.6839 14.4413 34.1213 13.8787C33.5587 13.3161 32.7956 13 32 13ZM42 21C41.2043 21 40.4413 21.3161 39.8787 21.8787C39.3161 22.4413 39 23.2044 39 24V40C39 40.7957 39.3161 41.5587 39.8787 42.1213C40.4413 42.6839 41.2043 43 42 43C42.7957 43 43.5587 42.6839 44.1213 42.1213C44.6839 41.5587 45 40.7957 45 40V24C45 23.2044 44.6839 22.4413 44.1213 21.8787C43.5587 21.3161 42.7957 21 42 21ZM52 17C51.2043 17 50.4413 17.3161 49.8787 17.8787C49.3161 18.4413 49 19.2044 49 20V44C49 44.7957 49.3161 45.5587 49.8787 46.1213C50.4413 46.6839 51.2043 47 52 47C52.7957 47 53.5587 46.6839 54.1213 46.1213C54.6839 45.5587 55 44.7957 55 44V20C55 19.2044 54.6839 18.4413 54.1213 17.8787C53.5587 17.3161 52.7957 17 52 17Z"
                      fill="currentColor"
                    />
                  </svg>
                </span>

                <div>
                  <p className="text-xs font-semibold tracking-[0.3em] text-slate-500 uppercase dark:text-slate-300">
                    Live session overview
                  </p>
                  <p className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">
                    {appConfig.pageTitle ?? 'Medical Note Taking Assistant'}
                  </p>
                  <p className="text-sm text-slate-500 dark:text-slate-300">
                    Secure WebRTC session powered by LiveKit Voice AI
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <span
                className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium tracking-[0.2em] uppercase ${sessionStatusBadge}`}
              >
                <span
                  className={`size-2 rounded-full ${
                    sessionStarted ? 'bg-emerald-400' : 'bg-slate-500'
                  }`}
                  aria-hidden="true"
                />
                {sessionStarted ? 'Session live' : 'Awaiting start'}
              </span>
              <span
                className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium tracking-[0.2em] uppercase ${agentStatus.badge}`}
              >
                <span className={`size-2 rounded-full ${agentStatus.dot}`} aria-hidden="true" />
                {agentStatus.label}
              </span>
              <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium tracking-[0.2em] text-slate-600 uppercase ring-1 ring-white/60 dark:bg-slate-800/60 dark:text-slate-200 dark:ring-slate-700/50">
                <span className="size-2 rounded-full bg-sky-400" aria-hidden="true" />
                Encrypted audio
              </span>
            </div>
          </header>

          <div className="mt-8 flex-1 min-h-0 overflow-hidden">
            <MedicalNotes className="h-full min-h-0" />
          </div>
        </section>

        <motion.div
          key="control-bar"
          initial={{ opacity: 0, translateY: '30%' }}
          animate={{
            opacity: sessionStarted ? 1 : 0,
            translateY: sessionStarted ? '0%' : '30%',
          }}
          transition={{ duration: 0.4, delay: sessionStarted ? 0.45 : 0, ease: 'easeOut' }}
          className="pointer-events-none"
        >
          <div className="pointer-events-auto mx-auto w-full max-w-xl rounded-full border border-white/60 bg-white/80 px-4 py-4 shadow-[0_24px_70px_-40px_rgba(15,23,42,0.6)] backdrop-blur-xl dark:border-slate-700/60 dark:bg-slate-900/80">
            <SimpleControlBar />
          </div>
        </motion.div>
      </div>
    </main>
  );
};
