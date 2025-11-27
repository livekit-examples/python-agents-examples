export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export interface MetadataMap {
  [key: string]: JsonValue;
}

export interface ParticipantSummary {
  sid: string;
  identity: string;
  name?: string;
  state?: number;
  kind?: number;
  metadata?: string | null;
  metadataDecoded?: MetadataMap | null;
  attributes?: Record<string, string>;
  joinedAt?: number | null;
  joinedAtMs?: number | null;
  isPublisher?: boolean;
}

export interface RoomSummary {
  sid: string;
  name: string;
  metadata?: string | null;
  metadataDecoded?: MetadataMap | null;
  emptyTimeout?: number | null;
  maxParticipants?: number | null;
  numParticipants?: number | null;
  numPublishers?: number | null;
  activeRecording?: boolean;
  creationTime?: number | null;
  creationTimeMs?: number | null;
}

export interface RoomWithParticipants {
  room: RoomSummary;
  participants: ParticipantSummary[];
}

export interface RoomsApiResponse {
  rooms: RoomWithParticipants[];
}
