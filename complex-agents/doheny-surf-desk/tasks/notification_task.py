"""Notification task for sending booking confirmations."""
import random
from datetime import datetime
from dataclasses import dataclass
from livekit.agents import AgentTask, function_tool

from utils import format_gear_checklist, load_reading_guidelines


def mock_send_notification(email: str, phone: str, message: str, channel: str = "email") -> dict:
    """Simulate sending a notification.
    
    Args:
        email: Customer email
        phone: Customer phone
        message: Notification message
        channel: "email" or "sms"
        
    Returns:
        Notification result with delivery status
    """
    # Always succeed for demo purposes
    message_id = f"MSG-{random.randint(100000, 999999)}"
    
    return {
        "delivered": True,
        "message_id": message_id,
        "channel": channel,
        "timestamp": datetime.now().isoformat(),
        "recipient": email if channel == "email" else phone
    }


@dataclass
class NotificationResult:
    """Result from sending a notification."""
    delivered: bool
    message_id: str
    channel: str  # "sms" | "email"


class NotificationTask(AgentTask[NotificationResult]):
    """Task to send booking confirmation via SMS and email."""
    
    def __init__(self, chat_ctx=None):
        # Load reading guidelines
        reading_guidelines = load_reading_guidelines()
        
        instructions = f"""
{reading_guidelines if reading_guidelines else ''}

{'-' * 50}

You are sending a booking confirmation to the customer.
            
The confirmation has been prepared and will include:
- Booking reference number
- Lesson date, time, and location
- Instructor name
- Equipment details
- What to bring (gear checklist)
- Cancellation policy
- Contact information
            
Your job is simply to confirm that the notification was sent successfully.
Keep it brief: "Perfect! I've sent your confirmation to [email] and [phone]. 
You should receive it within a few minutes."

When reading the email and phone number, follow the reading guidelines above.
"""
        super().__init__(
            instructions=instructions,
            chat_ctx=chat_ctx,
        )
        self._userdata = None
    
    async def on_enter(self) -> None:
        """Called when task starts."""
        self._userdata = self.session.userdata
        
        # Generate message content
        message_content = self._generate_confirmation_message()
        
        # Send mock notifications
        email_result = mock_send_notification(
            email=self._userdata.email,
            phone=self._userdata.phone,
            message=message_content,
            channel="email"
        )
        
        sms_result = mock_send_notification(
            email=self._userdata.email,
            phone=self._userdata.phone,
            message=f"Your surf lesson is confirmed! Booking: {self._userdata.booking_id}. Check your email for details.",
            channel="sms"
        )
        
        # Store results for confirmation
        self._email_result = email_result
        self._sms_result = sms_result
        
        # Auto-complete the task
        # Note: Main agent should inform user about confirmation being sent
        result = NotificationResult(
            delivered=self._email_result['delivered'],
            message_id=self._email_result['message_id'],
            channel=self._email_result['channel']
        )
        self.complete(result)
    
    def _generate_confirmation_message(self) -> str:
        """Generate the full confirmation message content."""
        ud = self._userdata
        
        message = f"""
DOHENY SURF DESK - BOOKING CONFIRMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Booking Reference: {ud.booking_id}
Customer: {ud.name}

LESSON DETAILS:
• Date: {ud.preferred_date}
• Time: {ud.preferred_time}
• Duration: 2 hours
• Location: {ud.spot_location}
• Instructor: {ud.instructor_name}

EQUIPMENT PROVIDED:
• Surfboard: {ud.board_size}
• Wetsuit: {ud.wetsuit_size}
{f'• Accessories: {", ".join(ud.accessories)}' if ud.accessories else ''}

{format_gear_checklist()}

CANCELLATION POLICY:
Free cancellation up to 24 hours before your lesson.
Cancel or reschedule by calling (949) 555-SURF or replying to this email.

PAYMENT:
Total Paid: ${ud.total_amount:.2f}
Payment Status: {ud.payment_status}

DIRECTIONS:
{ud.spot_location} - We'll meet at the main lifeguard tower.
Arrive 15 minutes early for gear fitting.

Questions? Call us at (949) 555-SURF (7873)
or email info@dohenysurfdesk.com

See you in the water! 🏄
- Doheny Surf Desk
"""
        return message
    
    @function_tool
    async def confirm_notification_sent(self) -> str:
        """Confirm that notification was successfully sent."""
        # Return email notification result (primary channel)
        result = NotificationResult(
            delivered=self._email_result['delivered'],
            message_id=self._email_result['message_id'],
            channel=self._email_result['channel']
        )
        self.complete(result)
        
        return (
            f"Confirmation notification sent successfully to {self._userdata.email} and {self._userdata.phone}. "
            f"The task is complete."
        )

