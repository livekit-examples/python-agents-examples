"""
---
title: Narrator Agent
category: complex-agents
tags: [rpg, storytelling, npc-interaction, voice-acting, exploration]
difficulty: advanced
description: Main storytelling agent for RPG games with voice acting and world interaction
demonstrates:
  - Dynamic storytelling and narrative flow
  - Multi-voice character portrayal with TTS switching
  - NPC interaction and dialogue management
  - World exploration and location transitions
  - Character creation and progression
  - Trading and inventory management
  - Skill check resolution and dice rolling
---
"""

import random
import asyncio
import logging
from typing import List, TYPE_CHECKING

from livekit.agents.llm import function_tool
from livekit.plugins import deepgram, openai, silero, inworld

from agents.base_agent import BaseGameAgent
from character import PlayerCharacter, NPCCharacter, CharacterClass, CharacterStats, Item
from generators.npc_generator import create_npc_by_role
from core.game_state import RunContext_T
from game_mechanics import SkillCheck, Combat, GameUtilities, DiceRoller
from utils.display import Colors
from utils.prompt_loader import load_prompt

if TYPE_CHECKING:
    from agents.combat_agent import CombatAgent

logger = logging.getLogger("dungeons-and-agents")


class NarratorAgent(BaseGameAgent):
    """Handles storytelling, exploration, and non-combat interactions"""
    
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt('narrator_prompt.yaml'),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=inworld.TTS(voice="Hades"),
            vad=silero.VAD.load()
        )
    
    async def on_enter(self) -> None:
        await super().on_enter()
        userdata = self.session.userdata
        
        # Track if we handled combat ending
        combat_was_just_ended = False
        
        # Check if we're returning from combat
        if userdata.combat_just_ended:
            combat_was_just_ended = True
            # Clear the flag
            userdata.combat_just_ended = False
            
            # Provide narrative flavor about the combat conclusion
            location = userdata.current_location.replace("_", " ")
            if userdata.combat_result:
                # Victory narrative with integrated rewards
                defeated_names = [name for name, _ in userdata.combat_result.get("defeated_enemies", [])]
                
                # Build the complete narrative message
                if len(defeated_names) == 1:
                    victory_message = f"The {defeated_names[0]} lies defeated before you."
                else:
                    victory_message = f"Your enemies lie defeated."
                
                # Add XP information naturally
                xp_gained = userdata.combat_result.get("xp_gained", 0)
                if xp_gained > 0:
                    victory_message += f" You gained {xp_gained} experience"
                    
                    # Add level up if applicable
                    if userdata.combat_result.get("level_up"):
                        victory_message += f" and feel your power growing - {userdata.combat_result['level_up']}"
                    else:
                        victory_message += " from the encounter"
                    
                    victory_message += "."
                
                # Add loot information naturally
                loot = userdata.combat_result.get("loot", [])
                gold_gained = userdata.combat_result.get("gold_gained", 0)
                
                if loot or gold_gained > 0:
                    victory_message += " Among their belongings, you find"
                    
                    items_found = []
                    if gold_gained > 0:
                        items_found.append(f"{gold_gained} gold pieces")
                    
                    # Add items from the loot list (already cleaned by combat agent)
                    items_found.extend(loot)
                    
                    if items_found:
                        if len(items_found) == 1:
                            victory_message += f" {items_found[0]}."
                        elif len(items_found) == 2:
                            victory_message += f" {items_found[0]} and {items_found[1]}."
                        else:
                            victory_message += f" {', '.join(items_found[:-1])}, and {items_found[-1]}."
                    else:
                        victory_message += " nothing of value."
                else:
                    victory_message += " They carried nothing of value."
                
                # Add atmospheric ending
                victory_message += f" The {location} grows quiet once more."
                
                self.session.say(victory_message)
                
                # Clear combat result
                userdata.combat_result = None
            else:
                # Fled or other non-victory ending
                self.session.say(f"You catch your breath, safe for now in the {location}.")
            
            # Add a small delay before continuing
            await asyncio.sleep(1.0)
            
        # Continue with normal entry logic
        if userdata.game_state == "character_creation":
            self.session.say("Welcome to Dungeons and Agents! Let's create your character. What is your name, brave adventurer?")
        elif userdata.game_state == "exploration" and not combat_was_just_ended:
            # Only describe location if not returning from combat
            location_desc = GameUtilities.describe_environment(userdata.current_location)
            self.session.say(location_desc)
    
    @function_tool
    async def say_in_character_voice(self, context: RunContext_T, voice: str, dialogue: str, character_name: str):
        """Say dialogue in a specific character voice for NPCs or other characters
        
        Available voices: Mark, Ashley, Deborah, Olivia, Dennis
        character_name: The name of the character speaking (e.g., "barkeep", "merchant", "goblin")
        """
        # Store the current voice
        original_voice = "Hades"  # Default narrator voice
        
        # Validate voice selection
        available_voices = ["Mark", "Ashley", "Deborah", "Olivia", "Dennis", "Timothy"]
        if voice not in available_voices:
            return f"Voice '{voice}' not available. Choose from: {', '.join(available_voices)}"
        
        # Update voice acting state and emit portrait change
        userdata = context.userdata
        userdata.voice_acting_character = character_name.lower()
        await self.emit_state_update("voice_acting_start", {
            "character_name": character_name.lower(),
            "voice": voice
        })
        
        # Change to the character voice
        self.tts.update_options(voice=voice)
        
        # Say the dialogue
        await self.session.say(dialogue)
        
        # Return to narrator voice
        self.tts.update_options(voice=original_voice)
        
        # Clear voice acting state and emit portrait return
        userdata.voice_acting_character = None
        await self.emit_state_update("voice_acting_end", {})
        
        # Log the voice acting for story context
        userdata.add_story_event(f"{character_name} spoke in {voice}'s voice: '{dialogue}'")
        
        return f"*{character_name} speaks*"
    
    @function_tool
    async def create_character(self, context: RunContext_T, name: str, character_class: str = "warrior"):
        """Create a new player character"""
        userdata = context.userdata
        
        # Map string to enum
        class_map = {
            "warrior": CharacterClass.WARRIOR,
            "mage": CharacterClass.MAGE,
            "rogue": CharacterClass.ROGUE,
            "cleric": CharacterClass.CLERIC
        }
        
        chosen_class = class_map.get(character_class.lower(), CharacterClass.WARRIOR)
        
        # Create character with randomized stats
        stats = CharacterStats(
            strength=random.randint(8, 18),
            dexterity=random.randint(8, 18),
            constitution=random.randint(8, 18),
            intelligence=random.randint(8, 18),
            wisdom=random.randint(8, 18),
            charisma=random.randint(8, 18)
        )
        
        userdata.player_character = PlayerCharacter(
            name=name,
            character_class=chosen_class,
            stats=stats
        )
        
        # Give starting equipment
        starting_gear = {
            CharacterClass.WARRIOR: [
                Item("Vorpal Blade of the Tester", "An overpowered blade", "weapon", {"damage": "3d6+3"}),
                Item("Armor of the Tester", "A magical armor that protects you from all attacks", "armor", {"ac_bonus": 20}),
            ],
            CharacterClass.MAGE: [
                Item("wooden staff", "A focus for magic", "weapon", {"damage": "1d6"}),
                Item("spellbook", "Contains your spells", "misc")
            ],
            CharacterClass.ROGUE: [
                Item("dagger", "Quick and deadly", "weapon", {"damage": "1d4+2"}),
                Item("lockpicks", "For opening things", "misc")
            ],
            CharacterClass.CLERIC: [
                Item("mace", "A holy weapon", "weapon", {"damage": "1d6+1"}),
                Item("holy symbol", "Channel divine power", "misc")
            ]
        }
        
        for item in starting_gear[chosen_class]:
            userdata.player_character.add_item(item)
            # Auto-equip weapons and armor
            if item.item_type in ["weapon", "armor"]:
                userdata.player_character.equip_item(item.name)
        
        # Add universal starting items
        userdata.player_character.add_item(Item("healing potion", "Restores health", "consumable", {"healing": "2d4+2"}, 2))
        userdata.player_character.gold = 50
        
        userdata.game_state = "exploration"
        userdata.add_story_event(f"{name} the {chosen_class.value} begins their adventure")
        
        return f"Character created! {name} the {chosen_class.value} stands ready. Your journey begins in the Stormhaven Tavern. The barkeep nods at you - perhaps you should talk to him about local rumors."
    
    @function_tool
    async def perform_skill_check(self, context: RunContext_T, skill: str, difficulty: str = "medium", context_description: str = ""):
        """Perform a skill check for the player"""
        userdata = context.userdata
        if not userdata.player_character:
            return "You need to create a character first!"
        
        success, roll_total, description, is_critical = SkillCheck.perform_check(
            userdata.player_character,
            skill.lower(),
            difficulty.lower()
        )
        
        userdata.add_story_event(f"Skill check: {description}")
        
        # Return system message about the check result
        dc = SkillCheck.DIFFICULTY_CLASSES.get(difficulty.lower(), 15)
        
        if is_critical == "nat20":
            return f"[SYSTEM: Critical Success! Natural 20! Total: {roll_total} vs DC {dc}. Outstanding success with bonus effects.]"
        elif is_critical == "nat1":
            return f"[SYSTEM: Critical Failure! Natural 1! Total: {roll_total} vs DC {dc}. Catastrophic failure with negative consequences.]"
        elif success:
            margin = roll_total - dc
            if margin >= 10:
                return f"[SYSTEM: Great Success! {roll_total} vs DC {dc}. Exceeded by {margin} points.]"
            elif margin >= 5:
                return f"[SYSTEM: Success! {roll_total} vs DC {dc}. Solid performance.]"
            else:
                return f"[SYSTEM: Narrow Success. {roll_total} vs DC {dc}. Just barely made it.]"
        else:
            margin = dc - roll_total
            if margin >= 10:
                return f"[SYSTEM: Severe Failure. {roll_total} vs DC {dc}. Failed by {margin} points. Major negative consequences.]"
            elif margin >= 5:
                return f"[SYSTEM: Failed. {roll_total} vs DC {dc}. Clear failure with consequences.]"
            else:
                return f"[SYSTEM: Near Miss. {roll_total} vs DC {dc}. Failed by only {margin} points.]"
    
    @function_tool
    async def interact_with_npc(self, context: RunContext_T, npc_name: str, action: str = "talk"):
        """Interact with an NPC"""
        userdata = context.userdata
        if not userdata.player_character:
            return "You need to create a character first!"
        
        # Find or create NPC
        npc = None
        npc_created = False
        for existing_npc in userdata.current_npcs:
            if existing_npc.name.lower() == npc_name.lower():
                npc = existing_npc
                break
        
        if not npc:
            # Create NPC with dynamic generation
            recent_events = userdata.story_context[-3:] if userdata.story_context else []
            npc = await create_npc_by_role(npc_name, userdata.current_location, recent_events)
            userdata.current_npcs.append(npc)
            npc_created = True
        
        if action == "talk":
            # Set active NPC and update game state
            userdata.active_npc = npc
            userdata.game_state = "dialogue"
            logger.info(f"Set active_npc to: {npc.name} (class: {npc.character_class.value})")
            
            charisma_mod = userdata.player_character.stats.get_modifier("charisma")
            reaction = npc.get_reaction(charisma_mod)
            dialogue = npc.get_dialogue("greeting")
            
            # Build the result message
            if npc_created:
                result = f"You see {npc.name}, a {npc.character_class.value}. "
            else:
                result = ""
            
            result += f"You approach {npc.name}. They seem {reaction}. {dialogue}"

            # Add quest hook for friendly NPCs
            if reaction in ["friendly", "very friendly"] and random.random() < 0.5:
                result += " 'Actually, I could use some help with something...'"
            
            # Add inventory hint for merchants
            if npc.merchant and reaction != "unfriendly":
                result += " You notice they have wares for trade."

            userdata.add_story_event(f"Talked to {npc.name} - reaction: {reaction}")
            return result
            
        elif action == "attack":
            # Build attack message
            if npc_created:
                result = f"You spot {npc.name}, a {npc.character_class.value}. You decide to attack!"
            else:
                result = f"You attack {npc.name}!"

            # Initiate combat
            npc.disposition = "hostile"

            # Store the message to say before combat
            self.session.say(result)

            return await self._initiate_combat(context, [npc])

        else:
            return f"You can 'talk' to or 'attack' {npc.name}, but '{action}' isn't a valid action."
    
    @function_tool
    async def end_dialogue(self, context: RunContext_T):
        """End dialogue with current NPC and return to exploration"""
        userdata = context.userdata
        if userdata.active_npc:
            npc_name = userdata.active_npc.name
            userdata.active_npc = None
            userdata.game_state = "exploration"
            
            return f"You bid farewell to {npc_name} and step back."
        else:
            return "You're not talking to anyone right now."
    
    @function_tool
    async def explore_area(self, context: RunContext_T, direction: str = "forward"):
        """Explore in a direction"""
        userdata = context.userdata
        if not userdata.player_character:
            return "You need to create a character first!"
        
        # Clear active NPC when exploring
        if userdata.active_npc:
            userdata.active_npc = None
        
        userdata.game_state = "exploration"
        
        # Simple location system - this could be enhanced with dynamic generation
        locations = {
            "tavern": {"north": "market", "east": "dungeon_entrance"},
            "market": {"south": "tavern", "north": "castle_gates"},
            "dungeon_entrance": {"west": "tavern", "down": "dungeon_level_1"},
            "dungeon_level_1": {"up": "dungeon_entrance"},
            "castle_gates": {"south": "market"}
        }
        
        current_loc = userdata.current_location
        connections = locations.get(current_loc, {})
        
        # Map general directions to specific ones
        direction_map = {
            "forward": "north",
            "back": "south",
            "left": "west", 
            "right": "east"
        }
        specific_direction = direction_map.get(direction.lower(), direction.lower())
        
        if specific_direction in connections:
            new_location = connections[specific_direction]
            userdata.current_location = new_location
            userdata.visited_locations.append(new_location)
            
            # Clear NPCs from previous location
            userdata.current_npcs = []
            
            # Chance of random encounter
            if "dungeon" in new_location and random.random() < 0.4:
                # Create enemies
                enemy_count = random.randint(1, 3)
                enemies = []
                for i in range(enemy_count):
                    from character import create_random_npc
                    enemy = create_random_npc(
                        name=f"Goblin {i+1}",
                        character_class=CharacterClass.WARRIOR,
                        level=1,
                        disposition="hostile"
                    )
                    enemies.append(enemy)
                
                userdata.current_npcs.extend(enemies)
                return await self._initiate_combat(context, enemies)
            
            location_desc = GameUtilities.describe_environment(new_location.split("_")[0])
            return f"You travel {specific_direction} to {new_location.replace('_', ' ')}. {location_desc}"
        else:
            return f"You cannot go {direction} from here. Available directions: {', '.join(connections.keys()) if connections else 'none'}"
    
    async def _initiate_combat(self, context: RunContext_T, enemies: List[NPCCharacter]):
        """Initiate combat and switch to combat agent"""
        userdata = context.userdata
        
        # Initialize combat
        userdata.combat_state = Combat.initialize_combat(userdata.player_character, enemies)
        userdata.game_state = "combat"
        userdata.current_agent_type = "combat"
        
        # Create combat description
        enemy_names = [e.name for e in enemies]
        if len(enemies) == 1:
            combat_start = f"Combat begins! You face {enemy_names[0]}!"
        else:
            combat_start = f"Combat begins! You face {', '.join(enemy_names[:-1])} and {enemy_names[-1]}!"
        
        userdata.add_story_event(combat_start)
        
        # Store current agent for context preservation
        userdata.prev_agent = self
        
        # Import here to avoid circular import
        from agents.combat_agent import CombatAgent
        return CombatAgent()
    
    @function_tool
    async def check_inventory(self, context: RunContext_T):
        """Check player's inventory"""
        userdata = context.userdata
        if not userdata.player_character:
            return "You need to create a character first!"
        
        pc = userdata.player_character
        inventory_desc = f"You have {pc.gold} gold pieces."
        
        if pc.equipped_weapon:
            inventory_desc += f" Wielding: {pc.equipped_weapon.name}."
        if pc.equipped_armor:
            inventory_desc += f" Wearing: {pc.equipped_armor.name}."
        
        if pc.inventory:
            items = []
            for item in pc.inventory:
                if item.quantity > 1:
                    items.append(f"{item.name} ({item.quantity})")
                else:
                    items.append(item.name)
            inventory_desc += f" In your pack: {', '.join(items)}."
        else:
            inventory_desc += " Your pack is empty."
        
        return inventory_desc
    
    @function_tool
    async def use_item(self, context: RunContext_T, item_name: str):
        """Use an item from inventory"""
        userdata = context.userdata
        if not userdata.player_character:
            return "You need to create a character first!"
        
        pc = userdata.player_character
        
        # Find item
        item = None
        for inv_item in pc.inventory:
            if inv_item.name.lower() == item_name.lower():
                item = inv_item
                break
        
        if not item:
            return f"You don't have a {item_name}."
        
        # Use item based on type
        if item.item_type == "consumable":
            if "healing" in item.properties:
                healing_roll, breakdown = DiceRoller.roll(item.properties["healing"])
                actual_healing = pc.heal(healing_roll)
                pc.remove_item(item.name)
                return f"You drink the {item.name}. {breakdown} - You heal {actual_healing} hit points! ({pc.current_health}/{pc.max_health} HP)"
        elif item.item_type in ["weapon", "armor"]:
            return pc.equip_item(item.name)
        else:
            return f"You examine the {item.name}. {item.description}"
    
    @function_tool
    async def start_combat(self, context: RunContext_T, enemy_type: str = "goblin", enemy_count: int = 1):
        """Start a combat encounter with specified enemies"""
        userdata = context.userdata
        if not userdata.player_character:
            return "You need to create a character first!"
        
        if userdata.game_state == "combat":
            return "You're already in combat!"
        
        # Create enemies based on type
        enemies = []
        enemy_configs = {
            "goblin": (CharacterClass.WARRIOR, 1, "hostile", "Don't underestimate them!"),
            "orc": (CharacterClass.WARRIOR, 2, "hostile", "Large and brutal"),
            "bandit": (CharacterClass.ROGUE, 2, "hostile", "Quick and cunning"),
            "skeleton": (CharacterClass.WARRIOR, 1, "hostile", "Undead warrior"),
            "dark_mage": (CharacterClass.MAGE, 3, "hostile", "Wielder of dark magic"),
            "wolf": (CharacterClass.ROGUE, 1, "hostile", "Savage beast")
        }
        
        config = enemy_configs.get(enemy_type.lower(), enemy_configs["goblin"])
        char_class, level, disposition, description = config
        
        for i in range(min(enemy_count, 5)):  # Cap at 5 enemies
            enemy_name = f"{enemy_type.capitalize()}" if enemy_count == 1 else f"{enemy_type.capitalize()} {i+1}"
            from character import create_random_npc
            enemy = create_random_npc(
                name=enemy_name,
                character_class=char_class,
                level=level,
                disposition=disposition
            )
            enemies.append(enemy)
        
        userdata.current_npcs.extend(enemies)
        
        # Narrative description
        if enemy_count == 1:
            encounter_desc = f"A {enemy_type} appears before you! {description}."
        else:
            encounter_desc = f"{enemy_count} {enemy_type}s appear before you! {description}."
        
        self.session.say(encounter_desc)
        
        # Initiate combat
        return await self._initiate_combat(context, enemies)
    
    @function_tool
    async def trade_with_npc(self, context: RunContext_T, npc_name: str, offer_item: str = "", offer_gold: int = 0, request_item: str = "", request_gold: int = 0):
        """Propose a trade with an NPC - offer items or gold in exchange for their items or gold"""
        userdata = context.userdata
        if not userdata.player_character:
            return "You need to create a character first!"
        
        pc = userdata.player_character
        
        # Find the NPC
        npc = None
        for existing_npc in userdata.current_npcs:
            if existing_npc.name.lower() == npc_name.lower():
                npc = existing_npc
                break
        
        if not npc:
            return f"There's no one named {npc_name} here."
        
        if npc.disposition == "hostile":
            return f"{npc.name} is too hostile to trade with you!"
        
        # Check what player is offering
        if offer_item and offer_item.strip():
            # Check if player has the item
            has_item = False
            for item in pc.inventory:
                if item.name.lower() == offer_item.lower():
                    has_item = True
                    break
            if not has_item:
                return f"You don't have a {offer_item} to offer."
        
        if offer_gold > 0 and pc.gold < offer_gold:
            return f"You don't have {offer_gold} gold to offer. You only have {pc.gold} gold."
        
        # Check what player is requesting
        if request_item and request_item.strip():
            # Check if NPC has the item
            npc_item = None
            for item in npc.inventory:
                if item.name.lower() == request_item.lower():
                    npc_item = item
                    break
            if not npc_item:
                return f"{npc.name} doesn't have a {request_item} to trade."
        
        if request_gold > 0 and npc.gold < request_gold:
            return f"{npc.name} doesn't have {request_gold} gold. They only have {npc.gold} gold."
        
        # Evaluate the trade (simple valuation system)
        offer_value = offer_gold
        request_value = request_gold
        
        # Simple item valuation
        item_values = {
            "weapon": 50,
            "armor": 75,
            "consumable": 20,
            "misc": 10
        }
        
        if offer_item and offer_item.strip():
            for item in pc.inventory:
                if item.name.lower() == offer_item.lower():
                    offer_value += item_values.get(item.item_type, 25)
                    break
        
        if request_item and request_item.strip():
            for item in npc.inventory:
                if item.name.lower() == request_item.lower():
                    request_value += item_values.get(item.item_type, 25)
                    break
        
        # NPC decision based on charisma and trade value
        charisma_mod = pc.stats.get_modifier("charisma")
        
        # Difficulty based on trade fairness
        if offer_value >= request_value * 1.5:
            dc = 5  # Very favorable to NPC
        elif offer_value >= request_value:
            dc = 10  # Fair trade
        elif offer_value >= request_value * 0.75:
            dc = 15  # Slightly unfavorable
        else:
            dc = 20  # Very unfavorable
        
        # Check if any trade is being proposed
        if offer_value == 0 and request_value == 0:
            return "You need to offer or request something to make a trade!"
        
        # Print trade evaluation
        print(f"\n{Colors.CYAN}{'$' * 40}{Colors.ENDC}")
        print(f"{Colors.BOLD}💰 TRADE NEGOTIATION{Colors.ENDC}")
        print(f"{Colors.BOLD}   Your offer: ", end="")
        if offer_item and offer_item.strip():
            print(f"{offer_item}", end="")
        if offer_gold > 0:
            print(f"{' + ' if (offer_item and offer_item.strip()) else ''}{offer_gold} gold", end="")
        print(f" (value: ~{offer_value})")
        
        print(f"{Colors.BOLD}   Requesting: ", end="")
        if request_item and request_item.strip():
            print(f"{request_item}", end="")
        if request_gold > 0:
            print(f"{' + ' if (request_item and request_item.strip()) else ''}{request_gold} gold", end="")
        print(f" (value: ~{request_value})")
        
        print(f"{Colors.BOLD}   Trade DC: {dc}{Colors.ENDC}")
        print(f"{Colors.CYAN}{'$' * 40}{Colors.ENDC}")
        
        # Make the check
        roll_total, roll_description, _ = DiceRoller.roll_d20(charisma_mod)
        
        if roll_total >= dc:
            # Execute the trade
            # Remove from player
            if offer_item and offer_item.strip():
                pc.remove_item(offer_item)
            if offer_gold > 0:
                pc.gold -= offer_gold
            
            # Remove from NPC and add to player
            if request_item and request_item.strip():
                for item in npc.inventory[:]:
                    if item.name.lower() == request_item.lower():
                        npc.inventory.remove(item)
                        pc.add_item(item)
                        break
            if request_gold > 0:
                npc.gold -= request_gold
                pc.gold += request_gold
            
            # Add to NPC what was offered
            if offer_item and offer_item.strip():
                for item in pc.inventory:
                    if item.name.lower() == offer_item.lower():
                        npc.inventory.append(item)
                        break
            if offer_gold > 0:
                npc.gold += offer_gold
            
            return f"{npc.name} accepts your trade! 'A fair exchange, traveler.'"
        else:
            refusals = [
                f"{npc.name} shakes their head. 'That's not a fair trade.'",
                f"{npc.name} frowns. 'You'll need to offer more than that.'",
                f"{npc.name} laughs. 'Surely you jest! That's not nearly enough.'"
            ]
            return random.choice(refusals)
    
    @function_tool
    async def check_npc_inventory(self, context: RunContext_T, npc_name: str):
        """Check what an NPC has for trade"""
        userdata = context.userdata
        if not userdata.player_character:
            return "You need to create a character first!"
        
        # Find or create the NPC
        npc = None
        npc_created = False
        for existing_npc in userdata.current_npcs:
            if existing_npc.name.lower() == npc_name.lower():
                npc = existing_npc
                break
        
        if not npc:
            # Create NPC with dynamic inventory
            recent_events = userdata.story_context[-3:] if userdata.story_context else []
            npc = await create_npc_by_role(npc_name, userdata.current_location, recent_events)
            userdata.current_npcs.append(npc)
            npc_created = True
        
        if npc.disposition == "hostile":
            return f"{npc.name} is too hostile to show you their wares!"
        
        # Build inventory description
        result = ""
        if npc_created:
            result = f"You find {npc.name}, a {npc.character_class.value}. "
        
        result += f"{npc.name} has {npc.gold} gold"
        
        if npc.inventory:
            items = []
            for item in npc.inventory:
                if item.quantity > 1:
                    items.append(f"{item.name} ({item.quantity})")
                else:
                    items.append(item.name)
            result += f" and carries: {', '.join(items)}."
        else:
            result += " but carries no items."
        
        if npc.merchant:
            result += " They seem eager to trade."
        elif npc.disposition == "friendly":
            result += " They might be willing to trade."
        
        return result