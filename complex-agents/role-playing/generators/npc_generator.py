"""
---
title: NPC Generator
category: complex-agents
tags: [rpg, procedural-generation, character-creation, personality-generation, dialogue-system]
difficulty: advanced
description: AI-powered NPC generation system with personality, backstory, and dynamic dialogue
demonstrates:
  - Dynamic NPC creation with context-aware traits
  - Parallel content generation for efficiency
  - YAML rule-based character archetypes
  - Personality and backstory generation
  - Dynamic dialogue creation and management
  - Integration with item generation systems
---
"""

import random
import yaml
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from livekit.plugins import openai
from livekit.agents.llm import ChatContext, ChatMessage

from character import NPCCharacter, CharacterClass, CharacterStats, create_random_npc
from generators.item_generator import ItemGenerator

logger = logging.getLogger("dungeons-and-agents")


class NPCGenerator:
    """Generates dynamic NPCs using LLM and rule files"""
    
    def __init__(self):
        self.rules = self._load_rules()
        self.item_generator = ItemGenerator()
    
    def _load_rules(self) -> dict:
        """Load NPC generation rules from YAML"""
        rules_path = Path(__file__).parent.parent / "rules" / "npc_generation_rules.yaml"
        try:
            with open(rules_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load NPC generation rules: {e}")
            return {}
    
    async def generate_npc(self, name: str, location: str, 
                          recent_events: List[str] = None,
                          npc_type: str = None) -> NPCCharacter:
        """Generate a complete NPC with personality, inventory, and backstory"""
        
        # Determine NPC type from name if not specified
        if not npc_type:
            npc_type = self._determine_npc_type(name)
        
        # Get rules for this NPC type
        type_rules = self.rules.get('npc_types', {}).get(npc_type, self.rules['npc_types']['commoner'])
        
        # Determine class and level
        character_class = self._select_class(type_rules['class_weights'])
        level = random.randint(*type_rules['level_range'])
        
        # Create base NPC
        npc = create_random_npc(
            name=name.title(),
            character_class=character_class,
            level=level,
            disposition=self._select_disposition(type_rules['disposition_weights'])
        )
        
        # Set gold based on type
        npc.gold = random.randint(*type_rules['gold_range'])
        
        # Set merchant flag
        if npc_type == 'merchant':
            npc.merchant = True
        
        # Generate personality, backstory, and inventory in parallel
        personality, backstory, inventory = await self._parallel_generate(
            npc, npc_type, location, recent_events or [], type_rules
        )
        
        # Apply generated content
        npc.personality = personality
        npc.backstory = backstory
        npc.inventory = inventory
        
        
        # Generate initial dialogue options
        npc.dialogue_options = await self._generate_dialogue(
            npc, npc_type, location, type_rules
        )
        
        return npc
    
    def _determine_npc_type(self, name: str) -> str:
        """Determine NPC type from name"""
        name_lower = name.lower()
        
        if any(word in name_lower for word in ['barkeep', 'innkeeper', 'merchant', 'trader', 'shopkeeper']):
            return 'merchant'
        elif any(word in name_lower for word in ['guard', 'soldier', 'captain', 'knight']):
            return 'guard'
        elif any(word in name_lower for word in ['wizard', 'mage', 'sorcerer', 'enchanter']):
            return 'wizard'
        else:
            return 'commoner'
    
    def _select_class(self, class_weights: Dict[str, float]) -> CharacterClass:
        """Select character class based on weights"""
        classes = []
        weights = []
        
        for class_name, weight in class_weights.items():
            classes.append(CharacterClass[class_name.upper()])
            weights.append(weight)
        
        return random.choices(classes, weights=weights)[0]
    
    def _select_disposition(self, disposition_weights: Dict[str, float]) -> str:
        """Select disposition based on weights"""
        dispositions = list(disposition_weights.keys())
        weights = list(disposition_weights.values())
        return random.choices(dispositions, weights=weights)[0]
    
    async def _parallel_generate(self, npc: NPCCharacter, npc_type: str, 
                                location: str, recent_events: List[str],
                                type_rules: dict) -> tuple:
        """Generate personality, backstory, and inventory in parallel"""
        
        # Prepare prompts
        traits = random.sample(type_rules['personality_traits'], 3)
        
        personality_prompt = self.rules['generation_prompts']['personality'].format(
            name=npc.name,
            character_class=npc.character_class.value,
            npc_type=npc_type,
            location=location,
            recent_events=', '.join(recent_events[-3:]) if recent_events else 'none',
            traits=', '.join(traits)
        )
        
        # Generate personality first (needed for backstory) - using Cerebras for speed
        personality = await self._generate_text(personality_prompt, use_cerebras=True)
        
        backstory_prompt = self.rules['generation_prompts']['backstory'].format(
            name=npc.name,
            level=npc.level,
            character_class=npc.character_class.value,
            npc_type=npc_type,
            personality=personality,
            location=location
        )
        
        # Generate backstory and inventory in parallel - using Cerebras for speed
        backstory_task = self._generate_text(backstory_prompt, use_cerebras=True)
        inventory_task = self.item_generator.generate_npc_inventory(
            npc.name,
            npc.character_class.value,
            npc.level,
            location,
            owner_type=npc_type,
            guidelines=type_rules['inventory_guidelines']
        )
        
        backstory = await backstory_task
        inventory = await inventory_task
        
        return personality, backstory, inventory
    
    async def _generate_dialogue(self, npc: NPCCharacter, npc_type: str,
                               location: str, type_rules: dict) -> List[str]:
        """Generate dialogue options for the NPC"""
        
        dialogue_prompt = self.rules['generation_prompts']['dialogue'].format(
            name=npc.name,
            personality=getattr(npc, 'personality', ''),
            backstory=getattr(npc, 'backstory', ''),
            context=f"Meeting in {location}",
            dialogue_style=type_rules['dialogue_style'],
            relationship="first meeting"
        )
        
        response = await self._generate_text(dialogue_prompt, use_cerebras=True)
        
        # Parse dialogue lines from response
        dialogue_lines = []
        for line in response.split('\n'):
            text = line.strip()
            if not text or text.startswith('#'):
                continue
            # Trim surrounding quotes, bullets, list markers, and numeric prefixes
            cleaned = text.strip("\"\\'-•*0123456789. ")
            if cleaned:
                dialogue_lines.append(cleaned)
        
        return dialogue_lines[:5]  # Keep first 5 lines
    
    async def _generate_text(self, prompt: str, model: str = "gpt-4o-mini", use_cerebras: bool = False) -> str:
        """Generate text using LLM"""
        llm = openai.LLM.with_cerebras() if use_cerebras else openai.LLM(model=model)
        
        ctx = ChatContext([
            ChatMessage(
                type="message",
                role="system",
                content=["You are a creative RPG content generator. Be concise and evocative."]
            ),
            ChatMessage(
                type="message",
                role="user",
                content=[prompt]
            )
        ])
        
        response = ""
        async with llm.chat(chat_ctx=ctx) as stream:
            async for chunk in stream:
                if not chunk:
                    continue
                content = getattr(chunk.delta, 'content', None) if hasattr(chunk, 'delta') else str(chunk)
                if content:
                    response += content
        
        return response.strip()


async def create_npc_by_role(npc_name: str, location: str = "tavern",
                           recent_events: List[str] = None) -> NPCCharacter:
    """Convenience function to create NPC using the generator"""
    generator = NPCGenerator()
    return await generator.generate_npc(npc_name, location, recent_events)