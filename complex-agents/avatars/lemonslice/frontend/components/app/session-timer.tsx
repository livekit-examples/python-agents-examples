'use client';

import { useEffect, useState } from 'react';
import { cn } from '@/lib/shadcn/utils';

interface SessionTimerProps {
  startTime: number;
  duration?: number; // in seconds, default 180 (3 minutes)
  className?: string;
}

export function SessionTimer({ startTime, duration = 180, className }: SessionTimerProps) {
  const [timeRemaining, setTimeRemaining] = useState(duration);

  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const remaining = Math.max(0, duration - elapsed);
      setTimeRemaining(remaining);
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime, duration]);

  const minutes = Math.floor(timeRemaining / 60);
  const seconds = timeRemaining % 60;
  const isLowTime = timeRemaining < 60;

  return (
    <div
      className={cn(
        'inline-flex items-center gap-2 rounded-full px-4 py-2 font-mono text-sm font-semibold',
        isLowTime
          ? 'bg-red-500/10 text-red-500 border border-red-500/30'
          : 'bg-muted text-muted-foreground border border-border',
        className
      )}
    >
      <svg
        className={cn('h-4 w-4', isLowTime && 'animate-pulse')}
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <circle cx="12" cy="12" r="10" />
        <path d="M12 6v6l4 2" />
      </svg>
      <span>
        {minutes}:{seconds.toString().padStart(2, '0')}
      </span>
    </div>
  );
}
