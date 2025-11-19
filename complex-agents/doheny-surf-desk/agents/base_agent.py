"""Base agent with shared handoff logic."""
import logging
from dataclasses import dataclass, field
from typing import Optional
from livekit.agents.voice import Agent, RunContext
from livekit.agents.llm import ChatContext

logger = logging.getLogger("doheny-surf-desk")


@dataclass
class SurfBookingData:
    """Session data for surf booking workflow."""
    # Profile
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    experience_level: Optional[str] = None  # "beginner" | "intermediate" | "advanced"
    
    # Booking
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    spot_location: Optional[str] = None  # "Doheny" | "San Onofre" | "Trestles"
    booking_id: Optional[str] = None
    instructor_name: Optional[str] = None
    
    # Gear
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    board_size: Optional[str] = None
    wetsuit_size: Optional[str] = None
    accessories: list = field(default_factory=list)
    
    # Payment
    payment_status: Optional[str] = None  # "pending" | "paid" | "failed"
    total_amount: Optional[float] = 0.0
    
    # Flags
    is_minor: bool = False
    has_injury: bool = False
    guardian_consent: Optional[bool] = None
    guardian_name: Optional[str] = None
    guardian_contact: Optional[str] = None
    
    # Agent registry for returning to frontdesk
    personas: dict = field(default_factory=dict)
    
    def is_profile_complete(self) -> bool:
        """Check if basic profile is complete."""
        return all([
            self.name,
            self.email,
            self.age,
            self.experience_level
        ])
    
    def is_booking_complete(self) -> bool:
        """Check if booking details are complete."""
        return all([
            self.preferred_date,
            self.preferred_time,
            self.spot_location,
            self.booking_id
        ])
    
    def is_gear_selected(self) -> bool:
        """Check if gear selection is complete."""
        return all([
            self.board_size,
            self.wetsuit_size
        ])
    
    def summarize(self) -> str:
        """Return a summary of current booking state."""
        parts = []
        
        if self.name:
            parts.append(f"Customer: {self.name}")
        if self.age:
            minor_status = " (MINOR)" if self.is_minor else ""
            parts.append(f"Age: {self.age}{minor_status}")
        if self.experience_level:
            parts.append(f"Experience: {self.experience_level}")
        if self.preferred_date and self.preferred_time:
            parts.append(f"Lesson: {self.preferred_date} at {self.preferred_time}")
        if self.spot_location:
            parts.append(f"Location: {self.spot_location}")
        if self.board_size or self.wetsuit_size:
            gear = []
            if self.board_size:
                gear.append(f"Board: {self.board_size}")
            if self.wetsuit_size:
                gear.append(f"Wetsuit: {self.wetsuit_size}")
            parts.append(" | ".join(gear))
        if self.total_amount:
            parts.append(f"Total: ${self.total_amount:.2f}")
        
        return " | ".join(parts) if parts else "No booking info yet"


RunContext_T = RunContext[SurfBookingData]

class BaseAgent(Agent):
    """Base agent with shared handoff logic.
    
    Uses the official LiveKit pattern for agent handoffs via chat_ctx passing.
    """
    
    def __init__(self, chat_ctx: Optional[ChatContext] = None, **kwargs):
        """Initialize agent with optional chat context from previous agent.
        
        Args:
            chat_ctx: Optional chat context to preserve conversation history
            **kwargs: Additional arguments passed to Agent constructor
        """
        super().__init__(chat_ctx=chat_ctx, **kwargs)
