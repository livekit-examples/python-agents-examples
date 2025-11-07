"""Age collection task."""
from dataclasses import dataclass
from livekit.agents import AgentTask, RunContext
from livekit.agents.llm.tool_context import function_tool, ToolError
from livekit.agents.voice import SpeechHandle


@dataclass
class AgeResult:
    """Result from age collection."""
    age: int
    is_minor: bool


class AgeTask(AgentTask[AgeResult]):
    """Task to collect age with minor detection."""
    
    def __init__(self):
        super().__init__(
            instructions="""You are collecting the customer's age.
Ask for it naturally. When they provide it:
1. Call record_age()
2. Confirm back to them
3. If under 18, warmly note that guardian consent will be needed later
4. When they confirm, call confirm_age()

CRITICAL: Never call confirm_age() in the same turn as record_age().
Wait for explicit user confirmation."""
        )
        self._age: int | None = None
        self._is_minor = False
        self._record_handle: SpeechHandle | None = None
        self._confirmed = False
    
    async def on_enter(self) -> None:
        """Called when task starts."""
        await self.session.generate_reply(
            instructions="Ask for their age."
        )
    
    @function_tool()
    async def record_age(self, age: int, ctx: RunContext) -> str:
        """Record age.
        
        Args:
            age: Customer's age
        """
        self._record_handle = ctx.speech_handle
        
        if age < 5:
            return f"Age {age} seems too young. Verify with user."
        if age > 100:
            return f"Age {age} seems unusual. Double-check with user."
        
        self._age = age
        self._is_minor = age < 18
        
        if self._is_minor:
            return (
                f"Age recorded: {age} (minor). "
                f"Say: 'Thanks! Since you're under 18, we'll need guardian consent later. "
                f"Can you confirm {age} is correct?' "
                f"DO NOT call confirm_age yet."
            )
        else:
            return (
                f"Age recorded: {age}. "
                f"Say: 'Can you confirm {age} is correct?' "
                f"DO NOT call confirm_age yet."
            )
    
    @function_tool()
    async def confirm_age(self, ctx: RunContext) -> str:
        """Confirm age after user validates."""
        await ctx.wait_for_playout()
        
        if ctx.speech_handle == self._record_handle:
            raise ToolError("User must confirm explicitly")
        
        if self._age is None:
            raise ToolError("No age recorded")
        
        self._confirmed = True
        self.complete(AgeResult(age=self._age, is_minor=self._is_minor))


