'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { BossCard } from '@/components/app/boss-card';
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
    <div ref={ref} className="flex flex-col items-center justify-center min-h-screen px-4">
      <section className="bg-background flex flex-col items-center text-center max-w-5xl w-full">
        {/* Header */}
        <div className="w-full flex justify-center items-center mb-2">
          <h1 className="text-4xl font-bold text-foreground">Salary Negotiation Coach</h1>
        </div>
        <p className="text-muted-foreground text-lg mb-8 max-w-2xl">
          Practice asking your boss for a raise.<br />Choose your boss personality and start your
          practice session.
        </p>

        {/* Boss selection cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full mb-8">
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
          className="w-full md:w-96 rounded-full font-mono text-xs font-bold tracking-wider uppercase cursor-pointer"
        >
          {startButtonText}
        </Button>

        {/* Tips section */}
        <div className="mt-12 p-6 bg-muted/50 rounded-lg max-w-2xl">
          <h3 className="text-lg font-semibold text-foreground mb-3">How it works</h3>
          <ul className="text-left text-sm text-muted-foreground space-y-2">
            <li>• Your session will last 3 minutes</li>
            <li>• Practice your salary negotiation conversation</li>
            <li>
              • Click "How am I doing?" anytime to get coaching feedback
            </li>
            <li>• The coach will provide tips and suggestions to improve</li>
          </ul>
        </div>
      </section>
    </div>
  );
};
