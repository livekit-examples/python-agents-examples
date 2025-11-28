import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, cli, Agent, AgentSession, AgentServer, inference
from livekit.plugins import openai, google, deepgram, silero

load_dotenv()

logger = logging.getLogger("google_llm")
logger.setLevel(logging.INFO)

# Load book text once
book_path = Path(__file__).parent / "lib" / "war_and_peace.txt"
try:
    with open(book_path, "r", encoding="utf-8") as f:
        war_and_peace_text = f.read()
except FileNotFoundError:
    logger.error(f"Could not find book at {book_path}")
    war_and_peace_text = "War and Peace text not found."

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=deepgram.STT(),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=openai.TTS(instructions="You are a literary discussion assistant with a pleasant voice. Speak in a natural, conversational tone that conveys enthusiasm for literature."),
        vad=ctx.proc.userdata["vad"],
    )
    
    agent = Agent(
        instructions=f"""
            You are a War and Peace book club assistant. You help users discuss and understand Leo Tolstoy's novel "War and Peace."

            You can answer questions about the plot, characters, themes, historical context, and literary analysis of the book.

            Here is the complete text of the book that you can reference:

            {war_and_peace_text}

            Be concise but informative in your responses. If asked about specific passages, quote directly from the text.
        """,
    )
    
    @session.on("session_start")
    def on_session_start():
        session.generate_reply("Welcome to the War and Peace book club! I'm here to discuss Leo Tolstoy's epic novel with you. What would you like to talk about?")

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
