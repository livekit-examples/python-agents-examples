'use client';

import { type ComponentProps, useContext, useEffect, useMemo, useRef, useState } from 'react';
import type { RpcInvocationData } from 'livekit-client';
import { RoomContext } from '@livekit/components-react';
import type { Icon } from '@phosphor-icons/react';
import {
  Microphone,
  MicrophoneSlash,
  PhoneDisconnect,
  Warning,
} from '@phosphor-icons/react/dist/ssr';
import type { AppConfig } from '@/app-config';
import { ChatTranscript } from '@/components/app/chat-transcript';
import { useSession } from '@/components/app/session-provider';
import { useInputControls } from '@/components/livekit/agent-control-bar/hooks/use-input-controls';
import { ScrollArea } from '@/components/livekit/scroll-area/scroll-area';
import { useChatMessages } from '@/hooks/useChatMessages';
import { useConnectionTimeout } from '@/hooks/useConnectionTimout';
import { useDebugMode } from '@/hooks/useDebug';
import { cn } from '@/lib/utils';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

interface SessionViewProps {
  appConfig: AppConfig;
}

export const SessionView = ({
  appConfig,
  ...props
}: ComponentProps<'section'> & SessionViewProps) => {
  useConnectionTimeout(200_000);
  useDebugMode({ enabled: IN_DEVELOPMENT });

  const messages = useChatMessages();
  const { endSession } = useSession();
  const { microphoneToggle } = useInputControls();
  const room = useContext(RoomContext);

  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [transcriptOpen, setTranscriptOpen] = useState(false);
  const [safetyAlert, setSafetyAlert] = useState<SafetyAlert>();
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds((seconds) => seconds + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!transcriptOpen || !scrollAreaRef.current) return;
    scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
  }, [messages, transcriptOpen]);

  const formattedTimer = useMemo(() => {
    const minutes = Math.floor(elapsedSeconds / 60)
      .toString()
      .padStart(2, '0');
    const seconds = (elapsedSeconds % 60).toString().padStart(2, '0');
    return `${minutes}:${seconds}`;
  }, [elapsedSeconds]);

  const handleToggleMic = () => {
    void microphoneToggle.toggle(!microphoneToggle.enabled);
  };

  const handleToggleTranscript = () => setTranscriptOpen((open) => !open);

  const handleEndCall = () => {
    endSession();
  };

  useEffect(() => {
    if (!room) return;
    const localParticipant = room.localParticipant;
    if (!localParticipant) return;

    const decoder = new TextDecoder();
    const decodePayload = (payload: RpcInvocationData['payload']) => {
      if (!payload) {
        return '';
      }
      if (typeof payload === 'string') {
        return payload;
      }
      if (Object.prototype.toString.call(payload) === '[object Uint8Array]') {
        return decoder.decode(payload as Uint8Array);
      }
      if (Object.prototype.toString.call(payload) === '[object ArrayBuffer]') {
        return decoder.decode(new Uint8Array(payload as ArrayBuffer));
      }
      return String(payload);
    };

    const handleViolation = async (rpcData: RpcInvocationData): Promise<string> => {
      try {
        const text = decodePayload(rpcData.payload);
        const data = text ? JSON.parse(text) : {};
        const severity = typeof data.severity === 'string' ? data.severity : undefined;
        const description = typeof data.description === 'string' ? data.description : undefined;

        const detailMessage =
          description || 'The moderation agent flagged this conversation for review.';
        const severityTitle = severity
          ? `Possible policy violation (${severity.toLowerCase()})`
          : 'Possible policy violation';

        setSafetyAlert({
          title: severityTitle,
          detail: detailMessage,
        });
        return JSON.stringify({ success: true });
      } catch (error) {
        console.error('Failed to handle moderation violation RPC', error);
        return JSON.stringify({ success: false, error: String(error) });
      }
    };

    localParticipant.registerRpcMethod('moderation.show_violation', handleViolation);

    return () => {
      localParticipant.unregisterRpcMethod('moderation.show_violation');
    };
  }, [room]);

  return (
    <section
      className="relative flex h-full w-full flex-col overflow-hidden bg-[#030d11]"
      {...props}
    >
      <div className="absolute inset-0 opacity-40">
        <div
          className="h-full w-full bg-cover bg-center"
          style={{
            backgroundImage:
              "url('https://lh3.googleusercontent.com/aida-public/AB6AXuBb3vSzkuF7OlLQ0IbS-7KFjK2K_OL8p58yb1-29EZV23z4bcY3DbdPgM7CGXWxOYl3ZvWzeYKeymLfFUBTzoQM2yRr4H2LPNSuCOj1bJrWWY4AH9vv4QuASM7OcnYi-2a8p1XaSy__gN4m1wloykDkKpcu52URFHmolJqxc7ymdw1A3Cwcw4xWgcAXRjhQJmA4GjxHuTIcq0zsX0jA6LQDDBq5XfQ-4k_NeQ96YUSNkchNfKTpbhVJn_T72A7BFZ7gVyJ5MurtBO4')",
          }}
        >
          <div className="h-full w-full bg-gradient-to-b from-transparent via-[#030d11]/70 to-[#030d11]" />
        </div>
      </div>

      <div className="relative z-10 flex flex-1 flex-col">
        <div className="px-6 pt-10">
          <div className="rounded-3xl border border-white/10 bg-black/50 p-4 text-white backdrop-blur">
            <p className="text-[11px] tracking-[0.5em] text-white/45 uppercase">
              {appConfig.companyName} dispatch
            </p>
            <div className="mt-1 flex items-center justify-between text-sm text-white/70">
              <span>Connected to Esteban</span>
              <span>{formattedTimer}</span>
            </div>
            <div className="mt-3 h-2 rounded-full bg-white/10">
              <div className="h-2 rounded-full bg-[#1fd5f9]" />
            </div>
          </div>
        </div>

        <div className="flex flex-1 flex-col items-center justify-start gap-5 px-6 py-6 text-white">
          <div className="w-full max-w-sm space-y-6 rounded-[32px] border border-white/10 bg-[#070e13]/90 p-6 text-center backdrop-blur">
            <div className="flex flex-col items-center gap-5">
              <div
                className="h-28 w-28 rounded-full border-4 border-white/10 bg-cover bg-center"
                style={{
                  backgroundImage:
                    "url('https://images.unsplash.com/photo-1504593811423-6dd665756598?auto=format&fit=crop&w=256&q=80')",
                }}
              />
              <div>
                <h2 className="text-2xl leading-tight font-bold">Esteban</h2>
                <p className="text-sm text-white/70">White Toyota Camry • ABC-1234</p>
              </div>
            </div>

            <div className="rounded-2xl border border-white/5 bg-black/20 p-4 text-left">
              <p className="text-xs tracking-[0.4em] text-white/50 uppercase">Rating</p>
              <div className="mt-2 flex items-center gap-3">
                <p className="text-4xl font-semibold text-white">4.9</p>
                <div className="flex gap-1">
                  {Array.from({ length: 5 }).map((_, index) => (
                    <span
                      key={index}
                      className={cn(
                        'h-1.5 w-6 rounded-full',
                        index === 4 ? 'bg-white/30' : 'bg-[#ffde80]'
                      )}
                    />
                  ))}
                </div>
              </div>
              <p className="mt-1 text-sm text-white/60">142 reviews</p>
            </div>
          </div>

          <div className="w-full max-w-sm">
            <SafetyAlertCard alert={safetyAlert} />
          </div>
        </div>

        <div className="relative z-10 mt-auto flex flex-col gap-4 px-6 pb-12 text-white">
          <div className="flex items-center justify-center gap-6">
            <CallControlButton
              label={microphoneToggle.enabled ? 'Mute' : 'Unmute'}
              icon={microphoneToggle.enabled ? Microphone : MicrophoneSlash}
              onClick={handleToggleMic}
              active={!microphoneToggle.enabled}
              disabled={microphoneToggle.pending}
            />
          </div>
          <button
            type="button"
            className="flex h-16 items-center justify-center rounded-full bg-[#ff5f6d] text-lg font-semibold text-white transition hover:brightness-110 active:scale-95"
            onClick={handleEndCall}
          >
            <PhoneDisconnect size={28} weight="bold" />
            <span className="ml-2">End Call</span>
          </button>
        </div>
      </div>

      <TranscriptOverlay
        open={transcriptOpen}
        onClose={handleToggleTranscript}
        messages={messages}
        scrollRef={scrollAreaRef as React.RefObject<HTMLDivElement>}
      />
    </section>
  );
};

