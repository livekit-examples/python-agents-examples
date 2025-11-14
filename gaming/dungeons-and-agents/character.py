from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import random


class CharacterClass(Enum):
    WARRIOR = "warrior"
    MAGE = "mage"
    ROGUE = "rogue"
    CLERIC = "cleric"


@dataclass
class CharacterStats:
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    def get_modifier(self, stat: str) -> int:
        """Calculate D&D-style ability modifier"""
        value = getattr(self, stat, 10)
        return (value - 10) // 2


@dataclass
class Item:
    name: str
    description: str
    item_type: str  # weapon, armor, consumable, misc
    properties: Dict[str, any] = field(default_factory=dict)
    quantity: int = 1


@dataclass
class Character:
    """Base character class for both players and NPCs"""
    name: str
    character_class: CharacterClass
    level: int = 1
    stats: CharacterStats = field(default_factory=CharacterStats)
    max_health: int = 10
    current_health: int = 10
    armor_class: int = 10
    
    # Combat stats
    initiative_bonus: int = 0
    attack_bonus: int = 0
    damage_dice: str = "1d6"  # e.g., "1d6", "2d8+2"
    
    def __post_init__(self):
        # Calculate derived stats
        self.initiative_bonus = self.stats.get_modifier("dexterity")
        
        # Base values before equipment
        self.base_armor_class = 10 + self.stats.get_modifier("dexterity")
        self.base_damage_dice = "1d4"  # Unarmed strike
        
        # Set initial AC and damage (will be overridden by equipment for players)
        self.armor_class = self.base_armor_class
        self.damage_dice = self.base_damage_dice
        
        # Set class-based stats
        if self.character_class == CharacterClass.WARRIOR:
            self.max_health = 10 + self.stats.get_modifier("constitution")
            self.attack_bonus = 2 + self.stats.get_modifier("strength")
            self.base_damage_dice = "1d6"  # Better unarmed for warriors
        elif self.character_class == CharacterClass.MAGE:
            self.max_health = 6 + self.stats.get_modifier("constitution")
            self.attack_bonus = self.stats.get_modifier("intelligence")
            self.base_damage_dice = "1d4"
        elif self.character_class == CharacterClass.ROGUE:
            self.max_health = 8 + self.stats.get_modifier("constitution")
            self.attack_bonus = 2 + self.stats.get_modifier("dexterity")
            self.base_damage_dice = "1d4"
        elif self.character_class == CharacterClass.CLERIC:
            self.max_health = 8 + self.stats.get_modifier("constitution")
            self.attack_bonus = 1 + self.stats.get_modifier("wisdom")
            self.base_damage_dice = "1d4"
        
        # Update damage dice to base value
        self.damage_dice = self.base_damage_dice
        self.current_health = self.max_health

    def take_damage(self, damage: int) -> Tuple[int, bool]:
        """Apply damage and return (actual damage taken, is_dead)"""
        actual_damage = min(damage, self.current_health)
        self.current_health -= actual_damage
        is_dead = self.current_health <= 0
        return actual_damage, is_dead

    def heal(self, amount: int) -> int:
        """Heal character and return actual amount healed"""
        actual_heal = min(amount, self.max_health - self.current_health)
        self.current_health += actual_heal
        return actual_heal

    def get_status_description(self) -> str:
        """Get a narrative description of character's current status"""
        health_percent = (self.current_health / self.max_health) * 100
        
        if health_percent >= 100:
            health_desc = "in perfect health"
        elif health_percent >= 75:
            health_desc = "lightly wounded"
        elif health_percent >= 50:
            health_desc = "moderately wounded"
        elif health_percent >= 25:
            health_desc = "severely wounded"
        else:
            health_desc = "near death"
        
        status = f"{self.name} is {health_desc} ({self.current_health}/{self.max_health} HP)"
        
        return status


