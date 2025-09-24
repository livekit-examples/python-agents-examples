"""
---
title: Game State Management
category: complex-agents
tags: [rpg, state-management, dataclass, session-data, type-safety]
difficulty: intermediate
description: Centralized game state management for RPG sessions with type-safe data structures
demonstrates:
  - Dataclass-based state management
  - Session data persistence across agent switches
  - Type-safe context handling with generics
  - Game progression tracking and history
  - Multi-agent state coordination
  - Combat state integration
---
"""

from dataclasses import dataclass, field
from typing import Optional, List, TYPE_CHECKING
from livekit.agents import JobContext, AgentSession
from livekit.agents.voice import RunContext

from character import PlayerCharacter, NPCCharacter
from game_mechanics import CombatState

if TYPE_CHECKING:
    from livekit.agents.voice import Agent


@dataclass
class GameUserData:
    """Store game state and data across the session"""
    ctx: JobContext
    session: AgentSession = None
    player_character: PlayerCharacter = None
    current_npcs: List[NPCCharacter] = field(default_factory=list)
    game_state: str = "character_creation"  # character_creation, exploration, combat, dialogue
    combat_state: Optional[CombatState] = None
    story_context: List[str] = field(default_factory=list)
    current_agent_type: str = "narrator"
    current_location: str = "tavern"
    prev_agent: Optional['Agent'] = None  # For context preservation
    active_npc: Optional[NPCCharacter] = None  # NPC currently in dialogue
    voice_acting_character: Optional[str] = None  # Character currently being voice acted
    combat_just_ended: bool = False  # Flag to indicate combat recently ended
    combat_result: Optional[dict] = None  # Store combat results (xp, loot) for narrator
    
    # Track game history
    completed_quests: List[str] = field(default_factory=list)
    visited_locations: List[str] = field(default_factory=list)
    
    def add_story_event(self, event: str):
        """Add an event to the story context"""
        self.story_context.append(event)
        # Keep only last 10 events to manage context size
        if len(self.story_context) > 10:
            self.story_context.pop(0)
    
    def summarize(self) -> str:
        """Provide a summary of current game state"""
        summary = f"Game State: {self.game_state}\n"
        if self.player_character:
            summary += f"Player: {self.player_character.name} - Level {self.player_character.level} {self.player_character.character_class.value}\n"
            summary += f"Health: {self.player_character.current_health}/{self.player_character.max_health}\n"
        if self.current_location:
            summary += f"Location: {self.current_location}\n"
        if self.combat_state and not self.combat_state.is_complete:
            summary += f"In combat with: {', '.join(c.name for c in self.combat_state.participants if isinstance(c, NPCCharacter))}\n"
        return summary


# Type alias for RunContext with our GameUserData
RunContext_T = RunContext[GameUserData]