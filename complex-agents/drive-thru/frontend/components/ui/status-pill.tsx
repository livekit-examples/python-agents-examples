'use client';

import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

export type StatusTone = 'neutral' | 'success' | 'warning' | 'critical' | 'info';

const toneStyles: Record<StatusTone, string> = {
  neutral: 'bg-bg3 text-fg2 border-border',
  success: 'bg-bgSuccess text-fgSuccess border-separatorSuccess',
  warning: 'bg-bgModerate text-fgModerate border-separatorModerate',
  critical: 'bg-bgSerious text-fgSerious border-separatorSerious',
  info: 'bg-bgAccent text-fgAccent border-separatorAccent',
};

export interface StatusPillProps {
  tone?: StatusTone;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function StatusPill({ tone = 'neutral', icon, children, className }: StatusPillProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full border px-2 py-1 text-xs font-medium',
        toneStyles[tone],
        className
      )}
    >
      {icon ? <span className="text-xs leading-none">{icon}</span> : null}
      <span className="truncate">{children}</span>
    </span>
  );
}
