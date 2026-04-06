from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from dotenv import load_dotenv
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli, inference
from livekit.agents.beta.workflows.dtmf_inputs import GetDtmfTask
from livekit.agents.llm.tool_context import ToolError
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("ivr-agent")
load_dotenv()


# ---------------------------------------------------------------------------
# IVR tree definition
# ---------------------------------------------------------------------------


ActionFn = Callable[[], Awaitable[str]]
BACK_KEY = "0"


@dataclass
class Menu:
    """A node in the IVR tree. Each option maps a digit to a submenu or an async action."""

    prompt: str
    options: dict[str, Menu | ActionFn]


# ---------------------------------------------------------------------------
# Leaf actions — this is where API calls, DB lookups, etc. would go
# ---------------------------------------------------------------------------


async def check_balance() -> str:
    return "Your current balance is $127.50, due on April 15th."


async def make_payment() -> str:
    return "Transferring you to our secure payment system now."


async def recent_charges() -> str:
    return "Your most recent charge was $49.99 on March 28th for your monthly plan."


async def restart_modem() -> str:
    return "We're sending a restart signal to your modem now. It may take up to 2 minutes."


async def run_speed_test() -> str:
    return "Your current download speed is 85 Mbps and upload is 12 Mbps. This is within normal range."


async def report_outage() -> str:
    return "We've logged an outage report for your area. A technician will investigate within 4 hours."


async def voicemail_setup() -> str:
    return "We're resetting your voicemail box now. You'll receive a text with setup instructions."


async def call_forwarding() -> str:
    return "Call forwarding has been toggled on your account. Check your settings for details."


async def report_dropped_calls() -> str:
    return "We've opened a ticket for dropped calls on your line. A specialist will follow up within 24 hours."


async def equipment_support() -> str:
    return "We'll ship replacement equipment within 2 business days."


async def connect_to_sales() -> str:
    return "A sales representative will be with you shortly. Please hold."


# ---------------------------------------------------------------------------
# IVR tree
# ---------------------------------------------------------------------------

ivr_tree = Menu(
    prompt="For billing, press 1. For technical support, press 2. For sales, press 3.",
    options={
        "1": Menu(
            prompt=(
                "To check your balance, press 1. "
                "To make a payment, press 2. "
                "To review recent charges, press 3."
            ),
            options={
                "1": check_balance,
                "2": make_payment,
                "3": recent_charges,
            },
        ),
        "2": Menu(
            prompt=(
                "For internet issues, press 1. "
                "For phone service, press 2. "
                "For equipment support, press 3."
            ),
            options={
                "1": Menu(
                    prompt=(
                        "To restart your modem remotely, press 1. "
                        "To run a speed test, press 2. "
                        "To report an outage, press 3."
                    ),
                    options={
                        "1": restart_modem,
                        "2": run_speed_test,
                        "3": report_outage,
                    },
                ),
                "2": Menu(
                    prompt=(
                        "For voicemail setup, press 1. "
                        "For call forwarding, press 2. "
                        "To report dropped calls, press 3."
                    ),
                    options={
                        "1": voicemail_setup,
                        "2": call_forwarding,
                        "3": report_dropped_calls,
                    },
                ),
                "3": equipment_support,
            },
        ),
        "3": connect_to_sales,
    },
)


class IVRAgent(Agent):
    def __init__(self, menu: Menu) -> None:
        super().__init__(
            instructions=(
                "You are an automated phone system for Horizon Wireless. "
                "Keep responses brief and professional. Only relay the menu "
                "options and messages you are given."
            ),
        )
        self.menu = menu

    async def on_enter(self) -> None:
        self.session.generate_reply(
            instructions="Welcome the caller to Horizon Wireless and let them know you'll help them navigate the menu.",
        )
        while not await self._navigate(self.menu, is_root=True):
            pass
        await self.session.generate_reply(
            instructions="Thank the caller and let them know they can call back anytime.",
            allow_interruptions=False,
        )

    async def _navigate(self, node: Menu, *, is_root: bool = False) -> bool:
        """Walk the IVR tree. Returns True when a leaf action was reached."""
        while True:
            prompt = node.prompt
            if not is_root:
                prompt += f" Or press {BACK_KEY} to go back."

            try:
                result = await GetDtmfTask(
                    num_digits=1,
                    chat_ctx=self.chat_ctx.copy(
                        exclude_instructions=True,
                        exclude_function_call=True,
                        exclude_handoff=True,
                        exclude_config_update=True,
                    ),
                    extra_instructions=prompt,
                )
            except ToolError as e:
                await self.session.generate_reply(
                    instructions=e.message, allow_interruptions=False
                )
                continue

            if result.user_input == BACK_KEY:
                return False

            choice = node.options.get(result.user_input)
            if choice is None:
                await self.session.generate_reply(
                    instructions="That wasn't a valid option. Please try again.",
                    allow_interruptions=False,
                )
                continue

            if isinstance(choice, Menu):
                if await self._navigate(choice):
                    return True
                continue  # child went back, re-prompt this level

            message = await choice()
            await self.session.generate_reply(
                instructions=message, allow_interruptions=False
            )
            return True


server = AgentServer()


@server.rtc_session(agent_name="my-telephony-agent")
async def entrypoint(ctx: JobContext) -> None:
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        vad=silero.VAD.load(),
        llm=inference.LLM("openai/gpt-4.1-mini"),
        stt=inference.STT("deepgram/nova-3"),
        tts=inference.TTS("cartesia/sonic-3"),
        turn_detection=MultilingualModel(),
    )

    await session.start(agent=IVRAgent(ivr_tree), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
