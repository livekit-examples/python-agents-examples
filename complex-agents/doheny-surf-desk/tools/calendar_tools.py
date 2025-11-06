"""Mock calendar and instructor availability tools."""
import random
from datetime import datetime, timedelta
from typing import List, Dict


def get_mock_availability(date: str, time_preference: str, spot: str) -> List[Dict]:
    """Get mock availability for instructors.
    
    Args:
        date: Preferred date (e.g., "tomorrow", "Saturday", "June 15")
        time_preference: Preferred time (e.g., "morning", "afternoon", "7am")
        spot: Surf spot location
        
    Returns:
        List of available slots with instructor details
    """
    instructors = [
        {"name": "Jake Sullivan", "specialty": "beginners", "rating": 4.9},
        {"name": "Maria Rodriguez", "specialty": "intermediate", "rating": 4.8},
        {"name": "Chris Johnson", "specialty": "advanced", "rating": 5.0},
        {"name": "Sarah Chen", "specialty": "kids", "rating": 4.9},
    ]
    
    # Parse time preference to generate realistic slots
    if "morning" in time_preference.lower() or "early" in time_preference.lower():
        base_hours = [6, 7, 8, 9]
    elif "afternoon" in time_preference.lower():
        base_hours = [13, 14, 15, 16]
    else:
        # Default: give a few morning and afternoon options
        base_hours = [7, 9, 14, 16]
    
    # Generate 3-4 available slots
    slots = []
    available_instructors = random.sample(instructors, min(3, len(instructors)))
    
    for i, hour in enumerate(base_hours[:3]):
        instructor = available_instructors[i % len(available_instructors)]
        time_str = f"{hour:02d}:00"
        
        # Mock tide conditions
        if hour < 10:
            tide = "Low tide" if hour < 8 else "Rising tide"
        else:
            tide = "High tide" if hour > 14 else "Mid tide"
        
        slot = {
            "time": time_str,
            "instructor": instructor["name"],
            "specialty": instructor["specialty"],
            "rating": instructor["rating"],
            "tide_condition": tide,
            "price": 79 if hour < 8 else 89,  # Early bird discount
            "available": True
        }
        slots.append(slot)
    
    return slots


def check_slot_availability(date: str, time: str, instructor: str) -> bool:
    """Check if a specific slot is available.
    
    Args:
        date: Date of lesson
        time: Time of lesson
        instructor: Instructor name
        
    Returns:
        True if available, False otherwise
    """
    # 95% of the time, slot is available for demo purposes
    return random.random() > 0.05


def create_mock_booking(
    customer_name: str,
    date: str,
    time: str,
    spot: str,
    instructor: str,
    experience: str
) -> Dict:
    """Create a mock booking record.
    
    Args:
        customer_name: Customer's name
        date: Lesson date
        time: Lesson time
        spot: Surf spot location
        instructor: Assigned instructor
        experience: Customer experience level
        
    Returns:
        Booking confirmation dictionary
    """
    booking_id = f"SURF-{random.randint(1000, 9999)}"
    
    return {
        "booking_id": booking_id,
        "customer_name": customer_name,
        "date": date,
        "time": time,
        "spot": spot,
        "instructor": instructor,
        "experience_level": experience,
        "duration": "2 hours",
        "status": "confirmed",
        "cancellation_deadline": "24 hours before lesson",
        "created_at": datetime.now().isoformat()
    }

