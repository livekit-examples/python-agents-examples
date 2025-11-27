'use client';

import { Headset } from 'lucide-react';
import { useRoomContext } from '@livekit/components-react';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const room = useRoomContext();
  const isConnecting = room.state === 'connecting';
  // Connection details are fetched on-demand when starting the session in useRoom
  const connectionReady = true;

  const disabled = isConnecting || !connectionReady;

  return (
    <div ref={ref} className="bg-bg0 flex min-h-screen items-center justify-center p-6">
      <div className="bg-bg1 border-separator1 w-full max-w-md rounded-xl border p-8 shadow-sm">
        <div className="flex flex-col items-center gap-6">
          {/* Icon */}
          <div className="bg-bgAccent1/20 border-fgAccent1/30 flex h-16 w-16 items-center justify-center rounded-full border">
            <Headset className="text-fgAccent1 h-8 w-8" />
          </div>

          {/* Title */}
          <div className="flex flex-col items-center gap-2 text-center">
            <h1 className="text-fg0 text-xl font-semibold">Model Battleground</h1>
            <p className="text-fg3 text-sm">Voice AI Model Comparison</p>
            <p className="text-fg4 mt-2 max-w-sm text-xs leading-relaxed">
              Compare different agent capabilities including STT, TTS, and LLM speeds in a
              side-by-side shootout of different models.
            </p>
          </div>

          {/* Local Development Notice */}
          <div className="bg-bgCaution1/20 border-fgCaution1/30 w-full rounded-lg border px-4 py-3">
            <p className="text-fg2 text-center text-xs leading-relaxed">
              <span className="text-fgCaution1 font-semibold">Local development:</span> Make sure to
              run the Python agent first with{' '}
              <code className="bg-bg2 text-fgAccent1 rounded px-1.5 py-0.5 font-mono">
                python agent.py dev
              </code>
            </p>
          </div>

          {/* Documentation Links */}
          <div className="flex items-center gap-4 text-xs">
            <a
              href="https://docs.livekit.io/agents/start/voice-ai/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-fg3 hover:text-fgAccent1 underline transition-colors"
            >
              LiveKit Voice AI Guide
            </a>
            <span className="text-separator2">•</span>
            <a
              href="https://livekit.io/join-slack"
              target="_blank"
              rel="noopener noreferrer"
              className="text-fg3 hover:text-fgAccent1 underline transition-colors"
            >
              LiveKit Slack
            </a>
          </div>

          {/* Connect Button */}
          <button
            type="button"
            onClick={onStartCall}
            disabled={disabled}
            className="bg-fgAccent1 text-bg0 hover:bg-fgAccent2 w-full rounded-lg px-6 py-3 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isConnecting ? 'Connecting…' : startButtonText || 'Connect to Room'}
          </button>

          {/* Connection Status */}
          {!connectionReady && !isConnecting ? (
            <p className="text-fg4 text-xs">Preparing connection details…</p>
          ) : null}
        </div>
      </div>
    </div>
  );
};
