"""
---
title: Hedra Avatar with Realtime
category: avatars
tags: [hedra, avatar, static_image, openai_realtime]
difficulty: intermediate
description: Visual avatar using Hedra with OpenAI Realtime model integration
demonstrates:
  - Hedra avatar session with dynamic image selection
  - OpenAI Realtime model for low-latency conversation
  - Minimal agent configuration with realtime model
  - Avatar participant identity management
---
"""

from dotenv import load_dotenv

from livekit import agents
from livekit.agents import (
    get_job_context,
)
from livekit.agents.voice import AgentSession, Agent
from livekit.plugins import (
    openai,
    silero,
    hedra,
)

from PIL import Image
import os

load_dotenv()

class StaticAvatarAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful voice AI assistant with a visual avatar."
        )


async def entrypoint(ctx: agents.JobContext):
    avatar_dir = os.path.dirname(os.path.abspath(__file__))
    avatar_image = None
    
    for ext in ['.png', '.jpg', '.jpeg']:
        image_path = os.path.join(avatar_dir, f'avatar{ext}')
        if os.path.exists(image_path):
            avatar_image = Image.open(image_path)
            break
    
    if not avatar_image:
        raise FileNotFoundError("No avatar image found. Please place an avatar.png, avatar.jpg, or avatar.jpeg in the avatars directory.")
    
    job_context = get_job_context()
    avatar_identity = "static-avatar"
    avatar_session = hedra.AvatarSession(
        avatar_participant_identity=avatar_identity,
        avatar_image=avatar_image,
    )

    session = AgentSession(
        llm=openai.realtime.RealtimeModel(),
        vad=silero.VAD.load()
    )
    
    await avatar_session.start(
        session, room=job_context.room
    )

    await session.start(
        room=ctx.room,
        agent=StaticAvatarAgent()
    )

    await session.generate_reply()


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))