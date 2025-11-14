import random
import re
from typing import Tuple, List, Optional, Dict, NamedTuple
from dataclasses import dataclass, field
from queue import Queue

from character import Character, PlayerCharacter, NPCCharacter, CharacterClass


from utils.display import Colors


class CombatAction(NamedTuple):
    """Represents a combat action to be narrated"""
    message: str
    delay: float = 0.0  # Optional delay before speaking
    priority: int = 0  # Higher priority actions go first (if needed)


@dataclass
class CombatState:
    """Tracks the state of an ongoing combat encounter"""
    participants: List[Character] = field(default_factory=list)
    initiative_order: List[Character] = field(default_factory=list)
    defeated_enemies: List[Character] = field(default_factory=list)  # Track defeated enemies for XP/loot
    current_turn_index: int = 0
    round_number: int = 1
    combat_log: List[str] = field(default_factory=list)
    is_complete: bool = False
    action_queue: Queue[CombatAction] = field(default_factory=Queue)
    
    def get_current_character(self) -> Optional[Character]:
        """Get the character whose turn it is"""
        if self.initiative_order and not self.is_complete:
            return self.initiative_order[self.current_turn_index]
        return None
    
    def next_turn(self):
        """Advance to the next turn"""
        self.current_turn_index += 1
        if self.current_turn_index >= len(self.initiative_order):
            self.current_turn_index = 0
            self.round_number += 1
            self.combat_log.append(f"\n--- Round {self.round_number} ---")
    
    def remove_defeated(self, character: Character):
        """Remove a defeated character from combat"""
        # Remove from participants list as well
        if character in self.participants:
            self.participants.remove(character)
            
        if character in self.initiative_order:
            # Adjust current turn index if needed
            char_index = self.initiative_order.index(character)
            if char_index < self.current_turn_index:
                self.current_turn_index -= 1
            elif char_index == self.current_turn_index and self.current_turn_index > 0:
                self.current_turn_index -= 1
            
            self.initiative_order.remove(character)
            
            # Check if combat is over
            player_alive = any(isinstance(c, PlayerCharacter) for c in self.initiative_order)
            enemies_alive = any(isinstance(c, NPCCharacter) for c in self.initiative_order)
            
            if not player_alive or not enemies_alive:
                self.is_complete = True


