'use client';

import React, { useEffect, useState } from 'react';
import type { RpcInvocationData } from 'livekit-client';
import { AnimatePresence, motion } from 'motion/react';
import { useRoomContext } from '@livekit/components-react';
import { DataCard } from '@/components/ui/data-card';
import { StatusPill, type StatusTone } from '@/components/ui/status-pill';
import { cn } from '@/lib/utils';

interface OrderItem {
  order_id: string;
  type: 'combo_meal' | 'happy_meal' | 'regular';
  name: string;
  price: number;
  details: Record<string, string>;
  meal_id?: string;
  item_id?: string;
  drink_size?: string;
  fries_size?: string;
  size?: string;
}

export interface OrderState {
  items: OrderItem[];
  total_price: number;
  item_count: number;
}

export interface CheckoutState {
  total_price: number;
  message: string;
}

declare global {
  interface Window {
    orderStatusCleanup?: () => void;
  }
}

const ORDER_TYPE_META: Record<OrderItem['type'], { label: string; tone: StatusTone }> = {
  combo_meal: { label: 'Combo Meal', tone: 'info' },
  happy_meal: { label: 'Happy Meal', tone: 'success' },
  regular: { label: 'A La Carte', tone: 'neutral' },
};

const MONEY_FORMATTER = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
});

function formatMoney(value: number) {
  return MONEY_FORMATTER.format(value);
}

function formatKey(label: string) {
  return label
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .split(' ')
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export interface OrderStatusProps {
  className?: string;
  showFooter?: boolean;
  onStateChange?: (orderState: OrderState | null, checkoutState: CheckoutState | null) => void;
}

export function OrderStatus({
  className,
  showFooter = true,
  onStateChange,
}: OrderStatusProps = {}) {
  const room = useRoomContext();
  const [orderState, setOrderState] = useState<OrderState | null>(null);
  const [checkoutState, setCheckoutState] = useState<CheckoutState | null>(null);

  useEffect(() => {
    onStateChange?.(orderState, checkoutState);
  }, [orderState, checkoutState, onStateChange]);

  useEffect(() => {
    if (!room) return;

    const setupRpc = async () => {
      if (room.state !== 'connected') {
        await new Promise<void>((resolve) => {
          const checkConnection = () => {
            if (room.state === 'connected') {
              resolve();
            } else {
              setTimeout(checkConnection, 100);
            }
          };
          checkConnection();
        });
      }

      const handleShowCheckout = async (data: RpcInvocationData): Promise<string> => {
        try {
          const checkoutData = JSON.parse(data.payload);
          setCheckoutState({
            total_price: checkoutData.total_price,
            message: checkoutData.message,
          });
          return JSON.stringify({ success: true });
        } catch (error) {
          console.error('Error handling show checkout:', error);
          return JSON.stringify({ success: false, error: String(error) });
        }
      };

      room.localParticipant.registerRpcMethod('show_checkout', handleShowCheckout);

      const fetchOrderState = async () => {
        try {
          const participants = Array.from(room.remoteParticipants.values());
          if (participants.length === 0) {
            console.warn('No remote participants found');
            return;
          }

          const agentParticipant = participants[0];

          const response = await room.localParticipant.performRpc({
            destinationIdentity: agentParticipant.identity,
            method: 'get_order_state',
            payload: '',
          });
          const data = JSON.parse(response);
          if (data.success) {
            setOrderState(data.data);
          }
        } catch (error) {
          console.error('Failed to fetch order state:', error);
        }
      };

      await fetchOrderState();
      const interval = setInterval(fetchOrderState, 1000);

      const cleanup = () => {
        clearInterval(interval);
        room.localParticipant.unregisterRpcMethod('show_checkout');
      };

      window.orderStatusCleanup = cleanup;
    };

    setupRpc();

    return () => {
      if (window.orderStatusCleanup) {
        window.orderStatusCleanup();
        window.orderStatusCleanup = undefined;
      }
    };
  }, [room]);

  if (checkoutState) {
    return (
      <div
        className={cn(
          'bg-bg1 text-fg1 flex flex-1 flex-col items-center justify-center px-6 text-center',
          className
        )}
      >
        <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
          <div className="max-w-3xl space-y-8">
            <motion.h1
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              className="text-fg0 text-5xl font-bold"
            >
              Thank you!
            </motion.h1>
            <motion.p
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="text-fg2 text-3xl"
            >
              Your total is{' '}
              <span className="text-fg0 font-semibold">
                {formatMoney(checkoutState.total_price)}
              </span>
            </motion.p>
            <motion.p
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-fg3 text-2xl"
            >
              {checkoutState.message || 'Please drive to the next window.'}
            </motion.p>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className={cn('bg-bg1 text-fg1 flex flex-col', className)}>
      <header className="border-separator1 bg-bg1/80 border-b backdrop-blur">
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-1 px-6 py-6">
          <h1 className="text-fg0 text-3xl font-semibold">Your Order</h1>
          <p className="text-fg3 text-sm">
            {orderState && orderState.item_count > 0
              ? `${orderState.item_count} ${orderState.item_count === 1 ? 'item' : 'items'} in progress`
              : "Welcome to McDonald's - your selections will appear here."}
          </p>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-6 py-6">
        {!orderState || orderState.item_count === 0 ? (
          <div className="border-separator1 bg-bg2/60 flex flex-1 items-center justify-center rounded-2xl border border-dashed text-center">
            <div className="space-y-2">
              <p className="text-fg2 text-lg font-medium">We&apos;re ready when you are.</p>
              <p className="text-fg4 text-sm">
                Items you add with the drive-thru agent will land here instantly.
              </p>
            </div>
          </div>
        ) : (
          <div className="lk-scrollable flex-1 overflow-y-auto pb-10">
            <AnimatePresence mode="popLayout">
              <div className="grid gap-4">
                {orderState.items.map((item) => {
                  const meta = ORDER_TYPE_META[item.type];
                  const detailEntries = Object.entries({
                    ...item.details,
                    ...(item.size ? { size: item.size } : {}),
                    ...(item.drink_size ? { drink_size: item.drink_size } : {}),
                    ...(item.fries_size ? { fries_size: item.fries_size } : {}),
                  });
                  const metrics = [
                    { label: 'Price', value: formatMoney(item.price) },
                    ...detailEntries.map(([key, value]) => ({
                      label: formatKey(key),
                      value,
                    })),
                  ];

                  return (
                    <motion.div
                      key={item.order_id}
                      layout
                      initial={{ opacity: 0, y: 16 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -16 }}
                      transition={{ duration: 0.2 }}
                    >
                      <DataCard
                        title={item.name}
                        subtitle={`Order #${item.order_id}`}
                        metrics={metrics}
                        status={<StatusPill tone={meta.tone}>{meta.label}</StatusPill>}
                        footer={
                          item.meal_id || item.item_id
                            ? [item.meal_id, item.item_id]
                                .filter(Boolean)
                                .map((value, index) => (index === 0 ? value : `• ${value}`))
                                .join(' ')
                            : undefined
                        }
                        interactive
                      />
                    </motion.div>
                  );
                })}
              </div>
            </AnimatePresence>
          </div>
        )}
      </main>

      {showFooter && orderState && orderState.item_count > 0 ? (
        <footer className="border-separator1 bg-bg1/95 border-t">
          <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-5">
            <div className="text-fg3 text-sm font-medium">Running total</div>
            <div className="text-fg0 text-2xl font-semibold">
              {formatMoney(orderState.total_price)}
            </div>
          </div>
        </footer>
      ) : null}
    </div>
  );
}
