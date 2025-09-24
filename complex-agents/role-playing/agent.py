"""
---
title: D&D Role-Playing Game
category: complex-agents
tags: [rpg, game_state, rpc_methods, item_generation, combat_system, npc_interaction]
difficulty: advanced
description: Dungeons & Dragons role-playing game with narrator and combat agents
demonstrates:
  - Complex game state management
  - Multiple RPC methods for game queries
  - Dynamic NPC and item generation
  - Combat system with initiative tracking
  - Character creation and stats management
  - Inventory and equipment system
  - Voice acting for different NPCs
---
"""

import logging
import json
from dotenv import load_dotenv

from livekit.agents import JobContext, WorkerOptions, cli, AgentSession
from livekit.rtc import RpcInvocationData

# Import our modular components
from core.game_state import GameUserData
from agents.narrator_agent import NarratorAgent

logger = logging.getLogger("dungeons-and-agents")
logger.setLevel(logging.INFO)

load_dotenv()


async def entrypoint(ctx: JobContext):
    """Main entry point for the game"""
    await ctx.connect()
    # Initialize user data
    userdata = GameUserData(ctx=ctx)
    
    # RPC Handlers
    async def get_game_state(data: RpcInvocationData) -> str:
        """Get current game state, player stats, and inventory"""
        try:
            response = {
                "success": True,
                "data": {
                    "game_state": userdata.game_state,
                    "player": None,
                    "inventory": [],
                    "equipped": {"weapon": None, "armor": None}
                }
            }
            
            if userdata.player_character:
                pc = userdata.player_character
                response["data"]["player"] = {
                    "name": pc.name,
                    "class": pc.character_class.value if hasattr(pc.character_class, 'value') else str(pc.character_class),
                    "level": pc.level,
                    "current_health": pc.current_health,
                    "max_health": pc.max_health,
                    "ac": pc.armor_class,
                    "gold": pc.gold,
                    "stats": {
                        "strength": pc.stats.strength,
                        "dexterity": pc.stats.dexterity,
                        "constitution": pc.stats.constitution,
                        "intelligence": pc.stats.intelligence,
                        "wisdom": pc.stats.wisdom,
                        "charisma": pc.stats.charisma
                    }
                }
                response["data"]["inventory"] = [
                    {
                        "name": item.name,
                        "type": item.item_type,
                        "quantity": item.quantity,
                        "description": item.description,
                        "properties": item.properties
                    } for item in pc.inventory
                ]
                response["data"]["equipped"] = {
                    "weapon": pc.equipped_weapon.name if pc.equipped_weapon else None,
                    "armor": pc.equipped_armor.name if pc.equipped_armor else None
                }
                
            return json.dumps(response)
        except Exception as e:
            logger.error(f"Error in get_game_state RPC: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    async def get_combat_state(data: RpcInvocationData) -> str:
        """Get current combat state"""
        try:
            response = {
                "success": True,
                "data": {
                    "in_combat": userdata.combat_state is not None,
                    "combat": None
                }
            }
            
            if userdata.combat_state:
                cs = userdata.combat_state
                current_character = cs.get_current_character()
                response["data"]["combat"] = {
                    "round": cs.round_number,
                    "current_turn_index": cs.current_turn_index,
                    "turn_order": [char.name for char in cs.initiative_order],
                    "participants": []
                }
                
                # Add all participants from the initiative order
                for char in cs.initiative_order:
                    participant_data = {
                        "name": char.name,
                        "type": "player" if isinstance(char, type(userdata.player_character)) and char == userdata.player_character else "enemy",
                        "current_health": char.current_health,
                        "max_health": char.max_health,
                        "ac": char.armor_class,
                        "is_current_turn": char == current_character
                    }
                    response["data"]["combat"]["participants"].append(participant_data)
                    
            return json.dumps(response)
        except Exception as e:
            logger.error(f"Error in get_combat_state RPC: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    async def get_inventory(data: RpcInvocationData) -> str:
        """Get detailed inventory information"""
        try:
            response = {
                "success": True,
                "data": {
                    "inventory": [],
                    "equipped": {"weapon": None, "armor": None},
                    "gold": 0
                }
            }
            
            if userdata.player_character:
                pc = userdata.player_character
                response["data"]["gold"] = pc.gold
                response["data"]["inventory"] = [
                    {
                        "name": item.name,
                        "type": item.item_type,
                        "quantity": item.quantity,
                        "description": item.description,
                        "properties": item.properties,
                        "is_equipped": (
                            (item == pc.equipped_weapon and item.item_type == "weapon") or 
                            (item == pc.equipped_armor and item.item_type == "armor")
                        )
                    } for item in pc.inventory
                ]
                response["data"]["equipped"] = {
                    "weapon": {
                        "name": pc.equipped_weapon.name,
                        "damage": pc.equipped_weapon.properties.get("damage", "1d4")
                    } if pc.equipped_weapon else None,
                    "armor": {
                        "name": pc.equipped_armor.name,
                        "ac": pc.equipped_armor.properties.get("armor_class", 10)
                    } if pc.equipped_armor else None
                }
                
            return json.dumps(response)
        except Exception as e:
            logger.error(f"Error in get_inventory RPC: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    async def get_current_context(data: RpcInvocationData) -> str:
        """Get current conversation context (agent type, voice acting character, etc)"""
        try:
            logger.info(f"get_current_context called - voice_acting_character: {userdata.voice_acting_character if userdata.voice_acting_character else 'None'}")
            
            response = {
                "success": True,
                "data": {
                    "agent_type": userdata.current_agent_type,
                    "game_state": userdata.game_state,
                    "voice_acting_character": userdata.voice_acting_character,
                    "in_combat": userdata.combat_state is not None
                }
            }
            
            logger.info(f"Returning context with voice_acting_character: {response['data']['voice_acting_character']}")
            
            return json.dumps(response)
        except Exception as e:
            logger.error(f"Error in get_current_context RPC: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    # Register RPC methods
    ctx.room.local_participant.register_rpc_method("get_game_state", get_game_state)
    ctx.room.local_participant.register_rpc_method("get_combat_state", get_combat_state)
    ctx.room.local_participant.register_rpc_method("get_inventory", get_inventory)
    ctx.room.local_participant.register_rpc_method("get_current_context", get_current_context)
    
    logger.info("RPC methods registered: get_game_state, get_combat_state, get_inventory, get_current_context")
    
    # Create initial agent
    narrator_agent = NarratorAgent()
    
    # Create session with user data
    session = AgentSession[GameUserData](userdata=userdata)
    
    userdata.session = session
    
    # Start with narrator agent
    await session.start(agent=narrator_agent, room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))