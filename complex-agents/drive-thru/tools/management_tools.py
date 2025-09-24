"""
---
title: Drive-Thru Order Management Tools
category: drive-thru
tags: [order_tools, rpc_integration, checkout_flow]
difficulty: intermediate
description: Order management tools for drive-thru system
demonstrates:
  - Order removal with validation
  - Order listing and formatting
  - Checkout completion flow
  - RPC integration for UI updates
  - Error handling with ToolError
  - Order total calculation
---
"""

"""Order management tools for drive-thru agent."""

import json
import logging
from typing import Annotated

from pydantic import Field

from livekit.agents import RunContext, ToolError, function_tool


logger = logging.getLogger("drive-thru-agent")


@function_tool
async def remove_order_item(
    ctx: RunContext,
    order_id: Annotated[
        list[str],
        Field(
            description="A list of internal `order_id`s of the items to remove. Use `list_order_items` to look it up if needed."
        ),
    ],
) -> str:
    """
    Removes one or more items from the user's order using their `order_id`s.

    Useful when the user asks to cancel or delete existing items (e.g., "Remove the cheeseburger").

    If the `order_id`s are unknown, call `list_order_items` first to retrieve them.
    """
    not_found = [oid for oid in order_id if oid not in ctx.userdata.order.items]
    if not_found:
        raise ToolError(f"error: no item(s) found with order_id(s): {', '.join(not_found)}")

    removed_items = [await ctx.userdata.order.remove(oid) for oid in order_id]
    
    return "Removed items:\n" + "\n".join(item.model_dump_json() for item in removed_items)


@function_tool
async def list_order_items(ctx: RunContext) -> str:
    """
    Retrieves the current list of items in the user's order, including each item's internal `order_id`.

    Helpful when:
    - An `order_id` is required before modifying or removing an existing item.
    - Confirming details or contents of the current order.

    Examples:
    - User requests modifying an item, but the item's `order_id` is unknown (e.g., "Change the fries from small to large").
    - User requests removing an item, but the item's `order_id` is unknown (e.g., "Remove the cheeseburger").
    - User asks about current order details (e.g., "What's in my order so far?").
    """
    items = ctx.userdata.order.items.values()
    if not items:
        return "The order is empty"

    return "\n".join(item.model_dump_json() for item in items)


@function_tool
async def complete_order(ctx: RunContext) -> str:
    """
    Completes the current order and directs the customer to the next window.

    Call this when:
    - The customer confirms their order is complete
    - They say things like "That's all", "That's it", "I'm done", "Complete my order"
    - They're ready to pay and proceed to the next window

    This will show the total and direct them to drive to the payment window.
    """
    order_items = ctx.userdata.order.get_formatted_order()
    if not order_items:
        return "Cannot complete order - the order is empty. Please add items first."

    total_price = sum(item["price"] for item in order_items)

    # Send RPC to show checkout screen
    try:
        room = ctx.userdata.room
        if room:
            # Send to all participants
            remote_participants = list(room.remote_participants.values())
            for participant in remote_participants:
                await room.local_participant.perform_rpc(
                    destination_identity=participant.identity,
                    method="show_checkout",
                    payload=json.dumps({
                        "total_price": total_price,
                        "message": f"Your total is ${total_price:.2f}. Please drive to the next window!"
                    })
                )
    except Exception as e:
        logger.error(f"Failed to send checkout RPC: {e}")

    return f"Order completed! Total: ${total_price:.2f}. Please drive to the next window for payment."