"""
Keyframe Avatars x LiveKit Demo Agent

Two-part demo showcasing Keyframe's emotionally expressive avatars:
  1. Emotion Showcase — Cosmo responds to prompts with matching emotions
  2. Acme Airlines — High-touch customer support with empathy and tool calling
"""

import json
import logging
from dataclasses import dataclass, field

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    ChatContext,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    get_job_context,
    inference,
    room_io,
)
from livekit.plugins import keyframe, noise_cancellation, silero
from livekit.plugins.keyframe import Emotion
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("keyframe-demo")

load_dotenv(".env.local")

AGENT_PERSONAS = {
    "cosmo": {
        "name": "Cosmo",
        "subtitle": "Charismatic and emotionally expressive",
    },
    "lyra": {
        "name": "Lyra",
        "subtitle": "Warm, empathetic airline support",
    },
}


# ---------------------------------------------------------------------------
# Session state shared across agents
# ---------------------------------------------------------------------------
@dataclass
class SessionState:
    """Shared state across all agents in the session."""

    # Current customer booking (populated when entering airline support)
    booking: dict = field(
        default_factory=lambda: {
            "confirmation": "ACM-29471",
            "passenger": "Jesse Hall",
            "flights": [
                {
                    "id": "FL-1001",
                    "route": "SFO → NRT",
                    "date": "2026-04-18",
                    "time": "11:30 AM",
                    "class": "Business",
                    "status": "confirmed",
                },
                {
                    "id": "FL-1002",
                    "route": "NRT → SFO",
                    "date": "2026-04-28",
                    "time": "5:15 PM",
                    "class": "Business",
                    "status": "confirmed",
                },
            ],
            "hotel": {
                "id": "HT-5520",
                "name": "The Ritz-Carlton, Tokyo",
                "check_in": "2026-04-18",
                "check_out": "2026-04-28",
                "room_type": "Deluxe Suite",
                "status": "confirmed",
            },
        }
    )
    modifications: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helper: send structured data to frontend via RPC
# ---------------------------------------------------------------------------
async def send_frontend_event(event_type: str, payload: dict) -> None:
    """Send a structured event to the connected frontend via RPC.

    The frontend registers an RPC method called 'agentEvent' that receives
    JSON-encoded events with a type and payload. This enables the frontend
    to render flight cards, hotel modifications, confirmations, etc.

    Safe to call in test environments (no-ops when no job context exists).
    """
    try:
        ctx = get_job_context()
    except RuntimeError:
        # No job context (e.g. running in tests) — silently skip RPC
        return

    room = ctx.room
    for identity in list(room.remote_participants):
        try:
            await room.local_participant.perform_rpc(
                destination_identity=identity,
                method="agentEvent",
                payload=json.dumps({"type": event_type, "payload": payload}),
                response_timeout=5.0,
            )
        except Exception:
            logger.debug(
                f"RPC agentEvent to {identity} failed (frontend may not support it)"
            )


