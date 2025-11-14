'use client';

import React from 'react';
import { Track } from 'livekit-client';
import { useRoomContext, useTrackToggle } from '@livekit/components-react';
import {
  MicrophoneIcon,
  MicrophoneSlashIcon,
  PhoneDisconnectIcon,
} from '@phosphor-icons/react/dist/ssr';
import { Button } from '@/components/ui/button';

export const SimpleControlBar = () => {
  const { buttonProps: micButtonProps, enabled: micEnabled } = useTrackToggle({
    source: Track.Source.Microphone,
  });
  const room = useRoomContext();

  return (
    <div className="flex w-full flex-wrap items-center justify-center gap-4 md:justify-between">
      <div className="hidden min-w-[200px] flex-col text-left md:flex">
        <span className="text-[0.65rem] font-semibold tracking-[0.3em] text-slate-500 uppercase dark:text-slate-300">
          Voice channel
        </span>
        <span className="mt-1 text-sm font-medium text-slate-700 dark:text-slate-200">
          {micEnabled ? 'Microphone live' : 'Microphone muted'}
        </span>
        <span className="text-xs text-slate-500 dark:text-slate-400">
          Toggle to control the clinician-side audio feed.
        </span>
      </div>

      <div className="flex items-center gap-3">
        <Button
          {...micButtonProps}
          size="icon"
          className={`group h-14 w-14 rounded-full border border-white/70 bg-white/90 shadow-lg shadow-slate-500/10 transition will-change-transform hover:-translate-y-0.5 hover:bg-white dark:border-slate-700/60 dark:bg-slate-900/70 ${
            micEnabled
              ? 'text-emerald-600 ring-1 ring-emerald-200/70 dark:text-emerald-200 dark:ring-emerald-400/20'
              : 'text-rose-600 ring-1 ring-rose-200/70 dark:text-rose-200 dark:ring-rose-400/30'
          }`}
        >
          {micEnabled ? (
            <MicrophoneIcon size={26} className="transition-transform group-active:scale-95" />
          ) : (
            <MicrophoneSlashIcon size={26} className="transition-transform group-active:scale-95" />
          )}
          <span className="sr-only">Toggle microphone</span>
        </Button>

        <Button
          onClick={() => room.disconnect()}
          size="lg"
          className="inline-flex items-center gap-3 rounded-full bg-gradient-to-r from-rose-500 via-rose-600 to-red-600 px-6 py-3 text-base font-semibold text-white normal-case shadow-lg shadow-rose-500/30 transition hover:-translate-y-0.5 hover:from-rose-500/90 hover:via-rose-600/90 hover:to-red-600/90 focus-visible:ring-rose-500/40"
        >
          <PhoneDisconnectIcon size={22} />
          <span className="hidden sm:inline">End Consultation</span>
          <span className="sm:hidden">Leave</span>
        </Button>
      </div>
    </div>
  );
};
