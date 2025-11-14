'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useRoomContext } from '@livekit/components-react';
import { RpcInvocationData } from 'livekit-client';
import { cn } from '@/lib/utils';

interface PlayerStats {
  name: string;
  class: string;
  level: number;
  current_health: number;
  max_health: number;
  ac: number;
  gold: number;
  stats: Record<string, number>;
}

interface InventoryItem {
  name: string;
  type: string;
  quantity: number;
  description: string;
  properties: Record<string, any>;
  is_equipped?: boolean;
}

interface CombatParticipant {
  name: string;
  type: 'player' | 'enemy';
  current_health: number;
  max_health: number;
  ac: number;
  is_current_turn: boolean;
}

interface GameState {
  game_state: string;
  player: PlayerStats | null;
  inventory: InventoryItem[];
  equipped: {
    weapon: string | null;
    armor: string | null;
  };
}

interface CombatState {
  in_combat: boolean;
  combat: {
    round: number;
    current_turn_index: number;
    turn_order: string[];
    participants: CombatParticipant[];
  } | null;
}

export function GameStatus() {
  const room = useRoomContext();
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [combatState, setCombatState] = useState<CombatState | null>(null);
  const [showInventory, setShowInventory] = useState(false);

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

      // RPC handler for game state updates
      const handleGameStateUpdate = async (data: RpcInvocationData): Promise<string> => {
        try {
          const update = JSON.parse(data.payload);
          
          // Refresh states based on update type
          if (update.type === 'combat_action' || update.type === 'character_defeated') {
            await fetchCombatState();
            await fetchGameState();
          } else if (update.type === 'inventory_changed') {
            await fetchGameState();
          }
          
          return JSON.stringify({ success: true });
        } catch (error) {
          console.error('Error handling game state update:', error);
          return JSON.stringify({ success: false, error: String(error) });
        }
      };

      room.localParticipant.registerRpcMethod('game_state_update', handleGameStateUpdate);

      // Fetch initial states
      const fetchGameState = async () => {
        try {
          // Get all participants (agent should be one of them)
          const participants = Array.from(room.remoteParticipants.values());
          if (participants.length === 0) {
            console.warn('No remote participants found');
            return;
          }
          
          // Find the agent participant
          const agentParticipant = participants[0]; // Usually the first remote participant
          
          const response = await room.localParticipant.performRpc({
            destinationIdentity: agentParticipant.identity,
            method: 'get_game_state',
            payload: ''
          });
          const data = JSON.parse(response);
          if (data.success) {
            setGameState(data.data);
          }
        } catch (error) {
          console.error('Failed to fetch game state:', error);
        }
      };

      const fetchCombatState = async () => {
        try {
          const participants = Array.from(room.remoteParticipants.values());
          if (participants.length === 0) {
            console.warn('No remote participants found');
            return;
          }
          
          const agentParticipant = participants[0];
          
          const response = await room.localParticipant.performRpc({
            destinationIdentity: agentParticipant.identity,
            method: 'get_combat_state',
            payload: ''
          });
          const data = JSON.parse(response);
          if (data.success) {
            setCombatState(data.data);
          }
        } catch (error) {
          console.error('Failed to fetch combat state:', error);
        }
      };

      // Initial fetch
      await fetchGameState();
      await fetchCombatState();

      // Poll for updates every 5 seconds
      const interval = setInterval(() => {
        fetchGameState();
        fetchCombatState();
      }, 5000);

      // Store cleanup function
      (window as any).gameStatusCleanup = () => {
        clearInterval(interval);
        room.localParticipant.unregisterRpcMethod('game_state_update');
      };
    };

    setupRpc();

    return () => {
      if ((window as any).gameStatusCleanup) {
        (window as any).gameStatusCleanup();
      }
    };
  }, [room]);

  if (!gameState?.player) {
    return null;
  }

  const healthPercentage = (gameState.player.current_health / gameState.player.max_health) * 100;
  const healthColor = healthPercentage > 50 ? 'bg-green-500' : healthPercentage > 25 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div className="fixed top-20 right-4 w-80 space-y-4 z-40">
      {/* Player Stats Card */}
      <motion.div
        initial={{ opacity: 0, x: 100 }}
        animate={{ opacity: 1, x: 0 }}
        className="bg-gray-900/90 backdrop-blur-sm rounded-lg p-4 border border-gray-700"
      >
        <h3 className="text-lg font-bold text-white mb-2">
          {gameState.player.name} - Level {gameState.player.level} {gameState.player.class}
        </h3>
        
        {/* Health Bar */}
        <div className="mb-3">
          <div className="flex justify-between text-sm text-gray-300 mb-1">
            <span>Health</span>
            <span>{gameState.player.current_health} / {gameState.player.max_health}</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
            <motion.div
              className={cn('h-full', healthColor)}
              initial={{ width: 0 }}
              animate={{ width: `${healthPercentage}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-gray-300">
            <span className="text-gray-400">AC:</span> {gameState.player.ac}
          </div>
          <div className="text-gray-300">
            <span className="text-gray-400">Gold:</span> {gameState.player.gold}
          </div>
        </div>

        {/* Equipped Items */}
        {(gameState.equipped.weapon || gameState.equipped.armor) && (
          <div className="mt-3 pt-3 border-t border-gray-700 text-sm">
            {gameState.equipped.weapon && (
              <div className="text-gray-300">
                <span className="text-gray-400">Weapon:</span> {gameState.equipped.weapon}
              </div>
            )}
            {gameState.equipped.armor && (
              <div className="text-gray-300">
                <span className="text-gray-400">Armor:</span> {gameState.equipped.armor}
              </div>
            )}
          </div>
        )}
      </motion.div>

      {/* Combat Status */}
      <AnimatePresence>
        {combatState?.in_combat && combatState.combat && (
          <motion.div
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 100 }}
            className="bg-red-900/90 backdrop-blur-sm rounded-lg p-4 border border-red-700"
          >
            <h3 className="text-lg font-bold text-white mb-2">Combat - Round {combatState.combat.round}</h3>
            
            <div className="space-y-2">
              {combatState.combat.participants.map((participant) => (
                <div
                  key={participant.name}
                  className={cn(
                    'p-2 rounded',
                    participant.is_current_turn ? 'bg-red-800/50 ring-2 ring-red-500' : 'bg-gray-800/50'
                  )}
                >
                  <div className="flex justify-between items-center">
                    <span className={cn(
                      'font-medium',
                      participant.type === 'player' ? 'text-blue-400' : 'text-red-400'
                    )}>
                      {participant.name}
                    </span>
                    <span className="text-sm text-gray-300">
                      {participant.current_health}/{participant.max_health} HP
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2 mt-1 overflow-hidden">
                    <div
                      className={participant.type === 'player' ? 'bg-blue-500' : 'bg-red-500'}
                      style={{ width: `${(participant.current_health / participant.max_health) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Inventory Toggle */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setShowInventory(!showInventory)}
        className="w-full bg-gray-900/90 backdrop-blur-sm rounded-lg p-3 border border-gray-700 text-white font-medium hover:bg-gray-800/90 transition-colors"
      >
        {showInventory ? 'Hide' : 'Show'} Inventory ({gameState.inventory.length} items)
      </motion.button>

      {/* Inventory */}
      <AnimatePresence>
        {showInventory && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-gray-900/90 backdrop-blur-sm rounded-lg p-4 border border-gray-700 max-h-96 overflow-y-auto"
          >
            <h3 className="text-lg font-bold text-white mb-2">Inventory</h3>
            
            {gameState.inventory.length === 0 ? (
              <p className="text-gray-400 text-sm">Your inventory is empty</p>
            ) : (
              <div className="space-y-2">
                {gameState.inventory.map((item, index) => (
                  <div
                    key={`${item.name}-${index}`}
                    className={cn(
                      'p-2 rounded bg-gray-800/50 text-sm',
                      item.is_equipped && 'ring-2 ring-blue-500'
                    )}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="text-white font-medium">{item.name}</span>
                        {item.quantity > 1 && (
                          <span className="text-gray-400 ml-1">x{item.quantity}</span>
                        )}
                        {item.is_equipped && (
                          <span className="text-blue-400 text-xs ml-2">[Equipped]</span>
                        )}
                      </div>
                      <span className="text-gray-400 text-xs">{item.type}</span>
                    </div>
                    {item.description && (
                      <p className="text-gray-400 text-xs mt-1">{item.description}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}