"""
---
title: Drive-Thru Order Placement Tools
category: drive-thru
tags: [dynamic_tool_generation, combo_meals, enum_validation, size_handling]
difficulty: advanced
description: Dynamic tool builders for different order types in drive-thru system
demonstrates:
  - Dynamic function tool generation
  - Enum validation from menu items
  - Complex parameter schemas with Pydantic
  - Size validation and error handling
  - Combo meal configuration
  - Happy meal ordering
  - Regular item ordering
  - Price and details tracking
---
"""

"""Order placement tools for drive-thru agent."""

from typing import Annotated, Literal

from pydantic import Field

from livekit.agents import FunctionTool, RunContext, ToolError, function_tool

from database import MenuItem, find_items_by_id
from order import OrderedCombo, OrderedHappy, OrderedRegular


def build_combo_order_tool(
    combo_items: list[MenuItem], 
    drink_items: list[MenuItem], 
    sauce_items: list[MenuItem] | None
) -> FunctionTool:
    """Build the combo meal ordering tool."""
    available_combo_ids = {item.id for item in combo_items}
    available_drink_ids = {item.id for item in drink_items}
    available_sauce_ids = {item.id for item in sauce_items} if sauce_items else set()

    @function_tool
    async def order_combo_meal(
        ctx: RunContext,
        meal_id: Annotated[
            str,
            Field(
                description="The ID of the combo meal the user requested.",
                json_schema_extra={"enum": list(available_combo_ids)},
            ),
        ],
        drink_id: Annotated[
            str,
            Field(
                description="The ID of the drink the user requested.",
                json_schema_extra={"enum": list(available_drink_ids)},
            ),
        ],
        drink_size: Literal["M", "L", "null"] | None,
        fries_size: Literal["M", "L"],
        sauce_id: Annotated[
            str | None,
            Field(
                description="The ID of the sauce the user requested. Optional.",
                json_schema_extra={"enum": list(available_sauce_ids) + [None]},
            ),
        ] = None,
    ) -> str:
        """
        Call this when the user orders a **Combo Meal**, like: "Number 4b with a large Sprite" or "I'll do a medium meal."

        Do not call this tool unless the user clearly refers to a known combo meal by name or number.
        Regular items like a single cheeseburger cannot be made into a meal unless such a combo explicitly exists.

        Only call this function once the user has clearly specified a drink as well as the food item — always ask for it if it's missing.
        The sauce is optional and can be omitted if the user does not request it.

        A meal can only be Medium or Large; Small is not an available option.
        Drink and fries sizes can differ (e.g., "large fries but a medium Coke").

        If the user says just "a large meal," assume both drink and fries are that size.

        When punching in the item, say something like "sure thing", or "yep absolutely", just something to acknowledge the order.
        Don't repeat the item name, just say something like "sure thing", or "yep absolutely".
        Don't say something like "Item XYZ coming right up!"
        """
        if not find_items_by_id(combo_items, meal_id):
            raise ToolError(f"error: the meal {meal_id} was not found")

        drink_sizes = find_items_by_id(drink_items, drink_id)
        if not drink_sizes:
            raise ToolError(f"error: the drink {drink_id} was not found")

        if drink_size == "null":
            drink_size = None

        available_sizes = list({item.size for item in drink_sizes if item.size})
        if drink_size is None and len(available_sizes) > 1:
            raise ToolError(
                f"error: {drink_id} comes with multiple sizes: {', '.join(available_sizes)}. "
                "Please clarify which size should be selected."
            )

        if drink_size is not None and not available_sizes:
            raise ToolError(
                f"error: size should not be specified for item {drink_id} as it does not support sizing options."
            )

        available_sizes = list({item.size for item in drink_sizes if item.size})
        if drink_size not in available_sizes:
            drink_size = None

        if sauce_id and not find_items_by_id(sauce_items, sauce_id):
            raise ToolError(f"error: the sauce {sauce_id} was not found")

        item = OrderedCombo(
            meal_id=meal_id,
            drink_id=drink_id,
            drink_size=drink_size,
            sauce_id=sauce_id,
            fries_size=fries_size,
        )
        
        # Get menu item details
        meal = find_items_by_id(combo_items, meal_id)[0]
        drink = find_items_by_id(drink_items, drink_id)[0] if drink_sizes else None
        sauce = find_items_by_id(sauce_items, sauce_id)[0] if sauce_id else None
        
        details = {
            "meal": meal.name,
            "drink": f"{drink.name} ({drink_size or 'Regular'})" if drink else "No drink",
            "fries": f"{fries_size} Fries"
        }
        if sauce:
            details["sauce"] = sauce.name
        
        await ctx.userdata.order.add(item, name=meal.name, price=meal.price, details=details)
        
        return f"The item was added: {item.model_dump_json()}"

    return order_combo_meal


