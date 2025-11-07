"""Experience level collection task."""
from dataclasses import dataclass
from livekit.agents import AgentTask, RunContext
from livekit.agents.llm.tool_context import function_tool, ToolError
from livekit.agents.voice import SpeechHandle


@dataclass
class ExperienceResult:
    """Result from experience collection."""
    experience_level: str
    spot_recommendation: str


class ExperienceTask(AgentTask[ExperienceResult]):
    """Task to collect surfing experience level."""
    
    def __init__(self):
        super().__init__(
            instructions="""You are collecting the customer's surfing experience level.
Ask about their experience (beginner/intermediate/advanced). When they tell you:
1. Call record_experience()
2. Share the spot recommendation
3. Ask for confirmation
4. When they confirm, call confirm_experience()

CRITICAL: Never call confirm_experience() in the same turn as record_experience().
Wait for explicit user confirmation."""
        )
        self._level = ""
        self._recommendation = ""
        self._record_handle: SpeechHandle | None = None
        self._confirmed = False
    
    async def on_enter(self) -> None:
        """Called when task starts."""
        await self.session.generate_reply(
            instructions="Ask about their surfing experience level."
        )
    
    @function_tool()
    async def record_experience(self, level: str, ctx: RunContext) -> str:
        """Record experience level.
        
        Args:
            level: Experience level (beginner/intermediate/advanced)
        """
        self._record_handle = ctx.speech_handle
        
        level_lower = level.lower()
        
        if "beginner" in level_lower or "never" in level_lower or "first" in level_lower:
            self._level = "beginner"
            self._recommendation = "Doheny State Beach - most beginner-friendly!"
        elif "advanced" in level_lower or "expert" in level_lower:
            self._level = "advanced"
            self._recommendation = "Trestles or San Onofre - great for advanced!"
        else:
            self._level = "intermediate"
            self._recommendation = "San Onofre or Doheny - fun waves for your level!"
        
        return (
            f"Experience recorded: {self._level}. "
            f"Say: 'Based on your {self._level} level, I recommend {self._recommendation} "
            f"Does that sound good?' "
            f"DO NOT call confirm_experience yet."
        )
    
    @function_tool()
    async def confirm_experience(self, ctx: RunContext) -> str:
        """Confirm experience after user validates."""
        await ctx.wait_for_playout()
        
        if ctx.speech_handle == self._record_handle:
            raise ToolError("User must confirm explicitly")
        
        if not self._level:
            raise ToolError("No experience level recorded")
        
        self._confirmed = True
        self.complete(ExperienceResult(
            experience_level=self._level,
            spot_recommendation=self._recommendation
        ))


