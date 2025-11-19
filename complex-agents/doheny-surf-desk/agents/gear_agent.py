"""Gear agent for recommending surfboard and wetsuit equipment."""
from livekit.agents.llm import function_tool

from .base_agent import BaseAgent, RunContext_T
from utils import load_prompt

# Some random business logic here to make it more interesting :-)
class GearAgent(BaseAgent):
    """Agent responsible for equipment recommendations and sizing."""
    
    def __init__(self, chat_ctx=None):
        super().__init__(
            instructions=load_prompt('gear_prompt.yaml'),
            chat_ctx=chat_ctx,
        )
    
    @function_tool
    async def record_measurements(
        self,
        context: RunContext_T,
        height_cm: int = None,
        weight_kg: int = None
    ) -> str:
        """Record customer height and weight for equipment sizing.
        
        Args:
            context: RunContext with userdata
            height_cm: Height in centimeters
            weight_kg: Weight in kilograms
            
        Returns:
            Confirmation message
        """
        userdata = context.userdata
        
        if height_cm:
            userdata.height_cm = height_cm
        if weight_kg:
            userdata.weight_kg = weight_kg
        
        parts = []
        if height_cm:
            parts.append(f"{height_cm}cm tall")
        if weight_kg:
            parts.append(f"{weight_kg}kg")
        
        return f"MEASUREMENTS_RECORDED: {' and '.join(parts)}"
    
    @function_tool
    async def recommend_board(self, context: RunContext_T) -> str:
        """Recommend surfboard based on customer profile.
        
        Args:
            context: RunContext with userdata
            
        Returns:
            Board recommendation with rationale
        """
        userdata = context.userdata
        
        if userdata.experience_level == "beginner":
            if userdata.weight_kg and userdata.weight_kg > 80:
                board = "9'0\" Soft-top Longboard"
                reason = "Extra volume for stability, perfect for learning"
            else:
                board = "8'0\" Soft-top Funboard"
                reason = "Great stability and easy to paddle, ideal for beginners"
        elif userdata.experience_level == "intermediate":
            if userdata.weight_kg and userdata.weight_kg > 75:
                board = "7'6\" Epoxy Funboard"
                reason = "Good volume with maneuverability, great for progressing"
            else:
                board = "7'0\" Hybrid Shortboard"
                reason = "Responsive yet forgiving, perfect for your level"
        else:  # advanced
            board = "6'2\" High-performance Shortboard"
            reason = "Maximum maneuverability and responsiveness"
        
        userdata.board_size = board
        
        return f"Recommend to user: {board}. {reason}"
    
    @function_tool
    async def recommend_wetsuit(self, context: RunContext_T) -> str:
        """Recommend wetsuit based on conditions and measurements.
        
        Args:
            context: RunContext with userdata
            
        Returns:
            Wetsuit recommendation with rationale
        """
        userdata = context.userdata
        
        spot = userdata.spot_location or "Doheny"
        if spot == "Doheny":
            water_temp = 62
        elif spot == "San Onofre":
            water_temp = 60
        else:
            water_temp = 59
        
        if water_temp >= 62:
            thickness = "3/2mm"
            description = "perfect for current water temps"
        else:
            thickness = "4/3mm"
            description = "extra warmth for cooler water"
        
        if userdata.height_cm:
            if userdata.height_cm < 165:
                size = "Small"
            elif userdata.height_cm < 175:
                size = "Medium"
            elif userdata.height_cm < 185:
                size = "Large"
            else:
                size = "X-Large"
        else:
            size = "Medium"
        
        wetsuit = f"{size} {thickness} Fullsuit"
        userdata.wetsuit_size = wetsuit
        
        return (f"Recommend to user: {wetsuit} - {description}. "
               f"Water temp at {spot} is around {water_temp}°F.")
    
    @function_tool
    async def add_accessories(
        self,
        context: RunContext_T,
        items: str
    ) -> str:
        """Add accessories to the gear package.
        
        Args:
            context: RunContext with userdata
            items: Comma-separated list of accessories (booties, gloves, rash guard)
            
        Returns:
            Confirmation with pricing
        """
        userdata = context.userdata
        
        accessories = [item.strip().lower() for item in items.split(',')]
        
        added = []
        total_cost = 0.0
        
        for accessory in accessories:
            if "bootie" in accessory:
                added.append("Booties ($5)")
                total_cost += 5.0
                userdata.accessories.append("Booties")
            elif "glove" in accessory:
                added.append("Gloves ($3)")
                total_cost += 3.0
                userdata.accessories.append("Gloves")
            elif "rash" in accessory or "guard" in accessory:
                added.append("Rash Guard ($10)")
                total_cost += 10.0
                userdata.accessories.append("Rash Guard")
        
        if not added:
            return "ASK_USER: Which accessories would you like? Options: Booties, gloves, or rash guard."
        
        return f"ACCESSORIES_ADDED: {', '.join(added)}. Total accessories: ${total_cost:.2f}"
    
    @function_tool
    async def finalize_gear_selection(self, context: RunContext_T) -> str:
        """Confirm gear selection is complete.
        
        Args:
            context: RunContext with userdata
            
        Returns:
            Summary of selected gear
        """
        userdata = context.userdata
        
        if not userdata.board_size or not userdata.wetsuit_size:
            return "INCOMPLETE: Board and wetsuit selection required before finalizing."
        
        summary = f"GEAR_SELECTION_COMPLETE:\n"
        summary += f"Surfboard: {userdata.board_size}\n"
        summary += f"Wetsuit: {userdata.wetsuit_size}\n"
        
        if userdata.accessories:
            summary += f"Accessories: {', '.join(userdata.accessories)}\n"
        
        summary += f"Location: {userdata.spot_location}\n"
        summary += f"Tell user: Their gear will be ready at {userdata.spot_location}."
        
        return summary
    
    @function_tool
    async def transfer_to_billing(self, context: RunContext_T) -> BaseAgent:
        """Transfer to Billing Agent after gear is selected.
        
        Args:
            context: RunContext with userdata
            
        Returns:
            BillingAgent instance
        """
        from agents.billing_agent import BillingAgent
        
        userdata = context.userdata
        
        if not userdata.is_gear_selected():
            return "BLOCKED: Complete board and wetsuit selection before transferring to billing."
        
        await self.session.say(
            "Awesome! You're all geared up. Now let's move on to the final step "
            "to finalize everything and get you confirmed!"
        )
        
        return BillingAgent(chat_ctx=self.chat_ctx)