class DiceRoller:
    """Handles all dice rolling mechanics"""
    
    @staticmethod
    def roll(dice_string: str) -> Tuple[int, str]:
        """
        Roll dice based on a dice string (e.g., "1d20", "2d6+3", "1d8-1")
        Returns (total, breakdown)
        """
        # Parse dice string
        match = re.match(r'(\d+)d(\d+)([\+\-]\d+)?', dice_string)
        if not match:
            return 0, "Invalid dice string"
        
        num_dice = int(match.group(1))
        die_size = int(match.group(2))
        modifier = 0
        
        if match.group(3):
            modifier = int(match.group(3))
        
        # Roll the dice
        rolls = [random.randint(1, die_size) for _ in range(num_dice)]
        total = sum(rolls) + modifier
        
        # Create breakdown string
        breakdown = f"{num_dice}d{die_size}: {rolls}"
        if modifier != 0:
            breakdown += f" {'+' if modifier > 0 else ''}{modifier}"
        breakdown += f" = {total}"
        
        # Print stylized output to console
        print(f"\n{Colors.CYAN}{'═' * 40}{Colors.ENDC}")
        print(f"{Colors.YELLOW}🎲 DICE ROLL: {dice_string}{Colors.ENDC}")
        print(f"{Colors.BOLD}   Rolls: {rolls}{Colors.ENDC}")
        if modifier != 0:
            print(f"{Colors.BOLD}   Modifier: {'+' if modifier > 0 else ''}{modifier}{Colors.ENDC}")
        print(f"{Colors.GREEN if total >= 15 else Colors.YELLOW if total >= 10 else Colors.RED}   ➤ Total: {total}{Colors.ENDC}")
        print(f"{Colors.CYAN}{'═' * 40}{Colors.ENDC}\n")
        
        return total, breakdown
    
    @staticmethod
    def roll_d20(modifier: int = 0, advantage: bool = False, disadvantage: bool = False) -> Tuple[int, str, bool]:
        """
        Roll a d20 with modifier and advantage/disadvantage
        Returns (total, breakdown, is_nat_20)
        """
        if advantage or disadvantage:
            roll1 = random.randint(1, 20)
            roll2 = random.randint(1, 20)
            
            if advantage:
                base_roll = max(roll1, roll2)
                breakdown = f"d20 with advantage: [{roll1}, {roll2}] → {base_roll}"
            else:
                base_roll = min(roll1, roll2)
                breakdown = f"d20 with disadvantage: [{roll1}, {roll2}] → {base_roll}"
        else:
            base_roll = random.randint(1, 20)
            breakdown = f"d20: {base_roll}"
        
        total = base_roll + modifier
        
        if modifier != 0:
            breakdown += f" {'+' if modifier > 0 else ''}{modifier} = {total}"
        
        is_nat_20 = base_roll == 20
        is_nat_1 = base_roll == 1
        
        # Print stylized d20 roll
        print(f"\n{Colors.BLUE}{'▬' * 40}{Colors.ENDC}")
        print(f"{Colors.HEADER}⚔️  D20 ROLL{Colors.ENDC}")
        
        if advantage or disadvantage:
            print(f"{Colors.BOLD}   Type: {'Advantage' if advantage else 'Disadvantage'}{Colors.ENDC}")
            print(f"{Colors.BOLD}   Rolls: [{roll1}, {roll2}] → {base_roll}{Colors.ENDC}")
        else:
            print(f"{Colors.BOLD}   Roll: {base_roll}{Colors.ENDC}")
        
        if is_nat_20:
            print(f"{Colors.GREEN}{Colors.BOLD}   ★ NATURAL 20! ★{Colors.ENDC}")
        elif is_nat_1:
            print(f"{Colors.RED}{Colors.BOLD}   ☠ NATURAL 1! ☠{Colors.ENDC}")
        
        if modifier != 0:
            print(f"{Colors.BOLD}   Modifier: {'+' if modifier > 0 else ''}{modifier}{Colors.ENDC}")
        
        color = Colors.GREEN if total >= 15 else Colors.YELLOW if total >= 10 else Colors.RED
        print(f"{color}   ➤ Total: {total}{Colors.ENDC}")
        print(f"{Colors.BLUE}{'▬' * 40}{Colors.ENDC}\n")
        
        return total, breakdown, is_nat_20
    
    @staticmethod
    def roll_initiative(character: Character) -> Tuple[int, str]:
        """Roll initiative for a character"""
        roll, breakdown = DiceRoller.roll("1d20")
        total = roll + character.initiative_bonus
        
        if character.initiative_bonus != 0:
            breakdown = f"Initiative: {roll} {'+' if character.initiative_bonus > 0 else ''}{character.initiative_bonus} = {total}"
        else:
            breakdown = f"Initiative: {total}"
            
        return total, breakdown


