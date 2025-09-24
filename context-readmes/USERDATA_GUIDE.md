# UserData in LiveKit Agents: A Comprehensive Guide

## Overview

UserData is a powerful design pattern used throughout LiveKit agents to manage state and share data across the entire agent lifecycle. It serves as a persistent context object that flows through agent sessions, function tools, and state transitions.

## Example Implementations

This guide references several real-world implementations of UserData:

- **[Nova Sonic Agent](../complex-agents/nova-sonic/agent.py)**: Multi-persona agent with survey, scheduling, and task management
- **[Form Filler Agent](../complex-agents/nova-sonic/form_agent.py)**: Single agent for filling forms with personal information
- **[Medical Triage System](../complex-agents/medical_office_triage/triage.py)**: Multi-agent system with persona switching
- **[Tavus Avatar](../avatars/tavus/tavus.py)**: Interactive learning agent with flash cards and quizzes
- **[IVR Agent](../complex-agents/ivr-agent/agent.py)**: Interactive voice response system with DTMF handling
- **[Nutrition Assistant](../complex-agents/nutrition-assistant/agent.py)**: Health tracking agent with database integration

## What is UserData?

UserData is typically implemented as a Python dataclass that stores:
- Session-level context and references
- Participant information
- Application state
- Business logic data
- External service references

## Why Use UserData?

1. **State Management**: Maintain state across multiple function tool invocations and agent lifecycle events
2. **Type Safety**: Leverage Python's type system for safer data access
3. **Context Propagation**: Share resources and data throughout the agent without global variables
4. **Clean Architecture**: Separate concerns by centralizing shared data in a structured format

## Basic Structure

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from livekit.agents import JobContext

@dataclass
class UserData:
    # Required context reference
    ctx: JobContext
    
    # Participant information
    participant_identity: str = ""
    
    # Application state
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    current_state: str = "initial"
    
    # Business logic data
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    session_data: Dict[str, Any] = field(default_factory=dict)
```

## How to Use UserData

### 1. Define Your UserData Class

```python
@dataclass
class MyUserData:
    ctx: JobContext
    user_name: str = ""
    interaction_count: int = 0
    tasks: List[str] = field(default_factory=list)
```

### 2. Initialize and Pass to AgentSession

```python
async def entrypoint(ctx: JobContext):
    await ctx.connect()
    
    # Create UserData instance
    userdata = MyUserData(ctx=ctx)
    
    # Create session with UserData
    session = AgentSession[MyUserData](
        userdata=userdata,
        llm=openai.LLM(),
        stt=deepgram.STT(),
        tts=elevenlabs.TTS(),
        vad=silero.VAD.load()
    )
    
    # Start the session
    await session.start(room=ctx.room, agent=MyAgent())
```

### 3. Access UserData in Agents

```python
class MyAgent(Agent):
    async def on_enter(self):
        # Access via self.session.userdata
        userdata = self.session.userdata
        participant_count = len(userdata.ctx.room.remote_participants)
        
        # Use the data
        await self.session.say(f"I see {participant_count} participants in the room")
```

### 4. Access UserData in Function Tools

```python
from livekit.agents.llm import function_tool
from livekit.agents.voice import RunContext

# Define typed RunContext
RunContext_T = RunContext[MyUserData]

class MyAgent(Agent):
    @function_tool
    async def add_task(self, task: str, context: RunContext_T):
        # Access via context.userdata
        userdata = context.userdata
        userdata.tasks.append(task)
        userdata.interaction_count += 1
        
        # Access room through ctx
        room = userdata.ctx.room
        await room.local_participant.set_attributes({
            "task_count": str(len(userdata.tasks))
        })
        
        return f"Added task: {task}. You now have {len(userdata.tasks)} tasks."
```

## Real-World Examples

### Example 1: Multi-Persona Agent (Nova Sonic)
*Source: [../complex-agents/nova-sonic/agent.py](../complex-agents/nova-sonic/agent.py)*

```python
@dataclass
class UserData:
    ctx: JobContext
    session: AgentSession = None
    current_persona: str = "survey_taker"
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    survey_responses: Dict[str, Any] = field(default_factory=dict)
    appointments: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_conversation_turn(self, role: str, content: str):
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "persona": self.current_persona
        })
```

### Example 2: Medical Triage System
*Source: [../complex-agents/medical_office_triage/triage.py](../complex-agents/medical_office_triage/triage.py)*

```python
@dataclass
class UserData:
    personas: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    ctx: Optional[JobContext] = None
    
    def summarize(self) -> str:
        return "User data: Medical office triage system"
