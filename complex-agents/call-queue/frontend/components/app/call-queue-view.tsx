'use client';

import React, { useMemo } from 'react';
import { PhoneDisconnectIcon } from '@phosphor-icons/react/dist/ssr';
import { useRoomQueue } from '@/hooks/useRoomQueue';
import { cn } from '@/lib/utils';
import type { MetadataMap, ParticipantSummary, RoomWithParticipants } from '@/types/call-queue';

const DEFAULT_SURVEY_TOTAL = 5;
const MIN_PROGRESS_TOTAL = 1;

interface QueueCardData {
  id: string;
  roomName: string;
  callerId: string;
  callerSubtitle?: string;
  duration: string;
  participants: ParticipantSummary[];
  participantCount: number;
  answeredQuestions: number;
  surveyTotal: number;
}

function SurveyProgress({ answered, total }: { answered: number; total: number }) {
  return (
    <div className="flex items-center gap-2">
      <p className="font-semibold text-white">
        {answered}/{total}
      </p>
      <div className="flex items-center gap-1">
        {Array.from({ length: total }).map((_, index) => (
          <span
            key={index}
            className={cn(
              'h-2.5 w-2.5 rounded-full transition-colors',
              index < answered ? 'bg-primary' : 'bg-white/20'
            )}
          />
        ))}
      </div>
    </div>
  );
}

function InfoBlock({
  label,
  value,
  subtitle,
  children,
}: {
  label: string;
  value?: string;
  subtitle?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-semibold tracking-[0.25em] text-white/50 uppercase">{label}</p>
      {value ? (
        <div>
          <p className="text-lg font-semibold text-white">{value}</p>
          {subtitle && <p className="text-sm text-white/60">{subtitle}</p>}
        </div>
      ) : (
        <div>{children}</div>
      )}
    </div>
  );
}

function CallQueueCard({ call }: { call: QueueCardData }) {
  const infoGridColumns = 'md:grid-cols-3';
  const participantLabel = call.participantCount === 1 ? 'participant' : 'participants';
  const maskedCallerId = maskDigitsExceptLastFour(call.callerId);
  const maskedRoomName = maskDigitsExceptLastFour(call.roomName) ?? call.roomName;

  return (
    <article className="flex flex-col gap-4 rounded-2xl border border-white/10 bg-[#070707] p-4 shadow-[0_0_40px_rgba(0,0,0,0.35)] transition hover:border-white/20 md:flex-row md:items-center">
      <div className="flex w-full flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-semibold tracking-[0.3em] text-white/40 uppercase">
          <span>{maskedRoomName}</span>
          <span>
            {call.participantCount} {participantLabel}
          </span>
        </div>
        <div className={cn('grid grid-cols-1 gap-4', infoGridColumns)}>
          <InfoBlock label="Participant" value={maskedCallerId} />
          <InfoBlock label="Call Duration" value={call.duration} />
          <InfoBlock label="Survey Questions Answered">
            <SurveyProgress answered={call.answeredQuestions} total={call.surveyTotal} />
          </InfoBlock>
        </div>
      </div>
    </article>
  );
}

function EmptyQueueState() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 py-12">
      <div className="flex w-full max-w-lg flex-col items-center gap-6 rounded-2xl border border-white/10 bg-[#070707] px-10 py-12 text-center shadow-[0_0_50px_rgba(0,0,0,0.45)]">
        <div className="text-primary">
          <PhoneDisconnectIcon size={64} weight="duotone" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold tracking-tight text-white">
            No calls in the queue yet.
          </h2>
          <p className="text-base text-white/70">Waiting for new calls...</p>
        </div>
        <p className="text-base font-semibold tracking-tight text-white">
          Call +1(518)500-1581 to take the survey
        </p>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex flex-1 items-center justify-center py-24">
      <p className="font-mono text-xs tracking-[0.4em] text-white/60 uppercase">Loading rooms…</p>
    </div>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
      {message}
    </div>
  );
}

