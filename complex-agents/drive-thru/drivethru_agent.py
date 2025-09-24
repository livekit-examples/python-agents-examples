"""
---
title: Drive-Thru Order Agent
category: complex-agents
tags: [ordering_system, modular_tools, rpc_handlers, background_audio, state_management]
difficulty: advanced
description: Restaurant drive-thru ordering system with modular tools and order management
demonstrates:
  - Modular tool organization for menu items
  - Dynamic tool generation based on menu data
  - Order state management with add/remove/list operations
  - Background audio playback during session
  - RPC handler registration for external control
  - Structured userdata for session state
---
"""

"""Main drive-thru agent implementation."""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

from agent_config import build_instructions
from rpc_handlers import register_rpc_handlers
from session_setup import Userdata, new_userdata, setup_background_audio, setup_session
from tools.management_tools import complete_order, list_order_items, remove_order_item
from tools.order_tools import (
    build_combo_order_tool,
    build_happy_order_tool,
    build_regular_order_tool,
)

from livekit.agents import Agent, JobContext, WorkerOptions, cli

load_dotenv()


class DriveThruAgent(Agent):
    """Drive-thru ordering agent with modular tool organization."""

    def __init__(self, *, userdata: Userdata) -> None:
        instructions = build_instructions(userdata)
        tools = [
            build_regular_order_tool(
                userdata.regular_items,
                userdata.drink_items,
                userdata.sauce_items
            ),
            build_combo_order_tool(
                userdata.combo_items,
                userdata.drink_items,
                userdata.sauce_items
            ),
            build_happy_order_tool(
                userdata.happy_items,
                userdata.drink_items,
                userdata.sauce_items
            ),
            remove_order_item,
            list_order_items,
            complete_order,
        ]

        super().__init__(
            instructions=instructions,
            tools=tools,
        )


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the drive-thru agent."""
    await ctx.connect()

    userdata = await new_userdata()
    userdata.room = ctx.room
    register_rpc_handlers(ctx.room, userdata)
    session = setup_session(userdata)
    background_audio = setup_background_audio()
    await session.start(agent=DriveThruAgent(userdata=userdata), room=ctx.room)
    await background_audio.start(room=ctx.room, agent_session=session)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))