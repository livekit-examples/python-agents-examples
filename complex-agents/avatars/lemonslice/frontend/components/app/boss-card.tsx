'use client';

import Image from 'next/image';
import type { BossPersonality } from '@/lib/boss-personalities';
import { cn } from '@/lib/shadcn/utils';

interface BossCardProps {
  boss: BossPersonality;
  selected?: boolean;
  onSelect: () => void;
}

export function BossCard({ boss, selected = false, onSelect }: BossCardProps) {
  return (
    <button
      onClick={onSelect}
      className={cn(
        'group relative flex cursor-pointer flex-col items-center gap-4 rounded-lg border-2 p-6 text-left transition-all',
        'hover:scale-105 hover:shadow-lg',
        selected
          ? `${boss.borderColor} ${boss.bgColor} scale-105 shadow-lg`
          : 'border-border bg-background hover:border-foreground/20'
      )}
    >
      {/* Boss image */}
      <div className="border-border relative h-32 w-32 overflow-hidden rounded-full border-4">
        <Image src={boss.imageUrl} alt={boss.name} fill className="object-cover" priority />
      </div>

      {/* Difficulty badge */}
      <div
        className={cn(
          'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold',
          selected ? boss.bgColor : 'bg-muted',
          selected ? boss.textColor : 'text-muted-foreground'
        )}
      >
        {boss.difficulty}
      </div>

      {/* Boss name */}
      <h3 className="text-foreground text-center text-xl font-bold">{boss.name}</h3>

      {/* Description */}
      <p className="text-muted-foreground text-center text-sm leading-relaxed">
        {boss.description}
      </p>

      {/* Selection indicator */}
      {selected && (
        <div className="absolute top-3 right-3">
          <svg className={cn('h-6 w-6', boss.textColor)} fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        </div>
      )}
    </button>
  );
}
