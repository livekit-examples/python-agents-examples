"""Name collection task."""
from dataclasses import dataclass
from livekit.agents import AgentTask, RunContext
from livekit.agents.llm.tool_context import function_tool


@dataclass
class NameResult:
    """Result from name collection."""
    name: str


class NameTask(AgentTask[NameResult]):
    """Task to collect customer's name."""
    
    def __init__(self):
        super().__init__(
            instructions="""You are collecting the customer's full name. Do not say hi, just ask for full name.
            Ask for their name naturally and directly.
            When they provide it, call record_name() to save it."""
        )
    
    async def on_enter(self) -> None:
        """Called when task starts."""
        await self.session.generate_reply(
            instructions="Ask for their full name in a friendly way."
        )
    
    @function_tool()
    async def record_name(self, name: str) -> str:
        """Record the customer's name.
        
        Args:
            name: Customer's full name
        """
        self.complete(NameResult(name=name))

