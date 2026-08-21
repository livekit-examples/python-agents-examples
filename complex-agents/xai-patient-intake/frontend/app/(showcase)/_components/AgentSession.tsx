import { useEffect, useRef } from 'react';
import { useSessionContext } from '@livekit/components-react';

import { SessionProvider } from '@/components/SessionProvider';

interface AgentHooksProps {
  onLeave: () => void;
}

function AgentHooks({ onLeave }: AgentHooksProps) {
  const session = useSessionContext();
  const hasConnectedRef = useRef(false);

  useEffect(() => {
    // No client-side noise filter on purpose. The worker runs the ai-coustics enhancer on the
    // way into STT (see agent.py), and stacking a second denoiser ahead of it over-suppresses
    // the quiet, trailing-off speech this agent is tuned to wait for. Suppressing on the server
    // also covers SIP callers, who never run this code.
    session.start({ tracks: { microphone: { enabled: true } } });
    return () => {
      session.end();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (session.isConnected) {
      hasConnectedRef.current = true;
    } else if (hasConnectedRef.current && session.connectionState !== 'connecting') {
      onLeave();
    }
  }, [session.isConnected, session.connectionState, onLeave]);

  return <></>;
}

interface AgentSessionProps {
  agentName: string;
  children: React.ReactNode;
  onLeave: () => void;
}

export function AgentSession({ agentName, children, onLeave }: AgentSessionProps) {
  return (
    <SessionProvider agentName={agentName}>
      <AgentHooks onLeave={onLeave} />
      {children}
    </SessionProvider>
  );
}
