'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { TokenSource } from 'livekit-client';
import { useSession } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react/dist/ssr';
import type { AppConfig } from '@/app-config';
import { AgentSessionProvider } from '@/components/agents-ui/agent-session-provider';
import { StartAudioButton } from '@/components/agents-ui/start-audio-button';
import { ViewController } from '@/components/app/view-controller';
import { Toaster } from '@/components/ui/sonner';
import { useDebugMode } from '@/hooks/useDebug';
import type { BossType } from '@/lib/boss-personalities';
import { getSandboxTokenSource } from '@/lib/utils';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

function AppSetup() {
  useDebugMode({ enabled: IN_DEVELOPMENT });

  return null;
}

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  const [selectedBoss, setSelectedBoss] = useState<BossType>('easy');
  const pendingStartRef = useRef(false);

  const tokenSource = useMemo(() => {
    const participantAttributes = { boss_type: selectedBoss };

    if (typeof process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT === 'string') {
      return getSandboxTokenSource(appConfig, participantAttributes);
    }

    // Use custom token source for non-sandbox to pass attributes
    return TokenSource.custom(async () => {
      const roomConfig = appConfig.agentName
        ? { agents: [{ agent_name: appConfig.agentName }] }
        : undefined;

      const res = await fetch('/api/connection-details', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_config: roomConfig,
          participant_attributes: participantAttributes,
        }),
      });
      return res.json();
    });
  }, [appConfig, selectedBoss]);

  const session = useSession(tokenSource, {
    ...(appConfig.agentName ? { agentName: appConfig.agentName } : {}),
    participantAttributes: { boss_type: selectedBoss },
  });

  const handleBossSelected = useCallback(
    (bossType: BossType) => {
      if (bossType === selectedBoss) {
        // Boss type is already selected, start directly
        session.start();
      } else {
        // Boss type is different, let useEffect handle start after state update
        setSelectedBoss(bossType);
        pendingStartRef.current = true;
      }
    },
    [selectedBoss, session]
  );

  // Start session after state updates
  useEffect(() => {
    if (pendingStartRef.current && !session.isConnected) {
      pendingStartRef.current = false;
      session.start();
    }
  }, [selectedBoss, session]);

  return (
    <AgentSessionProvider session={session}>
      <AppSetup />
      <main className="grid h-svh grid-cols-1 place-content-center">
        <ViewController appConfig={appConfig} onBossSelected={handleBossSelected} />
      </main>
      <StartAudioButton label="Start Audio" />
      <Toaster
        icons={{
          warning: <WarningIcon weight="bold" />,
        }}
        position="top-center"
        className="toaster group"
        style={
          {
            '--normal-bg': 'var(--popover)',
            '--normal-text': 'var(--popover-foreground)',
            '--normal-border': 'var(--border)',
          } as React.CSSProperties
        }
      />
    </AgentSessionProvider>
  );
}
