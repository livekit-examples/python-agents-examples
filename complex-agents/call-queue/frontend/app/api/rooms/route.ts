import { NextResponse } from 'next/server';
import type { ParticipantInfo, Room } from 'livekit-server-sdk';
import { getRoomServiceClient } from '@/lib/livekit-server';
import type { ParticipantSummary, RoomSummary, RoomsApiResponse } from '@/types/call-queue';

export const revalidate = 0;
export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const client = getRoomServiceClient();
    const rooms = await client.listRooms();

    const roomsWithParticipants = (
      await Promise.all(
        rooms.map(async (room) => {
          try {
            const participants = await client.listParticipants(room.name);
            return {
              room: serializeRoom(room),
              participants: participants.map(serializeParticipant),
            } satisfies RoomsApiResponse['rooms'][number];
          } catch (error) {
            if (isRoomNotFoundError(error)) {
              console.warn(
                `[Rooms API] Room ${room.name} disappeared before fetching participants`
              );
              return null;
            }
            throw error;
          }
        })
      )
    ).filter(Boolean) as RoomsApiResponse['rooms'];

    return NextResponse.json({ rooms: roomsWithParticipants });
  } catch (error) {
    console.error('Failed to fetch rooms from LiveKit', error);
    return NextResponse.json({ error: 'Unable to fetch rooms' }, { status: 500 });
  }
}

function serializeRoom(room: Room): RoomSummary {
  return {
    sid: room.sid,
    name: room.name,
    metadata: room.metadata ?? null,
    metadataDecoded: decodeMetadata(room.metadata),
    emptyTimeout: room.emptyTimeout ?? null,
    maxParticipants: room.maxParticipants ?? null,
    numParticipants: room.numParticipants ?? null,
    numPublishers: room.numPublishers ?? null,
    activeRecording: room.activeRecording,
    creationTime: convertNumeric(room.creationTime),
    creationTimeMs: convertNumeric(room.creationTimeMs),
  };
}

function serializeParticipant(participant: ParticipantInfo): ParticipantSummary {
  return {
    sid: participant.sid,
    identity: participant.identity,
    name: participant.name,
    state: participant.state,
    kind: participant.kind,
    metadata: participant.metadata ?? null,
    metadataDecoded: decodeMetadata(participant.metadata),
    attributes: participant.attributes ?? {},
    joinedAt: convertNumeric(participant.joinedAt),
    joinedAtMs: convertNumeric(participant.joinedAtMs),
    isPublisher: participant.isPublisher,
  };
}

function convertNumeric(value?: number | bigint | null): number | null {
  if (value === undefined || value === null) {
    return null;
  }
  return typeof value === 'bigint' ? Number(value) : value;
}

function decodeMetadata(metadata?: string | null) {
  if (!metadata) {
    return null;
  }

  try {
    return JSON.parse(metadata);
  } catch {
    return null;
  }
}

function isRoomNotFoundError(error: unknown) {
  if (!error || typeof error !== 'object') {
    return false;
  }

  const maybeError = error as { code?: string; status?: number; message?: string };
  const message = typeof maybeError.message === 'string' ? maybeError.message.toLowerCase() : '';
  return (
    maybeError.code === 'not_found' ||
    maybeError.status === 404 ||
    message.includes('does not exist')
  );
}
