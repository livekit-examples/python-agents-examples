import { useEffect, useState } from "react";
import {
  useConnectionState,
  useMaybeRoomContext,
} from "@livekit/components-react";
import {
  ConnectionState,
  Participant,
  RoomEvent,
  TrackPublication,
  TranscriptionSegment,
} from "livekit-client";

export function useTranscriber() {
  const state = useConnectionState();
  const room = useMaybeRoomContext();
  const [transcriptions, setTranscriptions] = useState<{
    [id: string]: TranscriptionSegment;
  }>({});

  useEffect(() => {
    if (state === ConnectionState.Disconnected) {
      setTranscriptions({});
    }
  }, [state]);

  useEffect(() => {
    if (!room) {
      return;
    }

    const updateTranscriptions = (
      segments: TranscriptionSegment[],
      participant?: Participant,
      publication?: TrackPublication
    ) => {
      void participant;
      void publication;

      setTranscriptions((prev) => {
        const newTranscriptions = { ...prev };
        for (const segment of segments) {
          newTranscriptions[segment.id] = segment;
        }
        return newTranscriptions;
      });
    };

    room.on(RoomEvent.TranscriptionReceived, updateTranscriptions);
    return () => {
      room.off(RoomEvent.TranscriptionReceived, updateTranscriptions);
    };
  }, [room, state]);

  return { state, transcriptions };
}
