'use client';

import { Tooltip as TooltipPrimitive } from 'radix-ui';

import type { AgentMetadata } from '@/app/(showcase)/_components/agent-metadata';
import { Badge } from '@/components/bytes';

interface ModelBadgeProps {
  agent: AgentMetadata;
}

/**
 * The headline badge, with the cascade behind it on hover.
 *
 * The badge names the family rather than one model ("Grok Voice Models"), because three
 * models are doing the work and picking one of them to print was always a half-truth. The
 * tooltip carries the rest: which model runs each stage of the pipeline.
 *
 * `Badge` is `pointer-events-none` (vendored that way from bytes-react), so the trigger has
 * to be the span around it rather than the badge itself.
 */
export function ModelBadge({ agent }: ModelBadgeProps) {
  if (!agent.headlineModel) {
    return null;
  }

  // No .toUpperCase() here: `text-mono-caps` in the badge already uppercases, and the
  // header used to do both.
  const label = agent.headlineModel;

  if (agent.models.length === 0) {
    return (
      <Badge variant="muted" size="large" className="shrink-0 tracking-wider">
        {label}
      </Badge>
    );
  }

  return (
    <TooltipPrimitive.Provider delayDuration={150}>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>
          <span className="shrink-0 cursor-help outline-none" tabIndex={0}>
            <Badge
              variant="muted"
              size="large"
              className="tracking-wider underline decoration-dotted underline-offset-4"
            >
              {label}
            </Badge>
          </span>
        </TooltipPrimitive.Trigger>
        <TooltipPrimitive.Portal>
          <TooltipPrimitive.Content
            side="bottom"
            align="start"
            sideOffset={6}
            collisionPadding={12}
            className="border-separator1 bg-bg2 text-fg1 animate-in fade-in-0 zoom-in-95 z-50 rounded-md border px-3 py-2 shadow-lg"
          >
            <p className="text-fg3 text-xxs mb-1.5 font-semibold tracking-wider uppercase">
              Cascaded pipeline
            </p>
            <dl className="grid grid-cols-[auto_auto] gap-x-4 gap-y-1 text-xs">
              {agent.models.map((model) => (
                <div key={model.role} className="contents">
                  <dt className="text-fg3">{model.role}</dt>
                  <dd className="text-fg1 font-mono">{model.name}</dd>
                </div>
              ))}
            </dl>
            <TooltipPrimitive.Arrow className="fill-bg2" />
          </TooltipPrimitive.Content>
        </TooltipPrimitive.Portal>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  );
}