interface CallControlButtonProps {
  label: string;
  icon: Icon;
  onClick: () => void;
  active?: boolean;
  disabled?: boolean;
}

function CallControlButton({
  label,
  icon: Icon,
  onClick,
  active,
  disabled,
}: CallControlButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'flex flex-col items-center gap-2 text-white transition',
        disabled && 'cursor-not-allowed opacity-60'
      )}
    >
      <span
        className={cn(
          'flex h-16 w-16 items-center justify-center rounded-full border border-white/10 shadow-lg shadow-black/40',
          active
            ? 'bg-[#1fd5f9]/20 text-[#1fd5f9]'
            : disabled
              ? 'bg-black/30 text-white/60'
              : 'bg-black/40 text-white hover:bg-black/60'
        )}
      >
        <Icon size={28} weight="bold" />
      </span>
      <span className="text-xs font-semibold tracking-wide uppercase">{label}</span>
    </button>
  );
}

interface SafetyAlert {
  title: string;
  detail: string;
}

function SafetyAlertCard({ alert }: { alert?: SafetyAlert }) {
  if (!alert) {
    return null;
  }

  return (
    <div className="rounded-3xl border border-red-500/30 bg-red-500/10 p-4 text-left shadow-[0_15px_60px_rgba(255,95,109,0.25)]">
      <div className="flex items-center gap-3">
        <span className="flex size-8 items-center justify-center rounded-full bg-red-500/20">
          <Warning size={18} weight="fill" className="text-red-200" />
        </span>
        <p className="text-sm font-semibold text-red-100">{alert.title}</p>
      </div>
      <p className="mt-1 text-xs text-red-100/80">{alert.detail}</p>
    </div>
  );
}

interface TranscriptOverlayProps {
  open: boolean;
  onClose: () => void;
  messages: ReturnType<typeof useChatMessages>;
  scrollRef: React.RefObject<HTMLDivElement>;
}

function TranscriptOverlay({ open, onClose, messages, scrollRef }: TranscriptOverlayProps) {
  return (
    <div
      className={cn(
        'pointer-events-none absolute inset-0 z-20 flex flex-col bg-black/80 text-white opacity-0 backdrop-blur-md transition-opacity',
        open && 'pointer-events-auto opacity-100'
      )}
    >
      <div className="flex items-center justify-between px-6 py-4 text-sm text-white/70">
        <span>Full transcript</span>
        <button
          type="button"
          className="rounded-full border border-white/20 px-3 py-1 text-xs tracking-widest text-white/70 uppercase transition hover:bg-white/10"
          onClick={onClose}
        >
          Close
        </button>
      </div>
      <ScrollArea ref={scrollRef} className="flex-1 px-6 pb-24">
        <ChatTranscript hidden={!open} messages={messages} className="space-y-3" />
      </ScrollArea>
    </div>
  );
}
