"""Mock tide and weather condition tools."""
import random
from typing import Dict, List
import aiohttp
import asyncio
from livekit.agents.llm.tool_context import ToolError

# Doheny Beach is in Dana Point, California (love this place!)
DANA_POINT_LATITUDE = 33.4670
DANA_POINT_LONGITUDE = -117.6981

async def get_weather_forecast(
    forecast_days: float
) -> str:
    url = "https://api.open-meteo.com/v1/forecast?daily=temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum,precipitation_probability_max,wind_speed_10m_max&timezone=auto"
    payload = {
        "latitude": DANA_POINT_LATITUDE,
        "longitude": DANA_POINT_LONGITUDE,
        "temperature_unit": "fahrenheit",
        "forecast_days": forecast_days,
    }

    try:
        session = aiohttp.ClientSession()
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(url, timeout=timeout, params=payload) as resp:
            body = await resp.text()
            if resp.status >= 400:
                raise ToolError(f"error: HTTP {resp.status}: {body}")
            return body
    except ToolError:
        raise
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        raise ToolError(f"error: {e!s}") from e
    finally:
        await session.close()


def get_tide_schedule(date: str, spot: str) -> Dict:
    """Get mock tide schedule for a specific date and spot.
    
    Args:
        date: Date to check
        spot: Surf spot location
        
    Returns:
        Tide schedule with times and heights
    """
    # Generate realistic tide times (approximately 6 hours apart)
    base_hour = random.randint(4, 6)  # Start with early morning low tide
    
    tides = [
        {"time": f"{base_hour:02d}:30", "type": "Low", "height": "1.2 ft"},
        {"time": f"{(base_hour + 6) % 24:02d}:15", "type": "High", "height": "5.8 ft"},
        {"time": f"{(base_hour + 12) % 24:02d}:45", "type": "Low", "height": "0.8 ft"},
        {"time": f"{(base_hour + 18) % 24:02d}:30", "type": "High", "height": "6.2 ft"},
    ]
    
    return {
        "date": date,
        "spot": spot,
        "tides": tides,
        "best_surf_times": [
            f"{(base_hour + 2) % 24:02d}:00-{(base_hour + 4) % 24:02d}:00 (rising tide)",
            f"{(base_hour + 8) % 24:02d}:00-{(base_hour + 10) % 24:02d}:00 (mid-high tide)"
        ]
    }


def get_surf_conditions(date: str, spot: str) -> Dict:
    """Get mock surf conditions for planning.
    
    Args:
        date: Date to check
        spot: Surf spot location
        
    Returns:
        Surf condition details
    """
    # Generate realistic conditions
    wave_heights = [
        "1-2 ft (small, perfect for beginners)",
        "2-3 ft (fun, good for all levels)",
        "3-4 ft (moderate, intermediate+)",
        "4-6 ft (challenging, advanced only)",
    ]
    
    # Bias toward beginner-friendly conditions
    wave_height = random.choice(wave_heights[:3])
    
    wind_conditions = [
        "Light offshore (excellent)",
        "Calm (good)",
        "Light onshore (fair)",
        "Variable (moderate)",
    ]
    
    water_temps = {
        "Doheny": "62°F",
        "San Onofre": "60°F",
        "Trestles": "59°F"
    }
    
    return {
        "date": date,
        "spot": spot,
        "wave_height": wave_height,
        "wave_period": f"{random.randint(10, 16)} seconds",
        "wind": random.choice(wind_conditions),
        "water_temp": water_temps.get(spot, "60°F"),
        "wetsuit_recommendation": "3/2mm full suit",
        "crowd_level": random.choice(["Light", "Moderate", "Busy"]),
        "overall_rating": random.choice(["Excellent", "Good", "Fair"]),
        "warnings": []  # No warnings for demo (Observer will handle special cases)
    }


def check_weather_warnings(date: str, spot: str) -> List[str]:
    """Check for weather warnings or alerts.
    
    Args:
        date: Date to check
        spot: Surf spot location
        
    Returns:
        List of warning messages (empty if no warnings)
    """
    # 10% chance of a warning for testing Observer agent
    if random.random() < 0.1:
        warnings = [
            f"High surf advisory: Waves 6-8ft expected on {date}",
            f"Strong rip current warning for {spot}",
            f"Wind advisory: Gusts up to 25mph expected",
        ]
        return [random.choice(warnings)]
    
    return []


def get_best_lesson_times(date: str, spot: str, experience: str) -> List[str]:
    """Get recommended lesson times based on conditions and experience.
    
    Args:
        date: Date for lesson
        spot: Surf spot location
        experience: Customer experience level
        
    Returns:
        List of recommended time slots with rationale
    """
    tide_schedule = get_tide_schedule(date, spot)
    recommendations = []
    
    if experience == "beginner":
        recommendations.append(
            "6:00am-8:00am: Early bird special, calm conditions, smaller crowds"
        )
        recommendations.append(
            "9:00am-11:00am: Mid-morning, rising tide, great for learning"
        )
    else:
        recommendations.append(
            "7:00am-9:00am: Best waves, offshore winds, good energy"
        )
        recommendations.append(
            "2:00pm-4:00pm: Afternoon session, solid swell, fewer beginners"
        )
    
    return recommendations