class SkillCheck:
    """Handles skill checks and ability checks"""
    
    DIFFICULTY_CLASSES = {
        "very_easy": 5,
        "easy": 10,
        "medium": 15,
        "hard": 20,
        "very_hard": 25,
        "nearly_impossible": 30
    }
    
    @staticmethod
    def perform_check(character: Character, skill: str, difficulty: str = "medium") -> Tuple[bool, int, str, str]:
        """
        Perform a skill check
        Returns (success, roll_total, description, critical_status)
        """
        dc = SkillCheck.DIFFICULTY_CLASSES.get(difficulty, 15)
        
        # Determine ability modifier based on skill
        ability_map = {
            # Strength-based skills
            "strength": "strength",
            "athletics": "strength",
            "intimidation": "strength",

            # Dexterity-based skills
            "dexterity": "dexterity",
            "stealth": "dexterity",
            "acrobatics": "dexterity",
            "sleight_of_hand": "dexterity",
            "lockpicking": "dexterity",
            "archery": "dexterity",

            # Intelligence-based skills
            "intelligence": "intelligence",
            "investigation": "intelligence",
            "arcana": "intelligence",
            "history": "intelligence",
            "nature": "intelligence",
            "religion": "intelligence",
            "medicine": "intelligence",
            "engineering": "intelligence",

            # Wisdom-based skills
            "wisdom": "wisdom",
            "perception": "wisdom",
            "insight": "wisdom",
            "survival": "wisdom",
            "animal_handling": "wisdom",
            "medicine_practical": "wisdom",

            # Charisma-based skills
            "charisma": "charisma",
            "persuasion": "charisma",
            "deception": "charisma",
            "performance": "charisma",
            "intimidation_social": "charisma",
            "leadership": "charisma"
        }
        
        ability = ability_map.get(skill, "wisdom")
        modifier = character.stats.get_modifier(ability)
        
        # Add skill proficiency if character has it
        if hasattr(character, 'skills') and skill in character.skills:
            modifier += character.skills[skill]
        
        # Print skill check header
        print(f"\n{Colors.HEADER}{'━' * 40}{Colors.ENDC}")
        print(f"{Colors.BOLD}📜 SKILL CHECK: {skill.upper()}{Colors.ENDC}")
        print(f"{Colors.BOLD}   Character: {character.name}{Colors.ENDC}")
        print(f"{Colors.BOLD}   Ability: {ability.capitalize()} (modifier: {'+' if modifier >= 0 else ''}{modifier}){Colors.ENDC}")
        print(f"{Colors.BOLD}   Difficulty: {difficulty.capitalize()} (DC {dc}){Colors.ENDC}")
        print(f"{Colors.HEADER}{'━' * 40}{Colors.ENDC}")
        
        roll_total, breakdown, is_nat20 = DiceRoller.roll_d20(modifier)
        
        # Check for natural 1
        base_roll = int(breakdown.split(':')[1].split()[0]) if ':' in breakdown else roll_total - modifier
        is_nat1 = base_roll == 1
        
        # Determine critical status
        critical_status = "nat20" if is_nat20 else "nat1" if is_nat1 else "normal"
        
        # Success is automatic on nat 20, failure on nat 1
        if is_nat20:
            success = True
        elif is_nat1:
            success = False
        else:
            success = roll_total >= dc
        
        # Print result
        print(f"\n{Colors.BOLD}   Result: {Colors.ENDC}", end="")
        if success:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ SUCCESS!{Colors.ENDC}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ FAILURE!{Colors.ENDC}")
        print(f"{Colors.HEADER}{'━' * 40}{Colors.ENDC}\n")
        
        description = f"{character.name} rolls {skill.capitalize()}: {breakdown} vs DC {dc} - {'Success!' if success else 'Failure!'}"
        
        return success, roll_total, description, critical_status


