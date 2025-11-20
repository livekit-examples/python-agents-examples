"""Billing agent for payment processing and booking finalization."""
from livekit.agents.llm import function_tool
from livekit.agents.beta.workflows import TaskGroup

from .base_agent import BaseAgent, RunContext_T
from utils import load_prompt
from tools.payment_tools import calculate_lesson_cost, process_mock_payment
from tasks.notification_task import NotificationTask
from tasks.consent_task import ConsentTask
from tasks.payment_details_task import PaymentDetailsTask


class BillingAgent(BaseAgent):
    """Agent responsible for payment processing and booking finalization."""
    
    def __init__(self, chat_ctx=None):
        # Note: We need LLM for tasks to use session.generate_reply()
        # Tasks will use the session's LLM, not the agent's LLM
        super().__init__(
            instructions=load_prompt('billing_prompt.yaml'),
            chat_ctx=chat_ctx,
        )
    
    async def on_enter(self) -> None:
        """Called when agent starts - calculate total first, then wait for user to proceed with payment."""
        userdata = self.session.userdata
        
        # Calculate total immediately so it's available
        import random
        is_weekend = random.choice([True, False])
        breakdown = calculate_lesson_cost(
            time=userdata.preferred_time or "09:00",
            is_weekend=is_weekend,
            accessories=userdata.accessories
        )
        userdata.total_amount = breakdown['total']
        
        # Greet and let user know they can ask about cost or proceed to payment
        await self.session.say(
            f"Great! I'm ready to finalize your booking. "
            f"The total comes to ${userdata.total_amount:.2f}. "
            f"Would you like to see a detailed breakdown, or are you ready to proceed with payment?"
        )
        
        # Note: We don't start TaskGroup here - it will be started when user is ready to pay
        # This allows calculate_total and other functions to work freely
    
    @function_tool
    async def calculate_total(self, context: RunContext_T) -> str:
        """Calculate the total cost of the lesson with breakdown.
        
        Args:
            context: RunContext with userdata
            
        Returns:
            Detailed cost breakdown
        """
        userdata = context.userdata
        
        import random
        is_weekend = random.choice([True, False])
        breakdown = calculate_lesson_cost(
            time=userdata.preferred_time or "09:00",
            is_weekend=is_weekend,
            accessories=userdata.accessories
        )
        
        userdata.total_amount = breakdown['total']
        
        response = "COST_BREAKDOWN:\n"
        response += f"2-Hour Surf Lesson: ${breakdown['lesson']:.2f}\n"
        
        for discount in breakdown['discounts']:
            response += f"{discount['name']}: ${discount['amount']:.2f}\n"
        
        for surcharge in breakdown['surcharges']:
            response += f"{surcharge['name']}: +${surcharge['amount']:.2f}\n"
        
        if breakdown['accessories']:
            response += "\nAccessories:\n"
            for accessory in breakdown['accessories']:
                response += f"  {accessory['name']}: ${accessory['amount']:.2f}\n"
        
        response += f"\nSubtotal: ${breakdown['subtotal']:.2f}\n"
        response += f"Tax (7.75%): ${breakdown['tax']:.2f}\n"
        response += f"TOTAL: ${breakdown['total']:.2f}\n"
        response += "Tell user: Present this breakdown to them."
        
        return response
    
    @function_tool
    async def apply_discount(
        self,
        context: RunContext_T,
        promo_code: str
    ) -> str:
        """Apply a promotional discount code.
        
        Args:
            context: RunContext with userdata
            promo_code: Promo code to apply
            
        Returns:
            Result of promo code application
        """
        from tools.payment_tools import apply_promo_code
        
        userdata = context.userdata
        
        if not userdata.total_amount:
            return "BLOCKED: Calculate total first before applying discount."
        
        result = apply_promo_code(promo_code, userdata.total_amount)
        
        if result['valid']:
            userdata.total_amount = result['new_total']
            return (f"PROMO_APPLIED: Code '{result['code']}' - {result['description']}. "
                   f"New total: ${result['new_total']:.2f} "
                   f"(saved ${result['discount_amount']:.2f}). Tell user: Promo code applied successfully.")
        else:
            return f"INVALID_PROMO: {result.get('error', '')}. Tell user: That promo code isn't valid."
    
    @function_tool
    async def check_minor_consent(self, context: RunContext_T) -> str:
        """Check if minor consent is required and collected.
        
        Args:
            context: RunContext with userdata
            
        Returns:
            Consent status message
        """
        userdata = context.userdata
        
        if not userdata.is_minor:
            return "CONSENT_STATUS: No guardian consent needed - customer is 18 or older."
        
        if userdata.guardian_consent:
            return (f"CONSENT_STATUS: Guardian consent already obtained from {userdata.guardian_name}. "
                   "Ready to proceed with payment.")
        
        return (f"CONSENT_REQUIRED: {userdata.name} is under 18. Use run_consent_task to collect guardian consent before payment.")
    
    @function_tool
    async def run_consent_task(self, context: RunContext_T) -> str:
        """Run the ConsentTask to collect guardian approval.
        
        Args:
            context: RunContext with userdata
            
        Returns:
            Result of consent collection
        """
        await context.wait_for_playout()
        consent_result = await ConsentTask(chat_ctx=self.chat_ctx)
        
        if consent_result.approved:
            return (f"CONSENT_OBTAINED: Guardian consent received from {consent_result.guardian_name}. "
                   "Proceed with payment.")
        else:
            return (f"CONSENT_DENIED: Cannot proceed without guardian consent. "
                   f"Place booking on hold. Tell user: Guardian can call (949) 555-SURF to complete consent and payment.")
    
    @function_tool
    async def process_payment(
        self,
        context: RunContext_T,
        card_info: str = None
    ) -> str:
        """Process the payment for the booking.
        
        If payment details are not collected yet, this will run TaskGroup to collect them first.
        
        Args:
            context: RunContext with userdata
            card_info: Optional card information (last 4 digits)
            
        Returns:
            Payment result message
        """
        userdata = context.userdata
        
        if not userdata.total_amount:
            return "BLOCKED: Calculate total first before processing payment."
        
        if userdata.is_minor and not userdata.guardian_consent:
            await context.wait_for_playout()
            consent_result = await ConsentTask(chat_ctx=self.chat_ctx)
            
            if not consent_result.approved:
                await self.session.say(
                    f"No problem. Your guardian can call us at (949) 555-SURF to complete the booking. "
                    f"Your booking ID is {userdata.booking_id}."
                )
                return "BLOCKED: Guardian consent required but not obtained."
            
            userdata.guardian_consent = True
            userdata.guardian_name = consent_result.guardian_name
            userdata.guardian_contact = consent_result.guardian_contact
        
        if not hasattr(userdata, '_payment_details_collected') or not userdata._payment_details_collected:
            await context.wait_for_playout()
            payment_details_result = await PaymentDetailsTask()
            userdata._payment_details_collected = True
            card_info = f"ending in {payment_details_result.card_number[-4:]}"
        
        # Process payment
        payment_result = process_mock_payment(
            amount=userdata.total_amount,
            customer_name=userdata.name,
            card_info=card_info
        )
        
        if payment_result['success']:
            userdata.payment_status = "paid"
            
            await self.session.say(
                f"Perfect! Your payment of ${payment_result['amount']:.2f} has been processed. "
                f"Transaction ID: {payment_result['transaction_id']}."
            )
            
            await self.session.say("Let me send you a confirmation email.")
            notification_result = await NotificationTask(chat_ctx=self.chat_ctx)
            
            if notification_result.delivered:
                await self.session.say(
                    f"All done! Confirmation sent to {userdata.email}. "
                    f"See you on {userdata.preferred_date} at {userdata.preferred_time}! "
                    f"Your booking ID is {userdata.booking_id}."
                )
            else:
                await self.session.say(
                    f"Your booking is confirmed! You should receive the confirmation email shortly. "
                    f"Your booking ID is {userdata.booking_id}."
                )
            
            return f"PAYMENT_SUCCESS: ${payment_result['amount']:.2f} charged. Transaction ID: {payment_result['transaction_id']}"
        else:
            userdata.payment_status = "failed"
            await self.session.say(
                f"I'm sorry, the payment was declined: {payment_result['error_message']}. "
                f"Would you like to try a different card, or I can hold this booking for 15 minutes?"
            )
            
            return (f"PAYMENT_FAILED: {payment_result['error_message']}\n"
                   f"Tell user: Payment was declined. Ask if they want to try again or hold booking for 15 minutes.")
    
    @function_tool
    async def send_confirmation(self, context: RunContext_T) -> str:
        """Send booking confirmation via NotificationTask.
        
        Args:
            context: RunContext with userdata
            
        Returns:
            Confirmation send result
        """
        userdata = context.userdata
        
        if userdata.payment_status != "paid":
            return "BLOCKED: Payment must be completed before sending confirmation."
        
        await context.wait_for_playout()
        notification_result = await NotificationTask(chat_ctx=self.chat_ctx)
        
        if notification_result.delivered:
            return (f"CONFIRMATION_SENT: To {userdata.email} "
                   f"(Message ID: {notification_result.message_id}). "
                   f"Tell user: Confirmation sent, should arrive within a few minutes.")
        else:
            return ("CONFIRMATION_FAILED: Issue sending confirmation. "
                   "Tell user: Booking is confirmed, you'll receive the details via email shortly.")
    
    @function_tool
    async def hold_booking(
        self,
        context: RunContext_T,
        duration_minutes: int = 15
    ) -> str:
        """Place booking on hold while customer resolves payment issues.
        
        Args:
            context: RunContext with userdata
            duration_minutes: How long to hold the booking
            
        Returns:
            Hold confirmation
        """
        userdata = context.userdata
        
        userdata.payment_status = "pending"
        
        return (f"BOOKING_ON_HOLD: Booking #{userdata.booking_id} held for {duration_minutes} minutes. "
               f"Instructor: {userdata.instructor_name}. "
               f"Tell user: Booking is reserved. Call (949) 555-SURF when ready to complete payment.")
    
    @function_tool
    async def return_to_frontdesk(self, context: RunContext_T) -> BaseAgent:
        """Return customer to front desk for new inquiry or assistance.
        
        Use this after booking is complete or if customer wants to ask additional questions.
        
        Args:
            context: RunContext with userdata
            
        Returns:
            FrontDeskAgent instance
        """
        await self.session.say(
            "Of course! Let me transfer you back to our front desk. Is there anything else I can help you with?"
        )
        
        # Get FrontDeskAgent from personas registry
        frontdesk = context.userdata.personas.get("frontdesk")
        if frontdesk:
            # Create new instance with current chat context
            from agents.frontdesk_agent import FrontDeskAgent
            return FrontDeskAgent(chat_ctx=self.chat_ctx)
        else:
            return "ERROR: FrontDesk agent not available in personas registry."

