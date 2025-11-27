import { useEffect, useState } from 'react';
import type { RoomWithParticipants, RoomsApiResponse } from '@/types/call-queue';

interface RoomQueueState {
  rooms: RoomWithParticipants[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: number | null;
}

const POLL_INTERVAL_MS = 1000;

export function useRoomQueue(pollInterval = POLL_INTERVAL_MS): RoomQueueState {
  const [state, setState] = useState<RoomQueueState>({
    rooms: [],
    isLoading: true,
    error: null,
    lastUpdated: null,
  });

  useEffect(() => {
    let mounted = true;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    let abortController: AbortController | null = null;

    const fetchRooms = async () => {
      abortController?.abort();
      abortController = new AbortController();

      try {
        const response = await fetch('/api/rooms', {
          method: 'GET',
          cache: 'no-store',
          signal: abortController.signal,
        });

        if (!response.ok) {
          const message = await response.text();
          throw new Error(message || 'Failed to fetch rooms');
        }

        const data = (await response.json()) as RoomsApiResponse;
        if (!mounted) {
          return;
        }

        setState({
          rooms: data.rooms ?? [],
          isLoading: false,
          error: null,
          lastUpdated: Date.now(),
        });
      } catch (error) {
        if (!mounted) {
          return;
        }
        if ((error as Error).name === 'AbortError') {
          return;
        }
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Unexpected error',
        }));
      } finally {
        if (mounted) {
          timeoutId = setTimeout(fetchRooms, Math.max(500, pollInterval));
        }
      }
    };

    fetchRooms();

    return () => {
      mounted = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      abortController?.abort();
    };
  }, [pollInterval]);

  return state;
}
