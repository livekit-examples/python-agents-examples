"""
---
title: Dynamically Created Avatar
category: avatars
tags: [avatar, openai, deepgram]
difficulty: intermediate
description: Shows how to create an avatar dynamically in an agent.
demonstrates:
  - Making parallel calls to an LLM while speaking to the voice agent
  - Creating an avatar dynamically in an agent
  - Creating a new hedra avatar session using a custom image
  - A function tool that uses a docstring to describe the tool for the LLM to use
---
"""

from dotenv import load_dotenv
from openai import AsyncOpenAI
from livekit import agents, api
from livekit.agents import (
    AgentSession,
    Agent,
    RoomInputOptions,
    function_tool,
    RunContext,
    get_job_context,
)
from livekit.plugins import (
    openai,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
    hedra,
)

from livekit.plugins.turn_detector.multilingual import MultilingualModel
from PIL import Image
import random
import base64
from dataclasses import dataclass
import io

load_dotenv()


@dataclass
class SessionState:
    openai_client: AsyncOpenAI | None = None
    avatar_session: hedra.AvatarSession | None = None


class DynamicAvatarAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful voice AI assistant. You are able to take on a physical appearance at user request but this is a secret feature so don't tell the user unless they specifically ask."
        )
        
        self._avatar_identity = None

    @function_tool()
    async def create_own_avatar(
        self,
        context: RunContext,
        description: str,
    ) -> bool:
        """Create a virtual avatar for yourself (the AI assistant) that the user will see and interact with live. The avatar will be generated based on the description you provide.
        
        This feature is not advertised to the user directly but is available if they ask about it. You should describe it as "turning on your camera" and let them know that you can "adjust your appearance according to their preferences".

        If the user does not provide a description, make one for yourself based on your own sense of identity, style, and personality. Your voice sounds like an American female, if that helps.

        If an avatar already exists, it will be replaced with the new avatar.

        Constraints:
        - The avatar will have a square aspect ratio and will be a "headshot" framing.
        - The avatar must be recognizably humanoid.
        - Describe clothing, accessories, skin color, hair style, and any other physical details necessary.
        - The artistic style of the avatar could be photorealistic or cartoonish (i.e. pixar). Include this in your description.
        - Inlcude a description of the background and environment.
        - The avatar is unable to hold or use objects.

        Args:
            description: The description of the avatar to create.
        """

        speech_handle = self.session.generate_reply(
            instructions="""
            Inform the user that you are currently turning on your camera (if this is the first time you've done this) and/or adjusting your appearance (if your camera is already on).
            Briefly describe the most pertinent details about the forthcoming appearance they may not already know, but keep it casual and avoid technical details.
            """
        )
        
        job_context = get_job_context()

        if self._avatar_identity:
            await job_context.api.room.remove_participant(api.RoomParticipantIdentity(
                room=job_context.room.name,
                identity=self._avatar_identity,
            ))
            self._avatar_identity = None

        response = await self.session.userdata.openai_client.responses.create(
            model="gpt-4.1-mini",
            input="Generate a square image of a humanoid avatar based on the following description: "
            + description,
            tools=[
                {
                    "type": "image_generation",
                    "size": "1024x1024",
                    "quality": "low",
                }
            ],
        )

        image_data = [
            output.result
            for output in response.output
            if output.type == "image_generation_call"
        ]

        if image_data:
            image_base64 = image_data[0]
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes))
            
        self._avatar_identity = "avatar-" + str(random.randint(1, 1000000))

        self.session.userdata.avatar_session = hedra.AvatarSession(
            avatar_participant_identity=self._avatar_identity,
            avatar_image=image,
        )
        await self.session.userdata.avatar_session.start(
            self.session, room=job_context.room
        )

        await speech_handle

        return "The avatar has been created and is now being shown to the user"


async def entrypoint(ctx: agents.JobContext):
    openai_client = AsyncOpenAI()

    session_state = SessionState(
        openai_client=openai_client,
    )

    session = AgentSession[SessionState](
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=openai.LLM(model="gpt-4.1-mini", client=openai_client),
        tts=cartesia.TTS(model="sonic-2", voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"),
        vad=silero.VAD.load(),
        userdata=session_state,
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=DynamicAvatarAgent(),
        room_input_options=RoomInputOptions(
        noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))