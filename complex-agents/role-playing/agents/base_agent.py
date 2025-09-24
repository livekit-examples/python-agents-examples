"""
---
title: Base Game Agent
category: complex-agents
tags: [rpg, game-state, agent-switching, context-preservation, rpc-communication]
difficulty: advanced
description: Base class for RPG game agents with context preservation and state management
demonstrates:
  - Agent inheritance patterns for game systems
  - Chat context preservation across agent switches
  - Game state integration and management
  - RPC communication for client updates
  - Agent lifecycle management with session data
  - Context truncation and memory management
---
"""

import logging
import json
from typing import List
from livekit.agents.voice import Agent
from livekit.agents.llm import ChatContext

from character import NPCCharacter

logger = logging.getLogger("dungeons-and-agents")


class BaseGameAgent(Agent):
    """Base class for all game agents"""
    
    async def on_enter(self) -> None:
        """Called when agent becomes active"""
        agent_name = self.__class__.__name__
        logger.info(f"Entering {agent_name}")
        
        from core.game_state import GameUserData
        userdata: GameUserData = self.session.userdata
        if userdata.ctx and userdata.ctx.room:
            await userdata.ctx.room.local_participant.set_attributes({"agent": agent_name})
        
        # Preserve chat context across agent switches
        chat_ctx = self.chat_ctx.copy()
        
        # If there was a previous agent, inherit its chat context
        if hasattr(userdata, 'prev_agent') and userdata.prev_agent:
            items_copy = self._truncate_chat_ctx(
                userdata.prev_agent.chat_ctx.items, 
                keep_function_call=True,
                keep_last_n_messages=200  # Keep many messages for RPG context
            )
            existing_ids = {item.id for item in chat_ctx.items}
            items_copy = [item for item in items_copy if item.id not in existing_ids]
            chat_ctx.items.extend(items_copy)
        
        # Add current game state as system message
        chat_ctx.add_message(
            role="system",
            content=f"Current game state:\n{userdata.summarize()}"
        )
        await self.update_chat_ctx(chat_ctx)
    
    def _truncate_chat_ctx(
        self,
        items: list,
        keep_last_n_messages: int = 200,
        keep_system_message: bool = False,
        keep_function_call: bool = False,
    ) -> list:
        """Truncate the chat context to keep the last n messages."""
        def _valid_item(item) -> bool:
            if not keep_system_message and item.type == "message" and item.role == "system":
                return False
            if not keep_function_call and item.type in ["function_call", "function_call_output"]:
                return False
            return True

        new_items = []
        for item in reversed(items):
            if _valid_item(item):
                new_items.append(item)
            if len(new_items) >= keep_last_n_messages:
                break
        new_items = new_items[::-1]

        # Remove orphaned function calls at the beginning
        while new_items and new_items[0].type in ["function_call", "function_call_output"]:
            new_items.pop(0)

        return new_items
    
    def _get_active_enemies(self, userdata) -> List[NPCCharacter]:
        """Get list of active enemy NPCs"""
        if userdata.combat_state and not userdata.combat_state.is_complete:
            return [c for c in userdata.combat_state.participants if isinstance(c, NPCCharacter)]
        return []
    
    async def emit_state_update(self, update_type: str, data: dict = None) -> None:
        """Emit a state update to all connected clients via RPC"""
        from core.game_state import GameUserData
        userdata: GameUserData = self.session.userdata
        
        if not userdata.ctx or not userdata.ctx.room:
            logger.warning("Cannot emit state update: no room context")
            return
            
        payload = {
            "type": update_type,
            "data": data or {}
        }
        
        logger.info(f"Emitting state update: {update_type}")
        
        try:
            room = userdata.ctx.room
            remote_participants = list(room.remote_participants.values())
            
            logger.info(f"Found {len(remote_participants)} remote participants to notify")
            
            for participant in remote_participants:
                try:
                    await room.local_participant.perform_rpc(
                        destination_identity=participant.identity,
                        method="game_state_update",
                        payload=json.dumps(payload)
                    )
                    logger.info(f"Successfully emitted {update_type} update to {participant.identity}")
                except Exception as e:
                    logger.error(f"Failed to emit update to {participant.identity}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to emit state update: {e}")