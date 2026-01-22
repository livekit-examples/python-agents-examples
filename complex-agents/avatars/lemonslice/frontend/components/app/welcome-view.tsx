'use client';

import { useState } from 'react';
import { BossCard } from '@/components/app/boss-card';
import { Button } from '@/components/ui/button';
import { BOSS_PERSONALITIES, type BossType } from '@/lib/boss-personalities';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: (bossType: BossType) => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [selectedBoss, setSelectedBoss] = useState<BossType>('easy');

  const handleStart = () => {
    onStartCall(selectedBoss);
  };

  return (
    <div ref={ref} className="flex min-h-screen flex-col items-center justify-center px-4">
      <section className="bg-background flex w-full max-w-5xl flex-col items-center text-center">
        {/* Header */}
        <div className="mb-2 flex w-full items-center justify-center">
          <h1 className="text-foreground text-4xl font-bold">Salary Negotiation Coach</h1>
        </div>
        <p className="text-muted-foreground mb-8 max-w-2xl text-lg">
          Practice asking your boss for a raise.
          <br />
          Choose your boss personality and start your practice session.
        </p>

        {/* Boss selection cards */}
        <div className="mb-8 grid w-full grid-cols-1 gap-4 md:grid-cols-3">
          {Object.values(BOSS_PERSONALITIES).map((boss) => (
            <BossCard
              key={boss.id}
              boss={boss}
              selected={selectedBoss === boss.id}
              onSelect={() => setSelectedBoss(boss.id)}
            />
          ))}
        </div>

        {/* Start button */}
        <Button
          size="lg"
          onClick={handleStart}
          className="w-full cursor-pointer rounded-full font-mono text-xs font-bold tracking-wider uppercase md:w-96"
        >
          {startButtonText}
        </Button>

        {/* Tips section */}
        <div className="bg-muted/50 mt-12 max-w-2xl rounded-lg p-6">
          <h3 className="text-foreground mb-3 text-lg font-semibold">How it works</h3>
          <ul className="text-muted-foreground space-y-2 text-left text-sm">
            <li>• Your session will last 3 minutes</li>
            <li>• Practice your salary negotiation conversation</li>
            <li>• Click &quot;How am I doing?&quot; anytime to get coaching feedback</li>
            <li>• The coach will provide tips and suggestions to improve</li>
          </ul>
        </div>
      </section>
    </div>
  );
};
