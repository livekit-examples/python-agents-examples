"""Phone collection task."""
from dataclasses import dataclass
from livekit.agents import AgentTask, RunContext
from livekit.agents.llm import function_tool, ToolError
from livekit.agents.voice import SpeechHandle

from utils import load_reading_guidelines


def validate_phone(phone: str) -> bool:
    """Basic phone number validation.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone looks valid (has at least 10 digits)
    """
    digits = ''.join(c for c in phone if c.isdigit())
    return len(digits) >= 10


@dataclass
class PhoneResult:
    """Result from phone collection."""
    phone: str


class PhoneTask(AgentTask[PhoneResult]):
    """Task to collect phone number with confirmation."""
    
    def __init__(self):
        reading_guidelines = load_reading_guidelines()
        super().__init__(
            instructions=f"""{reading_guidelines}
            
You are collecting the customer's phone number.
Ask for it naturally. When they provide it:
1. Call record_phone() 
2. Read it back following the reading guidelines
3. Ask for confirmation
4. When they confirm, call confirm_phone()

CRITICAL: Never call confirm_phone() in the same turn as record_phone().
Wait for explicit user confirmation."""
        )
        self._phone = ""
        self._record_handle: SpeechHandle | None = None
        self._confirmed = False
    
    async def on_enter(self) -> None:
        """Called when task starts."""
        await self.session.generate_reply(
            instructions="Ask for their phone number."
        )
    
    @function_tool()
    async def record_phone(self, phone: str, ctx: RunContext) -> str:
        """Record phone number.
        
        Args:
            phone: Phone number
        """
        self._record_handle = ctx.speech_handle
        
        if not validate_phone(phone):
            return f"Invalid format: '{phone}'. Ask user to repeat it."
        
        self._phone = phone
        return (
            f"Phone recorded: {phone}. "
            f"IMPORTANT: Read it back following reading guidelines and ask 'Is that correct?'. "
            f"DO NOT call confirm_phone yet."
        )
    
    @function_tool()
    async def confirm_phone(self, ctx: RunContext) -> str:
        """Confirm phone after user validates."""
        await ctx.wait_for_playout()
        
        if ctx.speech_handle == self._record_handle:
            raise ToolError("User must confirm explicitly")
        
        if not self._phone:
            raise ToolError("No phone recorded")
        
        self._confirmed = True
        self.complete(PhoneResult(phone=self._phone))

