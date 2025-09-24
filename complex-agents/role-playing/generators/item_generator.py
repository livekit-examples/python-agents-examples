"""
---
title: Item Generator
category: complex-agents
tags: [rpg, procedural-generation, llm-generation, yaml-configuration, item-creation]
difficulty: advanced
description: AI-powered procedural item generation system for RPG games
demonstrates:
  - LLM-driven content generation with structured prompts
  - YAML-based rule configuration for generation
  - Context-aware item creation based on NPC and location
  - Automated mechanical property assignment
  - Fallback systems for generation failures
  - JSON parsing and validation for generated content
---
"""

import json
import yaml
import logging
import random
from typing import List, Dict, Any, Optional
from pathlib import Path

from livekit.plugins import openai
from livekit.agents.llm import ChatContext, ChatMessage

from character import Item

logger = logging.getLogger("dungeons-and-agents")


class ItemGenerator:
    """Generates dynamic items using LLM and rule files"""
    
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self) -> dict:
        """Load item generation rules from YAML"""
        rules_path = Path(__file__).parent.parent / "rules" / "item_generation_rules.yaml"
        try:
            with open(rules_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load item generation rules: {e}")
            return {}
    
    async def generate_npc_inventory(self, npc_name: str, npc_class: str, 
                                   npc_level: int, location: str,
                                   owner_type: str = "commoner",
                                   guidelines: str = None) -> List[Item]:
        """Generate contextually appropriate inventory for an NPC"""
        
        # Build generation prompt
        location_mods = self.rules.get('location_modifiers', {}).get(location, {})
        
        prompt = f"""Generate a realistic inventory for this RPG NPC:
Name: {npc_name}
Class: {npc_class}
Level: {npc_level}
Type: {owner_type}
Location: {location}

Guidelines: {guidelines or 'Create appropriate items for this character.'}
Location context: {location_mods.get('item_condition', 'Normal condition')}

Return a JSON list of 3-6 items. Each item should have:
- name: string (unique, evocative item name)
- type: "weapon", "armor", "consumable", or "misc"
- quantity: number (1-5 for consumables, 1 for others)
- value: number (gold value, {10 * npc_level}-{50 * npc_level} based on rarity)
- description: string (1-2 sentences, include sensory details)

Make items feel real and appropriate to the character's role and location.
Include both practical items and 1-2 interesting/unique items.

Example format:
[
    {{"name": "Well-worn Iron Sword", "type": "weapon", "quantity": 1, "value": 35, "description": "The blade shows signs of frequent use but careful maintenance. Its leather-wrapped grip is worn smooth."}},
    {{"name": "Healing Potion", "type": "consumable", "quantity": 2, "value": 25, "description": "A small vial of glowing red liquid that smells of herbs and honey."}}
]"""
        
        # Generate items - using Cerebras for speed
        response = await self._generate_json(prompt, use_cerebras=True)
        
        # Parse and create Item objects
        items = []
        try:
            item_list = json.loads(response) if isinstance(response, str) else response
            
            for item_data in item_list:
                # Generate properties based on type and value
                properties = await self._generate_item_properties(
                    item_data['type'],
                    item_data['name'],
                    item_data.get('description', ''),
                    item_data['value'],
                    npc_level
                )
                
                item = Item(
                    name=item_data['name'],
                    description=item_data.get('description', f"A {item_data['type']}"),
                    item_type=item_data['type'],
                    properties=properties,
                    quantity=item_data.get('quantity', 1)
                )
                items.append(item)
                
        except Exception as e:
            logger.warning(f"Failed to parse generated inventory: {e}")
            # Fallback items
            items = self._create_fallback_items(npc_class, npc_level)
        
        return items
    
    
    async def _generate_item_properties(self, item_type: str, name: str, 
                                      description: str, value: int, 
                                      level: int) -> Dict[str, Any]:
        """Generate mechanical properties for an item"""
        
        properties = {}
        
        if item_type == "weapon":
            # Determine damage based on value and level
            if level <= 3:
                damage_options = ["1d4", "1d6", "1d8"]
            elif level <= 6:
                damage_options = ["1d6", "1d8", "1d10"]
            else:
                damage_options = ["1d8", "1d10", "2d6"]
            
            # Higher value = better damage
            if value < 30:
                properties["damage"] = damage_options[0]
            elif value < 60:
                properties["damage"] = damage_options[1]
            else:
                properties["damage"] = damage_options[2]
                
        elif item_type == "armor":
            # AC bonus based on value
            if value < 30:
                properties["ac_bonus"] = 1
            elif value < 50:
                properties["ac_bonus"] = 2
            elif value < 80:
                properties["ac_bonus"] = 3
            else:
                properties["ac_bonus"] = min(5, 3 + (value // 50))
                
        elif item_type == "consumable":
            if "healing" in name.lower() or "potion" in name.lower():
                # Healing scales with value
                if value < 20:
                    properties["healing"] = "1d4"
                elif value < 40:
                    properties["healing"] = "2d4"
                elif value < 60:
                    properties["healing"] = "2d4+2"
                else:
                    properties["healing"] = "3d4+3"
            elif "mana" in name.lower():
                properties["mana"] = "2d4"
                
        return properties
    
    async def _generate_json(self, prompt: str, model: str = "gpt-4o-mini", use_cerebras: bool = False) -> Any:
        """Generate JSON response using LLM"""
        llm = openai.LLM.with_cerebras() if use_cerebras else openai.LLM(model=model)
        
        ctx = ChatContext([
            ChatMessage(
                type="message",
                role="system",
                content=["You are an RPG item generator. Return ONLY valid JSON arrays. Be creative but appropriate to the context."]
            ),
            ChatMessage(type="message", role="user", content=[prompt])
        ])
        
        response = ""
        async with llm.chat(chat_ctx=ctx) as stream:
            async for chunk in stream:
                if not chunk:
                    continue
                content = getattr(chunk.delta, 'content', None) if hasattr(chunk, 'delta') else str(chunk)
                if content:
                    response += content
        
        # Try to parse and validate JSON
        try:
            return json.loads(response.strip())
        except:
            # Try to extract JSON from response
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            return []
    
    def _create_fallback_items(self, npc_class: str, level: int) -> List[Item]:
        """Create basic fallback items if generation fails"""
        items = []
        
        if npc_class == "warrior":
            items.append(Item("iron sword", "A simple blade", "weapon", {"damage": "1d8"}, 1))
        elif npc_class == "mage":
            items.append(Item("wooden staff", "A basic staff", "weapon", {"damage": "1d6"}, 1))
        elif npc_class == "rogue":
            items.append(Item("dagger", "A sharp blade", "weapon", {"damage": "1d4"}, 1))
        elif npc_class == "cleric":
            items.append(Item("mace", "A heavy weapon", "weapon", {"damage": "1d6"}, 1))
            
        # Add some basic items
        items.append(Item("bread", "A day's ration", "consumable", {}, 2))
        if random.random() < 0.5:
            items.append(Item("healing potion", "Restores health", "consumable", {"healing": "2d4"}, 1))
            
        return items