@dataclass
class PlayerCharacter(Character):
    """Extended character class for players with inventory and progression"""
    experience: int = 0
    inventory: List[Item] = field(default_factory=list)
    equipped_weapon: Optional[Item] = None
    equipped_armor: Optional[Item] = None
    gold: int = 0
    
    def __post_init__(self):
        super().__post_init__()
        # Update stats based on starting equipment
        self.update_equipment_stats()
    
    def update_equipment_stats(self):
        """Update AC and damage based on equipped items"""
        # Reset to base values
        self.armor_class = self.base_armor_class
        self.damage_dice = self.base_damage_dice
        
        # Apply armor bonuses
        if self.equipped_armor:
            if "armor_class" in self.equipped_armor.properties:
                # Armor provides flat AC
                self.armor_class = self.equipped_armor.properties["armor_class"]
                # Add dexterity modifier if light armor
                if self.equipped_armor.properties.get("armor_type", "light") == "light":
                    self.armor_class += self.stats.get_modifier("dexterity")
            elif "ac_bonus" in self.equipped_armor.properties:
                # Armor provides bonus to base AC
                self.armor_class = self.base_armor_class + self.equipped_armor.properties["ac_bonus"]
        
        # Apply weapon damage
        if self.equipped_weapon:
            if "damage" in self.equipped_weapon.properties:
                self.damage_dice = self.equipped_weapon.properties["damage"]

    def add_item(self, item: Item):
        """Add item to inventory"""
        # Check if item already exists and stack if possible
        for inv_item in self.inventory:
            if inv_item.name == item.name and inv_item.item_type in ["consumable", "misc"]:
                inv_item.quantity += item.quantity
                return
        self.inventory.append(item)

    def remove_item(self, item_name: str, quantity: int = 1) -> bool:
        """Remove item from inventory"""
        for item in self.inventory:
            if item.name == item_name:
                if item.quantity >= quantity:
                    item.quantity -= quantity
                    if item.quantity == 0:
                        self.inventory.remove(item)
                    return True
        return False

    def equip_item(self, item_name: str) -> str:
        """Equip a weapon or armor"""
        for item in self.inventory:
            if item.name.lower() == item_name.lower():
                if item.item_type == "weapon":
                    if self.equipped_weapon:
                        self.inventory.append(self.equipped_weapon)
                    self.equipped_weapon = item
                    self.inventory.remove(item)
                    # Update all equipment-based stats
                    self.update_equipment_stats()
                    return f"Equipped {item_name} as weapon (damage: {self.damage_dice})"
                elif item.item_type == "armor":
                    if self.equipped_armor:
                        self.inventory.append(self.equipped_armor)
                    self.equipped_armor = item
                    self.inventory.remove(item)
                    # Update all equipment-based stats
                    self.update_equipment_stats()
                    return f"Equipped {item_name} as armor (AC: {self.armor_class})"
        return f"Cannot equip {item_name} - not found in inventory"

    def gain_experience(self, xp: int) -> Optional[str]:
        """Add experience and check for level up"""
        self.experience += xp
        xp_needed = self.level * 1000  # Simple progression
        
        if self.experience >= xp_needed:
            self.level += 1
            self.experience -= xp_needed
            
            # Level up benefits
            health_gain = random.randint(1, 8) + self.stats.get_modifier("constitution")
            self.max_health += health_gain
            self.current_health += health_gain
            
            # Improve a random stat
            stat_names = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
            stat_to_improve = random.choice(stat_names)
            current_value = getattr(self.stats, stat_to_improve)
            setattr(self.stats, stat_to_improve, current_value + 1)
            
            return f"Level up! Now level {self.level}. {stat_to_improve.capitalize()} increased!"
        return None


