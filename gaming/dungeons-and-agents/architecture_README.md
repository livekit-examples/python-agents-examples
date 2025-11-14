# Dungeons and Agents - RPG Game Architecture

This is a modular, extensible RPG game built with LiveKit Agents. The architecture emphasizes dynamic content generation using LLMs while maintaining clean code organization.

## Architecture Overview

```
role-playing/
├── agent.py                 # Main entry point
├── agents/                  # Agent implementations
│   ├── base_agent.py       # Base class for all agents
│   ├── narrator_agent.py   # Handles exploration & dialogue
│   └── combat_agent.py     # Handles combat encounters
├── core/                    # Core game state management
│   ├── game_state.py       # Game state management
│   └── game_mechanics.py   # Core mechanics (dice, combat, skill checks)
├── generators/              # Dynamic content generation
│   ├── npc_generator.py    # NPC creation with LLM
│   └── item_generator.py   # Item generation with LLM
├── rules/                   # YAML rule files
│   ├── npc_generation_rules.yaml
│   ├── item_generation_rules.yaml
│   └── location_generation_rules.yaml
├── systems/                 # Game systems (to be implemented)
├── utils/                   # Utilities
│   └── display.py          # Console formatting
├── character.py             # Character classes
└── prompts/                 # Agent instruction prompts
```

## Key Features

### Dynamic Content Generation
- NPCs are generated dynamically with unique personalities, inventories, and backstories
- Items are created contextually based on location and owner
- Everything adapts to the current game state and recent events

### Modular Design
- Each agent handles specific game modes (exploration vs combat)
- Generators can be extended without modifying core code
- Rule files make it easy to adjust generation parameters

### Parallel LLM Processing
- Multiple aspects of NPCs (personality, inventory, backstory) are generated in parallel
- Efficient use of LLM resources for faster response times

## Adding New Features

### Adding a New NPC Type
1. Edit `rules/npc_generation_rules.yaml`
2. Add your NPC type with appropriate weights and guidelines
3. The generator will automatically use your new rules

### Adding New Items
1. Edit `rules/item_generation_rules.yaml`
2. Add new item categories or modify generation prompts
3. Items will be generated according to your specifications

### Creating New Game Systems
1. Add a new file in `systems/`
2. Import and use it in the appropriate agent
3. Follow the pattern of existing systems for consistency

## Running the Game

```bash
python agent.py dev
```

## Future Enhancements
- Quest generation system
- Dynamic location descriptions
- Persistent world state
- Multiplayer support
- More sophisticated combat AI
- Spell creation system
- Crafting mechanics