export const CallQueueView = React.forwardRef<HTMLDivElement, React.ComponentProps<'section'>>(
  function CallQueueView({ className, ...props }, ref) {
    const { rooms, isLoading, error } = useRoomQueue();
    const callQueue = useMemo(
      () => rooms.map(createQueueCardData).filter(Boolean) as QueueCardData[],
      [rooms]
    );
    const hasCalls = callQueue.length > 0;
    const showInitialLoading = isLoading && !hasCalls;
    const showEmptyState = !isLoading && !error && !hasCalls;
    const showHeader = !showEmptyState;

    return (
      <section
        ref={ref}
        className={cn(
          'font-display relative flex min-h-svh w-full flex-col bg-[#000000] px-6 py-12 text-white md:px-12',
          className
        )}
        {...props}
      >
        <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col">
          {showHeader && (
            <header className="mb-8 flex flex-col gap-6 md:mb-10">
              <p className="text-xs font-semibold tracking-[0.4em] text-white/50 uppercase">
                Live Queue
              </p>
              <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
                <div>
                  <h1 className="text-3xl font-semibold tracking-tight text-white md:text-4xl">
                    Call Queue
                  </h1>
                  <p className="text-white/70">Live calls waiting for an agent.</p>
                </div>
                <p className="text-sm font-semibold tracking-tight text-white md:text-right">
                  Call +1(518)500-1581 to take the survey
                </p>
              </div>
            </header>
          )}

          {error && <ErrorBanner message={error} />}

          {showInitialLoading ? (
            <LoadingState />
          ) : hasCalls ? (
            <div className="flex flex-col gap-4">
              {callQueue.map((call) => (
                <CallQueueCard key={call.id} call={call} />
              ))}
            </div>
          ) : (
            showEmptyState && <EmptyQueueState />
          )}
        </div>
      </section>
    );
  }
);

function createQueueCardData(roomEntry: RoomWithParticipants): QueueCardData | null {
  const { room, participants } = roomEntry;
  if (!room) {
    return null;
  }
  const sipParticipant = findSipParticipant(participants);
  if (!sipParticipant) {
    return null;
  }
  const participant = sipParticipant;

  const callerId = deriveCallerId(participant, room);
  const callerSubtitle = deriveCallerSubtitle(participant, callerId);
  const duration = formatDuration(resolveCreationTimeMs(room));
  const { answered, total } = deriveSurveyCounts(participant.metadataDecoded, room.metadataDecoded);

  return {
    id: room.sid || room.name,
    roomName: room.name,
    callerId,
    callerSubtitle,
    duration,
    participants,
    participantCount: participants.length,
    answeredQuestions: answered,
    surveyTotal: total,
  };
}

function findSipParticipant(participants: ParticipantSummary[]): ParticipantSummary | undefined {
  return participants.find((participant) => isSipParticipant(participant));
}

function isSipParticipant(participant: ParticipantSummary) {
  const identity = participant.identity?.toLowerCase();
  const attributes = participant.attributes ?? {};
  const metadataRole = coerceToString(getMetadataValue(participant.metadataDecoded, ['role']));
  const metadataSource = coerceToString(getMetadataValue(participant.metadataDecoded, ['source']));
  const attrRole = attributes.role?.toLowerCase();
  const attrSource = attributes.source?.toLowerCase();

  return (
    (identity?.startsWith('sip') ?? false) ||
    (identity?.startsWith('tel:') ?? false) ||
    attrRole === 'caller' ||
    attrSource === 'sip' ||
    metadataRole?.toLowerCase() === 'caller' ||
    metadataSource?.toLowerCase() === 'sip'
  );
}

function deriveCallerId(participant: ParticipantSummary, room: RoomWithParticipants['room']) {
  const metadataSources: Array<MetadataMap | null | undefined> = [
    participant.metadataDecoded,
    room.metadataDecoded,
  ];
  const attributeSources: Array<Record<string, string> | undefined> = [participant.attributes];

  const metadataValue = extractFirstString(metadataSources, [
    ['callerId'],
    ['caller_id'],
    ['caller', 'number'],
    ['caller', 'id'],
    ['sip', 'from'],
    ['from'],
    ['phoneNumber'],
    ['phone_number'],
  ]);

  if (metadataValue) {
    return metadataValue;
  }

  for (const attrs of attributeSources) {
    const attrValue = findFirstAttribute(attrs, ['callerId', 'caller_id', 'from', 'phone']);
    if (attrValue) {
      return attrValue;
    }
  }

  return participant.name || participant.identity || room.name || 'Unknown caller';
}

