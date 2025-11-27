'use client';

import { useEffect, useMemo, useState } from 'react';
import { Room, RoomEvent } from 'livekit-client';
import { RoomAudioRenderer, RoomContext } from '@livekit/components-react';
import { toastAlert } from '@/components/alert-toast';
import { SessionView } from '@/components/session-view';
import { Toaster } from '@/components/ui/sonner';
import useConnectionDetails from '@/hooks/useConnectionDetails';
import type { AppConfig } from '@/lib/types';

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  const room = useMemo(() => new Room(), []);
  const [sessionStarted, setSessionStarted] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const { connectionDetails, refreshConnectionDetails } = useConnectionDetails();

  useEffect(() => {
    const onDisconnected = () => {
      setSessionStarted(false);
      setIsConnecting(false);
      refreshConnectionDetails();
    };
    const onMediaDevicesError = (error: Error) => {
      toastAlert({
        title: 'Encountered an error with your media devices',
        description: `${error.name}: ${error.message}`,
      });
    };
    room.on(RoomEvent.MediaDevicesError, onMediaDevicesError);
    room.on(RoomEvent.Disconnected, onDisconnected);
    return () => {
      room.off(RoomEvent.Disconnected, onDisconnected);
      room.off(RoomEvent.MediaDevicesError, onMediaDevicesError);
    };
  }, [room, refreshConnectionDetails]);

  useEffect(() => {
    if (sessionStarted && room.state === 'disconnected' && connectionDetails) {
      let cancelled = false;
      setIsConnecting(true);
      Promise.all([
        room.localParticipant.setMicrophoneEnabled(true, undefined, {
          preConnectBuffer: appConfig.isPreConnectBufferEnabled,
        }),
        room.connect(connectionDetails.serverUrl, connectionDetails.participantToken),
      ])
        .then(() => {
          if (!cancelled) {
            setIsConnecting(false);
          }
        })
        .catch((error) => {
          if (!cancelled) {
            setIsConnecting(false);
            setSessionStarted(false);
          }
          toastAlert({
            title: 'There was an error connecting to the agent',
            description: `${error.name}: ${error.message}`,
          });
        });

      return () => {
        cancelled = true;
        setIsConnecting(false);
        room.disconnect();
      };
    }
    return () => {};
  }, [room, sessionStarted, connectionDetails, appConfig.isPreConnectBufferEnabled]);

  useEffect(() => {
    if (!sessionStarted) {
      setIsConnecting(false);
    }
  }, [sessionStarted]);

  const handleStartSession = () => {
    if (!connectionDetails) {
      refreshConnectionDetails();
    }
    setSessionStarted(true);
  };

  return (
    <>
      <RoomContext.Provider value={room}>
        <RoomAudioRenderer />
        <SessionView
          sessionStarted={sessionStarted}
          onStartSession={handleStartSession}
          isConnecting={isConnecting}
          connectionReady={Boolean(connectionDetails)}
        />
      </RoomContext.Provider>

      <Toaster />
    </>
  );
}
