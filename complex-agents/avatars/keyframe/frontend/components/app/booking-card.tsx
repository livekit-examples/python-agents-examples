'use client';

import { AnimatePresence, motion } from 'motion/react';
import type { BookingInfo } from '@/hooks/useAgentEvents';
import { cn } from '@/lib/shadcn/utils';

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={cn(
        'rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase',
        status === 'confirmed' && 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
        status === 'modified' && 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
        status === 'cancelled' && 'bg-red-500/15 text-red-600 line-through dark:text-red-400'
      )}
    >
      {status}
    </span>
  );
}

interface BookingCardProps {
  booking: BookingInfo | null;
}

export function BookingCard({ booking }: BookingCardProps) {
  return (
    <AnimatePresence>
      {booking && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="bg-card border-border pointer-events-auto w-72 rounded-lg border p-4 shadow-lg backdrop-blur-sm"
        >
          {/* Header */}
          <div className="mb-3 flex items-center justify-between">
            <span className="text-foreground font-mono text-xs font-bold tracking-wider uppercase">
              Acme Airlines
            </span>
            <span className="text-muted-foreground font-mono text-[10px]">
              {booking.confirmation}
            </span>
          </div>

          <p className="text-foreground mb-3 text-sm font-medium">{booking.passenger}</p>

          {/* Flights */}
          <div className="space-y-2">
            {booking.flights.map((flight) => (
              <div
                key={flight.id}
                className={cn(
                  'bg-muted/50 rounded-md p-2.5',
                  flight.status === 'cancelled' && 'opacity-50'
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-foreground text-xs font-medium">{flight.route}</span>
                  <StatusBadge status={flight.status} />
                </div>
                <div className="text-muted-foreground mt-1 flex items-center gap-2 text-[11px]">
                  <span>{flight.date}</span>
                  <span className="text-border">|</span>
                  <span>{flight.time}</span>
                  <span className="text-border">|</span>
                  <span>{flight.class}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Hotel */}
          <div
            className={cn(
              'bg-muted/50 mt-2 rounded-md p-2.5',
              booking.hotel.status === 'cancelled' && 'opacity-50'
            )}
          >
            <div className="flex items-center justify-between">
              <span className="text-foreground text-xs font-medium">{booking.hotel.name}</span>
              <StatusBadge status={booking.hotel.status} />
            </div>
            <div className="text-muted-foreground mt-1 flex items-center gap-2 text-[11px]">
              <span>
                {booking.hotel.check_in} &rarr; {booking.hotel.check_out}
              </span>
              <span className="text-border">|</span>
              <span>{booking.hotel.room_type}</span>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