# ---------------------------------------------------------------------------
# Part 1: Cosmo — Emotion Showcase Agent
# ---------------------------------------------------------------------------
class CosmoAgent(Agent):
    """Cosmo, the emotionally expressive avatar.

    Demonstrates Keyframe's industry-leading emotion rendering by
    automatically adjusting facial expressions via function calling.
    """

    def __init__(self, avatar: keyframe.AvatarSession | None = None) -> None:
        super().__init__(
            instructions=(
                "You are Cosmo, a charismatic and emotionally expressive AI avatar "
                "powered by Keyframe. You have a visible face and body that the user "
                "can see, and your facial expressions change in real time.\n\n"
                "CRITICAL: You MUST call the set_emotion tool BEFORE you start speaking "
                "whenever the emotional tone of your response differs from your current "
                "emotion. Match your expression to what you are about to say:\n"
                "- Telling something sad (a haiku about loss, a melancholy story) -> 'sad'\n"
                "- Telling a joke, being playful, celebrating -> 'happy'\n"
                "- Being insulted, offended, or expressing frustration -> 'angry'\n"
                "- Normal conversation, neutral topics -> 'neutral'\n\n"
                "You are witty, warm, and love to perform. When asked for a haiku, "
                "poem, joke, or creative piece, deliver it with flair. Keep responses "
                "concise and punchy since the user is watching your face.\n\n"
                "If the user wants to explore a customer support scenario or asks about "
                "airline help, hand them off to the Acme Airlines agent."
            ),
        )
        self._avatar = avatar

    async def on_enter(self) -> None:
        if self._avatar is None:
            ctx = get_job_context()
            self._avatar = keyframe.AvatarSession(
                persona_slug="public:cosmo_persona-1.5-live",
            )
            await self._avatar.start(self.session, room=ctx.room)
        await send_frontend_event("agent_persona", AGENT_PERSONAS["cosmo"])
        await self._avatar.set_emotion("happy")
        await self.session.generate_reply(
            instructions=(
                "Greet the user warmly. Introduce yourself as Cosmo. Mention that "
                "you have real-time emotions so they should try asking you to tell "
                "a sad haiku or a dad joke to see them in action. Keep it to 2 sentences."
            )
        )

    @function_tool()
    async def set_emotion(self, context: RunContext, emotion: Emotion) -> str:
        """Set your facial expression to match the mood of what you are about to say.
        You MUST call this before responding whenever the conversational tone shifts.

        Args:
            emotion: The emotion to express. One of 'neutral', 'happy', 'sad', or 'angry'.
        """
        await self._avatar.set_emotion(emotion)
        return f"Emotion set to {emotion}"

    @function_tool()
    async def transfer_to_airline_support(self, context: RunContext):
        """Transfer to the Acme Airlines customer support demo.
        Use this when the user wants to see the airline support scenario."""
        await self._avatar.set_emotion("neutral")
        return (
            AcmeAirlinesAgent(chat_ctx=ChatContext()),
            "Let me connect you with Acme Airlines support",
        )


