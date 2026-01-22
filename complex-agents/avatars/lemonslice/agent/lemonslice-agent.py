import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

from livekit.agents import Agent, AgentServer, AgentSession, AutoSubscribe, JobContext, cli, inference, room_io
from livekit.agents.llm import function_tool
from livekit.agents.voice import RunContext
from livekit.plugins import lemonslice

from utils import load_prompt

logger = logging.getLogger("lemonslice-salary-coach")
logger.setLevel(logging.INFO)

load_dotenv('.env.local')

server = AgentServer()


@dataclass
class BossConfig:
    """Configuration for each boss type including voice and avatar settings."""
    voice_id: str
    avatar_image_url: str
    avatar_prompt: str


# Boss configurations with unique voices and avatars
BOSS_CONFIGS = {
    "easy": BossConfig(
        voice_id="f786b574-daa5-4673-aa0c-cbe3e8534c02",  # Katie - warm, supportive female
        avatar_image_url=os.getenv("EASY_BOSS_IMAGE_URL", "https://iili.io/frL9tuj.png"),
        avatar_prompt="Be warm and encouraging in your movements. Use open gestures and smile naturally. Show genuine interest and supportiveness through body language.",
    ),
    "medium": BossConfig(
        voice_id="228fca29-3a0a-435c-8728-5cb483251068",  # Kiefer - professional, measured male
        avatar_image_url=os.getenv("MEDIUM_BOSS_IMAGE_URL", "https://iili.io/frL9L8u.png"),
        avatar_prompt="Be professional and thoughtful in your movements. Use controlled gestures. Show engagement through body language.",
    ),
    "hard": BossConfig(
        voice_id="66c6b81c-ddb7-4892-bdd5-19b5a7be38e7",  # Dorothy - confident, direct female
        avatar_image_url=os.getenv("HARD_BOSS_IMAGE_URL", "https://iili.io/frL9Qyb.png"),
        avatar_prompt="Be direct and professional in your movements. Use controlled gestures. Show confidence through body language.",
    ),
}


@dataclass
class UserData:
    """Stores session state for the salary negotiation practice."""
    ctx: Optional[JobContext] = None
    boss_type: str = "easy"
    mode: str = "roleplay"  # "coaching" or "roleplay"
    session_start_time: float = 0.0
    roleplay_start_time: float = 0.0
    negotiation_phase: str = "intro"  # "intro", "ask", "objection", "closing"
    coaching_requests: int = 0
    conversation_highlights: list[str] = field(default_factory=list)
    timer_task: Optional[asyncio.Task] = None
    session_ended: bool = False

    def summarize(self) -> str:
        return f"Salary negotiation practice. Difficulty: {self.boss_type}. Mode: {self.mode}"


RunContext_T = RunContext[UserData]


class BaseBossAgent(Agent):
    """Base class for all boss agents with coaching functionality."""
    
    def __init__(self, instructions: str, tts: inference.TTS) -> None:
        super().__init__(
            instructions=instructions,
            stt=inference.STT("deepgram/nova-3"),
            llm=inference.LLM("google/gemini-2.5-flash"),
            tts=tts,
        )

    async def on_enter(self) -> None:
        """Called when the agent first starts."""
        agent_name = self.__class__.__name__
        logger.info(f"Starting {agent_name}")

        userdata: UserData = self.session.userdata
        if userdata.ctx and userdata.ctx.room:
            await userdata.ctx.room.local_participant.set_attributes({
                "agent": agent_name,
                "mode": userdata.mode
            })

        # Start in roleplay mode
        userdata.mode = "roleplay"
        userdata.roleplay_start_time = time.time()
        
        # Start the 3-minute timer if not already started
        # Timer is None on first run, or done() if it completed/cancelled
        if userdata.timer_task is None or userdata.timer_task.done():
            userdata.timer_task = asyncio.create_task(
                self._start_session_timer(userdata, 180) 
            )

    async def on_exit(self) -> None:
        """Called when the agent session ends (disconnect or completion)."""
        userdata: UserData = self.session.userdata
        
        # Cancel timer if still running
        if userdata.timer_task and not userdata.timer_task.done():
            userdata.timer_task.cancel()
            logger.info("Session timer cancelled on exit")
        
        # Log session stats
        session_duration = time.time() - userdata.session_start_time
        logger.info(
            f"Session ended - Boss: {userdata.boss_type}, "
            f"Duration: {session_duration:.1f}s, "
            f"Coaching requests: {userdata.coaching_requests}, "
            f"Phase: {userdata.negotiation_phase}"
        )

    @function_tool()
    async def how_am_i_doing(self, context: RunContext_T) -> str:
        """User is asking for coaching feedback on their negotiation performance."""
        userdata = context.userdata
        userdata.mode = "coaching"
        userdata.coaching_requests += 1
        
        logger.info(f"Entering coaching mode (request #{userdata.coaching_requests})")
        
        # Update room attributes
        if userdata.ctx and userdata.ctx.room:
            await userdata.ctx.room.local_participant.set_attributes({
                "mode": "coaching"
            })
        
        # Update instructions to activate coaching mode
        await self.update_instructions(
            f"{self.instructions}\n\nIMPORTANT: You are now in COACHING MODE. Break character from the boss role completely and provide honest, specific feedback on their negotiation performance so far. Speak naturally using complete sentences and paragraphs. Do not use markdown, bullet points, headings, emojis, or symbols. After giving feedback, tell them you'll switch back to the boss role when they're ready, and then call the return_to_roleplay function to actually switch back to roleplay mode."
        )
        
        return "Switching to coaching mode to provide feedback."

    @function_tool()
    async def return_to_roleplay(self, context: RunContext_T) -> str:
        """Return from coaching mode back to the boss role-play."""
        userdata = context.userdata
        userdata.mode = "roleplay"
        
        logger.info("Returning to roleplay mode")
        
        # Update room attributes
        if userdata.ctx and userdata.ctx.room:
            await userdata.ctx.room.local_participant.set_attributes({
                "mode": "roleplay"
            })
        
        # Restore original boss instructions
        await self.update_instructions(self.instructions)
        
        return "Returning to boss role-play mode."

    async def _start_session_timer(self, userdata: UserData, duration: int):
        """Timer that ends the session after specified duration."""
        try:
            await asyncio.sleep(duration)
            if not userdata.session_ended:
                userdata.session_ended = True
                logger.info("Session timer expired - ending session")
                
                await self.session.say(
                    "Our practice session time is up. I hope you have a great day."
                )
                
                # Give time for the speech to be queued and start playing
                await asyncio.sleep(2.0)
                
                # Shutdown the job context to end the session
                if userdata.ctx:
                    userdata.ctx.shutdown("Session timer expired")
        except asyncio.CancelledError:
            logger.info("Session timer cancelled (user disconnected early)")
            # Don't re-raise - this is expected behavior
        except Exception as e:
            logger.error(f"Error in session timer: {e}")


