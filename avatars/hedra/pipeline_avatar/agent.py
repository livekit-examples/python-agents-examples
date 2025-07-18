from dotenv import load_dotenv

from livekit import agents
from livekit.agents import (
    AgentSession,
    Agent,
    RoomInputOptions,
    get_job_context,
)
from livekit.plugins import (
    openai,
    inworld,
    deepgram,
    noise_cancellation,
    silero,
    hedra,
)

from livekit.plugins.turn_detector.multilingual import MultilingualModel
from PIL import Image
from dataclasses import dataclass
import os

load_dotenv()


@dataclass
class SessionState:
    avatar_session: hedra.AvatarSession | None = None


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
    
    session_state = SessionState()
    
    job_context = get_job_context()
    avatar_identity = "static-avatar"
    session_state.avatar_session = hedra.AvatarSession(
        avatar_participant_identity=avatar_identity,
        avatar_image=avatar_image,
    )

    session = AgentSession[SessionState](
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=openai.LLM(),
        tts=inworld.TTS(voice="Alex"),
        vad=silero.VAD.load(),
        userdata=session_state,
        turn_detection=MultilingualModel(),
    )
    
    await session_state.avatar_session.start(
        session, room=job_context.room
    )

    await session.start(
        room=ctx.room,
        agent=StaticAvatarAgent(),
        room_input_options=RoomInputOptions(
        noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))