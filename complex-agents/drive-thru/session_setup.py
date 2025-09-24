"""
---
title: Drive-Thru Session Setup
category: drive-thru
tags: [session_management, userdata_initialization, background_audio_setup]
difficulty: intermediate
description: Session setup utilities for drive-thru ordering system
demonstrates:
  - Userdata initialization with menu items
  - Session configuration with agent configs
  - Background audio player setup
  - Database integration for menu loading
  - Max tool steps configuration
---
"""

"""Session setup for drive-thru agent."""

import os
from dataclasses import dataclass

from agent_config import (
    get_llm_config,
    get_stt_config,
    get_tts_config,
    get_turn_detection_config,
    get_vad_config,
)
from database import FakeDB, MenuItem
from order import OrderState

from livekit.agents import AgentSession, AudioConfig, BackgroundAudioPlayer


@dataclass
class Userdata:
    order: OrderState
    drink_items: list[MenuItem]
    combo_items: list[MenuItem]
    happy_items: list[MenuItem]
    regular_items: list[MenuItem]
    sauce_items: list[MenuItem] = None
    room: any = None


async def new_userdata() -> Userdata:
    """Create and initialize user data."""
    fake_db = FakeDB()
    drink_items = await fake_db.list_drinks()
    combo_items = await fake_db.list_combo_meals()
    happy_items = await fake_db.list_happy_meals()
    regular_items = await fake_db.list_regulars()
    sauce_items = await fake_db.list_sauces()

    order_state = OrderState(items={})
    userdata = Userdata(
        order=order_state,
        drink_items=drink_items,
        combo_items=combo_items,
        happy_items=happy_items,
        regular_items=regular_items,
        sauce_items=sauce_items,
    )
    return userdata


def setup_session(userdata: Userdata) -> AgentSession[Userdata]:
    """Setup the agent session with all configurations."""
    return AgentSession[Userdata](
        userdata=userdata,
        stt=get_stt_config(),
        llm=get_llm_config(),
        tts=get_tts_config(),
        turn_detection=get_turn_detection_config(),
        vad=get_vad_config(),
        max_tool_steps=10,
    )


def setup_background_audio() -> BackgroundAudioPlayer:
    """Setup background audio player."""
    return BackgroundAudioPlayer(
        ambient_sound=AudioConfig(
            str(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bg_noise.mp3")),
            volume=1.0,
        ),
    )