class EasyBossAgent(BaseBossAgent):
    """The Encourager - supportive, friendly boss who can also coach."""
    
    def __init__(self) -> None:
        config = BOSS_CONFIGS["easy"]
        super().__init__(
            instructions=load_prompt('easy_boss_prompt.yaml'),
            tts=inference.TTS("cartesia/sonic-3", voice=config.voice_id)
        )

    async def on_enter(self) -> None:
        """Called when entering the easy boss session."""
        await super().on_enter()
        self.session.generate_reply(
            instructions="Warmly greet the user as their supportive boss. Start the salary discussion meeting naturally. Keep it brief and welcoming."
        )


class MediumBossAgent(BaseBossAgent):
    """The Skeptic - fair but demanding boss who can also coach."""
    
    def __init__(self) -> None:
        config = BOSS_CONFIGS["medium"]
        super().__init__(
            instructions=load_prompt('medium_boss_prompt.yaml'),
            tts=inference.TTS("cartesia/sonic-3", voice=config.voice_id)
        )

    async def on_enter(self) -> None:
        """Called when entering the medium boss session."""
        await super().on_enter()
        self.session.generate_reply(
            instructions="Greet the user professionally as their skeptical boss. Ask what this meeting is about in a business-like manner."
        )


class HardBossAgent(BaseBossAgent):
    """The Busy Executive - impatient, difficult boss who can also coach."""
    
    def __init__(self) -> None:
        config = BOSS_CONFIGS["hard"]
        super().__init__(
            instructions=load_prompt('hard_boss_prompt.yaml'),
            tts=inference.TTS("cartesia/sonic-3", voice=config.voice_id)
        )

    async def on_enter(self) -> None:
        """Called when entering the hard boss session."""
        await super().on_enter()
        
        # Add transcript callback to log what the LLM generates
        def log_agent_speech(text: str):
            logger.info(f"HARD BOSS LLM OUTPUT: '{text}'")
        
        self.session.on("agent_speech_committed", log_agent_speech)
        
        self.session.generate_reply(
            instructions="Greet the user dismissively as their impatient executive boss. Let them know you only have a few minutes. Use complete sentences."
        )


@server.rtc_session(agent_name="lemonslice-salary-coach")
async def entrypoint(ctx: JobContext):
    """Main entry point for the salary negotiation coach."""
    logger.info("Starting salary negotiation coach session")
    
    # Connect to the room first
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Wait for participant to connect
    participant = await ctx.wait_for_participant()
    
    # Get boss type from participant attributes (default to "easy")
    boss_type = participant.attributes.get("boss_type", "easy")
    logger.info(f"Boss type selected: {boss_type}")
    
    # Validate boss type
    if boss_type not in ["easy", "medium", "hard"]:
        logger.warning(f"Invalid boss type '{boss_type}', defaulting to 'easy'")
        boss_type = "easy"
    
    # Get boss configuration for avatar and voice
    boss_config = BOSS_CONFIGS[boss_type]
    
    # Initialize user data
    userdata = UserData(
        ctx=ctx,
        boss_type=boss_type,
        session_start_time=time.time()
    )
    
    # Create the appropriate boss agent
    if boss_type == "easy":
        boss_agent = EasyBossAgent()
    elif boss_type == "medium":
        boss_agent = MediumBossAgent()
    else:  # hard
        boss_agent = HardBossAgent()
    
    # Create session with userdata
    session = AgentSession[UserData](
        stt=inference.STT("deepgram/nova-3"),
        llm=inference.LLM("google/gemini-2.5-flash"),
        tts=inference.TTS("cartesia/sonic-3", voice=boss_config.voice_id),
        resume_false_interruption=False,
        userdata=userdata
    )
    
    # Start lemonslice avatar with boss-specific image and prompt
    avatar = lemonslice.AvatarSession(
        agent_image_url=boss_config.avatar_image_url,
        agent_prompt=boss_config.avatar_prompt,
    )
    await avatar.start(session, room=ctx.room)
    
    # Start directly with the selected boss agent
    await session.start(
        agent=boss_agent,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            delete_room_on_close=True,
        ),
    )


if __name__ == "__main__":
    cli.run_app(server)
