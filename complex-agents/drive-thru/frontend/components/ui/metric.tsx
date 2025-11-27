'use client';

import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface MetricProps {
  label: ReactNode;
  value: ReactNode;
  helperText?: ReactNode;
  className?: string;
}

export function Metric({ label, value, helperText, className }: MetricProps) {
  return (
    <div className={cn('flex min-w-[7.5rem] flex-col gap-1', className)}>
      <span className="text-fg4 text-[0.65rem] font-semibold tracking-wide uppercase">{label}</span>
      <span className="text-fg1 text-sm font-medium">{value}</span>
      {helperText ? <span className="text-fg3 text-xs">{helperText}</span> : null}
    </div>
  );
}
