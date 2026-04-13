'use client';

import { useCallback, useEffect, useState } from 'react';
import { useLocalParticipant } from '@livekit/components-react';

export interface FlightInfo {
  id: string;
  route: string;
  date: string;
  time: string;
  class: string;
  status: string;
}

export interface HotelInfo {
  id: string;
  name: string;
  check_in: string;
  check_out: string;
  room_type: string;
  status: string;
}

export interface BookingInfo {
  confirmation: string;
  passenger: string;
  flights: FlightInfo[];
  hotel: HotelInfo;
}

export interface AgentEvent {
  type: string;
  payload: Record<string, unknown>;
}

export interface ActiveAgentInfo {
  name: 'Cosmo' | 'Lyra';
  subtitle: string;
}

const DEFAULT_ACTIVE_AGENT: ActiveAgentInfo = {
  name: 'Cosmo',
  subtitle: 'Charismatic and emotionally expressive',
};

/**
 * Hook that registers an RPC method to receive structured events from the agent.
 * Returns the current booking data and a list of modifications.
 */
export function useAgentEvents() {
  const { localParticipant } = useLocalParticipant();
  const [booking, setBooking] = useState<BookingInfo | null>(null);
  const [modifications, setModifications] = useState<AgentEvent[]>([]);
  const [activeAgent, setActiveAgent] = useState<ActiveAgentInfo>(DEFAULT_ACTIVE_AGENT);

  const handleEvent = useCallback((event: AgentEvent) => {
    switch (event.type) {
      case 'agent_persona': {
        const { booking: bookingData, ...agentInfo } = event.payload as Record<string, unknown>;
        setActiveAgent(agentInfo as unknown as ActiveAgentInfo);
        setModifications([]);
        if (bookingData) {
          setBooking(bookingData as unknown as BookingInfo);
        } else {
          setBooking(null);
        }
        break;
      }
      case 'booking_loaded':
        setBooking(event.payload as unknown as BookingInfo);
        break;
      case 'flight_modified':
      case 'flight_cancelled':
      case 'hotel_modified':
      case 'hotel_cancelled':
        setModifications((prev) => [...prev, event]);
        if (event.type.startsWith('flight')) {
          const flightId = (event.payload as Record<string, string>).flight_id;
          setBooking((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              flights: prev.flights.map((f) =>
                f.id === flightId
                  ? {
                      ...f,
                      status: event.type.includes('cancel') ? 'cancelled' : 'modified',
                      ...((event.payload as Record<string, string>).new_date
                        ? { date: (event.payload as Record<string, string>).new_date }
                        : {}),
                    }
                  : f
              ),
            };
          });
        }
        if (event.type.startsWith('hotel')) {
          setBooking((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              hotel: {
                ...prev.hotel,
                status: event.type.includes('cancel') ? 'cancelled' : 'modified',
                ...((event.payload as Record<string, string>).new_check_in
                  ? { check_in: (event.payload as Record<string, string>).new_check_in }
                  : {}),
                ...((event.payload as Record<string, string>).new_check_out
                  ? { check_out: (event.payload as Record<string, string>).new_check_out }
                  : {}),
              },
            };
          });
        }
        break;
      case 'modification_summary':
        if (event.payload.current_booking) {
          setBooking(event.payload.current_booking as unknown as BookingInfo);
        }
        break;
    }
  }, []);

  useEffect(() => {
    if (!localParticipant) return;

    localParticipant.registerRpcMethod('agentEvent', async (data) => {
      try {
        const event = JSON.parse(data.payload) as AgentEvent;
        handleEvent(event);
      } catch {
        console.warn('Failed to parse agent event:', data.payload);
      }
      return JSON.stringify({ ok: true });
    });
  }, [localParticipant, handleEvent]);

  return { booking, modifications, activeAgent };
}
