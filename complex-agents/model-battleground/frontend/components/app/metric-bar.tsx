'use client';

import { cn } from '@/lib/utils';

interface MetricBarProps {
  label: string;
  value: number; // 0-100
  latencyMs?: number;
  className?: string;
}

const formatLatency = (latencyMs?: number) => {
  if (typeof latencyMs !== 'number' || !Number.isFinite(latencyMs)) {
    return '—';
  }
  if (latencyMs >= 100) {
    return `${Math.round(latencyMs)}ms`;
  }
  return `${Math.round(latencyMs)}ms`;
};

export function MetricBar({ label, value, latencyMs, className }: MetricBarProps) {
  return (
    <div className={cn('group', className)}>
      <div className="mb-1 flex items-center justify-between">
        <span className="text-fg0 text-sm font-medium">{label}</span>
      </div>
      <div className="flex items-center gap-3">
        <div className="bg-separator1 h-2.5 w-full rounded-full">
          <div
            className={cn(
              'bg-fgAccent1 h-2.5 rounded-full transition-all duration-300',
              value > 0 && 'group-hover:brightness-125'
            )}
            style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
          />
        </div>
        <span className="text-fg3 font-mono text-xs whitespace-nowrap">
          {formatLatency(latencyMs)}
        </span>
      </div>
    </div>
  );
}
