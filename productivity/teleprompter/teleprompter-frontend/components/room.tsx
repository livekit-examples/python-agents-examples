"use client";

import { useCallback, useMemo } from "react";
import { Room, RoomEvent, Track, LocalAudioTrack } from "livekit-client";
import { LiveKitRoom, RoomAudioRenderer } from "@livekit/components-react";

import { Playground } from "@/components/playground";
import { useConnection } from "@/hooks/use-connection";

export function RoomComponent() {
  const { shouldConnect, wsUrl, token, connect, disconnect } = useConnection();

  const handleConnect = useCallback(
    async (c: boolean) => {
      if (c) {
        connect();
      } else {
        disconnect();
      }
    },
    [connect, disconnect],
  );

  const room = useMemo(() => {
    const r = new Room();
    r.on(RoomEvent.LocalTrackPublished, async (trackPublication) => {
      if (
        trackPublication.source === Track.Source.Microphone &&
        trackPublication.track instanceof LocalAudioTrack
      ) {
        const { KrispNoiseFilter, isKrispNoiseFilterSupported } = await import(
          "@livekit/krisp-noise-filter"
        );
        if (!isKrispNoiseFilterSupported()) {
          console.error(
            "Enhanced noise filter is not supported for this browser",
          );
          return;
        }
        try {
          await trackPublication.track?.setProcessor(KrispNoiseFilter());
        } catch (e) {
          void e;
          console.warn("Background noise reduction could not be enabled");
        }
      }
    });
    return r;
  }, []);

  return (
    <LiveKitRoom
      className="overflow-y-hidden w-full"
      serverUrl={wsUrl}
      token={token}
      room={room}
      connect={shouldConnect}
      onError={console.error}
    >
      <Playground onConnect={handleConnect} />
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
}