class Combat:
    """Handles combat mechanics"""
    
    @staticmethod
    def initialize_combat(player: PlayerCharacter, enemies: List[NPCCharacter]) -> CombatState:
        """Initialize a new combat encounter"""
        combat_state = CombatState()
        
        # Add all participants
        combat_state.participants = [player] + enemies
        
        # Print combat start
        print(f"\n{Colors.RED}{Colors.BOLD}{'🔥' * 20}{Colors.ENDC}")
        print(f"{Colors.RED}{Colors.BOLD}         ⚔️  COMBAT BEGINS! ⚔️{Colors.ENDC}")
        print(f"{Colors.RED}{Colors.BOLD}{'🔥' * 20}{Colors.ENDC}\n")
        
        # Roll initiative for everyone
        initiative_rolls = []
        combat_state.combat_log.append("=== COMBAT BEGINS ===")
        combat_state.combat_log.append("\nInitiative rolls:")
        
        print(f"{Colors.YELLOW}{Colors.BOLD}Rolling Initiative...{Colors.ENDC}")
        for character in combat_state.participants:
            initiative, breakdown = DiceRoller.roll_initiative(character)
            initiative_rolls.append((initiative, character))
            combat_state.combat_log.append(f"  {character.name}: {breakdown}")
        
        # Sort by initiative (highest first)
        initiative_rolls.sort(key=lambda x: x[0], reverse=True)
        combat_state.initiative_order = [char for _, char in initiative_rolls]
        
        # Print initiative order
        print(f"\n{Colors.CYAN}{Colors.BOLD}Initiative Order:{Colors.ENDC}")
        for i, (init_value, char) in enumerate(initiative_rolls):
            print(f"  {i+1}. {Colors.BOLD}{char.name}{Colors.ENDC} (Initiative: {init_value})")
        print()
        
        combat_state.combat_log.append(f"\nInitiative order: {', '.join(c.name for c in combat_state.initiative_order)}")
        combat_state.combat_log.append(f"\n--- Round 1 ---")
        
        return combat_state
    
    @staticmethod
    def perform_attack(attacker: Character, defender: Character) -> Tuple[bool, int, str]:
        """
        Perform an attack
        Returns (hit, damage, description)
        """
        # Print attack header
        print(f"\n{Colors.RED}{'⚔' * 20}{Colors.ENDC}")
        print(f"{Colors.BOLD}⚔️  ATTACK: {attacker.name} → {defender.name}{Colors.ENDC}")
        print(f"{Colors.BOLD}   Target AC: {defender.armor_class}{Colors.ENDC}")
        print(f"{Colors.RED}{'⚔' * 20}{Colors.ENDC}")
        
        # Attack roll
        attack_roll, attack_breakdown, is_crit = DiceRoller.roll_d20(attacker.attack_bonus)
        
        # Check if hit
        hit = attack_roll >= defender.armor_class or is_crit
        
        # Print hit/miss
        print(f"\n{Colors.BOLD}   Attack Result: {Colors.ENDC}", end="")
        if hit:
            print(f"{Colors.GREEN}{Colors.BOLD}HIT!{Colors.ENDC}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}MISS!{Colors.ENDC}")
        
        if not hit and not is_crit:
            print(f"{Colors.RED}{'⚔' * 20}{Colors.ENDC}\n")
            return False, 0, f"{attacker.name} attacks {defender.name}: {attack_breakdown} vs AC {defender.armor_class} - Miss!"
        
        # Roll damage
        damage_rolls = 2 if is_crit else 1  # Critical hits roll damage twice
        total_damage = 0
        damage_breakdowns = []
        
        print(f"\n{Colors.BOLD}   Rolling Damage...{Colors.ENDC}")
        for _ in range(damage_rolls):
            damage, breakdown = DiceRoller.roll(attacker.damage_dice)
            total_damage += damage
            damage_breakdowns.append(breakdown)
        
        # Apply damage
        actual_damage, is_dead = defender.take_damage(total_damage)
        
        # Print damage summary
        print(f"{Colors.BOLD}   Total Damage: {Colors.RED}{total_damage}{Colors.ENDC}")
        print(f"{Colors.BOLD}   {defender.name} HP: {Colors.ENDC}", end="")
        if is_dead:
            print(f"{Colors.RED}{Colors.BOLD}DEFEATED!{Colors.ENDC}")
        else:
            hp_percent = (defender.current_health / defender.max_health) * 100
            color = Colors.GREEN if hp_percent > 50 else Colors.YELLOW if hp_percent > 25 else Colors.RED
            print(f"{color}{defender.current_health}/{defender.max_health}{Colors.ENDC}")
        
        print(f"{Colors.RED}{'⚔' * 20}{Colors.ENDC}\n")
        
        # Build description
        description = f"{attacker.name} attacks {defender.name}: {attack_breakdown} vs AC {defender.armor_class} - Hit!"
        if is_crit:
            description += " CRITICAL HIT!"
        
        description += f"\nDamage: {' + '.join(damage_breakdowns)} = {total_damage}"
        description += f"\n{defender.name} takes {actual_damage} damage."
        
        if is_dead:
            description += f"\n{defender.name} has been defeated!"
        else:
            description += f" ({defender.current_health}/{defender.max_health} HP remaining)"
        
        return True, actual_damage, description
    
    @staticmethod
    def perform_defend(character: Character) -> str:
        """Perform a defend action (increases AC temporarily)"""
        # In a real implementation, this would set a temporary AC bonus
        return f"{character.name} takes a defensive stance, gaining +2 AC until their next turn."
    
    @staticmethod
    def attempt_flee(character: Character, enemies: List[Character]) -> Tuple[bool, str]:
        """Attempt to flee from combat"""
        # Base DC is 15, modified by number of enemies
        dc = 15 + len(enemies)
        
        # Use dexterity (athletics) check to escape
        modifier = character.stats.get_modifier("dexterity")
        roll_total, breakdown, _ = DiceRoller.roll_d20(modifier)
        
        success = roll_total >= dc
        
        if success:
            return True, f"{character.name} attempts to flee: {breakdown} vs DC {dc} - Success! They escape from combat!"
        else:
            return False, f"{character.name} attempts to flee: {breakdown} vs DC {dc} - Failed! They cannot escape!"


