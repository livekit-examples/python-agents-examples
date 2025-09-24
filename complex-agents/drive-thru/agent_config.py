"""Configuration for drive-thru agent."""

from database import COMMON_INSTRUCTIONS, menu_instructions

from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel


def build_instructions(userdata):
    """Build agent instructions from menu items."""
    instructions = (
        COMMON_INSTRUCTIONS
        + "\n\n"
        + menu_instructions("drink", items=userdata.drink_items)
        + "\n\n"
        + menu_instructions("combo_meal", items=userdata.combo_items)
        + "\n\n"
        + menu_instructions("happy_meal", items=userdata.happy_items)
        + "\n\n"
        + menu_instructions("regular", items=userdata.regular_items)
    )
    if userdata.sauce_items:
        instructions += "\n\n" + menu_instructions("sauce", items=userdata.sauce_items)
    
    return instructions


def get_stt_config():
    """Get STT configuration."""
    return deepgram.STT(
        model="nova-3",
        keyterms=[
            "Big Mac",
            "McFlurry",
            "McCrispy",
            "McNuggets",
            "Meal",
            "Sundae",
            "Oreo",
            "Jalapeno Ranch",
        ],
        mip_opt_out=True,
    )


def get_llm_config():
    """Get LLM configuration."""
    return openai.LLM(model="gpt-4o", parallel_tool_calls=False, temperature=0.45)


def get_tts_config():
    """Get TTS configuration."""
    return cartesia.TTS(voice="f786b574-daa5-4673-aa0c-cbe3e8534c02", speed="fast")
    # Alternative TTS option:
    # return elevenlabs.TTS(
    #     model="eleven_turbo_v2_5",
    #     voice_id="21m00Tcm4TlvDq8ikWAM",
    #     voice_settings=elevenlabs.VoiceSettings(
    #         speed=1.15, stability=0.5, similarity_boost=0.75
    #     ),
    # )


def get_turn_detection_config():
    """Get turn detection configuration."""
    return MultilingualModel()


def get_vad_config():
    """Get VAD configuration."""
    return silero.VAD.load()