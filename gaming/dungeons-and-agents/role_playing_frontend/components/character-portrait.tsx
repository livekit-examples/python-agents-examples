'use client';

import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useRoomContext, useVoiceAssistant } from '@livekit/components-react';
import { RpcInvocationData } from 'livekit-client';
import { cn } from '@/lib/utils';

interface CharacterPortraitProps {
  className?: string;
}

export function CharacterPortrait({ className }: CharacterPortraitProps) {
  const room = useRoomContext();
  const { agent } = useVoiceAssistant();
  const [currentPortrait, setCurrentPortrait] = useState<string>('/portraits/narrator_card.png');
  const [characterName, setCharacterName] = useState<string>('Narrator');
  const [isVisible, setIsVisible] = useState(true);
  // Remove intervalRef as we're not using polling anymore

  // Debug log to see if component is mounting
  console.log('[CharacterPortrait] Component render, room:', room?.name, 'state:', room?.state);

  useEffect(() => {
    if (!room || room.state !== 'connected' || !agent) return;

    console.log('[CharacterPortrait] Setting up portrait updates...');

    const agentPortraits: { [key: string]: { portrait: string; name: string } } = {
      'narrator': { portrait: '/portraits/narrator_card.png', name: 'Narrator' },
      'combat': { portrait: '/portraits/combat_card.png', name: 'Battle Mode' },
    };

    const npcPortraits: { [key: string]: { portrait: string; name: string } } = {
      'barkeep': { portrait: '/portraits/barkeep_card.png', name: 'Barkeep' },
      'goblin': { portrait: '/portraits/goblin_card.png', name: 'Goblin' },
      'merchant': { portrait: '/portraits/merchant_card.png', name: 'Merchant' },
      'rogue': { portrait: '/portraits/rogue_card.png', name: 'Rogue' },
    };

    // Function to update portrait based on context
    const updatePortraitFromContext = (context: any) => {
      console.log('[CharacterPortrait] Updating portrait from context:', JSON.stringify(context, null, 2));
      
      // Check if we have a voice acting character
      if (context.voice_acting_character) {
        const characterName = context.voice_acting_character.toLowerCase();
        console.log('[CharacterPortrait] Voice acting character detected:', characterName);
        
        if (npcPortraits[characterName]) {
          const newPortrait = npcPortraits[characterName].portrait;
          const newName = npcPortraits[characterName].name;
          console.log('[CharacterPortrait] Setting portrait to:', newPortrait);
          
          // Only update if actually changed
          setCurrentPortrait(prev => {
            if (prev !== newPortrait) {
              console.log('[CharacterPortrait] Portrait actually changing from', prev, 'to', newPortrait);
            }
            return newPortrait;
          });
          setCharacterName(newName);
        } else {
          console.log('[CharacterPortrait] No specific portrait for character, using fallback');
          // Fallback to generic portrait based on character type
          setCurrentPortrait('/portraits/villager_card.png');
          setCharacterName(characterName.charAt(0).toUpperCase() + characterName.slice(1));
        }
      } else {
        // Use agent portrait
        const portraitData = agentPortraits[context.agent_type] || agentPortraits['narrator'];
        console.log('[CharacterPortrait] No voice acting character, using agent portrait:', portraitData.portrait);
        setCurrentPortrait(portraitData.portrait);
        setCharacterName(portraitData.name);
      }
    };

    // Function to fetch current context
    const fetchCurrentContext = async () => {
      try {
        const agentParticipant = agent;
        console.log('[CharacterPortrait] Using agent identity for RPC:', agentParticipant.identity);
        console.log('[CharacterPortrait] Calling get_current_context RPC...');
        
        const response = await room.localParticipant.performRpc({
          destinationIdentity: agentParticipant.identity,
          method: 'get_current_context',
          payload: JSON.stringify({})
        });
        
        console.log('[CharacterPortrait] Raw RPC response:', response);
        console.log('[CharacterPortrait] Response type:', typeof response);
        
        let data;
        try {
          data = typeof response === 'string' ? JSON.parse(response) : response;
          console.log('[CharacterPortrait] Parsed data:', data);
        } catch (e) {
          console.error('[CharacterPortrait] Failed to parse response:', e);
          return;
        }
        
        if (data.success && data.data) {
          console.log('[CharacterPortrait] Calling updatePortraitFromContext with:', data.data);
          updatePortraitFromContext(data.data);
        } else {
          console.error('[CharacterPortrait] RPC returned unsuccessful response:', data);
        }
      } catch (error) {
        console.error('[CharacterPortrait] Failed to fetch context:', error);
      }
    };

      // Register RPC handler for game state updates
      const handleGameStateUpdate = async (data: RpcInvocationData): Promise<string> => {
        try {
          const update = JSON.parse(data.payload);
          console.log('[CharacterPortrait] Received game state update:', update);
          
          // Fetch updated context on relevant events
          if (update.type === 'voice_acting_start' || 
              update.type === 'voice_acting_end' || 
              update.type === 'combat_start') {
            console.log('[CharacterPortrait] Event matches, fetching context...');
            await fetchCurrentContext();
          }
          
          return "success";
        } catch (error) {
          console.error('[CharacterPortrait] Failed to handle game state update:', error);
          return "error: " + error;
        }
      };
      
      // Register the RPC method
      room.localParticipant.registerRpcMethod('game_state_update', handleGameStateUpdate);
      console.log('[CharacterPortrait] Registered game_state_update RPC handler');
      
    // Initial load to get current state
    console.log('[CharacterPortrait] Performing initial context fetch...');
    fetchCurrentContext();

    return () => {
      console.log('[CharacterPortrait] Cleanup');
      room.localParticipant.unregisterRpcMethod('game_state_update');
    };
  }, [room?.state, agent]); // Only re-run when room connection state or agent changes

  return (
    <AnimatePresence mode="wait">
      {isVisible && (
        <motion.div
          key={currentPortrait}
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className={cn(
            'relative overflow-hidden rounded-lg',
            'shadow-lg shadow-black/50',
            'aspect-[2/3]', // Fixed aspect ratio for portrait cards
            className
          )}
        >
          {/* Debug text if no image loads */}
          <div className="absolute inset-0 flex items-center justify-center bg-gray-800 text-white text-xs">
            {characterName}
          </div>
          
          {/* Portrait Image */}
          <img
            key={currentPortrait} // Force re-render when src changes
            src={currentPortrait}
            alt={characterName}
            className="h-full w-full object-cover relative z-10"
            onLoad={() => {
              console.log('[CharacterPortrait] Image loaded successfully:', currentPortrait);
            }}
            onError={(e) => {
              console.log('[CharacterPortrait] Image failed to load:', currentPortrait);
              // Fallback to narrator if image fails to load
              (e.target as HTMLImageElement).src = '/portraits/narrator_card.png';
            }}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}