def build_happy_order_tool(
    happy_items: list[MenuItem],
    drink_items: list[MenuItem],
    sauce_items: list[MenuItem] | None,
) -> FunctionTool:
    """Build the happy meal ordering tool."""
    available_happy_ids = {item.id for item in happy_items}
    available_drink_ids = {item.id for item in drink_items}
    available_sauce_ids = {item.id for item in sauce_items} if sauce_items else set()

    @function_tool
    async def order_happy_meal(
        ctx: RunContext,
        meal_id: Annotated[
            str,
            Field(
                description="The ID of the happy meal the user requested.",
                json_schema_extra={"enum": list(available_happy_ids)},
            ),
        ],
        drink_id: Annotated[
            str,
            Field(
                description="The ID of the drink the user requested.",
                json_schema_extra={"enum": list(available_drink_ids)},
            ),
        ],
        drink_size: Literal["S", "M", "L", "null"] | None,
        sauce_id: Annotated[
            str | None,
            Field(
                description="The ID of the sauce the user requested. Optional.",
                json_schema_extra={"enum": list(available_sauce_ids) + [None]},
            ),
        ] = None,
    ) -> str:
        """
        Call this when the user orders a **Happy Meal**, typically for children. These meals come with a main item, a drink, and optionally a sauce.

        The user must clearly specify a valid Happy Meal option (e.g., "Can I get a Happy Meal?").

        Before calling this tool:
        - Ensure the user has provided all required components: a valid meal, drink, and drink size.
        - Sauce is optional and can be omitted if the user does not request it.
        - If any required components are missing, prompt the user for the missing part before proceeding.

        Assume Small as default only if the user says "Happy Meal" and gives no size preference, but always ask for clarification if unsure.

        When punching in the item, say something like "sure thing", or "yep absolutely", just something to acknowledge the order.
        Don't repeat the item name, just say something like "sure thing", or "yep absolutely".
        Don't say something like "Item XYZ coming right up!"
        """
        if not find_items_by_id(happy_items, meal_id):
            raise ToolError(f"error: the meal {meal_id} was not found")

        drink_sizes = find_items_by_id(drink_items, drink_id)
        if not drink_sizes:
            raise ToolError(f"error: the drink {drink_id} was not found")

        if drink_size == "null":
            drink_size = None

        available_sizes = list({item.size for item in drink_sizes if item.size})
        if drink_size is None and len(available_sizes) > 1:
            raise ToolError(
                f"error: {drink_id} comes with multiple sizes: {', '.join(available_sizes)}. "
                "Please clarify which size should be selected."
            )

        if drink_size is not None and not available_sizes:
            drink_size = None

        if sauce_id and not find_items_by_id(sauce_items, sauce_id):
            raise ToolError(f"error: the sauce {sauce_id} was not found")

        item = OrderedHappy(
            meal_id=meal_id,
            drink_id=drink_id,
            drink_size=drink_size,
            sauce_id=sauce_id,
        )
        
        # Get menu item details
        meal = find_items_by_id(happy_items, meal_id)[0]
        drink = find_items_by_id(drink_items, drink_id)[0] if drink_sizes else None
        sauce = find_items_by_id(sauce_items, sauce_id)[0] if sauce_id else None
        
        details = {
            "meal": meal.name,
            "drink": f"{drink.name} ({drink_size or 'Regular'})" if drink else "No drink"
        }
        if sauce:
            details["sauce"] = sauce.name
        
        await ctx.userdata.order.add(item, name=meal.name, price=meal.price, details=details)
        
        return f"The item was added: {item.model_dump_json()}"

    return order_happy_meal


def build_regular_order_tool(
    regular_items: list[MenuItem],
    drink_items: list[MenuItem],
    sauce_items: list[MenuItem] | None,
) -> FunctionTool:
    """Build the regular item ordering tool."""
    all_items = regular_items + drink_items + (sauce_items or [])
    available_ids = {item.id for item in all_items}

    @function_tool
    async def order_regular_item(
        ctx: RunContext,
        item_id: Annotated[
            str,
            Field(
                description="The ID of the item the user requested.",
                json_schema_extra={"enum": list(available_ids)},
            ),
        ],
        size: Annotated[
            # models don't seem to understand `ItemSize | None`, adding the `null` inside the enum list as a workaround
            Literal["S", "M", "L", "null"] | None,
            Field(
                description="Size of the item, if applicable (e.g., 'S', 'M', 'L'), otherwise 'null'. "
            ),
        ] = "null",
    ) -> str:
        """
        Call this when the user orders **a single item on its own**, not as part of a Combo Meal or Happy Meal.

        The customer must provide clear and specific input. For example, item variants such as flavor must **always** be explicitly stated.

        The user might say—for example:
        - "Just the cheeseburger, no meal"
        - "A medium Coke"
        - "Can I get some ketchup?"
        - "Can I get a McFlurry Oreo?"

        When punching in the item, say something like "sure thing", or "yep absolutely", just something to acknowledge the order.
        Don't repeat the item name, just say something like "sure thing", or "yep absolutely".
        Don't say something like "Item XYZ coming right up!"
        """
        item_sizes = find_items_by_id(all_items, item_id)
        if not item_sizes:
            raise ToolError(f"error: {item_id} was not found.")

        if size == "null":
            size = None

        available_sizes = list({item.size for item in item_sizes if item.size})
        if size is None and len(available_sizes) > 1:
            raise ToolError(
                f"error: {item_id} comes with multiple sizes: {', '.join(available_sizes)}. "
                "Please clarify which size should be selected."
            )

        if size is not None and not available_sizes:
            size = None

        if (size and available_sizes) and size not in available_sizes:
            raise ToolError(
                f"error: unknown size {size} for {item_id}. Available sizes: {', '.join(available_sizes)}."
            )

        item = OrderedRegular(item_id=item_id, size=size)
        
        # Get menu item details
        menu_item = item_sizes[0]  # We already have the items from find_items_by_id
        
        details = {}
        if size:
            details["size"] = size
            
        name = menu_item.name
        if size:
            name = f"{size} {name}"
            
        await ctx.userdata.order.add(item, name=name, price=menu_item.price, details=details)
        
        return f"The item was added: {item.model_dump_json()}"

    return order_regular_item