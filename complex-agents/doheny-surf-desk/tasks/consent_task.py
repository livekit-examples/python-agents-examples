"""Consent task for collecting guardian approval for minors."""
from dataclasses import dataclass
from livekit.agents import AgentTask, function_tool

from utils import load_prompt


@dataclass
class ConsentResult:
    """Result from collecting guardian consent."""
    approved: bool
    guardian_name: str
    guardian_contact: str


class ConsentTask(AgentTask[ConsentResult]):
    """Task to collect parental/guardian consent for minors (under 18)."""
    
    def __init__(self, chat_ctx=None):
        instructions = load_prompt('consent_prompt.yaml')
        super().__init__(
            instructions=instructions,
            chat_ctx=chat_ctx,
        )
        self._guardian_name = None
        self._guardian_contact = None
    
    async def on_enter(self) -> None:
        """Called when task starts."""
        userdata = self.session.userdata
        
        await self.session.generate_reply(
            instructions=f"""
            Warmly say: "Since {userdata.name} is under 18, I need parental or 
            guardian consent before finalizing the booking. This is required by 
            California law for water sports activities.
            
            Is a parent or guardian available to provide consent right now?"
            
            IMPORTANT: 
            - If they say a guardian is present or identify themselves as the guardian, 
              proceed immediately to collect guardian info
            - If they say guardian is not available, use record_consent_denied
            - DO NOT ask them to call another phone number if guardian is present
            """
        )
    
    @function_tool
    async def record_guardian_info(
        self, 
        guardian_name: str,
        guardian_contact: str = ""
    ) -> str:
        """Record guardian name and contact information.
        
        Args:
            guardian_name: Full name of parent/guardian
            guardian_contact: Phone number or email of guardian (optional, can use customer's contact)
            
        Returns:
            Confirmation message
        """
        self._guardian_name = guardian_name
        self._guardian_contact = guardian_contact or self.session.userdata.phone or self.session.userdata.email
        
        return (
            f"Thank you, {guardian_name}. I've recorded your information.\n"
            f"IMPORTANT: You MUST speak now. Ask: 'Do you give consent for {self.session.userdata.name} "
            f"to participate in this surf lesson on {self.session.userdata.preferred_date}?'\n"
            f"Then WAIT for their response before calling record_consent_approved."
        )
    
    @function_tool
    async def record_consent_approved(self) -> str:
        """Record that guardian has approved the surf lesson."""
        if not self._guardian_name or not self._guardian_contact:
            return "ERROR: Guardian name and contact required before confirming consent."
        
        result = ConsentResult(
            approved=True,
            guardian_name=self._guardian_name,
            guardian_contact=self._guardian_contact
        )
        
        self.session.userdata.guardian_consent = True
        self.session.userdata.guardian_name = self._guardian_name
        self.session.userdata.guardian_contact = self._guardian_contact
        
        self.complete(result)
        
        return (
            f"Perfect! Guardian consent recorded from {self._guardian_name}. "
            f"You MUST speak now and thank the guardian warmly. Then proceed with the booking."
        )
    
    @function_tool
    async def record_consent_denied(self, reason: str = "Guardian unavailable") -> str:
        """Record that guardian denied consent or is unavailable.
        
        Args:
            reason: Reason consent was not given
        """
        result = ConsentResult(
            approved=False,
            guardian_name=self._guardian_name or "Not provided",
            guardian_contact=self._guardian_contact or "Not provided"
        )
        
        self.session.userdata.guardian_consent = False
        self.complete(result)
        