function deriveCallerSubtitle(participant: ParticipantSummary, callerId: string) {
  const metadataName = coerceToString(
    getMetadataValue(participant.metadataDecoded, ['caller', 'name'])
  );
  const candidates = [
    metadataName,
    participant.name,
    participant.identity !== callerId ? participant.identity : undefined,
  ].filter((value): value is string => Boolean(value && value !== callerId));

  return candidates[0];
}

function maskDigitsExceptLastFour(value: string | undefined): string | undefined {
  if (!value) {
    return value;
  }

  const digitsOnly = value.replace(/\D/g, '');
  if (digitsOnly.length === 0) {
    return value;
  }

  const visibleCount = Math.min(4, digitsOnly.length);
  const maskUntilIndex = digitsOnly.length - visibleCount;

  let digitIndex = 0;
  let result = '';

  for (const char of value) {
    if (/\d/.test(char)) {
      if (digitIndex < maskUntilIndex) {
        result += '*';
      } else {
        result += char;
      }
      digitIndex += 1;
    } else {
      result += char;
    }
  }

  return result;
}

function resolveCreationTimeMs(room?: RoomWithParticipants['room']) {
  if (!room) {
    return null;
  }
  if (room.creationTimeMs) {
    return room.creationTimeMs;
  }
  if (room.creationTime) {
    return room.creationTime * 1000;
  }
  return null;
}

function formatDuration(creationTimeMs: number | null) {
  if (!creationTimeMs) {
    return '--:--';
  }
  const elapsedMs = Math.max(0, Date.now() - creationTimeMs);
  const minutes = Math.floor(elapsedMs / 60000);
  const seconds = Math.floor((elapsedMs % 60000) / 1000);
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function getMetadataValue(metadata: MetadataMap | null | undefined, path: string[]) {
  if (!metadata) {
    return undefined;
  }
  return path.reduce<unknown>((current, key) => {
    if (current === null || current === undefined) {
      return undefined;
    }
    if (Array.isArray(current)) {
      const index = Number(key);
      if (Number.isNaN(index)) {
        return undefined;
      }
      return current[index];
    }
    if (typeof current !== 'object') {
      return undefined;
    }
    return (current as Record<string, unknown>)[key];
  }, metadata);
}

function extractFirstString(
  sources: Array<MetadataMap | null | undefined>,
  paths: string[][]
): string | undefined {
  for (const source of sources) {
    for (const path of paths) {
      const value = getMetadataValue(source, path);
      const stringValue = coerceToString(value);
      if (stringValue) {
        return stringValue;
      }
    }
  }
  return undefined;
}

function deriveSurveyCounts(
  participantMetadata?: MetadataMap | null,
  roomMetadata?: MetadataMap | null
) {
  const sources = [participantMetadata, roomMetadata];
  const answeredValue = extractFirstNumber(sources, [
    ['survey', 'answered'],
    ['survey', 'progress', 'answered'],
    ['surveyAnswered'],
    ['answered'],
  ]);

  const totalValue = extractFirstNumber(sources, [
    ['survey', 'total'],
    ['survey', 'progress', 'total'],
    ['surveyTotal'],
    ['total'],
  ]);

  const normalizedTotal = Math.max(
    MIN_PROGRESS_TOTAL,
    Math.round(totalValue ?? DEFAULT_SURVEY_TOTAL)
  );
  const normalizedAnswered = clampNumber(Math.round(answeredValue ?? 0), 0, normalizedTotal);

  return {
    answered: normalizedAnswered,
    total: normalizedTotal,
  };
}

function extractFirstNumber(
  sources: Array<MetadataMap | null | undefined>,
  paths: string[][]
): number | undefined {
  for (const source of sources) {
    for (const path of paths) {
      const value = getMetadataValue(source, path);
      const numberValue = coerceToNumber(value);
      if (numberValue !== undefined) {
        return numberValue;
      }
    }
  }
  return undefined;
}

function coerceToString(value: unknown): string | undefined {
  if (value === null || value === undefined) {
    return undefined;
  }
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : undefined;
  }
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  return undefined;
}

function coerceToNumber(value: unknown): number | undefined {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : undefined;
  }
  return undefined;
}

function findFirstAttribute(
  attributes: Record<string, string> | undefined,
  keys: string[]
): string | undefined {
  if (!attributes) {
    return undefined;
  }
  for (const key of keys) {
    const value = attributes[key];
    if (value && value.trim().length > 0) {
      return value;
    }
  }
  return undefined;
}

function clampNumber(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}
