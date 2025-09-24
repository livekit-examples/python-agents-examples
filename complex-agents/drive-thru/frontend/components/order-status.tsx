'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useRoomContext } from '@livekit/components-react';
import { RpcInvocationData } from 'livekit-client';
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

interface OrderState {
  items: OrderItem[];
  total_price: number;
  item_count: number;
}

interface CheckoutState {
  total_price: number;
  message: string;
}

export function OrderStatus() {
  const room = useRoomContext();
  const [orderState, setOrderState] = useState<OrderState | null>(null);
  const [checkoutState, setCheckoutState] = useState<CheckoutState | null>(null);

  useEffect(() => {
    if (!room) return;

    const setupRpc = async () => {
      if (room.state !== 'connected') {
        // Wait for room to connect
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

      // RPC handler for checkout screen
      const handleShowCheckout = async (data: RpcInvocationData): Promise<string> => {
        try {
          const checkoutData = JSON.parse(data.payload);
          setCheckoutState({
            total_price: checkoutData.total_price,
            message: checkoutData.message
          });
          return JSON.stringify({ success: true });
        } catch (error) {
          console.error('Error handling show checkout:', error);
          return JSON.stringify({ success: false, error: String(error) });
        }
      };

      room.localParticipant.registerRpcMethod('show_checkout', handleShowCheckout);

      // Fetch order state from agent
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
            payload: ''
          });
          const data = JSON.parse(response);
          if (data.success) {
            setOrderState(data.data);
          }
        } catch (error) {
          console.error('Failed to fetch order state:', error);
        }
      };

      // Initial fetch
      await fetchOrderState();

      // Poll for updates every 1 second
      const interval = setInterval(() => {
        fetchOrderState();
      }, 1000);

      // Store cleanup function
      (window as any).orderStatusCleanup = () => {
        clearInterval(interval);
        room.localParticipant.unregisterRpcMethod('show_checkout');
      };
    };

    setupRpc();

    return () => {
      if ((window as any).orderStatusCleanup) {
        (window as any).orderStatusCleanup();
      }
    };
  }, [room]);

  // Show checkout screen if checkout state is set
  if (checkoutState) {
    return (
      <div className="fixed inset-0 bg-white flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-4xl mx-auto p-8"
        >
          <motion.div
            initial={{ y: -20 }}
            animate={{ y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h1 className="text-7xl font-bold text-black mb-8">Thank You!</h1>
          </motion.div>
          
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            <p className="text-5xl text-gray-700 mb-4">
              Your total is <span className="font-bold text-black">${checkoutState.total_price.toFixed(2)}</span>
            </p>
          </motion.div>
          
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            <p className="text-4xl text-gray-600 mt-12">
              Please drive to the next window!
            </p>
          </motion.div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-white flex flex-col">
      {/* Fixed Header - Only show when there are items */}
      {orderState && orderState.item_count > 0 && (
        <div className="p-8 pb-4">
          <div className="max-w-6xl mx-auto">
            <h1 className="text-6xl font-bold text-black">Your Order</h1>
            <p className="text-2xl text-gray-600 mt-2">
              {orderState.item_count} {orderState.item_count === 1 ? 'item' : 'items'}
            </p>
          </div>
        </div>
      )}

      {/* Content Area */}
      {!orderState || orderState.item_count === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <p className="text-4xl text-gray-500">Welcome to McDonald's</p>
            <p className="text-2xl text-gray-400 mt-4">Please place your order</p>
          </motion.div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-8">
          <div className="max-w-6xl mx-auto">
            <div className="space-y-6 pb-8">
              <AnimatePresence mode="popLayout">
                {orderState.items.map((item) => (
                  <motion.div
                    key={item.order_id}
                    layout
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 50 }}
                    transition={{ duration: 0.3 }}
                    className="bg-gray-100 rounded-lg p-6 shadow-sm"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="text-3xl font-semibold text-black mb-2">{item.name}</h3>
                        {Object.keys(item.details).length > 0 && (
                          <div className="space-y-1">
                            {Object.entries(item.details).map(([key, value]) => (
                              <p key={key} className="text-xl text-gray-600">
                                <span className="capitalize">{key}:</span> {value}
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                      <span className="text-3xl font-bold text-black ml-8">
                        ${item.price.toFixed(2)}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        </div>
      )}

      {/* Fixed Total at Bottom */}
      {orderState && orderState.item_count > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="border-t-4 border-gray-200 p-8 pb-32 bg-white"
        >
          <div className="max-w-6xl mx-auto">
            <div className="flex justify-between items-center">
              <span className="text-5xl font-bold text-black">Total</span>
              <span className="text-5xl font-bold text-black">
                ${orderState.total_price.toFixed(2)}
              </span>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}