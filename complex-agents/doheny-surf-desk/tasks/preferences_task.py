"""Preferences collection task."""
from dataclasses import dataclass
from livekit.agents import AgentTask, RunContext
from livekit.agents.llm.tool_context import function_tool, ToolError
from livekit.agents.voice import SpeechHandle


@dataclass
class PreferencesResult:
    """Result from preferences collection."""
    preferred_date: str
    preferred_time: str
    spot_location: str


class PreferencesTask(AgentTask[PreferencesResult]):
    """Task to collect lesson preferences (date, time, location)."""
    
    def __init__(self):
        super().__init__(
            instructions="""You are collecting lesson preferences: date, time, and location.
Start by asking for their preferred DATE first.

Use record_preferences() each time you learn new information.
After recording the date, ask for TIME.
After recording the time, ask for LOCATION.
When you have all three:
1. Summarize them back to the user
2. Ask for confirmation
3. When they confirm, call confirm_preferences()

CRITICAL: Never call confirm_preferences() in the same turn as record_preferences().
Wait for explicit user confirmation of all details."""
        )
        self._date = ""
        self._time = ""
        self._location = ""
        self._record_handle: SpeechHandle | None = None
        self._confirmed = False
    
    async def on_enter(self) -> None:
        """Called when task starts."""
        await self.session.generate_reply(
            instructions="Ask for their preferred date only. Don't ask about time or location yet."
        )
    
    @function_tool()
    async def record_preferences(
        self,
        preferred_date: str = "",
        preferred_time: str = "",
        spot_location: str = "",
        ctx: RunContext = None
    ) -> str:
        """Record lesson preferences as they're provided.
        
        Args:
            preferred_date: Preferred date
            preferred_time: Preferred time
            spot_location: Preferred spot
        """
        if ctx:
            self._record_handle = ctx.speech_handle
        
        if preferred_date:
            self._date = preferred_date
        if preferred_time:
            self._time = preferred_time
        if spot_location:
            spot_lower = spot_location.lower()
            if "doheny" in spot_lower:
                self._location = "Doheny"
            elif "san onofre" in spot_lower or "onofre" in spot_lower:
                self._location = "San Onofre"
            elif "trestle" in spot_lower:
                self._location = "Trestles"
            else:
                self._location = spot_location
        
        missing = []
        if not self._date:
            missing.append("date")
        if not self._time:
            missing.append("time")
        if not self._location:
            missing.append("location")
        
        if missing:
            return f"Preferences updated. Still need: {', '.join(missing)}. Ask for them."
        else:
            return (
                f"All preferences collected: {self._date} at {self._time} in {self._location}. "
                f"Summarize these back and ask 'Can you confirm these details?' "
                f"DO NOT call confirm_preferences yet."
            )
    
    @function_tool()
    async def confirm_preferences(self, ctx: RunContext) -> str:
        """Confirm preferences after user validates."""
        await ctx.wait_for_playout()
        
        if ctx.speech_handle == self._record_handle:
            raise ToolError("User must confirm explicitly")
        
        if not self._date or not self._time or not self._location:
            missing = []
            if not self._date:
                missing.append("date")
            if not self._time:
                missing.append("time")
            if not self._location:
                missing.append("location")
            raise ToolError(f"Missing: {', '.join(missing)}")
        
        self._confirmed = True
        self.complete(PreferencesResult(
            preferred_date=self._date,
            preferred_time=self._time,
            spot_location=self._location
        ))