@dataclass  
class NPCCharacter(Character):
    """Extended character class for NPCs with behavior and dialogue"""
    disposition: str = "neutral"  # friendly, neutral, hostile
    dialogue_options: List[str] = field(default_factory=list)
    merchant: bool = False
    
    # NPC inventory and wealth
    inventory: List[Item] = field(default_factory=list)
    gold: int = 0
    
    def get_reaction(self, player_charisma_modifier: int = 0) -> str:
        """Determine NPC's reaction to player"""
        reaction_roll = random.randint(1, 20) + player_charisma_modifier
        
        if self.disposition == "hostile":
            reaction_roll -= 5
        elif self.disposition == "friendly":
            reaction_roll += 5
            
        if reaction_roll >= 15:
            return "very friendly"
        elif reaction_roll >= 10:
            return "friendly"
        elif reaction_roll >= 5:
            return "neutral"
        else:
            return "unfriendly"

    def get_dialogue(self, context: str = "greeting") -> str:
        """Get appropriate dialogue based on context"""
        if context == "greeting" and self.dialogue_options:
            return random.choice(self.dialogue_options)
        elif context == "combat" and self.disposition == "hostile":
            combat_phrases = [
                f"{self.name} shouts: 'You'll regret this!'",
                f"{self.name} growls: 'Prepare to meet your doom!'",
                f"{self.name} sneers: 'Another fool to crush!'"
            ]
            return random.choice(combat_phrases)
        else:
            return f"{self.name} remains silent."


def create_random_npc(name: str, character_class: CharacterClass, level: int = 1, disposition: str = "neutral") -> NPCCharacter:
    """Factory function to create a random NPC"""
    # Generate random stats
    stats = CharacterStats(
        strength=random.randint(8, 16),
        dexterity=random.randint(8, 16),
        constitution=random.randint(8, 16),
        intelligence=random.randint(8, 16),
        wisdom=random.randint(8, 16),
        charisma=random.randint(8, 16)
    )
    
    npc = NPCCharacter(
        name=name,
        character_class=character_class,
        level=level,
        stats=stats,
        disposition=disposition
    )
    
    # Give NPCs some gold based on level
    npc.gold = random.randint(10, 30) * level
    
    # Give NPCs random items based on class and level
    if character_class == CharacterClass.WARRIOR:
        if random.random() < 0.5:
            npc.inventory.append(Item("rusty sword", "An old but serviceable blade", "weapon", {"damage": "1d6"}))
        if random.random() < 0.3:
            npc.inventory.append(Item("leather armor", "Basic protection", "armor", {"ac_bonus": 1}))
    elif character_class == CharacterClass.MAGE:
        if random.random() < 0.4:
            npc.inventory.append(Item("mana potion", "Restores magical energy", "consumable", {"mana": "2d4"}))
        if random.random() < 0.2:
            npc.inventory.append(Item("scroll of firebolt", "A magical scroll", "misc"))
    elif character_class == CharacterClass.ROGUE:
        if random.random() < 0.5:
            npc.inventory.append(Item("dagger", "Quick and sharp", "weapon", {"damage": "1d4"}))
        if random.random() < 0.3:
            npc.inventory.append(Item("lockpicks", "For opening things", "misc"))
    elif character_class == CharacterClass.CLERIC:
        if random.random() < 0.6:
            npc.inventory.append(Item("healing potion", "Restores health", "consumable", {"healing": "2d4+2"}))
    
    # All NPCs have a chance for random items
    if random.random() < 0.3:
        npc.inventory.append(Item("bread", "A loaf of bread", "consumable", {"healing": "1d4"}))
    if random.random() < 0.2:
        npc.inventory.append(Item("torch", "Provides light", "misc"))
    
    # Add some random dialogue
    if disposition == "friendly":
        npc.dialogue_options = [
            f"Greetings, traveler! I am {name}.",
            "What brings you to these parts?",
            "May the storms guide your path!",
            "Perhaps we could trade?"
        ]
    elif disposition == "hostile":
        npc.dialogue_options = [
            f"You dare approach {name}?",
            "Leave now, or face the consequences!",
            "Your presence offends me!"
        ]
    else:
        npc.dialogue_options = [
            f"Yes? I am {name}.",
            "What do you want?",
            "I have little time for conversation.",
            "Are you looking to trade?"
        ]
    
    # Set merchant flag for friendly NPCs with items
    if disposition == "friendly" and npc.inventory:
        npc.merchant = random.random() < 0.5
    
    return npc