class SpellCasting:
    """Handles spell casting mechanics"""
    
    SPELLS = {
        "firebolt": {
            "damage": "1d10",
            "type": "fire",
            "range": "long",
            "description": "A bolt of fire"
        },
        "heal": {
            "healing": "1d8+2",
            "type": "healing",
            "range": "touch",
            "description": "Divine magic heals wounds"
        },
        "shield": {
            "effect": "ac_bonus",
            "bonus": 5,
            "duration": 1,
            "description": "A magical shield provides protection"
        }
    }
    
    @staticmethod
    def cast_spell(caster: Character, spell_name: str, target: Optional[Character] = None) -> str:
        """Cast a spell"""
        if spell_name not in SpellCasting.SPELLS:
            return f"{caster.name} doesn't know the spell '{spell_name}'!"
        
        spell = SpellCasting.SPELLS[spell_name]
        
        # Check if caster can cast spells
        if caster.character_class not in [CharacterClass.MAGE, CharacterClass.CLERIC]:
            return f"{caster.name} cannot cast spells as a {caster.character_class.value}!"
        
        # Check spell type restrictions
        if spell_name == "heal" and caster.character_class != CharacterClass.CLERIC:
            return f"Only clerics can cast healing spells!"
        
        # Add cinematic spell descriptions
        spell_descriptions = {
            "firebolt": f"A bolt of fire shoots from {caster.name}'s hand, streaking through the air!",
            "heal": f"Divine light emanates from {caster.name}'s hands!",
            "shield": f"{caster.name} weaves protective magic around themselves!"
        }
        
        result = spell_descriptions.get(spell_name, f"{caster.name} casts {spell_name}!")
        
        if "damage" in spell and target:
            damage, breakdown = DiceRoller.roll(spell["damage"])
            print(f"[SpellCasting] {target.name} health before damage: {target.current_health}/{target.max_health}")
            actual_damage, is_dead = target.take_damage(damage)
            print(f"[SpellCasting] Damage roll: {damage}, Actual damage: {actual_damage}")
            print(f"[SpellCasting] {target.name} health after damage: {target.current_health}/{target.max_health}")
            print(f"[SpellCasting] Is dead: {is_dead}")
            
            # Add impact description
            if spell_name == "firebolt":
                result += f" The firebolt strikes {target.name} with searing heat!"
            else:
                result += f" The spell strikes {target.name}!"
                
            result += f" {target.name} takes {actual_damage} damage"
            
            # Add status description
            if is_dead:
                result += f" and collapses, defeated!"
            elif target.current_health < target.max_health * 0.25:
                result += f" and staggers, badly wounded!"
            elif target.current_health < target.max_health * 0.5:
                result += f" and reels from the impact!"
            else:
                result += "!"
        
        elif "healing" in spell:
            if not target:
                target = caster
            healing, breakdown = DiceRoller.roll(spell["healing"])
            actual_healing = target.heal(healing)
            result += f"\n{breakdown} healing to {target.name}!"
            result += f"\n{target.name} heals {actual_healing} HP. ({target.current_health}/{target.max_health} HP)"
        
        elif "effect" in spell:
            if spell["effect"] == "ac_bonus":
                result += f"\n{caster.name} gains +{spell['bonus']} AC for {spell['duration']} round(s)!"
        
        return result


class GameUtilities:
    """Various utility functions for the game"""
    
    @staticmethod
    def transfer_loot(from_character: NPCCharacter, to_character: PlayerCharacter) -> str:
        """Transfer all items and gold from defeated enemy to player"""
        loot_description = []
        
        # Transfer gold
        if from_character.gold > 0:
            to_character.gold += from_character.gold
            loot_description.append(f"{from_character.gold} gold")
            from_character.gold = 0
        
        # Transfer items
        for item in from_character.inventory:
            to_character.add_item(item)
            if item.quantity > 1:
                loot_description.append(f"{item.quantity} {item.name}")
            else:
                loot_description.append(item.name)
        from_character.inventory.clear()
        
        if loot_description:
            return f"You found: {', '.join(loot_description)}"
        else:
            return "The enemy had nothing of value."
    
    @staticmethod
    def describe_environment(location_type: str) -> str:
        """Generate a description for an environment"""
        environments = {
            "dungeon": [
                "The air is damp and musty. Water drips from the stone ceiling.",
                "Torches flicker on the walls, casting dancing shadows.",
                "The stone corridor stretches into darkness ahead."
            ],
            "forest": [
                "Sunlight filters through the canopy above.",
                "The sound of birds and rustling leaves fills the air.",
                "A narrow path winds between ancient trees."
            ],
            "tavern": [
                "The warm glow of the fireplace illuminates the room.",
                "The smell of ale and roasted meat fills your nostrils.",
                "Patrons chat and laugh at wooden tables."
            ]
        }
        
        return random.choice(environments.get(location_type, ["You find yourself in an unfamiliar place."]))