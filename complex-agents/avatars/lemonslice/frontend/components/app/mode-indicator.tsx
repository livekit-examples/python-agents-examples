'use client';

import { MODE_COLORS } from '@/lib/boss-personalities';
import { cn } from '@/lib/shadcn/utils';

interface ModeIndicatorProps {
  mode: 'roleplay' | 'coaching' | undefined;
  className?: string;
}

export function ModeIndicator({ mode, className }: ModeIndicatorProps) {
  if (!mode) return null;

  const colors = MODE_COLORS[mode];

  return (
    <div className={cn('inline-flex items-center justify-center gap-2', className)}>
      <div
        className={cn(
          'h-2 w-2 animate-pulse rounded-full',
          colors.textColor.replace('text-', 'bg-')
        )}
      />
      <span className={cn('text-sm font-medium', colors.textColor)}>{colors.label}</span>
    </div>
  );
}
