"""Scheduler agent for booking lesson time slots."""
import json
from typing import Annotated
from livekit.agents.llm import function_tool
from numpy import number

from .base_agent import BaseAgent, RunContext_T
from utils import load_prompt
from tools.calendar_tools import get_mock_availability, create_mock_booking
from tools.tide_tools import get_tide_schedule, get_surf_conditions, get_weather_forecast


class SchedulerAgent(BaseAgent):
    """Agent responsible for finding and booking lesson time slots."""
    
    def __init__(self, chat_ctx=None):
        from utils import get_current_date
        super().__init__(
            instructions=load_prompt('scheduler_prompt.yaml', current_date=get_current_date()),
            chat_ctx=chat_ctx,
        )
    
    @function_tool
    async def check_availability(
        self,
        context: RunContext_T,
        date: str = None,
        time_preference: str = None,
        spot: str = None
    ) -> str:
        """Check instructor availability for lesson booking.
        
        Returns a BRIEF list of available times only. User can then ask for details about specific slots.
        
        Args:
            context: RunContext with userdata
            date: Preferred date (uses userdata if not provided)
            time_preference: Preferred time (uses userdata if not provided)
            spot: Surf spot (uses userdata if not provided)
            
        Returns:
            Brief list of available times
        """
        userdata = context.userdata
        
        check_date = date or userdata.preferred_date or "tomorrow"
        check_time = time_preference or userdata.preferred_time or "morning"
        check_spot = spot or userdata.spot_location or "Doheny"
        
        context.userdata._last_checked_date = check_date
        context.userdata._last_checked_time = check_time
        context.userdata._last_checked_spot = check_spot
        
        slots = get_mock_availability(check_date, check_time, check_spot)
        
        response = f"AVAILABLE_TIMES for {check_date} at {check_spot}:\n"
        times = [slot['time'] for slot in slots]
        response += f"{', '.join(times)}\n\n"
        
        response += (
            "IMPORTANT: Tell user ONLY the available times, like this:\n"
            f"'We have lessons available at {', '.join(times)}. Which time works best for you, "
            f"or would you like to hear more details about any of these slots?'\n\n"
            "DO NOT read all the details yet. Wait for them to ask about a specific time or request details."
        )
        
        return response
    
    @function_tool
    async def get_slot_details(
        self,
        context: RunContext_T,
        time: str
    ) -> str:
        """Get detailed information about a specific time slot.
        
        Use this when user asks for details about a specific time.
        
        Args:
            context: RunContext with userdata
            time: The time slot to get details for (e.g., "7:00 AM" or "07:00")
            
        Returns:
            Detailed information about that slot
        """
        userdata = context.userdata
        
        check_date = getattr(userdata, '_last_checked_date', userdata.preferred_date or "tomorrow")
        check_spot = getattr(userdata, '_last_checked_spot', userdata.spot_location or "Doheny")
        check_time = getattr(userdata, '_last_checked_time', "morning")
        
        slots = get_mock_availability(check_date, check_time, check_spot)
        conditions = get_surf_conditions(check_date, check_spot)
        
        requested_slot = None
        for slot in slots:
            if time.replace(' ', '').lower() in slot['time'].replace(' ', '').lower():
                requested_slot = slot
                break
        
        if not requested_slot:
            return f"ERROR: No slot found for {time}. Available times: {', '.join([s['time'] for s in slots])}"
        
        experience = userdata.experience_level.lower()
        specialty = requested_slot['specialty'].lower()
        
        suitability = ""
        if experience == 'beginner' and 'intermediate' in specialty:
            suitability = "⚠️ Note: This instructor specializes in intermediate - may not be ideal for beginners."
        elif experience == 'beginner' and ('beginner' in specialty or 'kids' in specialty):
            suitability = "✓ Great match for beginners!"
        elif experience == 'intermediate' and 'intermediate' in specialty:
            suitability = "✓ Perfect match for your level!"
        elif experience == 'advanced' and 'advanced' in specialty:
            suitability = "✓ Excellent for advanced surfers!"
        
        response = f"DETAILS for {requested_slot['time']} slot:\n\n"
        response += f"Instructor: {requested_slot['instructor']}\n"
        response += f"Specialty: {requested_slot['specialty']} specialist\n"
        response += f"Rating: {requested_slot['rating']}⭐\n"
        response += f"Conditions: {requested_slot['tide_condition']}, {conditions['wave_height']}\n"
        response += f"Price: ${requested_slot['price']}\n"
        if suitability:
            response += f"\n{suitability}\n"
        
        response += f"\nTell user: Present these details and ask if this slot works for them."
        
        return response
    
    @function_tool
    async def book_slot(
        self,
        context: RunContext_T,
        date: str,
        time: str,
        instructor: str,
        spot: str = None
    ) -> str:
        """Confirm and book a specific lesson slot.
        
        Args:
            context: RunContext with userdata
            date: Lesson date
            time: Lesson time (e.g., "07:00")
            instructor: Instructor name
            spot: Surf spot location
            
        Returns:
            Booking confirmation
        """
        userdata = context.userdata
        
        booking_spot = spot or userdata.spot_location or "Doheny"
        
        if userdata.booking_id and userdata.instructor_name:
            if userdata.instructor_name != instructor:
                return (
                    f"⚠️ BOOKING_CHANGE_DETECTED:\n"
                    f"Current booking: {userdata.instructor_name} at {userdata.preferred_time}\n"
                    f"Requested change: {instructor} at {time}\n\n"
                    f"IMPORTANT: Before proceeding, verify this change was explicitly requested.\n"
                    f"Tell user: 'Just to confirm - would you like me to change your booking from "
                    f"{userdata.instructor_name} to {instructor}? This will also change your time from "
                    f"{userdata.preferred_time} to {time}.'\n"
                    f"If they confirm, call book_slot again. If they did NOT request this change, "
                    f"apologize and keep the original booking."
                )
        
        available_slots = get_mock_availability(date, time.split(':')[0] + ":00" if ':' in time else time, booking_spot)
        
        instructor_found = None
        for slot in available_slots:
            if instructor.lower() in slot['instructor'].lower():
                instructor_found = slot
                break
        
        if instructor_found:
            specialty = instructor_found.get('specialty', '').lower()
            experience = userdata.experience_level.lower()
            
            if experience == 'beginner' and 'intermediate' in specialty:
                return (
                    f"⚠️ SKILL_MISMATCH_WARNING:\n"
                    f"Customer experience: {userdata.experience_level}\n"
                    f"Instructor specialty: {instructor_found['specialty']}\n\n"
                    f"SAFETY CONCERN: This instructor specializes in intermediate lessons, but the "
                    f"customer is a beginner. This is not recommended for safety reasons.\n"
                    f"Tell user: 'I notice {instructor} specializes in intermediate lessons, but you mentioned "
                    f"you're a beginner. For your safety and the best learning experience, I'd recommend "
                    f"an instructor who specializes in beginners. Would you like me to show you those options?'"
                )
        
        booking = create_mock_booking(
            customer_name=userdata.name,
            date=date,
            time=time,
            spot=booking_spot,
            instructor=instructor,
            experience=userdata.experience_level
        )
        
        userdata.booking_id = booking['booking_id']
        userdata.preferred_date = date
        userdata.preferred_time = time
        userdata.spot_location = booking_spot
        userdata.instructor_name = instructor
        
        return (f"✓ BOOKING_CONFIRMED:\n"
                f"Booking ID: {booking['booking_id']}\n"
                f"Date: {date} at {time}\n"
                f"Location: {booking_spot}\n"
                f"Instructor: {instructor}\n"
                f"Duration: 2 hours\n"
                f"Cancellation policy: Free cancellation up to 24 hours before lesson.\n"
                f"Tell user: Booking confirmed successfully!")
    
    @function_tool
    async def suggest_alternative_times(
        self,
        context: RunContext_T,
        reason: str = "No availability at requested time"
    ) -> str:
        """Suggest alternative time slots when preferred time isn't available.
        
        Uses brief format - just times, not all details.
        
        Args:
            context: RunContext with userdata
            reason: Reason why alternative is needed
            
        Returns:
            Brief alternative suggestions
        """
        userdata = context.userdata
        
        morning_slots = get_mock_availability(
            userdata.preferred_date or "tomorrow",
            "morning",
            userdata.spot_location or "Doheny"
        )
        
        afternoon_slots = get_mock_availability(
            userdata.preferred_date or "tomorrow",
            "afternoon",
            userdata.spot_location or "Doheny"
        )
        
        morning_times = [slot['time'] for slot in morning_slots[:3]]
        afternoon_times = [slot['time'] for slot in afternoon_slots[:3]]
        
        response = f"ALTERNATIVE_TIMES:\n\n"
        response += f"MORNING: {', '.join(morning_times)}\n"
        response += f"AFTERNOON: {', '.join(afternoon_times)}\n\n"
        
        response += (
            "IMPORTANT: Tell user these alternative times briefly:\n"
            f"'We have morning slots at {', '.join(morning_times)} "
            f"and afternoon slots at {', '.join(afternoon_times)}. "
            f"Early morning lessons often have the best conditions. "
            f"Which time interests you, or would you like details about any of these?'\n\n"
            "Wait for them to choose or ask for details before showing full information."
        )
        
        return response

    @function_tool(name="get_weather_forecast")
    async def get_weather_forecast(self, context: RunContext_T, forecast_days: int) -> str:
        """Get weather forecast for the next few days.
        
        Args:
            context: RunContext with userdata
            forecast_days: Number of days to forecast
        """
        weather_forecast = await get_weather_forecast(forecast_days)
        return json.loads(weather_forecast)
    
    @function_tool
    async def get_surf_report(self, context: RunContext_T, date: str, spot: str) -> str:
        """Get detailed surf conditions for planning.
        
        Args:
            context: RunContext with userdata
            date: Date to check
            spot: Surf spot location
            
        Returns:
            Detailed surf report
        """
        conditions = get_surf_conditions(date, spot)
        tide_schedule = get_tide_schedule(date, spot)
        
        report = f"SURF_REPORT: {spot} on {date}:\n\n"
        report += f"Waves: {conditions['wave_height']} @ {conditions['wave_period']}\n"
        report += f"Wind: {conditions['wind']}\n"
        report += f"Water temp: {conditions['water_temp']} - {conditions['wetsuit_recommendation']}\n"
        report += f"Crowd level: {conditions['crowd_level']}\n"
        report += f"Overall: {conditions['overall_rating']} conditions\n\n"
        
        report += "TIDE SCHEDULE:\n"
        for tide in tide_schedule['tides']:
            report += f"• {tide['time']} - {tide['type']} tide ({tide['height']})\n"
        
        report += f"\nBest times: {', '.join(tide_schedule['best_surf_times'])}\n"
        report += "Tell user: Present this surf report to them."
        
        return report
    
    @function_tool
    async def transfer_to_gear(self, context: RunContext_T) -> BaseAgent:
        """Transfer to Gear Agent after booking is confirmed.
        
        Args:
            context: RunContext with userdata
            
        Returns:
            GearAgent instance
        """
        from agents.gear_agent import GearAgent
        
        userdata = context.userdata
        
        if not userdata.is_booking_complete():
            return "BLOCKED: Confirm a booking time slot before transferring to gear selection."
        
        await self.session.say(
            "Perfect! Your lesson is all set. Now let's move on to the next step and "
            "get you set up with the right surfboard and wetsuit."
        )
        
        return GearAgent(chat_ctx=self.chat_ctx)

