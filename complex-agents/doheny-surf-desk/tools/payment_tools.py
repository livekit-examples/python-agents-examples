"""Mock payment processing tools."""
import random
from datetime import datetime
from typing import Dict, Optional


PRICING = {
    "lesson_base": 89.00,
    "early_bird_discount": -10.00,  # Before 8am
    "weekend_surcharge": 15.00,
    "booties": 5.00,
    "gloves": 3.00,
    "rash_guard": 10.00,
}


def calculate_lesson_cost(
    time: str,
    is_weekend: bool = False,
    accessories: list = None
) -> Dict:
    """Calculate total lesson cost with breakdown.
    
    Args:
        time: Lesson time (e.g., "07:00")
        is_weekend: Whether lesson is on weekend
        accessories: List of additional accessories
        
    Returns:
        Cost breakdown dictionary
    """
    accessories = accessories or []
    
    breakdown = {
        "lesson": PRICING["lesson_base"],
        "discounts": [],
        "surcharges": [],
        "accessories": [],
    }
    
    # Check for early bird discount
    try:
        hour = int(time.split(":")[0])
        if hour < 8:
            breakdown["discounts"].append({
                "name": "Early Bird Special",
                "amount": PRICING["early_bird_discount"]
            })
    except:
        pass
    
    # Weekend surcharge
    if is_weekend:
        breakdown["surcharges"].append({
            "name": "Weekend Premium",
            "amount": PRICING["weekend_surcharge"]
        })
    
    # Add accessories
    for accessory in accessories:
        accessory_lower = accessory.lower()
        if "bootie" in accessory_lower and "booties" in PRICING:
            breakdown["accessories"].append({
                "name": "Booties",
                "amount": PRICING["booties"]
            })
        elif "glove" in accessory_lower and "gloves" in PRICING:
            breakdown["accessories"].append({
                "name": "Gloves",
                "amount": PRICING["gloves"]
            })
        elif "rash" in accessory_lower and "rash_guard" in PRICING:
            breakdown["accessories"].append({
                "name": "Rash Guard",
                "amount": PRICING["rash_guard"]
            })
    
    # Calculate subtotal
    subtotal = breakdown["lesson"]
    for discount in breakdown["discounts"]:
        subtotal += discount["amount"]  # Discounts are negative
    for surcharge in breakdown["surcharges"]:
        subtotal += surcharge["amount"]
    for accessory in breakdown["accessories"]:
        subtotal += accessory["amount"]
    
    breakdown["subtotal"] = subtotal
    breakdown["tax"] = round(subtotal * 0.0775, 2)  # CA sales tax
    breakdown["total"] = round(subtotal + breakdown["tax"], 2)
    
    return breakdown


def process_mock_payment(
    amount: float,
    customer_name: str,
    card_info: Optional[str] = None
) -> Dict:
    """Process a mock payment transaction.
    
    Args:
        amount: Payment amount
        customer_name: Customer name
        card_info: Optional card information
        
    Returns:
        Payment result with success status and details
    """
    # 90% success rate for realistic testing
    success = random.random() > 0.1
    
    transaction_id = f"TXN-{random.randint(10000, 99999)}"
    
    if success:
        return {
            "success": True,
            "transaction_id": transaction_id,
            "amount": amount,
            "customer": customer_name,
            "timestamp": datetime.now().isoformat(),
            "payment_method": card_info or "Credit Card ending in 1234",
            "status": "completed",
            "receipt_url": f"https://dohenysurfdesk.com/receipts/{transaction_id}"
        }
    else:
        return {
            "success": False,
            "transaction_id": transaction_id,
            "amount": amount,
            "customer": customer_name,
            "timestamp": datetime.now().isoformat(),
            "error_code": "insufficient_funds",
            "error_message": "Card declined - insufficient funds",
            "status": "failed",
            "retry_allowed": True
        }


def apply_promo_code(code: str, current_total: float) -> Dict:
    """Apply a promotional code to the booking.
    
    Args:
        code: Promo code
        current_total: Current booking total
        
    Returns:
        Discount information if valid
    """
    promo_codes = {
        "FIRSTWAVE": {"type": "percentage", "value": 15, "description": "15% off first lesson"},
        "SUMMER2024": {"type": "fixed", "value": 10, "description": "$10 off any lesson"},
        "LOCALRIDER": {"type": "percentage", "value": 10, "description": "10% locals discount"},
    }
    
    code_upper = code.upper()
    if code_upper in promo_codes:
        promo = promo_codes[code_upper]
        if promo["type"] == "percentage":
            discount_amount = round(current_total * (promo["value"] / 100), 2)
        else:
            discount_amount = promo["value"]
        
        return {
            "valid": True,
            "code": code_upper,
            "description": promo["description"],
            "discount_amount": discount_amount,
            "new_total": round(current_total - discount_amount, 2)
        }
    
    return {
        "valid": False,
        "code": code,
        "error": "Invalid promo code"
    }


def refund_booking(booking_id: str, amount: float) -> Dict:
    """Process a mock refund.
    
    Args:
        booking_id: Booking ID to refund
        amount: Refund amount
        
    Returns:
        Refund confirmation
    """
    return {
        "success": True,
        "refund_id": f"REF-{random.randint(10000, 99999)}",
        "booking_id": booking_id,
        "amount": amount,
        "status": "processed",
        "estimated_arrival": "3-5 business days",
        "timestamp": datetime.now().isoformat()
    }

