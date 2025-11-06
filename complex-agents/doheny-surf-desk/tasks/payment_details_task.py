"""Payment details collection task."""
from dataclasses import dataclass
from livekit.agents import AgentTask
from livekit.agents.llm.tool_context import function_tool


@dataclass
class PaymentDetailsResult:
    """Result from payment details collection."""
    card_number: str
    cardholder_name: str
    cvv: str

# TODO: Update from https://github.com/livekit/agents/pull/3813/files later
class PaymentDetailsTask(AgentTask[PaymentDetailsResult]):
    """Task to collect credit card information."""
    
    def __init__(self):
        super().__init__(
            instructions="""You are collecting credit card information for payment.

Collect in this order:
1. Full card number (16 digits for Visa/Mastercard/Discover, 15 for Amex)
2. Name on the card
3. CVV security code (4 digits for Amex, 3 digits for others)

Ask for one piece of information at a time.
When you have all three, call record_payment_details().

IMPORTANT: 
- Keep responses SHORT (voice conversation)
- Read back the card number to confirm
- Amex: 15 digits, 4-digit CVV on front
- Visa/MC/Discover: 16 digits, 3-digit CVV on back"""
        )
        self._card_number = ""
        self._cardholder_name = ""
        self._cvv = ""
    
    async def on_enter(self) -> None:
        """Called when task starts."""
        await self.session.generate_reply(
            instructions="Ask for their full credit card number (15 or 16 digits)."
        )
    
    @function_tool()
    async def record_payment_details(
        self,
        card_number: str,
        cardholder_name: str,
        cvv: str
    ) -> str:
        """Record credit card details.
        
        Args:
            card_number: Full card number (15 for Amex, 16 for others)
            cardholder_name: Name on the card
            cvv: CVV security code (4 digits for Amex, 3 for others)
        """
        card_clean = card_number.replace(" ", "").replace("-", "")
        
        if not card_clean.isdigit() or len(card_clean) not in [15, 16]:
            return f"Invalid card number format. Should be 15 digits (Amex) or 16 digits. Try again."
        
        is_amex = len(card_clean) == 15 and card_clean[:2] in ['34', '37']
        
        if is_amex:
            if not cvv.isdigit() or len(cvv) != 4:
                return f"Invalid CVV. Amex requires 4 digits on the front of the card."
        else:
            if not cvv.isdigit() or len(cvv) != 3:
                return f"Invalid CVV. Should be 3 digits on the back of the card."
        
        if not cardholder_name or len(cardholder_name) < 2:
            return "Invalid name. Please provide the full name on the card."
        
        self._card_number = card_clean
        self._cardholder_name = cardholder_name
        self._cvv = cvv
        
        if len(card_clean) == 15:
            formatted_card = f"{card_clean[:4]} {card_clean[4:10]} {card_clean[10:]}"
        else:
            formatted_card = f"{card_clean[:4]} {card_clean[4:8]} {card_clean[8:12]} {card_clean[12:]}"
        
        await self.session.say(
            f"Perfect! Card number {formatted_card}, "
            f"CVV {cvv}, for {cardholder_name}. Processing payment now."
        )
        
        self.complete(PaymentDetailsResult(
            card_number=card_clean,
            cardholder_name=cardholder_name,
            cvv=cvv
        ))
        return "Payment details recorded. Task complete."

