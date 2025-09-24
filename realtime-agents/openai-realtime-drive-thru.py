"""
---
title: Drive-Thru Order System (Duplicate)
category: realtime-agents
tags: [duplicate_example, ordering_system]
difficulty: advanced
description: Duplicate of realtime/openai-realtime-drive-thru.py
demonstrates:
  - Same drive-thru ordering implementation
  - Duplicate for testing purposes
  - Full menu and order management
---
"""

import librosa
import random, math
import numpy as np
import os
from typing import AsyncIterable, List, Dict, Any, Optional
from dotenv import load_dotenv
from pathlib import Path
from livekit.agents.llm import function_tool
from livekit import agents, rtc
from livekit.agents import utils, mcp
from livekit.agents.voice import AgentSession, Agent, RunContext
from livekit.plugins import (
    openai,
    silero
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from dataclasses import dataclass, field
import json

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')


@dataclass
class MenuItem:
    name: str
    price: float
    category: str
    can_be_combo: bool = False
    sizes: List[str] = field(default_factory=list)
    extras: List[str] = field(default_factory=list)


@dataclass
class OrderItem:
    menu_item: MenuItem
    quantity: int = 1
    size: Optional[str] = None
    is_combo: bool = False
    extras: List[str] = field(default_factory=list)
    special_requests: List[str] = field(default_factory=list)
    
    @property
    def total_price(self) -> float:
        base_price = self.menu_item.price
        # Size pricing
        if self.size == "large":
            base_price *= 1.3
        elif self.size == "small":
            base_price *= 0.8
        # Combo adds drink and fries for $2.99
        if self.is_combo:
            base_price += 2.99
        # Extras are $0.50 each
        base_price += len(self.extras) * 0.50
        return base_price * self.quantity


@dataclass
class DriveThruUserData:
    order_items: List[OrderItem] = field(default_factory=list)
    current_item_context: Optional[Dict[str, Any]] = None
    last_mentioned_item: Optional[str] = None
    order_state: str = "taking_order"  # taking_order, confirming_order, payment, completed


# Menu database
MENU_ITEMS = {
    "burger": MenuItem("Burger", 8.99, "main", True, ["small", "regular", "large"], ["cheese", "bacon", "extra patty"]),
    "cheeseburger": MenuItem("Cheeseburger", 9.49, "main", True, ["small", "regular", "large"], ["bacon", "extra cheese", "extra patty"]),
    "chicken sandwich": MenuItem("Chicken Sandwich", 7.99, "main", True, ["regular", "spicy"], ["cheese", "bacon"]),
    "chicken strips": MenuItem("Chicken Strips", 6.99, "main", True, ["3 piece", "5 piece", "8 piece"], ["extra sauce"]),
    "fries": MenuItem("Fries", 2.99, "side", False, ["small", "medium", "large"], ["cheese sauce", "chili"]),
    "onion rings": MenuItem("Onion Rings", 3.49, "side", False, ["small", "large"], []),
    "soda": MenuItem("Soda", 1.99, "drink", False, ["small", "medium", "large"], []),
    "cola": MenuItem("Cola", 1.99, "drink", False, ["small", "medium", "large"], []),
    "coke": MenuItem("Coke", 1.99, "drink", False, ["small", "medium", "large"], []),
    "pepsi": MenuItem("Pepsi", 1.99, "drink", False, ["small", "medium", "large"], []),
    "sprite": MenuItem("Sprite", 1.99, "drink", False, ["small", "medium", "large"], []),
    "water": MenuItem("Water", 0.99, "drink", False, ["bottle"], []),
    "shake": MenuItem("Shake", 3.99, "dessert", False, ["small", "large"], ["chocolate", "vanilla", "strawberry"]),
    "milkshake": MenuItem("Milkshake", 3.99, "dessert", False, ["small", "large"], ["chocolate", "vanilla", "strawberry"]),
    "apple pie": MenuItem("Apple Pie", 2.49, "dessert", False, [], ["a la mode"]),
}


class DriveThruAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="""
You are a friendly drive-thru order taker at a fast food restaurant. Your job is to:
1. Take customer orders accurately
2. Suggest combos when appropriate (burger/sandwich + fries + drink saves money)
3. Clarify ambiguous requests
4. Confirm orders before finalizing
5. Handle modifications and special requests

Be conversational and helpful. When customers are vague (like "give me a burger" without specifying type or size), 
use your tools to add items with reasonable defaults, but always confirm. Use "regular" size as default if not specified.

IMPORTANT: Always use the appropriate tools to manage the order. Don't just talk about adding items - actually use the tools!
""")

    @function_tool
    async def add_item(self, context: RunContext[DriveThruUserData], 
                      item_name: str, 
                      quantity: int = 1,
                      size: Optional[str] = None,
                      make_it_a_combo: bool = False,
                      extras: Optional[List[str]] = None,
                      special_requests: Optional[str] = None):
        """
        Add an item to the current order. Use this whenever a customer orders something.
        
        Args:
            item_name: Name of the menu item (e.g., "burger", "cheeseburger", "fries")
            quantity: How many of this item
            size: Size of the item (e.g., "small", "medium", "large", "regular")
            make_it_a_combo: Whether to make this a combo meal (adds fries and drink)
            extras: List of extras to add (e.g., ["cheese", "bacon"])
            special_requests: Any special preparation requests
        """
        # Find the menu item (fuzzy matching)
        item_key = item_name.lower().strip()
        menu_item = None
        
        # Direct match first
        if item_key in MENU_ITEMS:
            menu_item = MENU_ITEMS[item_key]
        else:
            # Fuzzy match
            for key, item in MENU_ITEMS.items():
                if item_key in key or key in item_key:
                    menu_item = item
                    break
        
        if not menu_item:
            return f"Sorry, I couldn't find '{item_name}' on our menu. We have burgers, chicken sandwiches, chicken strips, fries, drinks, and desserts."
        
        # Create order item
        order_item = OrderItem(
            menu_item=menu_item,
            quantity=quantity,
            size=size or "regular",
            is_combo=make_it_a_combo and menu_item.can_be_combo,
            extras=extras or [],
            special_requests=[special_requests] if special_requests else []
        )
        
        context.userdata.order_items.append(order_item)
        context.userdata.last_mentioned_item = menu_item.name
        
        response = f"Added {quantity} {menu_item.name}"
        if size:
            response += f" ({size})"
        if order_item.is_combo:
            response += " as a combo"
        if extras:
            response += f" with {', '.join(extras)}"
        
        # Print order state after adding item
        self._print_order_state(context)
        
        return response

    @function_tool
    async def modify_last_item(self, context: RunContext[DriveThruUserData],
                              new_quantity: Optional[int] = None,
                              new_size: Optional[str] = None,
                              add_extras: Optional[List[str]] = None,
                              remove_extras: Optional[List[str]] = None,
                              make_combo: Optional[bool] = None,
                              special_request: Optional[str] = None):
        """
        Modify the most recently added item. Use this when customer says things like
        "actually, make that large" or "add cheese to that" or "make it a combo".
        
        Args:
            new_quantity: Change the quantity
            new_size: Change the size
            add_extras: Extras to add
            remove_extras: Extras to remove
            make_combo: Whether to make/unmake it a combo
            special_request: Add a special request
        """
        if not context.userdata.order_items:
            return "No items in the order to modify."
        
        last_item = context.userdata.order_items[-1]
        modifications = []
        
        if new_quantity is not None:
            last_item.quantity = new_quantity
            modifications.append(f"quantity to {new_quantity}")
        
        if new_size is not None:
            last_item.size = new_size
            modifications.append(f"size to {new_size}")
        
        if add_extras:
            for extra in add_extras:
                if extra not in last_item.extras:
                    last_item.extras.append(extra)
            modifications.append(f"added {', '.join(add_extras)}")
        
        if remove_extras:
            for extra in remove_extras:
                if extra in last_item.extras:
                    last_item.extras.remove(extra)
            modifications.append(f"removed {', '.join(remove_extras)}")
        
        if make_combo is not None:
            if make_combo and last_item.menu_item.can_be_combo:
                last_item.is_combo = True
                modifications.append("made it a combo")
            elif not make_combo:
                last_item.is_combo = False
                modifications.append("removed combo")
        
        if special_request:
            last_item.special_requests.append(special_request)
            modifications.append(f"special request: {special_request}")
        
        if modifications:
            # Print order state after modification
            self._print_order_state(context)
            return f"Updated {last_item.menu_item.name}: {', '.join(modifications)}"
        else:
            return "No modifications made."

    @function_tool
    async def remove_item(self, context: RunContext[DriveThruUserData],
                         item_name: Optional[str] = None,
                         item_index: Optional[int] = None):
        """
        Remove an item from the order. Can specify by name or by position (1-based index).
        
        Args:
            item_name: Name of the item to remove
            item_index: Position of the item to remove (1 for first item, 2 for second, etc.)
        """
        if not context.userdata.order_items:
            return "No items in the order to remove."
        
        if item_index is not None:
            # Convert to 0-based index
            idx = item_index - 1
            if 0 <= idx < len(context.userdata.order_items):
                removed = context.userdata.order_items.pop(idx)
                # Print order state after removal
                self._print_order_state(context)
                return f"Removed {removed.menu_item.name} from the order."
            else:
                return f"Invalid item number. Order has {len(context.userdata.order_items)} items."
        
        elif item_name:
            # Find by name
            item_name_lower = item_name.lower()
            for i, order_item in enumerate(context.userdata.order_items):
                if item_name_lower in order_item.menu_item.name.lower():
                    removed = context.userdata.order_items.pop(i)
                    # Print order state after removal
                    self._print_order_state(context)
                    return f"Removed {removed.menu_item.name} from the order."
            return f"Couldn't find '{item_name}' in the order."
        
        else:
            # Remove last item
            removed = context.userdata.order_items.pop()
            # Print order state after removal
            self._print_order_state(context)
            return f"Removed {removed.menu_item.name} from the order."

    @function_tool
    async def change_item_quantity(self, context: RunContext[DriveThruUserData],
                                  item_identifier: str,
                                  new_quantity: int):
        """
        Change the quantity of a specific item. Use this when customer says things like
        "I want 3 burgers instead of 2" or "change the fries to 2 orders".
        
        Args:
            item_identifier: Name or description of the item to change
            new_quantity: The new quantity
        """
        item_lower = item_identifier.lower()
        
        for order_item in context.userdata.order_items:
            if item_lower in order_item.menu_item.name.lower():
                old_qty = order_item.quantity
                order_item.quantity = new_quantity
                # Print order state after quantity change
                self._print_order_state(context)
                return f"Changed {order_item.menu_item.name} from {old_qty} to {new_quantity}."
        
        return f"Couldn't find '{item_identifier}' in the order to update quantity."

    @function_tool
    async def make_everything_combo(self, context: RunContext[DriveThruUserData]):
        """
        Convert all eligible items in the order to combos. Use when customer says
        "make everything a combo" or "combo all of those".
        """
        converted = []
        for item in context.userdata.order_items:
            if item.menu_item.can_be_combo and not item.is_combo:
                item.is_combo = True
                converted.append(item.menu_item.name)
        
        if converted:
            # Print order state after converting to combos
            self._print_order_state(context)
            return f"Made these items combos: {', '.join(converted)}"
        else:
            return "No items to convert to combos."

    @function_tool
    async def add_to_everything(self, context: RunContext[DriveThruUserData],
                               addition: str):
        """
        Add something to all applicable items. Use when customer says things like
        "add cheese to everything" or "make everything large".
        
        Args:
            addition: What to add (e.g., "cheese", "large", "extra sauce")
        """
        addition_lower = addition.lower()
        modified = []
        
        # Check if it's a size
        if addition_lower in ["small", "medium", "large", "regular"]:
            for item in context.userdata.order_items:
                if item.menu_item.sizes:
                    item.size = addition_lower
                    modified.append(item.menu_item.name)
        else:
            # Assume it's an extra
            for item in context.userdata.order_items:
                if addition_lower in [e.lower() for e in item.menu_item.extras]:
                    if addition_lower not in [e.lower() for e in item.extras]:
                        item.extras.append(addition)
                        modified.append(item.menu_item.name)
        
        if modified:
            # Print order state after adding to everything
            self._print_order_state(context)
            return f"Added {addition} to: {', '.join(modified)}"
        else:
            return f"Couldn't add {addition} to any items."

    @function_tool
    async def get_order_summary(self, context: RunContext[DriveThruUserData]):
        """
        Get a summary of the current order with prices. Use this to confirm the order
        or when customer asks what they've ordered.
        """
        if not context.userdata.order_items:
            return "No items in the order yet."
        
        summary_lines = ["Current order:"]
        total = 0.0
        
        for i, item in enumerate(context.userdata.order_items, 1):
            line = f"{i}. {item.quantity}x {item.menu_item.name}"
            if item.size != "regular":
                line += f" ({item.size})"
            if item.is_combo:
                line += " - Combo"
            if item.extras:
                line += f" with {', '.join(item.extras)}"
            if item.special_requests:
                line += f" [{', '.join(item.special_requests)}]"
            line += f" - ${item.total_price:.2f}"
            summary_lines.append(line)
            total += item.total_price
        
        summary_lines.append(f"\nTotal: ${total:.2f}")
        return "\n".join(summary_lines)

    @function_tool
    async def clear_order(self, context: RunContext[DriveThruUserData]):
        """
        Clear the entire order and start over. Use when customer wants to cancel
        everything and start fresh.
        """
        context.userdata.order_items.clear()
        context.userdata.current_item_context = None
        context.userdata.last_mentioned_item = None
        # Print order state after clearing
        self._print_order_state(context)
        return "Order cleared. Starting fresh!"

    @function_tool
    async def finalize_order(self, context: RunContext[DriveThruUserData]):
        """
        Finalize the order and proceed to payment. Use this when the customer
        confirms they're done ordering.
        """
        if not context.userdata.order_items:
            return "No items in the order to finalize."
        
        total = sum(item.total_price for item in context.userdata.order_items)
        context.userdata.order_state = "payment"
        
        # Print order state after finalizing
        self._print_order_state(context)
        
        return f"Order finalized! Your total is ${total:.2f}. Please proceed to the payment window."

    @function_tool
    async def apply_discount(self, context: RunContext[DriveThruUserData],
                           discount_code: str):
        """
        Apply a discount code to the order. Common codes might be "student", "senior",
        "employee", etc.
        
        Args:
            discount_code: The discount code to apply
        """
        # Simulate some discount codes
        discounts = {
            "student": 0.10,
            "senior": 0.15,
            "employee": 0.20,
            "happy": 0.05,  # Happy hour
            "birthday": 0.25
        }
        
        if discount_code.lower() in discounts:
            discount_pct = discounts[discount_code.lower()]
            total = sum(item.total_price for item in context.userdata.order_items)
            discount_amt = total * discount_pct
            new_total = total - discount_amt
            return f"Applied {discount_code} discount: {discount_pct*100:.0f}% off. New total: ${new_total:.2f} (saved ${discount_amt:.2f})"
        else:
            return f"Sorry, '{discount_code}' is not a valid discount code."

    def _print_order_state(self, context: RunContext[DriveThruUserData]):
        """Helper method to print the current order state"""
        print("\n=== Current Order State ===")
        if not context.userdata.order_items:
            print("No items in order")
        else:
            total = 0.0
            for i, item in enumerate(context.userdata.order_items, 1):
                line = f"{i}. {item.quantity}x {item.menu_item.name}"
                if item.size != "regular":
                    line += f" ({item.size})"
                if item.is_combo:
                    line += " - Combo"
                if item.extras:
                    line += f" with {', '.join(item.extras)}"
                if item.special_requests:
                    line += f" [{', '.join(item.special_requests)}]"
                line += f" - ${item.total_price:.2f}"
                print(line)
                total += item.total_price
            print(f"Total: ${total:.2f}")
        print(f"Order State: {context.userdata.order_state}")
        print("==========================\n")


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    session = AgentSession[DriveThruUserData](
        userdata=DriveThruUserData(),
        llm=openai.realtime.RealtimeModel(
            model="gpt-4o-realtime-preview-2025-06-03"
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel()
    )

    await session.start(
        room=ctx.room,
        agent=DriveThruAssistant()
    )

    await session.generate_reply()


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))