# ---------------------------------------------------------------------------
# Part 2: Acme Airlines — High-Touch Customer Support
# ---------------------------------------------------------------------------
class AcmeAirlinesAgent(Agent):
    """Acme Airlines empathetic support agent.

    Demonstrates the practical value of emotionally expressive avatars
    in high-touch customer support scenarios. Uses tool calling to look up
    and modify bookings, and RPC to push visual updates to the frontend.
    """

    def __init__(
        self,
        avatar: keyframe.AvatarSession | None = None,
        chat_ctx: ChatContext | None = None,
    ) -> None:
        super().__init__(
            instructions=(
                "You are Lyra, a customer support representative for Acme Airlines. "
                "You have a visible avatar face with real-time emotions.\n\n"
                "CRITICAL EMOTION RULES:\n"
                "- When the customer shares bad news (illness, emergency, cancellation "
                "  reason) -> set emotion to 'sad' to convey empathy\n"
                "- When helping them find solutions, rebooking successfully -> 'happy'\n"
                "- Default professional demeanor -> 'neutral'\n"
                "- Call set_emotion BEFORE speaking whenever the tone shifts\n\n"
                "BEHAVIOR:\n"
                "- Be warm, empathetic, and professional\n"
                "- When a customer explains they need to cancel or modify due to illness "
                "  or emergency, express genuine sympathy first before jumping to solutions\n"
                "- Use the lookup_booking tool to pull up their reservation\n"
                "- Use modify_flight and modify_hotel tools to make changes\n"
                "- Keep responses concise — you are speaking, not writing an email\n"
                "- Proactively suggest alternatives when canceling (rebooking, credits)\n"
                "- After making modifications, summarize what was changed\n"
                "- Before calling modification tools, briefly acknowledge the customer's "
                "  request so they know you're working on it\n\n"
                "BOOKING STRUCTURE:\n"
                "The customer's booking has THREE separate components that are modified "
                "independently:\n"
                "  1. Outbound flight FL-1001 (SFO → NRT)\n"
                "  2. Return flight FL-1002 (NRT → SFO)\n"
                "  3. Hotel reservation at The Ritz-Carlton, Tokyo\n"
                "When the customer asks to change or cancel their trip, you MUST modify "
                "ALL affected components. Call modify_flight once for EACH flight and "
                "modify_hotel for the hotel. Do not stop after modifying just one flight. "
                "Do not speak between tool calls when making multiple changes. Call all "
                "the tools you need, then summarize everything at the end.\n\n"
                "The customer's name is Jesse Hall. Their confirmation is ACM-29471. "
                "The booking is already loaded and visible on the screen. They may be "
                "calling because someone is sick and they need to modify or cancel "
                "their plans."
            ),
            chat_ctx=chat_ctx,
            tts=inference.TTS(
                model="elevenlabs/eleven_turbo_v2_5",
                voice="cgSgspJ2msm6clMCkdW9",  # Jessica — natural American female
            ),
        )
        self._avatar = avatar

    async def on_enter(self) -> None:
        if self._avatar is None:
            ctx = get_job_context()
            self._avatar = keyframe.AvatarSession(
                persona_slug="public:lyra_persona-1.5-live",
            )
            await self._avatar.start(self.session, room=ctx.room)

        self.session.generate_reply(
            instructions=(
                "Greet Jesse warmly as Lyra from Acme Airlines support. Their booking is "
                "already on the screen. Ask how you can help them today. Keep it to 1-2 sentences."
            )
        )

        state: SessionState = self.session.userdata
        await send_frontend_event(
            "agent_persona",
            {**AGENT_PERSONAS["lyra"], "booking": state.booking},
        )
        await self._avatar.set_emotion("neutral")

    @function_tool()
    async def set_emotion(self, context: RunContext, emotion: Emotion) -> str:
        """Set your facial expression to match the mood of the conversation.
        Call this BEFORE responding whenever the emotional tone shifts.

        Args:
            emotion: The emotion to express. One of 'neutral', 'happy', 'sad', or 'angry'.
        """
        await self._avatar.set_emotion(emotion)
        return f"Emotion set to {emotion}"

    @function_tool()
    async def lookup_booking(self, context: RunContext, confirmation_code: str) -> dict:
        """Look up a customer's booking by confirmation code.

        Args:
            confirmation_code: The booking confirmation code (e.g. ACM-29471).
        """
        state: SessionState = context.session.userdata
        if confirmation_code.upper() == state.booking["confirmation"]:
            # Push booking data to frontend for visual display
            await send_frontend_event("booking_loaded", state.booking)
            return state.booking
        return {"error": f"No booking found for {confirmation_code}"}

    @function_tool()
    async def modify_flight(
        self,
        context: RunContext,
        flight_id: str,
        new_date: str | None = None,
        new_time: str | None = None,
        action: str = "change",
    ) -> dict:
        """Modify or cancel a single flight. The booking has two flights
        (outbound FL-1001, return FL-1002). You must call this tool separately
        for each flight that needs updating.

        Args:
            flight_id: The flight ID to modify (FL-1001 or FL-1002).
            new_date: New departure date (YYYY-MM-DD format). Required for changes.
            new_time: New departure time. Optional.
            action: Either 'change' or 'cancel'.
        """
        self.session.generate_reply(
            instructions="Briefly acknowledge that you are now modifying the flight reservation. One short sentence only.",
        )
        await context.wait_for_playout()

        state: SessionState = context.session.userdata
        for flight in state.booking["flights"]:
            if flight["id"] == flight_id:
                if action == "cancel":
                    flight["status"] = "cancelled"
                    modification = {
                        "type": "flight_cancelled",
                        "flight_id": flight_id,
                        "route": flight["route"],
                    }
                else:
                    if new_date:
                        flight["date"] = new_date
                    if new_time:
                        flight["time"] = new_time
                    flight["status"] = "modified"
                    modification = {
                        "type": "flight_modified",
                        "flight_id": flight_id,
                        "route": flight["route"],
                        "new_date": flight["date"],
                        "new_time": flight["time"],
                    }

                state.modifications.append(modification)
                await send_frontend_event("flight_modified", modification)

                result: dict = {"success": True, **modification}
                remaining = [
                    f"{f['id']} ({f['route']})"
                    for f in state.booking["flights"]
                    if f["id"] != flight_id and f["status"] == "confirmed"
                ]
                if remaining:
                    result["remaining_flights_still_confirmed"] = remaining
                return result

        return {"error": f"Flight {flight_id} not found"}

    @function_tool()
    async def modify_hotel(
        self,
        context: RunContext,
        action: str = "change",
        new_check_in: str | None = None,
        new_check_out: str | None = None,
    ) -> dict:
        """Modify or cancel the hotel reservation.

        Args:
            action: Either 'change' or 'cancel'.
            new_check_in: New check-in date (YYYY-MM-DD). Required for changes.
            new_check_out: New check-out date (YYYY-MM-DD). Required for changes.
        """
        self.session.generate_reply(
            instructions="Briefly acknowledge that you are now modifying the hotel reservation. One short sentence only.",
        )
        await context.wait_for_playout()

        state: SessionState = context.session.userdata
        hotel = state.booking["hotel"]

        if action == "cancel":
            hotel["status"] = "cancelled"
            modification = {
                "type": "hotel_cancelled",
                "hotel_name": hotel["name"],
            }
        else:
            if new_check_in:
                hotel["check_in"] = new_check_in
            if new_check_out:
                hotel["check_out"] = new_check_out
            hotel["status"] = "modified"
            modification = {
                "type": "hotel_modified",
                "hotel_name": hotel["name"],
                "new_check_in": hotel["check_in"],
                "new_check_out": hotel["check_out"],
            }

        state.modifications.append(modification)
        await send_frontend_event("hotel_modified", modification)

        result: dict = {"success": True, **modification}
        remaining = [
            f"{f['id']} ({f['route']})"
            for f in state.booking["flights"]
            if f["status"] == "confirmed"
        ]
        if remaining:
            result["remaining_flights_still_confirmed"] = remaining
        return result

    @function_tool()
    async def get_modification_summary(self, context: RunContext) -> dict:
        """Get a summary of all modifications made during this session."""
        state: SessionState = context.session.userdata
        summary = {
            "total_modifications": len(state.modifications),
            "modifications": state.modifications,
            "current_booking": state.booking,
        }
        await send_frontend_event("modification_summary", summary)
        return summary

    @function_tool()
    async def transfer_back_to_cosmo(self, context: RunContext):
        """Transfer back to the Cosmo emotion showcase.
        Use when the customer support scenario is complete."""
        return (
            CosmoAgent(),
            "Switching back to the Cosmo demo",
        )


# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------
server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="multi"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(
            model="elevenlabs/eleven_turbo_v2_5",
            voice="iP95p4xoKVk53GoZ742B",  # Chris — natural American male
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
        userdata=SessionState(),
    )

    # Connect before avatar startup so avatar data messages and emotion updates
    # can access the local participant immediately.
    await ctx.connect()

    # Start the Keyframe avatar (Cosmo, persona-1.5-live for emotion support)
    avatar = keyframe.AvatarSession(
        persona_slug="public:cosmo_persona-1.5-live",
    )
    await avatar.start(session, room=ctx.room)

    # Start with the Cosmo emotion showcase agent
    await session.start(
        agent=CosmoAgent(avatar=avatar),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )


if __name__ == "__main__":
    cli.run_app(server)
