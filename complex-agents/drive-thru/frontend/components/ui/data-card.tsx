'use client';

import type { ComponentPropsWithoutRef, ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Metric, type MetricProps } from './metric';

export interface DataCardProps extends Omit<ComponentPropsWithoutRef<'div'>, 'title'> {
  title: ReactNode;
  subtitle?: ReactNode;
  description?: ReactNode;
  metrics?: MetricProps[];
  status?: ReactNode;
  footer?: ReactNode;
  interactive?: boolean;
}

export function DataCard({
  title,
  subtitle,
  description,
  metrics,
  status,
  footer,
  interactive = false,
  className,
  ...props
}: DataCardProps) {
  return (
    <div
      className={cn(
        'group bg-bg1/90 flex flex-col gap-4 rounded-xl border border-white p-5 shadow-sm transition duration-150 ease-out',
        'hover:bg-bg2 focus-visible:outline-ring hover:border-white hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
        interactive && 'cursor-pointer',
        className
      )}
      {...props}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-fgAccent text-base font-semibold">{title}</div>
          {subtitle ? <div className="text-fg3 text-sm">{subtitle}</div> : null}
        </div>
        {status ? <div className="shrink-0">{status}</div> : null}
      </div>

      {description ? <div className="text-fg2 text-sm">{description}</div> : null}

      {metrics && metrics.length > 0 ? (
        <div className="flex flex-wrap gap-6">
          {metrics.map((metric, index) => (
            <Metric key={index} {...metric} />
          ))}
        </div>
      ) : null}

      {footer ? <div className="text-fg4 mt-auto text-xs">{footer}</div> : null}
    </div>
  );
}