```

### Example 3: Interactive Learning (Tavus Avatar)
*Source: [../avatars/tavus/tavus.py](../avatars/tavus/tavus.py)*

```python
@dataclass
class UserData:
    ctx: Optional[JobContext] = None
    flash_cards: List[FlashCard] = field(default_factory=list)
    quizzes: List[Quiz] = field(default_factory=list)
    
    def add_flash_card(self, question: str, answer: str) -> FlashCard:
        card = FlashCard(
            id=str(uuid.uuid4()),
            question=question,
            answer=answer
        )
        self.flash_cards.append(card)
        return card
```

### Example 4: IVR System with DTMF Handling
*Source: [../complex-agents/ivr-agent/agent.py](../complex-agents/ivr-agent/agent.py)*

```python
@dataclass
class UserData:
    """Store user data for the navigator agent."""
    ctx: JobContext
    last_dtmf_press: float = 0
    task: Optional[str] = None
```

### Example 5: Nutrition Assistant with Database
*Source: [../complex-agents/nutrition-assistant/agent.py](../complex-agents/nutrition-assistant/agent.py)*

```python
@dataclass
class NutritionUserData:
    participant_identity: str
    ctx: agents.JobContext = None
```

## Best Practices

### 1. Always Include JobContext
```python
@dataclass
class UserData:
    ctx: JobContext  # Essential for room access
```

### 2. Use Type Hints
```python
RunContext_T = RunContext[UserData]  # Type alias for clarity

@function_tool
async def my_function(self, context: RunContext_T):
    # Now context.userdata is properly typed
```

### 3. Initialize Collections with field()
```python
@dataclass
class UserData:
    # Good - each instance gets its own list
    items: List[str] = field(default_factory=list)
    
    # Bad - all instances share the same list!
    # items: List[str] = []
```

### 4. Add Helper Methods
```python
@dataclass
class UserData:
    messages: List[Message] = field(default_factory=list)
    
    def add_message(self, content: str, role: str = "user"):
        self.messages.append(Message(content=content, role=role))
    
    def get_recent_messages(self, count: int = 5):
        return self.messages[-count:]
```

### 5. Handle State Transitions
```python
@dataclass
class UserData:
    state: str = "initial"
    state_history: List[str] = field(default_factory=list)
    
    def transition_to(self, new_state: str):
        self.state_history.append(self.state)
        self.state = new_state
```

## Advanced Patterns

### Global UserData Access (AWS Plugin Workaround)
Some plugins may not properly pass context. In such cases:

```python
# Global variable as fallback
_global_userdata: Optional[UserData] = None

async def entrypoint(ctx: JobContext):
    global _global_userdata
    userdata = UserData(ctx=ctx)
    _global_userdata = userdata  # Set global reference
    
    # Continue with normal setup...
```

### Persisting Data Across Agent Switches
```python
@dataclass
class UserData:
    personas: dict[str, Agent] = field(default_factory=dict)
    shared_context: dict = field(default_factory=dict)
    
async def transfer_to_agent(self, name: str, context: RunContext_T) -> Agent:
    userdata = context.userdata
    userdata.shared_context["previous_agent"] = type(self).__name__
    return userdata.personas[name]
```

### Database Integration
```python
@dataclass
class UserData:
    ctx: JobContext
    db_connection: Optional[Connection] = None
    user_id: Optional[str] = None
    
    async def initialize_db(self):
        self.db_connection = await create_connection("database.db")
        
    async def save_interaction(self, message: str):
        if self.db_connection:
            await self.db_connection.execute(
                "INSERT INTO interactions (user_id, message) VALUES (?, ?)",
                (self.user_id, message)
            )
```

## Common Use Cases

1. **Multi-Agent Systems**: Store references to different agents and manage transitions
2. **Conversation History**: Track messages, responses, and context across interactions
3. **Form Filling**: Store personal information and form submissions
4. **Task Management**: Maintain todo lists, appointments, and reminders
5. **Session Analytics**: Track metrics, user behavior, and interaction patterns
6. **External Service Integration**: Store API clients, database connections, and service references

## Debugging Tips

1. **Log UserData State**: Add logging to track state changes
```python
logger.info(f"UserData state: {userdata.__dict__}")
```

2. **Validate Data**: Add validation methods
```python
def validate(self) -> bool:
    return self.ctx is not None and self.participant_identity
```

3. **Reset Methods**: Implement cleanup for testing
```python
def reset(self):
    self.conversation_history.clear()
    self.state = "initial"
```

## Summary

UserData is a fundamental pattern in LiveKit agents that provides:
- Centralized state management
- Type-safe data access
- Clean separation of concerns
- Flexibility for complex applications

By properly implementing UserData, you can build sophisticated, stateful agents that maintain context throughout their lifecycle while keeping your code organized and maintainable.