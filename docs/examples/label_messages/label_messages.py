import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, cli, Agent, AgentSession, AgentServer, inference, ConversationItemAddedEvent
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("label-messages")
logger.setLevel(logging.INFO)

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
    )

    agent = Agent(
        instructions="You are a helpful agent. When the user speaks, you listen and respond.",
    )

    @session.on("conversation_item_added")
    def conversation_item_added(item: ConversationItemAddedEvent):
        print(item)

    @session.on("session_start")
    def on_session_start():
        session.generate_reply()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
