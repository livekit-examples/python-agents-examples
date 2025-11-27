'use client';

import { RoomAudioRenderer, StartAudio } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { SessionProvider } from '@/components/app/session-provider';
import { ViewController } from '@/components/app/view-controller';
import { Toaster } from '@/components/livekit/toaster';

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  return (
    <SessionProvider appConfig={appConfig}>
      <main className="flex min-h-svh items-center justify-center bg-[#01060a] px-4 py-6">
        <div className="relative aspect-[9/19] min-h-[720px] w-full max-w-[430px] overflow-hidden rounded-[48px] border border-white/10 bg-[#020b10] shadow-[0_55px_160px_rgba(4,12,18,0.85)]">
          <div className="pointer-events-none absolute inset-4 rounded-[40px] border border-white/10" />
          <div className="relative z-10 flex h-full w-full rounded-[40px] bg-[#020b10]">
            <ViewController />
          </div>
        </div>
      </main>
      <StartAudio label="Start Audio" />
      <RoomAudioRenderer />
      <Toaster />
    </SessionProvider>
  );
}
