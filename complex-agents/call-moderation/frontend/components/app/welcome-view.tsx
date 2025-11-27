'use client';

import {
  type ButtonHTMLAttributes,
  type ComponentProps,
  type ReactNode,
  forwardRef,
  useEffect,
  useMemo,
  useState,
} from 'react';
import type { Icon } from '@phosphor-icons/react';
import {
  X as CloseIcon,
  Minus,
  NavigationArrow,
  PhoneCall,
  Plus,
  ShareFat,
  Star,
} from '@phosphor-icons/react/dist/ssr';
import { cn } from '@/lib/utils';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

type TripPhase = 'idle' | 'matching';

export const WelcomeView = forwardRef<HTMLDivElement, ComponentProps<'div'> & WelcomeViewProps>(
  function WelcomeView({ startButtonText, onStartCall, ...props }, ref) {
    const [phase, setPhase] = useState<TripPhase>('idle');
    const [progress, setProgress] = useState(55);

    useEffect(() => {
      if (phase !== 'matching') return;
      const timer = setInterval(() => {
        setProgress((current) => {
          if (current >= 95) {
            return 60;
          }
          return Math.min(96, current + 5 + Math.random() * 10);
        });
      }, 3500);
      return () => clearInterval(timer);
    }, [phase]);

    return (
      <div
        ref={ref}
        className="flex h-full w-full items-center justify-center bg-[#020b10] px-4 py-6 text-white"
        {...props}
      >
        <div className="mx-auto flex h-full min-h-0 w-full max-w-sm flex-col px-3 py-4">
          {phase === 'idle' ? (
            <div className="flex flex-1 items-center justify-center">
              <IdleState onHailRide={() => setPhase('matching')} />
            </div>
          ) : (
            <div className="flex min-h-0 flex-1 overflow-hidden">
              <div className="flex w-full flex-col overflow-y-auto">
                <MatchingState
                  progress={progress}
                  startButtonText={startButtonText}
                  onContactDriver={onStartCall}
                  onReset={() => setPhase('idle')}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }
);

interface IdleStateProps {
  onHailRide: () => void;
}

function IdleState({ onHailRide }: IdleStateProps) {
  return (
    <div className="relative flex flex-col items-center gap-8 rounded-[36px] border border-white/5 bg-[#050f13] p-10 text-center">
      <div className="absolute inset-x-10 top-6 flex items-center justify-between text-xs tracking-[0.4em] text-white/40 uppercase">
        <span>Hail</span>
        <span>Ride</span>
      </div>
      <div className="pt-10">
        <h1 className="text-3xl font-semibold text-white">Need to get somewhere fast?</h1>
        <p className="mt-4 text-base leading-relaxed text-white/70">
          Tap below and we&apos;ll locate the closest top-rated driver for you.
        </p>
      </div>
      <div className="w-full rounded-3xl bg-[#061821] p-2 shadow-inner shadow-black/60">
        <button
          type="button"
          className="flex h-16 w-full items-center justify-center rounded-2xl bg-[#1fd5f9] text-lg font-semibold text-[#021219] transition-transform duration-200 hover:brightness-110 active:scale-95"
          onClick={onHailRide}
        >
          Hail Ride
        </button>
      </div>
      <p className="text-sm text-white/50">LiveKit powers your personal dispatch center.</p>
    </div>
  );
}

interface MatchingStateProps {
  onReset: () => void;
  onContactDriver: () => void;
  progress: number;
  startButtonText: string;
}

function MatchingState({
  onReset,
  onContactDriver,
  progress,
  startButtonText,
}: MatchingStateProps) {
  const statusText = useMemo(() => {
    if (progress > 80) {
      return 'Esteban is almost there—look for the white Camry.';
    }
    if (progress > 50) {
      return 'Matched with Esteban. He is en route to your pickup.';
    }
    return 'Finding the closest top-rated driver for you.';
  }, [progress]);

  return (
    <div className="overflow-hidden rounded-[40px] border border-white/10 bg-[#03080b] text-white shadow-[0_40px_120px_rgba(0,0,0,0.6)]">
      {/* Map */}
      <div className="relative h-[360px] w-full">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage:
              "url('https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=700&q=60')",
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-b from-black/20 via-black/40 to-[#03080b]" />
        </div>
        <div className="absolute inset-x-0 top-0 flex items-center justify-between px-4 py-4 text-xs font-semibold text-white/80">
          <button
            type="button"
            onClick={onReset}
            className="rounded-full bg-black/50 px-3 py-1 text-[11px] tracking-widest text-white/70 uppercase transition hover:bg-black/70"
          >
            Change pickup
          </button>
          <span className="rounded-full bg-black/50 px-3 py-1 tracking-wider text-white/70">
            Ride #A1B9
          </span>
        </div>
        <div className="absolute inset-x-0 bottom-4 flex items-end justify-between px-4">
          <div className="flex flex-col gap-2">
            <MapControlGroup>
              <MapButton aria-label="Zoom in">
                <Plus size={20} weight="bold" />
              </MapButton>
              <MapButton aria-label="Zoom out">
                <Minus size={20} weight="bold" />
              </MapButton>
            </MapControlGroup>
            <MapButton aria-label="Re-center">
              <NavigationArrow size={20} weight="bold" />
            </MapButton>
          </div>
          <div className="rounded-3xl bg-black/70 px-4 py-2 text-right shadow-lg shadow-black/40">
            <p className="text-[13px] tracking-[0.4em] text-white/50 uppercase">Arriving in</p>
            <p className="text-3xl leading-tight font-semibold text-white">5 min</p>
          </div>
        </div>
      </div>

      {/* Bottom Sheet */}
      <div className="flex flex-col gap-5 bg-[#030d11] p-6">
        <div className="flex flex-col gap-3 rounded-3xl border border-white/5 bg-black/30 p-4">
          <div className="flex items-center justify-between text-sm">
            <div>
              <p className="text-sm text-white/60">Drop-off ETA</p>
              <p className="text-lg font-semibold text-white">10:15 PM</p>
            </div>
            <span className="text-sm font-semibold text-[#1fd5f9]">En route</span>
          </div>
          <div className="h-2 w-full rounded-full bg-white/10">
            <div
              className="h-2 rounded-full bg-[#1fd5f9]"
              style={{ width: `${Math.min(100, Math.max(20, progress))}%` }}
            />
          </div>
          <p className="text-sm text-white/70">{statusText}</p>
        </div>

        <div className="flex items-center gap-4 rounded-3xl border border-white/5 bg-black/30 p-4">
          <div
            className="h-16 w-16 flex-shrink-0 rounded-full bg-cover bg-center"
            style={{
              backgroundImage:
                "url('https://images.unsplash.com/photo-1504593811423-6dd665756598?auto=format&fit=crop&w=256&q=80')",
            }}
          />
          <div className="flex flex-col gap-1">
            <p className="text-xl leading-tight font-semibold">Esteban</p>
            <p className="text-sm text-white/70">White Toyota Camry • ABC-1234</p>
            <div className="flex items-center gap-1 text-sm text-white/70">
              <Star size={16} weight="fill" className="text-yellow-300" />
              <span>4.9 rating • 142 trips</span>
            </div>
          </div>
          <span className="ml-auto rounded-full border border-white/20 px-3 py-1 text-xs text-white/70">
            Preferred
          </span>
        </div>

        <button
          type="button"
          className="flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-[#1fd5f9] text-base font-semibold text-[#021219] shadow-xl shadow-[#1fd5f9]/30 transition hover:brightness-110 active:scale-[0.99]"
          onClick={onContactDriver}
        >
          <PhoneCall size={22} weight="bold" />
          {startButtonText}
        </button>

        <div className="grid grid-cols-2 gap-4 pt-2">
          <ActionButton icon={ShareFat} label="Share Trip" />
          <ActionButton icon={CloseIcon} label="Cancel Ride" variant="danger" />
        </div>
      </div>
    </div>
  );
}

interface MapButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

function MapButton({ children, className, ...props }: MapButtonProps) {
  return (
    <button
      type="button"
      className={cn(
        'flex size-12 items-center justify-center rounded-2xl bg-black/60 text-white shadow-lg shadow-black/40 transition hover:bg-black/80',
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

function MapControlGroup({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-hidden rounded-[22px] border border-white/5 bg-black/60 shadow-lg shadow-black/40">
      {children}
    </div>
  );
}

interface ActionButtonProps {
  icon: Icon;
  label: string;
  variant?: 'default' | 'danger';
}

function ActionButton({ icon: Icon, label, variant = 'default' }: ActionButtonProps) {
  return (
    <button
      type="button"
      className={cn(
        'flex flex-col items-center justify-center gap-2 rounded-3xl border border-white/10 px-4 py-4 text-center text-sm font-semibold transition',
        variant === 'danger'
          ? 'bg-[#2a0c0c] text-[#ff9faf] hover:bg-[#401318]'
          : 'bg-black/30 text-white hover:bg-black/50'
      )}
    >
      <div
        className={cn(
          'flex h-12 w-12 items-center justify-center rounded-full border',
          variant === 'danger'
            ? 'border-[#ff9faf]/50 bg-[#ff5f6d]/20 text-[#ff9faf]'
            : 'border-white/20 bg-white/5 text-white'
        )}
      >
        <Icon size={22} weight="bold" />
      </div>
      {label}
    </button>
  );
}
