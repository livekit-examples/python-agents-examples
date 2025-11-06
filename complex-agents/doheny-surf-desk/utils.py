"""Utility functions for Doheny Surf Desk."""
import yaml
from pathlib import Path
from datetime import datetime
import zoneinfo


def load_reading_guidelines() -> str:
    """Load reading guidelines from YAML file.
    
    Returns:
        Reading guidelines text, or empty string if file not found
    """
    guidelines_path = Path(__file__).parent / "prompts" / "reading_guidelines.yaml"
    if guidelines_path.exists():
        with open(guidelines_path, 'r') as f:
            guidelines_data = yaml.safe_load(f)
            return guidelines_data.get('prompt', '')
    return ''


def get_current_date() -> str:
    """Get current date and day of week for California/Los Angeles timezone.
    
    Returns:
        Single line with day of week and date
    """
    try:
        pacific_tz = zoneinfo.ZoneInfo("America/Los_Angeles")
        now = datetime.now(pacific_tz)
        return now.strftime("%A, %B %d, %Y")
    except Exception:
        now = datetime.utcnow()
        return now.strftime("%A, %B %d, %Y")


def load_prompt(filename: str, include_reading_guidelines: bool = True, **variables) -> str:
    """Load a prompt from a YAML file with variable substitution.
    
    Args:
        filename: Name of the YAML file (e.g., 'scheduler_prompt.yaml')
        include_reading_guidelines: If True, prepend reading guidelines
        **variables: Variables to substitute in the prompt (e.g., current_date="...")
        
    Returns:
        The prompt text with variables substituted
    """
    prompt_path = Path(__file__).parent / "prompts" / filename
    with open(prompt_path, 'r') as f:
        data = yaml.safe_load(f)
        prompt_text = data.get('prompt', '')
    
    if variables:
        prompt_text = prompt_text.format(**variables)
    
    if include_reading_guidelines:
        guidelines = load_reading_guidelines()
        if guidelines:
            prompt_text = f"{guidelines}\n\n{'-' * 50}\n\n{prompt_text}"
    
    return prompt_text


def format_booking_summary(userdata) -> str:
    """Format booking information into a readable summary.
    
    Args:
        userdata: SurfBookingData instance
        
    Returns:
        Formatted booking summary string
    """
    lines = []
    
    if userdata.name:
        lines.append(f"Name: {userdata.name}")
    if userdata.email:
        lines.append(f"Email: {userdata.email}")
    if userdata.phone:
        lines.append(f"Phone: {userdata.phone}")
    if userdata.age:
        lines.append(f"Age: {userdata.age}")
    if userdata.experience_level:
        lines.append(f"Experience: {userdata.experience_level}")
    if userdata.preferred_date:
        lines.append(f"Date: {userdata.preferred_date}")
    if userdata.preferred_time:
        lines.append(f"Time: {userdata.preferred_time}")
    if userdata.spot_location:
        lines.append(f"Location: {userdata.spot_location}")
    if userdata.board_size:
        lines.append(f"Board: {userdata.board_size}")
    if userdata.wetsuit_size:
        lines.append(f"Wetsuit: {userdata.wetsuit_size}")
    if userdata.total_amount:
        lines.append(f"Total: ${userdata.total_amount:.2f}")
    
    return "\n".join(lines)


def format_gear_checklist() -> str:
    """Return a standard gear checklist for surf lessons.
    
    Returns:
        Checklist as formatted string
    """
    return """What to bring:
- Swimsuit (wear under wetsuit)
- Towel
- Sunscreen (reef-safe)
- Water bottle
- Change of clothes

We provide:
- Surfboard
- Wetsuit
- Leash
- Wax
- First aid kit"""

