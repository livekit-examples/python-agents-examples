"""Front desk agent for initial consultation and routing."""
from livekit.agents.llm import function_tool

from .base_agent import BaseAgent, RunContext_T
from utils import load_prompt


class FrontDeskAgent(BaseAgent):
    """Agent responsible for greeting customers and routing them appropriately."""
    
    def __init__(self, chat_ctx=None):
        super().__init__(
            instructions=load_prompt('frontdesk_prompt.yaml'),
            chat_ctx=chat_ctx,
        )
    
    async def on_enter(self) -> None:
        """Called when agent starts."""
        await self.session.generate_reply(
            instructions="Warmly greet the customer and introduce yourself as Michael from Doheny Surf Desk. "
            "Ask how you can help them today - are they looking to book a surf lesson, "
            "or do they have questions about surfing, lessons, or locations?"
        )
    
    @function_tool
    async def start_booking(self, context: RunContext_T) -> BaseAgent:
        """Start the booking process by transferring to Intake Agent.
        
        Use this when customer is ready to book a lesson.
        
        Args:
            context: RunContext with userdata
            
        Returns:
            IntakeAgent instance
        """
        from agents.intake_agent import IntakeAgent
        
        await self.session.say(
            "Perfect! Let's get you booked for an awesome surf lesson. "
            "I'll collect some information to find the perfect setup for you."
        )
        
        return IntakeAgent(chat_ctx=self.chat_ctx)
